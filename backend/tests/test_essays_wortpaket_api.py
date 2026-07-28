"""The two endpoints that expose an essay's word package.

The interesting cases are not the happy path. They are: a package that belongs
to a topic the essay no longer has, a word whose card disappeared between the
build and the read, and the order the model chose — which is the entire value of
the second call and the easiest thing to lose by re-sorting on the way out.
"""
from __future__ import annotations

import pytest
from app.db.models import Essay, EssayWordPackage, UserWordList, VocabCard
from app.vocab import norm, wortpaket
from sqlalchemy import select


@pytest.fixture(autouse=True)
def _no_real_jobs(monkeypatch):
    """The route starts a background build; these tests are about the HTTP
    contract, so record the call instead of spending two model calls."""
    started: list[tuple[int, int]] = []
    import app.api.routes.essays as essays_routes
    monkeypatch.setattr(essays_routes, "start_package_job",
                        lambda pkg_id, user_id: started.append((pkg_id, user_id)))
    wortpaket.reset_catalog_cache()
    yield started
    wortpaket.reset_catalog_cache()


async def _card(session, lemma, ru, *, zipf=4.0, band="C1"):
    session.add(VocabCard(
        lemma=lemma, lemma_norm=norm.fold_de(lemma), lemma_ascii=norm.ascii_de(lemma),
        level="unlisted", band=band, pos="noun", article="die", ru=ru,
        confidence="high", data={"ru_all": [ru]}, zipf=zipf, topic="recht_gesetz",
        source_created_at=0.0,
    ))
    await session.commit()


async def _essay(client, topic="Sollten Smartphones an Schulen verboten werden?"):
    r = await client.post("/api/essays", json={
        "title": "Probe", "text": "", "essay_type": "argumentativ",
        "topic": topic, "level": "B2", "content_json": {}})
    assert r.status_code == 200, r.text
    return r.json()["id"]


# ── POST ─────────────────────────────────────────────────────────────────────

async def test_post_creates_a_pending_package_and_starts_the_build(client, _no_real_jobs):
    essay_id = await _essay(client)
    r = await client.post(f"/api/essays/{essay_id}/wortpaket")
    assert r.status_code == 202
    assert r.json()["status"] == "pending"
    assert len(_no_real_jobs) == 1, "the build was handed to the background"


async def test_post_twice_reuses_the_row_and_clears_the_old_words(client, db_session,
                                                                  _no_real_jobs):
    """A rebuild must not leave the previous topic's words on screen under a
    spinner that claims to be building this one."""
    essay_id = await _essay(client)
    await client.post(f"/api/essays/{essay_id}/wortpaket")
    row = (await db_session.execute(select(EssayWordPackage))).scalar_one()
    row.status, row.lemmas = "ready", ["Verbot"]
    await db_session.commit()

    await client.post(f"/api/essays/{essay_id}/wortpaket")
    rows = (await db_session.execute(select(EssayWordPackage))).scalars().all()
    assert len(rows) == 1, "one package per essay"
    await db_session.refresh(rows[0])
    assert rows[0].status == "pending"
    assert rows[0].lemmas == []


async def test_post_records_the_topic_it_was_built_from(client, db_session, _no_real_jobs):
    essay_id = await _essay(client, topic="Brauchen wir ein Tempolimit?")
    await client.post(f"/api/essays/{essay_id}/wortpaket")
    row = (await db_session.execute(select(EssayWordPackage))).scalar_one()
    assert row.thema == "Brauchen wir ein Tempolimit?"
    assert row.niveau == "B2"


async def test_post_refuses_an_essay_without_a_topic(client, _no_real_jobs):
    essay_id = await _essay(client, topic="   ")
    r = await client.post(f"/api/essays/{essay_id}/wortpaket")
    assert r.status_code == 422


async def test_post_refuses_a_guest(guest_client, _no_real_jobs):
    """Guests may write. The package spends an account's own Mistral key and
    excludes an account's own saved words — neither exists for a guest."""
    r = await guest_client.post("/api/essays", json={
        "title": "g", "text": "", "essay_type": "argumentativ",
        "topic": "Tempolimit", "level": "B1", "content_json": {}})
    essay_id = r.json()["id"]
    assert (await guest_client.post(f"/api/essays/{essay_id}/wortpaket")).status_code == 401


async def test_post_on_someone_elses_essay_is_a_404(client, db_session, _no_real_jobs):
    other = Essay(user_id=99_999, title="not yours", topic="Tempolimit", level="B2")
    db_session.add(other)
    await db_session.commit()
    assert (await client.post(f"/api/essays/{other.id}/wortpaket")).status_code == 404


async def test_post_rejects_an_id_bigger_than_the_key_type(client, _no_real_jobs):
    """The OverflowError class of bug: an unbounded path int reaches the driver
    and answers 500. `DbId` makes it a 422."""
    r = await client.post("/api/essays/9223372036854775808/wortpaket")
    assert r.status_code == 422


# ── GET ──────────────────────────────────────────────────────────────────────

async def test_get_before_any_build_says_none(client, _no_real_jobs):
    essay_id = await _essay(client)
    body = (await client.get(f"/api/essays/{essay_id}/wortpaket")).json()
    assert body["status"] == "none"
    assert body["words"] == []
    assert body["stale"] is False


async def test_get_returns_words_in_the_order_the_model_chose(client, db_session,
                                                              _no_real_jobs):
    """Usefulness for this prompt is what call 2 produced. Re-sorting by
    frequency on the way out would throw it away and look like nothing."""
    await _card(db_session, "Selten", "редкое", zipf=2.6)
    await _card(db_session, "Haeufig", "частое", zipf=5.5)
    essay_id = await _essay(client)
    await client.post(f"/api/essays/{essay_id}/wortpaket")
    row = (await db_session.execute(select(EssayWordPackage))).scalar_one()
    row.status, row.lemmas = "ready", ["Selten", "Haeufig"]
    await db_session.commit()

    body = (await client.get(f"/api/essays/{essay_id}/wortpaket")).json()
    assert [w["lemma"] for w in body["words"]] == ["Selten", "Haeufig"]


async def test_get_marks_saved_words_instead_of_hiding_them(client, db_session,
                                                            _no_real_jobs):
    """A row vanishing under the cursor at the moment it is clicked is how the
    next word gets added by accident."""
    await _card(db_session, "Verbot", "запрет")
    await _card(db_session, "Sucht", "зависимость")
    essay_id = await _essay(client)
    await client.post(f"/api/essays/{essay_id}/wortpaket")
    row = (await db_session.execute(select(EssayWordPackage))).scalar_one()
    row.status, row.lemmas = "ready", ["Verbot", "Sucht"]
    user_id = (await db_session.execute(select(Essay.user_id))).scalars().first()
    db_session.add(UserWordList(user_id=user_id, lemma="Sucht", ru="зависимость"))
    await db_session.commit()

    words = (await client.get(f"/api/essays/{essay_id}/wortpaket")).json()["words"]
    assert {w["lemma"]: w["in_list"] for w in words} == {"Verbot": False, "Sucht": True}


async def test_get_drops_a_word_whose_card_disappeared(client, db_session, _no_real_jobs):
    """Re-enrichment can skip a word or rename it to the 1996 spelling. Shipping
    the row anyway means a card endpoint that 404s on click."""
    await _card(db_session, "Verbot", "запрет")
    essay_id = await _essay(client)
    await client.post(f"/api/essays/{essay_id}/wortpaket")
    row = (await db_session.execute(select(EssayWordPackage))).scalar_one()
    row.status, row.lemmas = "ready", ["Verbot", "Verschwunden"]
    await db_session.commit()

    words = (await client.get(f"/api/essays/{essay_id}/wortpaket")).json()["words"]
    assert [w["lemma"] for w in words] == ["Verbot"]


async def test_get_flags_a_package_built_for_a_different_topic(client, db_session,
                                                              _no_real_jobs):
    essay_id = await _essay(client, topic="Tempolimit auf Autobahnen?")
    await client.post(f"/api/essays/{essay_id}/wortpaket")
    essay = await db_session.get(Essay, essay_id)
    essay.topic = "Sollten Smartphones an Schulen verboten werden?"
    await db_session.commit()

    body = (await client.get(f"/api/essays/{essay_id}/wortpaket")).json()
    assert body["stale"] is True
    assert body["thema"] == "Tempolimit auf Autobahnen?", "the row says what it used"


async def test_get_surfaces_a_failure_with_its_stage(client, db_session, _no_real_jobs):
    essay_id = await _essay(client)
    await client.post(f"/api/essays/{essay_id}/wortpaket")
    row = (await db_session.execute(select(EssayWordPackage))).scalar_one()
    row.status, row.error_message = "failed", "[topics] model named no known topic"
    await db_session.commit()

    body = (await client.get(f"/api/essays/{essay_id}/wortpaket")).json()
    assert body["status"] == "failed"
    assert "[topics]" in body["error"]


async def test_a_long_prompt_survives_the_round_trip(client, _no_real_jobs):
    """`topic` was `varchar(128)`, and Postgres rejects rather than truncates —
    a real exam question failed to save at all."""
    long_topic = (
        "Immer mehr Jugendliche verbringen ihre Freizeit fast ausschliesslich "
        "online. Sollten soziale Medien für Kinder unter 16 Jahren gesetzlich "
        "verboten werden, um sie vor Sucht und Cybermobbing zu schützen?"
    )
    assert len(long_topic) > 128, "shorter than the old column and proves nothing"
    essay_id = await _essay(client, topic=long_topic)
    r = await client.get(f"/api/essays/{essay_id}")
    assert r.json()["topic"] == long_topic

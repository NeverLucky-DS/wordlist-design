"""Wörterbuch: normalization, pg_trgm lookup, replica sync, personal word list.

Everything that touches the database here runs on real Postgres (`pg_*` fixtures)
rather than the SQLite suite: the lookup is built on pg_trgm, and testing it
against a LIKE fallback would prove nothing about what actually ships. The
fixtures skip when no Postgres is reachable.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

import pytest

from app.db.models import UserWordList, VocabCard, VocabCardTranslation
from app.vocab import mirror, norm, search as search_mod


# ── pure normalization ───────────────────────────────────────────────────────
def test_fold_de_substitutes_umlauts_the_orthographic_way():
    assert norm.fold_de("Grün") == "gruen"
    assert norm.fold_de("Straße") == "strasse"
    assert norm.fold_de("Möglichkeit") == "moeglichkeit"


def test_ascii_de_flattens_umlauts():
    assert norm.ascii_de("Grün") == "grun"
    assert norm.ascii_de("Möglichkeit") == "moglichkeit"
    # ß has no bare-vowel form; both folds agree on ss
    assert norm.ascii_de("Straße") == "strasse"


def test_fold_ru_normalises_yo():
    assert norm.fold_ru("Всё") == "все"


def test_detect_lang_by_script():
    assert norm.detect_lang("Fortschritt") == "de"
    assert norm.detect_lang("прогресс") == "ru"
    # a stray Latin character must not flip a Russian query to German
    assert norm.detect_lang("прогресс x") == "ru"


@pytest.mark.parametrize(
    "level,band",
    [("a1", "B1"), ("a2", "B1"), ("b1", "B1"), ("b2", "B2"),
     ("c1", "C1"), ("c2", "C1"), ("unlisted", "C1"), (None, "C1"), ("junk", "C1")],
)
def test_band_clamps_every_level_into_the_brush_set(level, band):
    """No word may end up without a wash — the brush set is B1/B2/C1 only."""
    assert norm.band_of(level) == band


@pytest.mark.parametrize(
    "pos,article,expected",
    [
        ("noun", "der", "der"), ("noun", "die", "die"), ("noun", "das", "das"),
        ("verb", None, "verb"), ("adj", None, "adj"),
        ("adv", None, "adj"),      # adjective/adverb line is thin in German
        ("other", None, "adj"),    # function words have no wash of their own
        # nominalized adjectives (der/die Jugendliche) genuinely have no article
        ("noun", None, "adj"), ("noun", "", "adj"),
    ],
)
def test_type_maps_onto_the_five_brushes(pos, article, expected):
    assert norm.type_of(pos, article) == expected


# ── helpers ──────────────────────────────────────────────────────────────────
async def _add_card(session, lemma, ru, *, ru_all=None, level="b1", pos="noun",
                    article="die", topic="allgemein", created=1.0, zipf=None):
    meanings = ru_all or [ru]
    session.add(VocabCard(
        lemma=lemma,
        lemma_norm=norm.fold_de(lemma),
        lemma_ascii=norm.ascii_de(lemma),
        level=level, band=norm.band_of(level), topic=topic, pos=pos,
        article=article, ru=ru, confidence="high", register="neutral",
        data={"ru_all": meanings, "definition_de": f"{lemma} …", "examples": []},
        zipf=zipf, source_created_at=created,
    ))
    for i, m in enumerate(meanings):
        session.add(VocabCardTranslation(
            lemma=lemma, idx=i, ru=m, ru_norm=norm.fold_ru(m)))
    await session.commit()


def _lemmas(result) -> list[str]:
    return [i["lemma"] for i in result["items"]]


# ── lookup: German side ──────────────────────────────────────────────────────
async def test_search_de_finds_exact_lemma(pg_session):
    await _add_card(pg_session, "Fortschritt", "прогресс", article="der")
    result = await search_mod.search(pg_session, "Fortschritt")
    assert result["lang"] == "de"
    assert _lemmas(result) == ["Fortschritt"]


async def test_search_de_survives_a_typo(pg_session):
    await _add_card(pg_session, "Fortschritt", "прогресс", article="der")
    assert "Fortschritt" in _lemmas(await search_mod.search(pg_session, "fortschrit"))


@pytest.mark.parametrize("typed", ["grün", "gruen", "grun", "GRÜN"])
async def test_search_de_accepts_every_umlaut_spelling(pg_session, typed):
    """The whole reason `lemma_ascii` exists: someone on a keyboard without
    umlauts types "gruen" or "grun", and both must land on grün."""
    await _add_card(pg_session, "grün", "зелёный", level="b1", pos="adj", article=None)
    await _add_card(pg_session, "Grund", "причина", level="b1", article="der")
    result = await search_mod.search(pg_session, typed)
    assert result["items"], f"{typed!r} found nothing"
    assert result["items"][0]["lemma"] == "grün"


async def test_search_de_ranks_exact_above_prefix(pg_session):
    await _add_card(pg_session, "grün", "зелёный", pos="adj", article=None)
    await _add_card(pg_session, "grünen", "зеленеть", pos="verb", article=None)
    assert _lemmas(await search_mod.search(pg_session, "grün"))[0] == "grün"


# ── lookup: Russian side ─────────────────────────────────────────────────────
async def test_search_ru_finds_by_primary_meaning(pg_session):
    await _add_card(pg_session, "Abhängigkeit", "зависимость")
    result = await search_mod.search(pg_session, "зависимость")
    assert result["lang"] == "ru"
    assert _lemmas(result) == ["Abhängigkeit"]


@pytest.mark.parametrize("typed", ["зависимости", "зависимостью", "зависимост"])
async def test_search_ru_survives_inflection(pg_session, typed):
    """No Russian stemmer — trigram similarity carries declension on its own."""
    await _add_card(pg_session, "Abhängigkeit", "зависимость")
    assert "Abhängigkeit" in _lemmas(await search_mod.search(pg_session, typed))


async def test_search_ru_finds_a_secondary_meaning(pg_session):
    """A word must be reachable through any of its `ru_all` meanings, not just
    the headline one."""
    await _add_card(pg_session, "durchziehen", "проходить насквозь",
                    ru_all=["проходить насквозь", "протягивать", "пронизывать"],
                    pos="verb", article=None)
    assert "durchziehen" in _lemmas(await search_mod.search(pg_session, "протягивать"))


async def test_search_ru_prefers_the_card_whose_primary_meaning_matches(pg_session):
    await _add_card(pg_session, "Sucht", "зависимость")
    await _add_card(pg_session, "Nebenwirkung", "побочный эффект",
                    ru_all=["побочный эффект", "зависимость"])
    assert _lemmas(await search_mod.search(pg_session, "зависимость"))[0] == "Sucht"


# ── lookup: the honest miss ──────────────────────────────────────────────────
async def test_search_returns_nothing_for_a_word_we_do_not_have(pg_session):
    """The base is still being enriched, so "not found" is a real answer and
    must not be papered over with unrelated near-matches."""
    await _add_card(pg_session, "Fortschritt", "прогресс", article="der")
    assert await search_mod.search(pg_session, "щщщщщщ") == {
        "lang": "ru", "query": "щщщщщщ", "items": []}


async def test_search_ignores_a_blank_query(pg_session):
    assert (await search_mod.search(pg_session, "   "))["items"] == []


# ── ranking: how common the word is ─────────────────────────────────────────
async def test_search_ru_ranks_the_common_word_first(pg_session):
    """Measured on the live base: "быстрый" answered fix, rasch, prompt, rapide,
    zügig and then schnell — the 354th most common word in German — LAST. Every
    exact hit ties at 2.0, so the order fell to lemma length and the shortest,
    rarest word won."""
    for lemma, zipf in (("fix", 4.02), ("rasch", 4.31), ("prompt", 3.67),
                        ("rapide", 3.45), ("zügig", 3.72), ("schnell", 5.51)):
        await _add_card(pg_session, lemma, "быстрый", pos="adj", article=None,
                        zipf=zipf)
    assert _lemmas(await search_mod.search(pg_session, "быстрый"))[0] == "schnell"


async def test_search_de_ranks_the_common_word_first(pg_session):
    await _add_card(pg_session, "Bank", "банк", article="die", zipf=5.0)
    await _add_card(pg_session, "Bankrott", "банкротство", article="der", zipf=3.0)
    await _add_card(pg_session, "Bankett", "банкет", article="das", zipf=2.5)
    assert _lemmas(await search_mod.search(pg_session, "Bank"))[0] == "Bank"


async def test_search_ranks_cards_without_frequency_last(pg_session):
    await _add_card(pg_session, "Schluss", "конец", article="der", zipf=None)
    await _add_card(pg_session, "Schlusspunkt", "точка", article="der", zipf=3.0)
    # Both are prefix hits; the one with a known frequency must not lose to NULL.
    assert _lemmas(await search_mod.search(pg_session, "Schluss")) == [
        "Schluss", "Schlusspunkt"]   # exact still beats prefix regardless


async def test_search_does_not_let_wildcards_leak_into_like(pg_session):
    await _add_card(pg_session, "Fortschritt", "прогресс", article="der")
    assert (await search_mod.search(pg_session, "%"))["items"] == []


# ── replica sync ─────────────────────────────────────────────────────────────
def _make_enrichment_db(path, rows):
    # Build the source through `ensure_schema` rather than a hand-copied CREATE:
    # the copy silently drifted when `cards.zipf` was added and every mirror test
    # failed on a column the real schema had all along.
    from app.vocab import enrich

    enrich.ensure_schema()
    con = sqlite3.connect(path)
    for r in rows:
        con.execute(
            "INSERT OR REPLACE INTO cards(lemma,level,topic,pos,article,ru,"
            "confidence,register,data,model,prompt_version,schema_version,"
            "enriched_by,created_at,zipf) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (r["lemma"], r.get("level", "b1"), r.get("topic", "allgemein"),
             r.get("pos", "noun"), r.get("article", "die"), r["ru"], "high",
             "neutral", json.dumps({"ru_all": r.get("ru_all", [r["ru"]])}),
             "m", "p", 1, 1, r["created_at"], r.get("zipf")),
        )
    con.commit()
    con.close()


@pytest.fixture
def enrichment_db(tmp_path, monkeypatch):
    path = tmp_path / "enrichment.db"

    def _use(rows):
        monkeypatch.setattr("app.vocab.enrich.ENRICH_DB", path)
        _make_enrichment_db(path, rows)   # after the patch: ensure_schema reads it
        return path

    return _use


async def test_mirror_copies_cards_and_their_meanings(pg_session, enrichment_db):
    enrichment_db([
        {"lemma": "Fortschritt", "ru": "прогресс", "article": "der", "created_at": 10.0},
        {"lemma": "grün", "ru": "зелёный", "pos": "adj", "article": None,
         "ru_all": ["зелёный", "незрелый"], "created_at": 11.0},
    ])
    result = await mirror.sync_cards(pg_session)
    assert result == {"ok": True, "synced": 2, "pruned": 0, "total": 2}

    card = await pg_session.get(VocabCard, "grün")
    assert (card.lemma_norm, card.lemma_ascii) == ("gruen", "grun")
    assert card.band == "B1"
    translations = (await pg_session.execute(
        VocabCardTranslation.__table__.select().where(
            VocabCardTranslation.lemma == "grün"))).all()
    assert {t.ru for t in translations} == {"зелёный", "незрелый"}


async def test_mirror_is_incremental(pg_session, enrichment_db):
    path = enrichment_db([
        {"lemma": "Fortschritt", "ru": "прогресс", "created_at": 10.0}])
    assert (await mirror.sync_cards(pg_session))["synced"] == 1

    _make_enrichment_db(path, [{"lemma": "Wandel", "ru": "перемена",
                                "created_at": 20.0}])
    result = await mirror.sync_cards(pg_session)
    assert result["synced"] == 1 and result["total"] == 2


async def test_mirror_picks_up_a_re_enriched_card(pg_session, enrichment_db):
    """`save_cards` rewrites the row with a fresh `created_at`, so an updated
    card rides the same watermark as a new one."""
    path = enrichment_db([
        {"lemma": "Fortschritt", "ru": "прогресс", "created_at": 10.0}])
    await mirror.sync_cards(pg_session)

    _make_enrichment_db(path, [{"lemma": "Fortschritt", "ru": "продвижение",
                                "ru_all": ["продвижение"], "created_at": 30.0}])
    assert (await mirror.sync_cards(pg_session))["synced"] == 1
    pg_session.expire_all()
    assert (await pg_session.get(VocabCard, "Fortschritt")).ru == "продвижение"


async def test_mirror_drops_meanings_that_disappeared_on_re_enrichment(
        pg_session, enrichment_db):
    path = enrichment_db([{"lemma": "Sucht", "ru": "зависимость",
                           "ru_all": ["зависимость", "мания"], "created_at": 10.0}])
    await mirror.sync_cards(pg_session)

    _make_enrichment_db(path, [{"lemma": "Sucht", "ru": "зависимость",
                                "ru_all": ["зависимость"], "created_at": 40.0}])
    await mirror.sync_cards(pg_session)
    # a stale meaning left behind would keep matching searches for "мания"
    assert _lemmas(await search_mod.search(pg_session, "мания")) == []


async def test_mirror_survives_a_repeat_run(pg_session, enrichment_db):
    enrichment_db([{"lemma": "Fortschritt", "ru": "прогресс", "created_at": 10.0}])
    await mirror.sync_cards(pg_session)
    assert (await mirror.sync_cards(pg_session)) == {"ok": True, "synced": 0,
                                                     "pruned": 0, "total": 1}


async def test_mirror_carries_frequency_across(pg_session, enrichment_db):
    enrichment_db([{"lemma": "schnell", "ru": "быстрый", "created_at": 10.0,
                    "zipf": 5.51}])
    await mirror.sync_cards(pg_session)
    assert (await pg_session.get(VocabCard, "schnell")).zipf == pytest.approx(5.51)


async def test_mirror_prunes_a_card_the_source_dropped(pg_session, enrichment_db):
    """A repair pass can `skip` a word we already published, which deletes its
    card. The forward cursor can only add, so without pruning the replica would
    keep serving the entry we just rejected — forever."""
    path = enrichment_db([
        {"lemma": "Nacht", "ru": "ночь", "created_at": 10.0},
        {"lemma": "nacht", "ru": "ночь", "created_at": 10.0},
    ])
    await mirror.sync_cards(pg_session)
    assert await pg_session.get(VocabCard, "nacht") is not None

    con = sqlite3.connect(path)
    con.execute("DELETE FROM cards WHERE lemma='nacht'")
    con.commit()
    con.close()

    assert (await mirror.sync_cards(pg_session))["pruned"] == 1
    assert await pg_session.get(VocabCard, "nacht") is None
    assert await pg_session.get(VocabCard, "Nacht") is not None   # only the artifact


async def test_mirror_refuses_to_prune_against_an_unreadable_source(
        pg_session, enrichment_db, monkeypatch):
    """If enrichment.db vanishes, "delete everything not in an empty set" would
    wipe the dictionary. A stale replica is recoverable; an empty one is an outage."""
    enrichment_db([{"lemma": "Fortschritt", "ru": "прогресс", "created_at": 10.0}])
    await mirror.sync_cards(pg_session)
    monkeypatch.setattr("app.vocab.enrich.ENRICH_DB", tmp_missing := Path("/nonexistent.db"))
    assert not tmp_missing.exists()
    assert await mirror.prune_orphans(pg_session) == 0
    assert await pg_session.get(VocabCard, "Fortschritt") is not None


async def test_full_replay_picks_up_a_column_backfilled_in_place(
        pg_session, enrichment_db):
    """`plan_repairs` fills `cards.zipf` with an UPDATE, which does not move
    `created_at` — so the incremental cursor can never see it and ranking would
    stay broken until each card happened to be re-enriched."""
    path = enrichment_db([{"lemma": "schnell", "ru": "быстрый", "created_at": 10.0}])
    await mirror.sync_cards(pg_session)
    assert (await pg_session.get(VocabCard, "schnell")).zipf is None

    con = sqlite3.connect(path)
    con.execute("UPDATE cards SET zipf=5.51 WHERE lemma='schnell'")
    con.commit()
    con.close()

    assert (await mirror.sync_cards(pg_session))["synced"] == 0     # cursor is blind
    result = await mirror.sync_cards(pg_session, since=(0.0, ""))   # replay sees it
    assert result["synced"] == 1
    await pg_session.refresh(await pg_session.get(VocabCard, "schnell"))
    assert (await pg_session.get(VocabCard, "schnell")).zipf == pytest.approx(5.51)


# ── personal word list ───────────────────────────────────────────────────────
async def test_word_list_requires_an_account(pg_guest_client):
    """No guest mode here, by decision — unlike essays."""
    assert (await pg_guest_client.get("/api/vocab/list")).status_code == 401
    assert (await pg_guest_client.post(
        "/api/vocab/list", json={"lemma": "Fortschritt"})).status_code == 401


async def test_lookup_stays_public(pg_guest_client, pg_session):
    await _add_card(pg_session, "Fortschritt", "прогресс", article="der")
    response = await pg_guest_client.get("/api/vocab/search", params={"q": "прогресс"})
    assert response.status_code == 200
    assert _lemmas(response.json()) == ["Fortschritt"]


async def test_add_word_snapshots_the_card(pg_client, pg_session):
    await _add_card(pg_session, "Fortschritt", "прогресс", level="b2", article="der")
    response = await pg_client.post("/api/vocab/list", json={"lemma": "Fortschritt"})
    assert response.status_code == 201
    assert response.json() == {
        "lemma": "Fortschritt", "ru": "прогресс", "level": "b2", "band": "B2",
        "type": "der", "pos": "noun", "article": "der", "topic": "allgemein",
        "status": "learning", "added_at": response.json()["added_at"],
    }


async def test_add_word_twice_is_idempotent(pg_client, pg_session):
    """A double click, or a retry from the future extension, must not duplicate."""
    await _add_card(pg_session, "Fortschritt", "прогресс", article="der")
    assert (await pg_client.post("/api/vocab/list",
                                 json={"lemma": "Fortschritt"})).status_code == 201
    assert (await pg_client.post("/api/vocab/list",
                                 json={"lemma": "Fortschritt"})).status_code == 201
    assert (await pg_client.get("/api/vocab/list")).json()["total"] == 1


async def test_add_unknown_word_is_rejected(pg_client):
    response = await pg_client.post("/api/vocab/list", json={"lemma": "Nichtwort"})
    assert response.status_code == 404


async def test_list_returns_newest_first_and_pages(pg_client, pg_session):
    for i, lemma in enumerate(["Alpha", "Beta", "Gamma"]):
        await _add_card(pg_session, lemma, f"перевод{i}")
        await pg_client.post("/api/vocab/list", json={"lemma": lemma})
        time.sleep(0.01)  # added_at resolution — keep the order deterministic

    first = (await pg_client.get("/api/vocab/list", params={"limit": 2})).json()
    assert [i["lemma"] for i in first["items"]] == ["Gamma", "Beta"]
    assert first["total"] == 3

    second = (await pg_client.get(
        "/api/vocab/list", params={"limit": 2, "offset": 2})).json()
    assert [i["lemma"] for i in second["items"]] == ["Alpha"]


async def test_remove_word(pg_client, pg_session):
    await _add_card(pg_session, "Fortschritt", "прогресс", article="der")
    await pg_client.post("/api/vocab/list", json={"lemma": "Fortschritt"})
    assert (await pg_client.delete(
        "/api/vocab/list/Fortschritt")).status_code == 204
    assert (await pg_client.get("/api/vocab/list")).json()["total"] == 0


async def test_remove_is_scoped_to_the_owner(pg_client, pg_session):
    """One account must not be able to delete another's word."""
    from app.db.models import User

    await _add_card(pg_session, "Fortschritt", "прогресс", article="der")
    await pg_client.post("/api/vocab/list", json={"lemma": "Fortschritt"})
    other = User(email="other@example.com", password_hash="x")
    pg_session.add(other)
    await pg_session.flush()
    pg_session.add(UserWordList(user_id=other.id, lemma="Fortschritt",
                                ru="прогресс", level="b1", band="B1", pos="noun"))
    await pg_session.commit()

    await pg_client.delete("/api/vocab/list/Fortschritt")
    remaining = (await pg_session.execute(
        UserWordList.__table__.select())).all()
    assert [r.user_id for r in remaining] == [other.id]


async def test_stats_count_by_band(pg_client, pg_session):
    await _add_card(pg_session, "Fortschritt", "прогресс", level="b1", article="der")
    await _add_card(pg_session, "Wandel", "перемена", level="b2", article="der")
    await _add_card(pg_session, "durchziehen", "протягивать", level="unlisted",
                    pos="verb", article=None)
    for lemma in ["Fortschritt", "Wandel", "durchziehen"]:
        await pg_client.post("/api/vocab/list", json={"lemma": lemma})

    stats = (await pg_client.get("/api/vocab/list/stats")).json()
    # `unlisted` is displayed as C1 — see norm.LEVEL_BAND
    assert stats == {"total": 3, "bands": {"B1": 1, "B2": 1, "C1": 1}}


async def test_search_marks_words_already_on_the_list(pg_client, pg_session):
    await _add_card(pg_session, "Fortschritt", "прогресс", article="der")
    await _add_card(pg_session, "Fortsetzung", "продолжение", article="die")
    await pg_client.post("/api/vocab/list", json={"lemma": "Fortschritt"})

    items = (await pg_client.get(
        "/api/vocab/search", params={"q": "Forts"})).json()["items"]
    flags = {i["lemma"]: i["in_list"] for i in items}
    assert flags == {"Fortschritt": True, "Fortsetzung": False}


async def test_entry_returns_the_full_card(pg_client, pg_session):
    await _add_card(pg_session, "durchziehen", "проходить насквозь",
                    ru_all=["проходить насквозь", "протягивать"],
                    pos="verb", article=None, level="unlisted")
    card = (await pg_client.get("/api/vocab/entry/durchziehen")).json()
    assert card["ru_all"] == ["проходить насквозь", "протягивать"]
    assert (card["band"], card["type"]) == ("C1", "verb")
    assert card["in_list"] is False


async def test_entry_404s_for_an_unknown_lemma(pg_guest_client):
    assert (await pg_guest_client.get("/api/vocab/entry/Nichtwort")).status_code == 404

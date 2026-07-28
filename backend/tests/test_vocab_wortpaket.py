"""Building the word package for one essay topic.

Most of what is asserted here is what must NOT reach the user. The package is
assembled by a language model choosing from rows we sent it, and the two ways
that goes wrong are both silent: the model returns a word we never sent (so it
has no card, and the reader clicks into nothing), or it returns a word whose
spelling differs only in case (so we hand back the wrong card while every count
still looks right).

The case rule is not pedantry. Folding case at exactly this kind of join has
already cost this project once: `parse_response` in the enrichment path indexed
by `word.lower()`, 635 pairs in the base came out byte-identical, and `morgen`
"tomorrow" stopped existing — a search for it answered `Frühstück`. `Morgen` and
`morgen` are different words and every matcher here has to keep believing that.
"""
from __future__ import annotations

import pytest
from app.db.models import UserWordList, VocabCard
from app.vocab import norm, wortpaket


@pytest.fixture(autouse=True)
def _clear_catalog_cache():
    wortpaket.reset_catalog_cache()
    yield
    wortpaket.reset_catalog_cache()


async def _card(session, lemma, ru, *, topic="digitalisierung_computer", zipf=5.0,
                form_kind=None, level="unlisted", level_est=None):
    session.add(VocabCard(
        lemma=lemma, lemma_norm=norm.fold_de(lemma), lemma_ascii=norm.ascii_de(lemma),
        level=level, level_est=level_est, band="C1", pos="noun", article="das", ru=ru,
        confidence="high", data={"ru_all": [ru]}, zipf=zipf, topic=topic,
        form_kind=form_kind, source_created_at=0.0,
    ))
    await session.commit()


# ── call 1: which topics ─────────────────────────────────────────────────────

def test_parse_topics_drops_slugs_we_never_sent():
    """A slug outside the catalog is not a near miss — it is an invented topic."""
    counts = {"digitalisierung_computer": 200, "sport": 150}
    reply = {"topics": [
        {"slug": "digitalisierung_computer", "closeness": 0.9},
        {"slug": "smartphones_in_schulen", "closeness": 0.95},   # no such topic
        {"slug": "sport", "closeness": 0.3},
    ]}
    assert wortpaket.parse_topics(reply, counts) == [
        ("digitalisierung_computer", 0.9), ("sport", 0.3),
    ]


def test_parse_topics_drops_topics_with_no_candidates():
    """A real slug with an empty pool would make the pool arithmetic lie."""
    counts = {"sport": 150}   # `musik` exists in the taxonomy but has no candidates
    reply = {"topics": [{"slug": "musik", "closeness": 0.99},
                        {"slug": "sport", "closeness": 0.4}]}
    assert wortpaket.parse_topics(reply, counts) == [("sport", 0.4)]


def test_parse_topics_sorts_by_closeness_and_survives_junk():
    counts = {"a": 10, "b": 10, "c": 10}
    reply = {"topics": [
        {"slug": "a", "closeness": 0.2},
        "not a dict",
        {"slug": "b", "closeness": "unparseable"},
        {"slug": "c", "closeness": 4.0},      # clamped to 1.0
        {"slug": "a", "closeness": 0.9},      # duplicate: first wins
    ]}
    assert wortpaket.parse_topics(reply, counts) == [("c", 1.0), ("a", 0.2)]


def test_choose_topics_does_not_stop_at_a_full_pool():
    """The regression this file exists for.

    An earlier rule stopped adding topics once the pool passed 1 000 rows. On
    the live base that meant `digitalisierung_computer` and `schule_unterricht`
    — big, and about the SUBJECT — filled the pool between them, and
    `recht_gesetz` never got in. `Verbot` and `Jugendschutz` live in
    `recht_gesetz`, and an essay arguing for a ban is made of those words, not
    of `Video` and `Programm`.
    """
    counts = {"digitalisierung_computer": 900, "schule_unterricht": 700,
              "recht_gesetz": 184, "sucht_psyche": 60}
    ranked = [("digitalisierung_computer", 0.95), ("schule_unterricht", 0.9),
              ("recht_gesetz", 0.8), ("sucht_psyche", 0.6)]
    chosen = [slug for slug, _ in wortpaket.choose_topics(ranked, counts)]
    assert chosen == ["digitalisierung_computer", "schule_unterricht",
                      "recht_gesetz", "sucht_psyche"]


def test_choose_topics_skips_a_topic_with_nothing_in_it():
    counts = {"a": 100, "c": 100}
    ranked = [("a", 0.9), ("b", 0.85), ("c", 0.8)]
    assert wortpaket.choose_topics(ranked, counts) == [("a", 0.9), ("c", 0.8)]


def test_choose_topics_keeps_the_best_match_however_weak():
    """No package at all is worse than one built from a weak match: call 2 still
    gets to reject every word in it."""
    counts = {"a": 40}
    assert wortpaket.choose_topics([("a", 0.05)], counts) == [("a", 0.05)]


def test_choose_topics_drops_weak_matches_after_the_first():
    counts = {"a": 40, "b": 40, "c": 40}
    ranked = [("a", 0.8), ("b", 0.1), ("c", 0.05)]
    assert wortpaket.choose_topics(ranked, counts) == [("a", 0.8)]


def test_choose_topics_never_exceeds_the_topic_cap():
    slugs = [f"t{i}" for i in range(wortpaket.MAX_TOPICS + 3)]
    counts = {s: 20 for s in slugs}
    assert len(wortpaket.choose_topics([(s, 0.9) for s in slugs], counts)) \
        == wortpaket.MAX_TOPICS


# ── call 2: validating the hundred ───────────────────────────────────────────

def _cands(*pairs):
    return [{"lemma": lemma, "ru": ru, "level": "", "zipf": zipf, "pos": "noun",
             "article": None, "topic": "t"} for lemma, ru, zipf in pairs]


def test_parse_ranking_drops_words_we_never_sent():
    cands = _cands(("Verbot", "запрет", 4.0), ("Sucht", "зависимость", 3.8))
    reply = {"lemmas": ["Verbot", "Handyverbotsgesetz", "Sucht"]}
    kept, dropped = wortpaket.parse_ranking(reply, cands)
    assert kept == ["Verbot", "Sucht"]
    assert dropped == ["Handyverbotsgesetz"]


def test_parse_ranking_treats_case_as_meaning():
    """`Morgen` (the morning) and `morgen` (tomorrow) are different words with
    different cards. Matching one to the other is how `morgen` stopped existing
    the last time this project folded case at a join."""
    cands = _cands(("morgen", "завтра", 5.9))
    kept, dropped = wortpaket.parse_ranking({"lemmas": ["Morgen"]}, cands)
    assert kept == []
    assert dropped == ["Morgen"]


def test_parse_ranking_dedupes_and_caps():
    cands = _cands(*[(f"W{i}", "x", 3.0) for i in range(10)])
    reply = {"lemmas": ["W1", "W1", "W2", "W3", 42, None]}
    kept, _ = wortpaket.parse_ranking(reply, cands, size=2)
    assert kept == ["W1", "W2"]


def test_backfill_tops_up_by_frequency_without_disturbing_the_model_order():
    cands = _cands(("selten", "редкий", 2.6), ("häufig", "частый", 5.5),
                   ("mittel", "средний", 4.0))
    out = wortpaket.backfill(["selten"], cands, size=3)
    assert out == ["selten", "häufig", "mittel"]


def test_backfill_is_a_noop_when_the_model_filled_the_list():
    cands = _cands(("a", "a", 5.0), ("b", "b", 4.0))
    assert wortpaket.backfill(["a", "b"], cands, size=2) == ["a", "b"]


def test_backfill_survives_candidates_without_a_frequency():
    cands = _cands(("mit", "с", 4.0)) + [
        {"lemma": "ohne", "ru": "без", "level": "", "zipf": None,
         "pos": "noun", "article": None, "topic": "t"}]
    out = wortpaket.backfill([], cands, size=2)
    assert out == ["mit", "ohne"]   # NULL frequency sorts last, not first


# ── candidates from the database ─────────────────────────────────────────────

async def test_candidates_exclude_forms_rare_words_and_saved_words(db_session):
    await _card(db_session, "Verbot", "запрет", zipf=4.2)
    await _card(db_session, "Sucht", "зависимость", zipf=3.9)
    await _card(db_session, "Gemacht", "сделанный", zipf=5.9, form_kind="inflection")
    await _card(db_session, "Nischenwort", "нишевое", zipf=1.2)
    await _card(db_session, "Ablenkung", "отвлечение", zipf=3.5)

    rows = await wortpaket.candidates(
        db_session, ["digitalisierung_computer"], exclude={"Ablenkung"})
    got = {r["lemma"] for r in rows}

    assert got == {"Verbot", "Sucht"}, "forms, rare words and saved words all stay out"


async def test_candidates_prefer_a_real_level_over_our_estimate(db_session):
    await _card(db_session, "Handy", "мобильник", zipf=4.5, level="b1", level_est="a2")
    await _card(db_session, "Endlager", "могильник", zipf=2.9, level_est="c1")
    rows = {r["lemma"]: r["level"] for r in
            await wortpaket.candidates(db_session, ["digitalisierung_computer"])}
    assert rows == {"Handy": "b1", "Endlager": "c1"}


async def test_candidates_cap_each_topic_so_a_big_one_cannot_crowd_out_a_small(db_session):
    """A global `ORDER BY zipf LIMIT n` would return the big topic and nothing
    else — which is exactly what happened on the live base, and why the small
    topic holding the argument vocabulary contributed zero words."""
    for i in range(10):
        await _card(db_session, f"Gross{i}", "часто", topic="schule_unterricht",
                    zipf=6.0 - i * 0.01)
    await _card(db_session, "Verbot", "запрет", topic="recht_gesetz", zipf=4.47)
    await _card(db_session, "Jugendschutz", "защита", topic="recht_gesetz", zipf=3.12)

    rows = await wortpaket.candidates(
        db_session, ["schule_unterricht", "recht_gesetz"], per_topic=3)
    by_topic: dict[str, int] = {}
    for r in rows:
        by_topic[r["topic"]] = by_topic.get(r["topic"], 0) + 1

    assert by_topic == {"schule_unterricht": 3, "recht_gesetz": 2}
    assert {"Verbot", "Jugendschutz"} <= {r["lemma"] for r in rows}


async def test_candidates_take_the_most_frequent_of_each_topic(db_session):
    await _card(db_session, "Häufig", "частый", topic="recht_gesetz", zipf=5.0)
    await _card(db_session, "Mittel", "средний", topic="recht_gesetz", zipf=4.0)
    await _card(db_session, "Selten", "редкий", topic="recht_gesetz", zipf=2.6)
    rows = await wortpaket.candidates(db_session, ["recht_gesetz"], per_topic=2)
    assert [r["lemma"] for r in rows] == ["Häufig", "Mittel"]


async def test_candidates_return_nothing_for_no_topics(db_session):
    await _card(db_session, "Verbot", "запрет")
    assert await wortpaket.candidates(db_session, []) == []


async def test_saved_lemmas_are_scoped_to_one_user(db_session):
    db_session.add_all([
        UserWordList(user_id=1, lemma="Verbot", ru="запрет"),
        UserWordList(user_id=2, lemma="Sucht", ru="зависимость"),
    ])
    await db_session.commit()
    assert await wortpaket.saved_lemmas(db_session, 1) == {"Verbot"}


# ── catalog ──────────────────────────────────────────────────────────────────

async def test_catalog_counts_only_countable_candidates(db_session):
    await _card(db_session, "Verbot", "запрет", zipf=4.2)
    await _card(db_session, "Gemacht", "сделанный", zipf=5.9, form_kind="inflection")
    await _card(db_session, "Nischenwort", "нишевое", zipf=1.2)
    await _card(db_session, "Tor", "ворота", topic="sport", zipf=4.0)

    counts = await wortpaket.catalog_counts(db_session)
    assert counts == {"digitalisierung_computer": 1, "sport": 1}


async def test_catalog_counts_ignore_topics_outside_the_taxonomy(db_session):
    """A stale slug left over from an older tagging pass must not become a topic
    the model can name. `topic_pipeline_leftover` is deliberately not in
    `topics.py` — the taxonomy there is the only list the catalog may offer."""
    await _card(db_session, "Verbot", "запрет", topic="topic_pipeline_leftover")
    assert await wortpaket.catalog_counts(db_session) == {}


async def test_catalog_cache_invalidates_when_cards_arrive(db_session):
    await _card(db_session, "Verbot", "запрет")
    assert await wortpaket.catalog_counts(db_session) == {"digitalisierung_computer": 1}
    await _card(db_session, "Sucht", "зависимость")
    assert await wortpaket.catalog_counts(db_session) == {"digitalisierung_computer": 2}


# ── the whole build ──────────────────────────────────────────────────────────

class _FakeCall:
    """Answer call 1 then call 2, recording what each was actually asked.

    A class rather than a closure with an attribute bolted on: `seen` is read by
    the test that checks the catalog reaches the model, and a function attribute
    is invisible to the type checker.
    """

    def __init__(self, topics_reply: dict, rank_reply: dict):
        self.topics_reply = topics_reply
        self.rank_reply = rank_reply
        self.seen: list[str] = []

    def __call__(self, messages, api_key, model) -> dict:
        self.seen.append(messages[1]["content"])
        return self.topics_reply if len(self.seen) == 1 else self.rank_reply


async def _three_cards(session):
    await _card(session, "Verbot", "запрет", zipf=4.2)
    await _card(session, "Sucht", "зависимость", zipf=3.9)
    await _card(session, "Ablenkung", "отвлечение", zipf=3.5)


async def test_build_returns_only_words_that_have_cards(db_session):
    await _three_cards(db_session)
    call = _FakeCall(
        {"topics": [{"slug": "digitalisierung_computer", "closeness": 0.9}]},
        {"lemmas": ["Sucht", "Handyverbotsgesetz", "Verbot"]},
    )
    out = await wortpaket.build(
        db_session, thema="Sollten Smartphones an Schulen verboten werden?",
        niveau="B2", api_key="k", model="m", size=3, call=call)

    assert out["lemmas"][:2] == ["Sucht", "Verbot"], "model order is kept"
    assert "Handyverbotsgesetz" not in out["lemmas"], "invented word never ships"
    assert out["lemmas"][2] == "Ablenkung", "the gap is filled by frequency"
    assert out["stats"]["dropped"] == 1
    assert out["stats"]["backfilled"] == 1


async def test_build_sends_the_counts_so_the_model_can_see_pool_sizes(db_session):
    await _three_cards(db_session)
    call = _FakeCall(
        {"topics": [{"slug": "digitalisierung_computer", "closeness": 0.9}]},
        {"lemmas": ["Verbot"]},
    )
    await wortpaket.build(db_session, thema="Smartphoneverbot", niveau="B2",
                          api_key="k", model="m", size=1, call=call)
    catalog_msg = call.seen[0]
    assert "digitalisierung_computer\tDigitalisierung & Computer\t3" in catalog_msg


async def test_build_excludes_what_the_user_already_saved(db_session):
    await _three_cards(db_session)
    call = _FakeCall(
        {"topics": [{"slug": "digitalisierung_computer", "closeness": 0.9}]},
        {"lemmas": []},
    )
    out = await wortpaket.build(db_session, thema="x", niveau="B2", api_key="k",
                                model="m", size=10, exclude={"Verbot"}, call=call)
    assert "Verbot" not in out["lemmas"]
    assert out["stats"]["pool"] == 2


async def test_build_refuses_an_empty_thema(db_session):
    with pytest.raises(wortpaket.WortpaketError) as exc:
        await wortpaket.build(db_session, thema="   ", niveau="B2",
                              api_key="k", model="m", call=_FakeCall({}, {}))
    assert exc.value.stage == "input"


async def test_build_fails_loudly_when_the_model_names_no_known_topic(db_session):
    await _three_cards(db_session)
    call = _FakeCall({"topics": [{"slug": "erfundenes_thema", "closeness": 1.0}]}, {})
    with pytest.raises(wortpaket.WortpaketError) as exc:
        await wortpaket.build(db_session, thema="x", niveau="B2",
                              api_key="k", model="m", call=call)
    assert exc.value.stage == "topics"


async def test_build_fails_when_exclusions_empty_the_pool(db_session):
    """Better an explicit failure than a package of nothing that looks fine."""
    await _three_cards(db_session)
    call = _FakeCall(
        {"topics": [{"slug": "digitalisierung_computer", "closeness": 0.9}]}, {})
    with pytest.raises(wortpaket.WortpaketError) as exc:
        await wortpaket.build(db_session, thema="x", niveau="B2", api_key="k",
                              model="m",
                              exclude={"Verbot", "Sucht", "Ablenkung"}, call=call)
    assert exc.value.stage == "candidates"


async def test_build_reports_which_call_failed(db_session):
    await _three_cards(db_session)

    def call(messages, api_key, model):
        if "Kandidaten" in messages[1]["content"]:
            raise TimeoutError("upstream gave up")
        return {"topics": [{"slug": "digitalisierung_computer", "closeness": 0.9}]}

    with pytest.raises(wortpaket.WortpaketError) as exc:
        await wortpaket.build(db_session, thema="x", niveau="B2",
                              api_key="k", model="m", call=call)
    assert exc.value.stage == "rank"
    assert "TimeoutError" in exc.value.detail


async def test_stats_line_survives_a_half_built_package(db_session):
    """It is printed on the failure path too, where most keys are missing."""
    assert "—" in wortpaket.stats_line({"thema": "x", "niveau": "B2"})

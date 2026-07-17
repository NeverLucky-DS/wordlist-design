"""Enrichment format + storage: claim atomicity, poison-word cap, rebuild
safety, and card validation."""
from __future__ import annotations

import sqlite3

import pytest

from app.vocab import enrich

_COLS = ("lemma", "article", "pos", "forms", "translations", "examples",
         "synonyms", "collocations", "idioms", "sources", "by_source",
         "zipf", "freq_rank", "level")


def _make_vocab(path, words):
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE words(lemma TEXT UNIQUE, article TEXT, pos TEXT, forms TEXT,"
        " translations TEXT, examples TEXT, synonyms TEXT, collocations TEXT,"
        " idioms TEXT, sources TEXT, by_source TEXT, zipf REAL, freq_rank INTEGER,"
        " level TEXT)")
    for w in words:
        con.execute(
            "INSERT INTO words(lemma,article,pos,forms,translations,examples,"
            "synonyms,collocations,idioms,sources,by_source,zipf,freq_rank,level)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (w["lemma"], w.get("article"), "[]", "[]", '["x"]', "[]", "[]", "[]",
             "[]", "[]", "{}", 3.0, w["rank"], w["level"]))
    con.commit()
    con.close()


@pytest.fixture
def db(tmp_path, monkeypatch):
    vocab = tmp_path / "vocab.db"
    enrich_db = tmp_path / "enrichment.db"
    _make_vocab(vocab, [
        {"lemma": "Haus", "level": "a1", "rank": 10, "article": "das"},
        {"lemma": "gelten", "level": "b1", "rank": 20},
        {"lemma": "Rahmen", "level": "b2", "rank": 5},
        {"lemma": "Xyzzy", "level": "unlisted", "rank": 99},
    ])
    monkeypatch.setattr(enrich, "VOCAB_DB", vocab)
    monkeypatch.setattr(enrich, "ENRICH_DB", enrich_db)
    enrich.ensure_schema()
    return {"vocab": vocab, "enrich": enrich_db}


def test_claim_orders_by_level_priority(db):
    got = [w["lemma"] for w in enrich.claim(user_id=1, n=2)]
    assert got == ["Haus", "gelten"]   # a1 before b1 before b2/unlisted


def test_claim_is_disjoint(db):
    first = {w["lemma"] for w in enrich.claim(1, 2)}
    second = {w["lemma"] for w in enrich.claim(2, 2)}
    assert first.isdisjoint(second)    # a fresh lease is never re-handed


def test_save_marks_done_and_excludes_from_claim(db):
    enrich.claim(1, 1)   # leases Haus
    card = enrich.normalize_card({
        "word": "Haus", "pos": "noun", "article": "das", "ru": "дом",
        "definition_de": "Ein Gebäude zum Wohnen.", "topic": "wohnen_zuhause",
        "examples": [{"de": "Das **Haus** ist groß.", "ru": "Дом большой."}],
    })
    enrich.save_cards(1, {"Haus": card}, {"Haus": "a1"}, "test-model")
    later = [w["lemma"] for w in enrich.claim(1, 10)]
    assert "Haus" not in later
    assert enrich.progress()["enriched"] == 1


def test_poison_word_fails_after_max_attempts(db):
    # a word the model never returns a valid card for
    for _ in range(enrich.MAX_ATTEMPTS):
        batch = enrich.claim(1, 1)
        # simulate immediate re-claim of the same poison word by expiring lease
        enrich.fail_words([w["lemma"] for w in batch])
    con = sqlite3.connect(db["enrich"])
    failed = con.execute("SELECT COUNT(*) FROM word_status WHERE status='failed'").fetchone()[0]
    con.close()
    assert failed >= 1
    # failed words are never handed out again
    remaining = {w["lemma"] for w in enrich.claim(1, 10)}
    assert enrich.progress()["failed"] >= 1


def test_rebuild_of_vocab_keeps_progress(db):
    enrich.claim(1, 1)
    card = enrich.normalize_card({
        "word": "Haus", "pos": "noun", "article": "das", "ru": "дом",
        "definition_de": "Ein Gebäude.", "topic": "wohnen_zuhause",
        "examples": [{"de": "Das **Haus**.", "ru": "Дом."}],
    })
    enrich.save_cards(1, {"Haus": card}, {"Haus": "a1"}, "m")
    # rebuild vocab.db from scratch (as build.py does: drop + recreate)
    db["vocab"].unlink()
    _make_vocab(db["vocab"], [
        {"lemma": "Haus", "level": "a1", "rank": 10, "article": "das"},
        {"lemma": "neu", "level": "a2", "rank": 30},
    ])
    # Haus stays done (status lives in enrichment.db, survived the rebuild)
    later = {w["lemma"] for w in enrich.claim(1, 10)}
    assert "Haus" not in later
    assert "neu" in later


# ── pure format functions ────────────────────────────────────────────────────
def test_normalize_rejects_missing_core():
    assert enrich.normalize_card({"word": "x", "ru": "", "definition_de": "d"}) is None
    assert enrich.normalize_card({"word": "x", "ru": "r", "definition_de": ""}) is None
    assert enrich.normalize_card({"word": "x", "ru": "r", "definition_de": "d",
                                  "examples": []}) is None


def test_normalize_coerces_topic_and_grammar():
    card = enrich.normalize_card({
        "word": "gelten", "pos": "verb", "article": "der",   # bogus article on verb
        "ru": "действовать", "definition_de": "Gültig sein.",
        "topic": "not-a-real-slug",                          # invalid → general
        "grammar": {"genitiv": "des x", "partizip2": "gegolten", "hilfsverb": "haben"},
        "examples": [{"de": "Es **gilt**.", "ru": "Действует."}],
    })
    assert card["article"] is None                     # article dropped for verb
    assert card["topic"] == enrich.GENERAL_TOPIC       # invalid topic coerced
    assert "genitiv" not in card["grammar"]            # noun key pruned for verb
    assert card["grammar"].get("partizip2") == "gegolten"


def test_parse_response_tracks_unmatched():
    parsed = {"words": [
        {"word": "Haus", "pos": "noun", "article": "das", "ru": "дом",
         "definition_de": "Gebäude.", "topic": "wohnen_zuhause",
         "examples": [{"de": "**Haus**", "ru": "дом"}]},
    ]}
    cards, skipped, unmatched, renamed = enrich.parse_response(["Haus", "Baum"], parsed)
    assert "Haus" in cards
    assert skipped == []
    assert unmatched == ["Baum"]     # dropped word tracked, never silently lost
    assert renamed == {}


def test_parse_response_routes_model_skip():
    parsed = {"words": [
        {"word": "ER", "skip": True, "skip_reason": "Groß-/Kleinschreibungs-Duplikat"},
        {"word": "Haus", "pos": "noun", "article": "das", "ru": "дом",
         "definition_de": "Gebäude.", "topic": "wohnen_zuhause",
         "examples": [{"de": "**Haus**", "ru": "дом"}]},
    ]}
    cards, skipped, unmatched, _ = enrich.parse_response(["ER", "Haus"], parsed)
    assert list(cards) == ["Haus"]
    assert skipped == ["ER"]         # model-rejected word → skipped, not a card
    assert unmatched == []


def _item(word, ru, pos="noun", **kw):
    """A minimal valid model item for `word`."""
    return {"word": word, "pos": pos, "ru": ru, "definition_de": f"{word}.",
            "topic": "zeit_zeitangaben",
            "examples": [{"de": f"**{word}**", "ru": ru}], **kw}


# ── the homograph bug: case must never be folded during lookup ───────────────
def test_homograph_pair_keeps_both_distinct_answers():
    """The regression that cost 635 pairs: Morgen and morgen were sent in one
    batch, the model answered both, and the folded index handed the SAME card to
    both lemmas — so `morgen`=завтра did not exist in the base at all."""
    parsed = {"words": [_item("Morgen", "утро", article="der"),
                        _item("morgen", "завтра", pos="adv")]}
    cards, skipped, unmatched, renamed = enrich.parse_response(
        ["Morgen", "morgen"], parsed)
    assert cards["Morgen"]["ru"] == "утро"
    assert cards["morgen"]["ru"] == "завтра"
    assert cards["Morgen"] != cards["morgen"]     # never the same card twice
    assert (skipped, unmatched, renamed) == ([], [], {})


def test_homograph_half_missing_is_unmatched_not_copied():
    """If the model answers only one spelling, the other must be retried — NOT
    quietly given its twin's card, which is exactly how the duplicates appeared."""
    parsed = {"words": [_item("Morgen", "утро", article="der")]}
    cards, _, unmatched, _ = enrich.parse_response(["Morgen", "morgen"], parsed)
    assert list(cards) == ["Morgen"]
    assert unmatched == ["morgen"]


def test_model_skip_of_case_artifact_is_not_swallowed():
    """`nacht` is a case artifact and the model says so; the fold used to drop the
    skip and file Nacht's card under it too."""
    parsed = {"words": [_item("Nacht", "ночь", article="die"),
                        {"word": "nacht", "skip": True, "skip_reason": "Artefakt"}]}
    cards, skipped, unmatched, _ = enrich.parse_response(["Nacht", "nacht"], parsed)
    assert list(cards) == ["Nacht"]
    assert skipped == ["nacht"]
    assert unmatched == []


def test_recased_reply_matches_when_unambiguous_and_keeps_our_spelling():
    """Only "morgen" was sent, the model replied "Morgen". The fold may resolve
    that — but our lemma is the homograph key, so it wins."""
    parsed = {"words": [_item("Morgen", "завтра", pos="adv")]}
    cards, _, unmatched, renamed = enrich.parse_response(["morgen"], parsed)
    assert list(cards) == ["morgen"]
    assert renamed == {}          # a pure case change is not an orthography fix
    assert unmatched == []


# ── pre-1996 spellings: the model corrects them, we file under the new one ───
def test_pre_reform_spelling_is_renamed_to_the_modern_one():
    """348 words (Bewusstsein, Einfluss, Prozess…) died in `failed` because the
    model returns the post-1996 spelling and the name no longer matched."""
    parsed = {"words": [_item("Schluss", "конец", article="der")]}
    cards, _, unmatched, renamed = enrich.parse_response(["Schluß"], parsed)
    assert list(cards) == ["Schluß"]          # work state stays on the sent lemma
    assert renamed == {"Schluß": "Schluss"}   # the card is filed under the modern one
    assert unmatched == []


def test_rename_is_refused_when_the_fold_is_ambiguous():
    """Two sent lemmas folding together can only be matched by name — never let
    the ß/ss fallback re-open the door the case fix just closed."""
    parsed = {"words": [_item("Masse", "масса", article="die")]}
    cards, _, unmatched, renamed = enrich.parse_response(["Maße", "Masse"], parsed)
    assert list(cards) == ["Masse"]      # exact hit only
    assert unmatched == ["Maße"]
    assert renamed == {}


def test_unrelated_word_is_never_renamed_onto():
    parsed = {"words": [_item("Haus", "дом", article="das")]}
    cards, _, unmatched, renamed = enrich.parse_response(["Baum"], parsed)
    assert cards == {} and renamed == {} and unmatched == ["Baum"]


def test_save_cards_rename_files_card_new_but_status_old(db):
    """The card moves to the modern spelling; the work state must NOT, or the old
    lemma looks unenriched and gets served again forever."""
    card = enrich.normalize_card(_item("Schluss", "конец", article="der"))
    enrich.save_cards(1, {"Schluß": card}, {"Schluß": "b1"}, "m",
                      renamed={"Schluß": "Schluss"})
    con = sqlite3.connect(db["enrich"])
    stored = [r[0] for r in con.execute("SELECT lemma FROM cards")]
    status = con.execute(
        "SELECT status FROM word_status WHERE lemma='Schluß'").fetchone()
    con.close()
    assert stored == ["Schluss"]        # filed under the modern spelling only
    assert status[0] == "done"          # …and the old lemma is settled


def test_is_junk_matches_fragments_and_acronyms():
    assert enrich.is_junk("mit-")     # trailing hyphen fragment
    assert enrich.is_junk("-heit")    # leading hyphen affix
    assert enrich.is_junk("a")        # single char
    assert enrich.is_junk("ER")       # all-caps acronym / case dupe
    assert enrich.is_junk("SPD")
    assert not enrich.is_junk("Haus")
    assert not enrich.is_junk("gehen")
    assert not enrich.is_junk("Umwelt")


def test_claim_never_serves_junk(db):
    # inject junk lemmas at the very top of the queue
    con = sqlite3.connect(db["vocab"])
    for rank, lemma in ((1, "mit-"), (2, "ER"), (3, "a")):
        con.execute(
            "INSERT INTO words(lemma,article,pos,forms,translations,examples,"
            "synonyms,collocations,idioms,sources,by_source,zipf,freq_rank,level)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (lemma, None, "[]", "[]", '["x"]', "[]", "[]", "[]", "[]", "[]", "{}",
             9.0, rank, "a1"))
    con.commit()
    con.close()
    served = {w["lemma"] for w in enrich.claim(1, 20)}
    assert served.isdisjoint({"mit-", "ER", "a"})
    assert "Haus" in served          # real words still served
    assert enrich.progress()["junk"] >= 3


def _add_word(path, lemma, level="a1", rank=50, zipf=3.0):
    con = sqlite3.connect(path)
    con.execute(
        "INSERT INTO words(lemma,article,pos,forms,translations,examples,"
        "synonyms,collocations,idioms,sources,by_source,zipf,freq_rank,level)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (lemma, None, "[]", "[]", '["x"]', "[]", "[]", "[]", "[]", "[]", "{}",
         zipf, rank, level))
    con.commit()
    con.close()


# ── phases ──────────────────────────────────────────────────────────────────
def test_case_partners_handles_non_ascii():
    # SQL lower() would leave 'Über' alone; the pairing must be Unicode-aware.
    assert enrich.case_partners("Über") == {"über"}
    assert enrich.case_partners("über") == {"Über"}
    assert enrich.case_partners("Morgen") == {"morgen"}


def test_claim_co_batches_case_partners(db):
    """A homograph pair has to reach the model together — that is the only way
    the prompt can tell утро from завтра and drop the artifact half."""
    _add_word(db["vocab"], "Morgen", rank=1)
    _add_word(db["vocab"], "morgen", rank=900, level="unlisted")   # far apart
    served = {w["lemma"] for w in enrich.claim(1, 1)}
    assert served == {"Morgen", "morgen"}   # partner pulled in despite the ordering


def test_claim_partner_expansion_does_not_re_serve(db):
    _add_word(db["vocab"], "Morgen", rank=1)
    _add_word(db["vocab"], "morgen", rank=900, level="unlisted")
    first = {w["lemma"] for w in enrich.claim(1, 1)}
    second = {w["lemma"] for w in enrich.claim(2, 5)}
    assert first == {"Morgen", "morgen"}
    assert second.isdisjoint(first)          # leases still disjoint across workers


def test_repair_phase_is_claimed_before_backfill(db):
    card = enrich.normalize_card(_item("Haus", "дом", article="das"))
    enrich.save_cards(1, {"Haus": card}, {"Haus": "a1"}, "m")
    enrich.requeue(["Haus"], drop_card=False, phase="repair_case")
    # Rahmen is b2 and Haus a1, but phase outranks level either way.
    assert enrich.claim(1, 1)[0]["lemma"] == "Haus"
    assert enrich.progress()["phase"] == "repair_case"


def test_plan_repairs_tags_identical_case_cards_once(db):
    _add_word(db["vocab"], "Morgen", rank=1)
    _add_word(db["vocab"], "morgen", rank=2)
    same = enrich.normalize_card(_item("Morgen", "утро", article="der"))
    enrich.save_cards(1, {"Morgen": same, "morgen": same},
                      {"Morgen": "a1", "morgen": "a1"}, "m")
    first = enrich.plan_repairs()
    assert first["repair_case"] == 2          # both halves queued
    assert enrich.progress()["phase"] == "repair_case"
    # Idempotent: a second pass must not re-queue what it already tagged, or the
    # run would loop on these words every single start.
    assert enrich.plan_repairs()["repair_case"] == 0


def test_plan_repairs_leaves_distinct_case_cards_alone(db):
    _add_word(db["vocab"], "Morgen", rank=1)
    _add_word(db["vocab"], "morgen", rank=2)
    enrich.save_cards(
        1,
        {"Morgen": enrich.normalize_card(_item("Morgen", "утро", article="der")),
         "morgen": enrich.normalize_card(_item("morgen", "завтра", pos="adv"))},
        {"Morgen": "a1", "morgen": "a1"}, "m")
    assert enrich.plan_repairs()["repair_case"] == 0   # already correct → untouched


def test_plan_repairs_requeues_failed_words_once(db):
    for _ in range(enrich.MAX_ATTEMPTS):
        enrich.fail_words(["Haus"])
    assert enrich.progress()["failed"] == 1
    assert enrich.plan_repairs()["repair_ortho"] == 1
    assert enrich.claim(1, 1)[0]["lemma"] == "Haus"    # gets another chance
    assert enrich.plan_repairs()["repair_ortho"] == 0  # but only the one


def test_plan_repairs_backfills_zipf(db):
    card = enrich.normalize_card(_item("Haus", "дом", article="das"))
    enrich.save_cards(1, {"Haus": card}, {"Haus": "a1"}, "m")   # no zipf passed
    con = sqlite3.connect(db["enrich"])
    assert con.execute("SELECT zipf FROM cards WHERE lemma='Haus'").fetchone()[0] is None
    con.close()
    assert enrich.plan_repairs()["zipf_filled"] == 1
    con = sqlite3.connect(db["enrich"])
    assert con.execute("SELECT zipf FROM cards WHERE lemma='Haus'").fetchone()[0] == 3.0
    con.close()


def test_plan_repairs_settles_when_a_card_has_no_source_row(db):
    """A renamed card (Schluss) has no vocab.db row, so its zipf can never be
    filled. Without a guard the UPDATE keeps matching it on every run, keeps
    reporting work done, and fires a full 64k mirror replay at every start."""
    card = enrich.normalize_card(_item("Schluss", "конец", article="der"))
    enrich.save_cards(1, {"Haus": card}, {"Haus": "a1"}, "m",
                      renamed={"Haus": "Schluss"})
    assert enrich.plan_repairs()["zipf_filled"] == 0   # nothing fillable
    assert enrich.plan_repairs()["zipf_filled"] == 0   # and it stays that way


def test_save_cards_stores_zipf(db):
    card = enrich.normalize_card(_item("Haus", "дом", article="das"))
    enrich.save_cards(1, {"Haus": card}, {"Haus": "a1"}, "m", zipfs={"Haus": 5.5})
    con = sqlite3.connect(db["enrich"])
    assert con.execute("SELECT zipf FROM cards WHERE lemma='Haus'").fetchone()[0] == 5.5
    con.close()


def test_skip_drops_an_existing_card(db):
    """A repair pass re-judges a word we already published; if the model now says
    it is not a word, the card must not stay in the index."""
    card = enrich.normalize_card(_item("morgen", "утро", article="der"))
    enrich.save_cards(1, {"morgen": card}, {"morgen": "a1"}, "m")
    enrich.skip_words(["morgen"])
    assert enrich.get_card("morgen") is None
    assert enrich.progress()["skipped"] == 1


# ── token accounting ────────────────────────────────────────────────────────
def test_usage_accumulates_per_account(db):
    enrich.record_usage(1, {"prompt_tokens": 900, "completion_tokens": 100,
                            "total_tokens": 1000})
    enrich.record_usage(1, {"prompt_tokens": 50, "completion_tokens": 5,
                            "total_tokens": 55})
    enrich.record_usage(2, {"total_tokens": 7})
    usage = enrich.usage_by_user()
    assert usage[1]["total_tokens"] == 1055
    assert usage[1]["calls"] == 2
    assert usage[1]["prompt_tokens"] == 950
    assert usage[2]["total_tokens"] == 7      # accounts are tallied separately
    assert usage[1]["today_tokens"] == 1055


def test_usage_counts_a_call_even_without_numbers(db):
    """The call happened and cost real money; only the price tag is missing."""
    enrich.record_usage(1, {})
    assert enrich.usage_by_user()[1] == {
        "today_tokens": 0, "today_calls": 1, "total_tokens": 0,
        "prompt_tokens": 0, "completion_tokens": 0, "calls": 1}


def test_usage_tolerates_junk_numbers(db):
    enrich.record_usage(1, {"total_tokens": "не число", "prompt_tokens": -5})
    u = enrich.usage_by_user()[1]
    assert u["calls"] == 1 and u["total_tokens"] == 0 and u["prompt_tokens"] == 0


def test_usage_of_an_account_that_never_ran_is_absent(db):
    assert enrich.usage_by_user() == {}


def test_progress_falls_back_to_backfill_phase(db):
    p = enrich.progress()
    assert p["phase"] == "backfill"           # untagged words are the backfill
    assert [x["name"] for x in p["phases"]] == [
        "repair_pairs", "repair_case", "repair_ortho", "repair_split", "backfill"]


def test_skip_and_requeue(db):
    enrich.skip_words(["Xyzzy"])     # unlisted, no twin — the model's call to make
    assert enrich.progress()["skipped"] == 1
    assert "Xyzzy" not in {w["lemma"] for w in enrich.claim(1, 10)}  # not re-served

    card = enrich.normalize_card({
        "word": "gelten", "pos": "verb", "ru": "действовать",
        "definition_de": "Gültig sein.", "topic": "recht_gesetz",
        "confidence": "low",
        "examples": [{"de": "Es **gilt**.", "ru": "Действует."}],
    })
    enrich.save_cards(1, {"gelten": card}, {"gelten": "b1"}, "m")
    assert enrich.progress()["low_confidence"] == 1
    assert enrich.requeue_low_confidence() == 1
    # requeued word comes back as raw and its card is gone
    assert enrich.get_card("gelten") is None
    assert "gelten" in {w["lemma"] for w in enrich.claim(1, 10)}


@pytest.fixture
def pair(tmp_path, monkeypatch):
    """A case pair where BOTH halves are real words — the shape that broke."""
    vocab = tmp_path / "vocab.db"
    _make_vocab(vocab, [
        {"lemma": "haben", "level": "a1", "rank": 86},
        {"lemma": "Haben", "level": "a1", "rank": 85, "article": "das"},
    ])
    monkeypatch.setattr(enrich, "VOCAB_DB", vocab)
    monkeypatch.setattr(enrich, "ENRICH_DB", tmp_path / "enrichment.db")
    enrich.ensure_schema()


def _card(lemma, ru):
    return enrich.normalize_card({
        "word": lemma, "pos": "verb", "ru": ru, "definition_de": "Etwas besitzen.",
        "topic": "recht_gesetz", "confidence": "high",
        "examples": [{"de": f"Ich **{lemma}**.", "ru": "Я."}],
    })


def test_skipping_a_whole_pair_is_refused(pair):
    """The bug that killed haben/kommen/atmen: the model rejects both halves and
    the word leaves the dictionary entirely."""
    enrich.skip_words(["haben", "Haben"])
    assert enrich.progress()["skipped"] == 0
    assert enrich.get_card("haben") is None          # refusing is not inventing
    # ...and they go back into circulation rather than becoming a silent hole
    assert {"haben", "Haben"} <= {w["lemma"] for w in enrich.claim(1, 10)}


def test_skip_is_accepted_once_the_twin_holds_a_card(pair):
    """A decided pair must still be skippable — that is `nacht`/`Nacht` working."""
    enrich.save_cards(1, {"haben": _card("haben", "иметь")}, {"haben": "a1"}, "m")
    enrich.skip_words(["Haben"])
    assert enrich.progress()["skipped"] == 1
    assert "Haben" not in {w["lemma"] for w in enrich.claim(1, 10)}


def test_an_insisting_model_lands_on_failed_not_on_a_silent_skip(pair):
    for _ in range(enrich.MAX_ATTEMPTS):
        enrich.skip_words(["haben"])
    p = enrich.progress()
    assert p["failed"] == 1 and p["skipped"] == 0     # visible, and it terminates
    assert "haben" not in {w["lemma"] for w in enrich.claim(1, 10)}


def test_plan_repairs_reclaims_a_pair_killed_before_the_guard(pair):
    # damage as it exists in the live base: both halves skipped, no card anywhere
    for lemma in ("haben", "Haben"):
        enrich._conn().execute(
            "INSERT INTO word_status(lemma,status,updated_at) VALUES(?,'skipped',0)",
            (lemma,)).connection.commit()
    assert enrich.plan_repairs()[enrich.PAIRS] == 2
    assert {"haben", "Haben"} <= {w["lemma"] for w in enrich.claim(1, 10)}
    # second run finds nothing: the tag is the self-limit, so no start-up loop
    assert enrich.plan_repairs()[enrich.PAIRS] == 0


@pytest.mark.parametrize("text, crammed", [
    ("приходить, прибывать", True),            # two meanings in one entry
    ("прибыль, доход", True),
    ("приходить (сюда)", False),               # a parenthetical is one meaning
    ("человек, присматривающий за ребёнком", True),   # false positive, on purpose
    ("иметь", False),
])
def test_cramming_is_detected_by_a_top_level_comma(text, crammed):
    assert enrich._splits_meanings(text) is crammed


def test_plan_repairs_requeues_crammed_cards_without_touching_them(db):
    card = enrich.normalize_card({
        "word": "gelten", "pos": "verb", "ru": "действовать, иметь силу",
        "ru_all": ["действовать, иметь силу", "считаться"],
        "definition_de": "Gültig sein.", "topic": "recht_gesetz",
        "confidence": "high",
        "examples": [{"de": "Es **gilt**.", "ru": "Действует."}],
    })
    enrich.save_cards(1, {"gelten": card}, {"gelten": "b1"}, "m")
    assert enrich.plan_repairs()[enrich.SPLIT] == 1
    # the card stays live while it waits — search must not lose the word
    assert enrich.get_card("gelten") is not None
    assert "gelten" in {w["lemma"] for w in enrich.claim(1, 10)}
    assert enrich.plan_repairs()[enrich.SPLIT] == 0     # self-limiting on its tag

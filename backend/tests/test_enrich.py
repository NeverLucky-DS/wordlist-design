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
    cards, skipped, unmatched = enrich.parse_response(["Haus", "Baum"], parsed)
    assert "Haus" in cards
    assert skipped == []
    assert unmatched == ["Baum"]     # dropped word tracked, never silently lost


def test_parse_response_routes_model_skip():
    parsed = {"words": [
        {"word": "ER", "skip": True, "skip_reason": "Groß-/Kleinschreibungs-Duplikat"},
        {"word": "Haus", "pos": "noun", "article": "das", "ru": "дом",
         "definition_de": "Gebäude.", "topic": "wohnen_zuhause",
         "examples": [{"de": "**Haus**", "ru": "дом"}]},
    ]}
    cards, skipped, unmatched = enrich.parse_response(["ER", "Haus"], parsed)
    assert list(cards) == ["Haus"]
    assert skipped == ["ER"]         # model-rejected word → skipped, not a card
    assert unmatched == []


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


def test_skip_and_requeue(db):
    enrich.claim(1, 1)               # lease Haus
    enrich.skip_words(["Haus"])
    assert enrich.progress()["skipped"] == 1
    assert "Haus" not in {w["lemma"] for w in enrich.claim(1, 10)}  # not re-served

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

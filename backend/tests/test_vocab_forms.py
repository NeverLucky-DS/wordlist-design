"""Telling headwords apart from the word forms the source dictionary also lists.

The interesting cases are all about WHERE a marker sits. A dictionary opens a
form's entry with "part II от machen", but it also drops "Tag- дневной в сл. сл."
at the tail of an eight-thousand-character entry for `Tag` — matching anywhere
in the body demotes some of the commonest nouns in German, so most of what is
asserted here is what must NOT be tagged.
"""
from __future__ import annotations

import json
import sqlite3

import pytest

from app.vocab import enrich, forms


def _make_vocab(path, entries):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE words(lemma TEXT UNIQUE, translations TEXT)")
    con.executemany("INSERT INTO words(lemma,translations) VALUES(?,?)",
                    [(l, json.dumps(t)) for l, t in entries])
    con.commit()
    con.close()


@pytest.fixture
def db(tmp_path, monkeypatch):
    vocab = tmp_path / "vocab.db"
    _make_vocab(vocab, [
        # forms — the marker opens the entry
        ("gemacht", ["1. part II от machen 2. part adj сделанный"]),
        ("Fakten", ["pl от Faktum"]),
        ("gäbe", ["gäbe prät conj от geben"]),
        ("alleine", ["разг. см. allein 1."]),
        ("mal", ["сокр. от einmal разг."]),
        ("Schnell", ["Schnell- в сл. сл.: быстроходный; скоростной"]),
        # real words — a trailing compound note after a long, ordinary entry
        ("Tag", ["1) день; сутки 2) " + "день. " * 200 + "Tag- дневной в сл. сл."]),
        ("Welt", ["1) мир, свет " + "общество " * 200 + "Welt- в сл. сл.: всемирный"]),
        # a lexicalised participle: the marker is present but buried past sense 1
        ("verwandt", ["1) родственный; сродни " + "близкий " * 90
                      + "2. part II от verwenden"]),
        # ordinary words with no marker at all
        ("machen", ["делать"]),
        ("Faktum", ["факт"]),
        ("geben", ["давать"]),
        ("allein", ["один"]),
        ("einmal", ["однажды"]),
        ("schnell", ["быстрый"]),
        ("Essen", ["еда"]),
        ("essen", ["есть"]),
        ("sie", ["она"]),
        ("Sie", ["Вы"]),
    ])
    enrich_db = tmp_path / "enrichment.db"
    monkeypatch.setattr(enrich, "VOCAB_DB", vocab)
    monkeypatch.setattr(enrich, "ENRICH_DB", enrich_db)
    enrich.ensure_schema()
    con = enrich._conn()
    # Every source word also has a card — that is what tagging operates on.
    # `Essen` carries an article so the capitalised-twin rule must spare it.
    articles = {"Essen": "das", "Tag": "der", "Welt": "die", "Fakten": None}
    for (lemma,) in con.execute("SELECT lemma FROM v.words").fetchall():
        con.execute(
            "INSERT INTO cards(lemma,pos,article,ru,created_at) VALUES(?,?,?,?,0)",
            (lemma, "noun" if lemma[:1].isupper() else "verb",
             articles.get(lemma), "x"))
    con.commit()
    return con


def _tags(con):
    return {r["lemma"]: (r["form_kind"], r["form_of"])
            for r in con.execute(
                "SELECT lemma, form_kind, form_of FROM cards WHERE form_kind IS NOT NULL")}


def test_marker_at_the_head_tags_the_form(db):
    forms.tag_forms(db)
    tags = _tags(db)
    assert tags["gemacht"] == ("inflection", "machen")
    assert tags["Fakten"] == ("inflection", "Faktum")
    assert tags["gäbe"] == ("inflection", "geben")
    assert tags["alleine"] == ("variant", "allein")
    assert tags["mal"] == ("abbrev", "einmal")
    assert tags["Schnell"] == ("compound", "schnell")


def test_trailing_compound_note_leaves_a_real_word_alone(db):
    """`Tag` mentions "Tag- в сл. сл." 8k characters in. Tagging on a bare
    substring match demoted Hand, Weg, Tag, Tod, Grund, Welt, Höhe and Art."""
    forms.tag_forms(db)
    tags = _tags(db)
    assert "Tag" not in tags
    assert "Welt" not in tags


def test_lexicalised_participle_is_not_a_form(db):
    """`verwandt` is an adjective in its own right; its entry only reaches
    "part II от verwenden" after the real senses."""
    forms.tag_forms(db)
    assert "verwandt" not in _tags(db)


def test_nominalisation_with_an_article_survives_the_twin_rule(db):
    """`das Essen` is a word; `Sie` next to `sie` is a sentence-initial capital.
    The article is what separates them."""
    forms.tag_forms(db)
    tags = _tags(db)
    assert "Essen" not in tags
    assert tags["Sie"] == ("capitalised", "sie")


def test_plain_words_are_untouched(db):
    forms.tag_forms(db)
    tags = _tags(db)
    for word in ("machen", "Faktum", "geben", "allein", "einmal", "schnell", "essen"):
        assert word not in tags


def test_rerun_is_idempotent(db):
    first = forms.tag_forms(db)
    second = forms.tag_forms(db)
    assert second["tagged"] == first["tagged"]
    assert second["cleared"] == 0


def test_a_tag_is_released_when_it_no_longer_applies(db):
    """A card tagged by an earlier, looser rule must not keep the tag forever —
    otherwise every false positive we fix stays demoted in production."""
    forms.tag_forms(db)
    db.execute("UPDATE cards SET form_kind='inflection', form_of='x' WHERE lemma='machen'")
    db.commit()
    stats = forms.tag_forms(db)
    assert stats["cleared"] == 1
    assert "machen" not in _tags(db)

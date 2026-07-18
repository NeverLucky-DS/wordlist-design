"""Paradigm extraction from a Wiktionary dump.

The fixtures are trimmed copies of real `de-extract` entries, so the tag shapes
here are the ones the importer meets in production — including the noise it has
to drop (obsolete spellings, regional variants) and the declined comparative
cells that must not be mistaken for the bare degree.
"""
from __future__ import annotations

import gzip
import json
import sqlite3

import pytest

from app.vocab import morph


def _forms(*items):
    return [{"form": f, "tags": list(t)} for f, t in items]


GEBEN = {
    "word": "geben", "pos": "verb", "lang_code": "de",
    "forms": _forms(
        ("ich gebe", ("first-person", "singular", "present", "active", "indicative")),
        ("du gibst", ("second-person", "singular", "present", "active", "indicative")),
        ("er/sie/es gibt", ("third-person", "singular", "present", "active", "indicative")),
        ("wir geben", ("first-person", "plural", "present", "active", "indicative")),
        ("ihr gebt", ("second-person", "plural", "present", "active", "indicative")),
        ("sie geben", ("third-person", "plural", "present", "active", "indicative")),
        ("ich gab", ("past", "first-person", "singular", "active", "indicative")),
        ("gegeben", ("participle-2", "perfect")),
        ("haben", ("auxiliary", "perfect")),
        ("gib!", ("imperative", "second-person", "singular", "present", "active")),
        ("gebt!", ("imperative", "plural")),
        ("ich gäbe", ("subjunctive-ii", "first-person", "singular", "active")),
        ("gäb", ("subjunctive-ii", "first-person", "singular", "active", "obsolete")),
        ("strong", ("table-tags",)),
    ),
}

HAUS = {
    "word": "Haus", "pos": "noun", "lang_code": "de",
    "forms": _forms(
        ("Haus", ("nominative", "singular")), ("Hauses", ("genitive", "singular")),
        ("Haus", ("dative", "singular")), ("Haus", ("accusative", "singular")),
        ("Häuser", ("nominative", "plural")), ("Häuser", ("genitive", "plural")),
        ("Häusern", ("dative", "plural")), ("Häuser", ("accusative", "plural")),
        ("Hauß", ("alternative", "obsolete")),
        ("Häuschen", ("diminutive", "neuter")),
    ),
}

GUT = {
    "word": "gut", "pos": "adj", "lang_code": "de",
    "forms": _forms(
        ("besser", ("comparative",)),
        ("am besten", ("superlative",)),
        # the declined cells — same degree tag, many more tags
        ("besserer", ("comparative", "nominative", "strong", "singular", "masculine")),
        ("bessere", ("comparative", "nominative", "strong", "singular", "feminine")),
    ),
}

ENGLISH = {"word": "give", "pos": "verb", "lang_code": "en", "forms": _forms(("gives", ("present",)))}


def test_verb_paradigm_keeps_the_stem_change():
    p = morph.paradigm_of(GEBEN)
    assert p["praesens"] == {"ich": "gebe", "du": "gibst", "er": "gibt",
                             "wir": "geben", "ihr": "gebt", "sie": "geben"}
    assert p["praeteritum"] == "gab"
    assert p["partizip2"] == "gegeben"
    assert p["hilfsverb"] == "haben"


def test_subject_pronoun_and_bang_are_stripped():
    """Forms arrive as "du gibst" and "gib!"; the UI supplies the label itself,
    so storing the pronoun would print it twice."""
    p = morph.paradigm_of(GEBEN)
    assert p["imperativ_du"] == "gib"
    assert p["imperativ_ihr"] == "gebt"
    assert p["konjunktiv2"] == "gäbe"       # not the obsolete "gäb"


def test_noun_paradigm_covers_all_four_cases():
    p = morph.paradigm_of(HAUS)
    assert p["sg"] == {"nom": "Haus", "gen": "Hauses", "dat": "Haus", "akk": "Haus"}
    assert p["pl"]["dat"] == "Häusern"      # the -n a learner keeps dropping


def test_obsolete_and_diminutive_forms_are_dropped():
    p = morph.paradigm_of(HAUS)
    assert "Hauß" not in json_values(p)
    assert "Häuschen" not in json_values(p)


def test_bare_degree_wins_over_its_declined_cells():
    """"besser" and "besserer" both carry `comparative`; only the tag COUNT
    tells them apart."""
    assert morph.paradigm_of(GUT) == {"komparativ": "besser", "superlativ": "am besten"}


def test_unknown_pos_yields_nothing():
    assert morph.paradigm_of({"word": "und", "pos": "conj", "forms": []}) == {}


def json_values(obj):
    if isinstance(obj, dict):
        return [v for sub in obj.values() for v in json_values(sub)]
    if isinstance(obj, list):
        return [v for sub in obj for v in json_values(sub)]
    return [obj]


@pytest.fixture
def dump(tmp_path):
    path = tmp_path / "dump.jsonl.gz"
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for entry in (GEBEN, HAUS, GUT, ENGLISH):
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path


@pytest.fixture
def con(tmp_path):
    c = sqlite3.connect(tmp_path / "enrichment.db")
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE cards(lemma TEXT PRIMARY KEY, pos TEXT)")
    c.executemany("INSERT INTO cards(lemma,pos) VALUES(?,?)",
                  [("geben", "verb"), ("Haus", "noun"), ("Xyzzy", "noun")])
    c.commit()
    return c


def test_import_reads_gzip_and_skips_other_languages(dump, con):
    stats = morph.import_dump(dump, con)
    assert stats["read"] == 3        # the English entry never reaches the filter
    rows = {r["lemma"] for r in con.execute("SELECT lemma FROM morphology")}
    assert rows == {"geben", "Haus"}  # `gut` has no card, `Xyzzy` no dump entry


def test_import_only_known_can_be_turned_off(dump, con):
    morph.import_dump(dump, con, only_known=False)
    rows = {r["lemma"] for r in con.execute("SELECT lemma FROM morphology")}
    assert "gut" in rows


def test_import_is_rerunnable(dump, con):
    first = morph.import_dump(dump, con)
    second = morph.import_dump(dump, con)
    assert second["stored"] == first["stored"]
    assert second["total"] == first["total"]


def test_pos_is_part_of_the_key(dump, con):
    """Morgen (noun) and morgen (adverb) are different words; a paradigm keyed on
    lemma alone would hand one of them the other's table."""
    morph.import_dump(dump, con)
    row = con.execute(
        "SELECT data FROM morphology WHERE lemma='geben' AND pos='verb'").fetchone()
    assert row is not None
    assert con.execute(
        "SELECT COUNT(*) FROM morphology WHERE lemma='geben' AND pos='noun'"
    ).fetchone()[0] == 0

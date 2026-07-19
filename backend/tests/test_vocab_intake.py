"""Admitting new headwords from a Wiktionary dump, and the closed class by hand.

Both modules exist because of one measurement (2026-07-19, external corpus of
Goethe-topic Wikipedia articles): 82 % of the words we failed to explain were
missing from the source outright, not botched by the model. So most of what is
asserted here is about what must NOT get in — proper nouns and abbreviations are
9 % of the dump, and re-admitting them would undo the skip rule's work.
"""
from __future__ import annotations

import gzip
import json
import sqlite3

import pytest

from app.vocab import funcwords, intake


def _dump(path, entries):
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for e in entries:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    return path


def _entry(word, pos, glosses=("eine Bedeutung",), **kw):
    e = {"word": word, "pos": pos, "lang_code": "de",
         "senses": [{"glosses": list(glosses)}]}
    e.update(kw)
    return e


def _vocab(path, lemmas=()):
    con = sqlite3.connect(path)
    con.execute("""CREATE TABLE words(
        id INTEGER PRIMARY KEY, lemma TEXT UNIQUE, article TEXT, pos TEXT,
        forms TEXT, translations TEXT, examples TEXT, synonyms TEXT,
        collocations TEXT, idioms TEXT, sources TEXT, by_source TEXT,
        zipf REAL, freq_rank INTEGER, level TEXT, enriched INTEGER DEFAULT 0)""")
    con.executemany("INSERT INTO words(lemma) VALUES(?)", [(l,) for l in lemmas])
    con.commit()
    con.close()
    return path


def _names(rows):
    return [r["lemma"] for r in rows]


# ── what gets in ─────────────────────────────────────────────────────────────
def test_admits_a_modern_word_the_old_dictionary_never_had(tmp_path):
    """`Internet` sits at zipf 5.23 and was not even a candidate before."""
    dump = _dump(tmp_path / "d.jsonl.gz", [
        _entry("Internet", "noun", ["weltweites Rechnernetz"], tags=["neuter"])])
    rows = list(intake.candidates(dump, min_zipf=2.5, known=set()))
    assert _names(rows) == ["Internet"]
    assert rows[0]["article"] == "das"
    assert json.loads(rows[0]["sources"]) == ["wiktionary"]
    # The German gloss is the only evidence the model gets — it must survive.
    by_source = json.loads(rows[0]["by_source"])["wiktionary"]
    assert by_source["glosses_de"] == ["weltweites Rechnernetz"]
    assert by_source["translations"] == []


def test_gender_tag_becomes_the_article(tmp_path):
    dump = _dump(tmp_path / "d.jsonl.gz", [
        _entry("Suchmaschine", "noun", tags=["feminine"]),
        _entry("Datenschutz", "noun", tags=["masculine"])])
    rows = {r["lemma"]: r["article"] for r in
            intake.candidates(dump, min_zipf=0, known=set())}
    assert rows == {"Suchmaschine": "die", "Datenschutz": "der"}


# ── what must stay out ───────────────────────────────────────────────────────
def test_proper_nouns_and_abbreviations_are_refused(tmp_path):
    """9 % of the dump is `pos: name`. Berlin/München/Peter is exactly the
    noise the skip rule already paid tokens to remove."""
    dump = _dump(tmp_path / "d.jsonl.gz", [
        _entry("Berlin", "name", ["Hauptstadt Deutschlands"]),
        _entry("EU", "abbrev", ["Europäische Union"]),
        _entry("Klimawandel", "noun", ["Änderung des Klimas"])])
    assert _names(list(intake.candidates(dump, min_zipf=0, known=set()))) \
        == ["Klimawandel"]


def test_affixes_and_phrases_are_refused(tmp_path):
    dump = _dump(tmp_path / "d.jsonl.gz", [
        _entry("un-", "prefix"), _entry("-heit", "suffix"),
        _entry("guten Tag", "phrase"), _entry("Nachhaltigkeit", "noun")])
    assert _names(list(intake.candidates(dump, min_zipf=0, known=set()))) \
        == ["Nachhaltigkeit"]


def test_entry_whose_senses_are_all_form_of_is_refused(tmp_path):
    """Only when EVERY sense is a form-of. A real word often carries one
    incidental form-of reading beside its own meaning, and dropping it on `any`
    would gut the base the way morph.py's form_of would."""
    dump = _dump(tmp_path / "d.jsonl.gz", [
        {"word": "gemachtes", "pos": "adj", "lang_code": "de",
         "senses": [{"form_of": [{"word": "machen"}]}]},
        {"word": "schon", "pos": "adv", "lang_code": "de",
         "senses": [{"form_of": [{"word": "schonen"}]},
                    {"glosses": ["bereits, zu einem früheren Zeitpunkt"]}]}])
    assert _names(list(intake.candidates(dump, min_zipf=0, known=set()))) \
        == ["schon"]


def test_multi_word_entries_are_refused(tmp_path):
    """The base held ZERO multi-word lemmas across 108 084 rows, and the first
    import let 922 in. Sorted by frequency the top of that list was conjugated
    phrase forms in BOTH word orders — `war dabei` and `dabei war` alike."""
    dump = _dump(tmp_path / "d.jsonl.gz", [
        _entry("war dabei", "verb"), _entry("dabei war", "verb"),
        _entry("von Zeit zu Zeit", "adv"),   # useful, but a collocation not a headword
        _entry("Internet", "noun")])
    assert _names(list(intake.candidates(dump, min_zipf=0, known=set()))) \
        == ["Internet"]


def test_frequency_floor_and_junk_filter(tmp_path):
    dump = _dump(tmp_path / "d.jsonl.gz", [
        _entry("Internet", "noun"),
        _entry("Quastenflosserartiger", "noun"),   # real, but far below the floor
        _entry("DER", "noun"),                     # all-caps -> junk
        _entry("x", "noun")])                      # single char -> junk
    assert _names(list(intake.candidates(dump, min_zipf=3.0, known=set()))) \
        == ["Internet"]


def test_known_lemma_is_not_readmitted_case_exactly(tmp_path):
    """Case is meaning here (Morgen vs morgen), so the check must not fold it."""
    dump = _dump(tmp_path / "d.jsonl.gz", [
        _entry("Morgen", "noun"), _entry("morgen", "adv")])
    rows = _names(list(intake.candidates(dump, min_zipf=0, known={"Morgen"})))
    assert rows == ["morgen"]


def test_a_lemma_we_already_hold_a_card_for_is_not_readmitted(tmp_path):
    """The 1996 rename files the CARD under the modern spelling while vocab.db
    only ever knew the old one — `Fluss` has a finished card, `Fluß` is the
    intake row. Keying off vocab.db alone would buy `Fluss` a second time and
    let INSERT OR REPLACE overwrite a good card."""
    vocab = _vocab(tmp_path / "vocab.db", ["Fluß"])
    enrichment = tmp_path / "enrichment.db"
    con = sqlite3.connect(enrichment)
    con.execute("CREATE TABLE cards(lemma TEXT PRIMARY KEY)")
    con.execute("INSERT INTO cards(lemma) VALUES('Fluss')")
    con.commit()
    con.close()

    known = intake.known_lemmas(vocab, enrichment)
    assert {"Fluß", "Fluss"} <= known

    dump = _dump(tmp_path / "d.jsonl.gz", [
        _entry("Fluss", "noun"), _entry("Schloss", "noun")])
    stats = intake.append(dump, vocab, min_zipf=0, enrichment=enrichment)
    assert stats["sample"] == ["Schloss"]


# ── writing ──────────────────────────────────────────────────────────────────
def test_empty_stub_database_raises_instead_of_admitting_everything(tmp_path):
    """VOCAB_DB defaults to an empty stub beside the real database whenever the
    env var is unset. Reading it silently gives `known = 0`, which makes every
    word we already own look new — the first real dry run reported 36 455 of
    them, `Mensch` and `Software` included."""
    stub = tmp_path / "vocab.db"
    sqlite3.connect(stub).close()          # exists, but has no `words` table
    with pytest.raises(RuntimeError, match="empty stub"):
        intake.known_lemmas(stub)


def test_a_real_but_empty_table_still_refuses(tmp_path):
    vocab = _vocab(tmp_path / "vocab.db")   # correct schema, no rows
    with pytest.raises(RuntimeError, match="refusing"):
        intake.known_lemmas(vocab)


def test_append_is_additive_and_rerunnable(tmp_path):
    vocab = _vocab(tmp_path / "vocab.db", ["Haus"])
    dump = _dump(tmp_path / "d.jsonl.gz", [
        _entry("Haus", "noun"), _entry("Internet", "noun")])

    first = intake.append(dump, vocab, min_zipf=0)
    assert first["written"] == 1
    second = intake.append(dump, vocab, min_zipf=0)
    assert second["written"] == 0          # nothing new, nothing duplicated


def test_written_counts_the_table_not_the_known_set(tmp_path):
    """`known` is deliberately wider than the words table — it also holds lemmas
    that have a card but no intake row (500 of them on the live base). Deriving
    `written` from it undercounted a real 20 074-row import as 19 574."""
    vocab = _vocab(tmp_path / "vocab.db", ["Haus"])
    enrichment = tmp_path / "e.db"
    con = sqlite3.connect(enrichment)
    con.execute("CREATE TABLE cards(lemma TEXT PRIMARY KEY)")
    con.execute("INSERT INTO cards(lemma) VALUES('Fluss')")   # card, no intake row
    con.commit()
    con.close()

    dump = _dump(tmp_path / "d.jsonl.gz", [_entry("Internet", "noun")])
    stats = intake.append(dump, vocab, min_zipf=0, enrichment=enrichment)
    assert stats["known"] == 2      # Haus + Fluss
    assert stats["written"] == 1    # but only one row was actually added
    assert stats["total"] == 2

    con = sqlite3.connect(vocab)
    rows = con.execute("SELECT lemma, level, enriched FROM words "
                       "ORDER BY lemma").fetchall()
    con.close()
    assert rows == [("Haus", None, 0), ("Internet", "unlisted", 0)]


def test_dry_run_writes_nothing(tmp_path):
    vocab = _vocab(tmp_path / "vocab.db", ["Haus"])
    dump = _dump(tmp_path / "d.jsonl.gz", [_entry("Internet", "noun")])
    stats = intake.append(dump, vocab, min_zipf=0, dry_run=True)
    assert stats["new"] == 1 and stats["written"] == 0
    con = sqlite3.connect(vocab)
    assert [r[0] for r in con.execute("SELECT lemma FROM words")] == ["Haus"]
    con.close()


# ── the closed class, written by hand ────────────────────────────────────────
@pytest.fixture
def cards_db(tmp_path):
    con = sqlite3.connect(tmp_path / "e.db")
    con.execute("""CREATE TABLE cards(lemma TEXT PRIMARY KEY, level TEXT,
        topic TEXT, pos TEXT, article TEXT, ru TEXT, confidence TEXT,
        register TEXT, data TEXT, model TEXT, prompt_version TEXT,
        schema_version INTEGER, enriched_by INTEGER, created_at REAL, zipf REAL)""")
    con.execute("""CREATE TABLE word_status(lemma TEXT PRIMARY KEY,
        status TEXT NOT NULL DEFAULT 'raw', attempts INTEGER NOT NULL DEFAULT 0,
        lease_owner INTEGER, lease_at REAL, updated_at REAL, phase TEXT)""")
    con.commit()
    yield con
    con.close()


def test_seed_writes_the_articles_the_model_would_not(cards_db):
    """`die` is zipf 7.48 and came back `skipped`; `der` went `failed` after
    three attempts. Both statuses are terminal — nothing brings them back."""
    stats = funcwords.seed(cards_db)
    assert stats["written"] == len(funcwords.CARDS)

    got = dict(cards_db.execute("SELECT lemma, ru FROM cards").fetchall())
    for article in ("der", "die", "den", "dem", "des"):
        assert article in got
    assert cards_db.execute(
        "SELECT status FROM word_status WHERE lemma='die'").fetchone()[0] == "done"


def test_contractions_spell_out_what_is_inside_them(cards_db):
    """"im = in dem" is A1 grammar a learner must simply be told, which is the
    whole reason the Wortform rule should not have eaten it."""
    funcwords.seed(cards_db)
    data = json.loads(cards_db.execute(
        "SELECT data FROM cards WHERE lemma='im'").fetchone()[0])
    assert data["grammar"]["zusammensetzung"] == "in + dem"
    assert data["grammar"]["kasus"] == "Dativ"
    assert data["examples"] and all(
        e["de"] and e["ru"] for e in data["examples"])


def test_seed_is_idempotent(cards_db):
    funcwords.seed(cards_db)
    before = cards_db.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
    funcwords.seed(cards_db)
    assert cards_db.execute("SELECT COUNT(*) FROM cards").fetchone()[0] == before


def test_repair_phases_cannot_requeue_a_handwritten_card(tmp_path, monkeypatch):
    """`der` and `des` sit in `failed`, which is what repair_ortho collects. Left
    unguarded it would hand them back to the model, the model would skip them by
    design, and `skip_words` would delete the card — the closed class would
    vanish again one run after being seeded."""
    from app.vocab import enrich

    monkeypatch.setattr(enrich, "ENRICH_DB", tmp_path / "e.db")
    monkeypatch.setattr(enrich, "VOCAB_DB", tmp_path / "missing-vocab.db")
    enrich.ensure_schema()

    con = enrich._conn()
    funcwords.seed(con)
    con.execute("""INSERT INTO cards(lemma, ru, model) VALUES('Handy','мобильник','mistral')""")
    con.commit()
    con.close()

    assert enrich.requeue(["der", "des", "Handy"], drop_card=True) == 1

    con = enrich._conn()
    live = {r[0] for r in con.execute("SELECT lemma FROM cards")}
    status = dict(con.execute("SELECT lemma, status FROM word_status").fetchall())
    con.close()
    assert {"der", "des"} <= live       # handwritten cards survive
    assert "Handy" not in live          # an ordinary card is still dropped
    assert status["der"] == "done"      # and is not put back up for grabs


def test_seed_never_clobbers_a_generated_card(cards_db):
    """If a later model pass produces a real card for one of these, it wins."""
    cards_db.execute(
        "INSERT INTO cards(lemma, ru, model) VALUES('euch', 'настоящая', 'mistral')")
    cards_db.commit()
    stats = funcwords.seed(cards_db)
    assert stats["kept_generated"] == 1
    assert cards_db.execute(
        "SELECT ru FROM cards WHERE lemma='euch'").fetchone()[0] == "настоящая"


# ── grammar keys per part of speech ──────────────────────────────────────────
def test_adverb_grammar_is_no_longer_silently_dropped():
    """`_norm_grammar` keeps only the keys listed for the part of speech, so a
    missing entry throws the model's answer away no matter how good it was. That
    is what emptied every one of the 1 271 adverb cards."""
    from app.vocab import enrich

    assert enrich._norm_grammar("adv", {"komparativ": "lieber",
                                        "superlativ": "am liebsten"}) == {
        "komparativ": "lieber", "superlativ": "am liebsten"}
    # The closed class needs the case a preposition governs.
    assert enrich._norm_grammar("other", {"kasus": "Dativ",
                                          "zusammensetzung": "in + dem"}) == {
        "kasus": "Dativ", "zusammensetzung": "in + dem"}


def test_grammar_keys_foreign_to_the_part_of_speech_are_still_dropped():
    from app.vocab import enrich

    assert enrich._norm_grammar("adv", {"genitiv": "des gern"}) == {}
    assert enrich._norm_grammar("noun", {"genitiv": "des Hauses",
                                         "plural": "die Häuser",
                                         "komparativ": "nonsense"}) == {
        "genitiv": "des Hauses", "plural": "die Häuser"}


def test_prompt_tells_the_model_that_a_wiktionary_row_is_not_thin_evidence():
    """New rows carry no Russian and one source, and the skip rules list exactly
    those as marks of a real word. Without this the model would skip the modern
    vocabulary the whole intake exists to add."""
    from app.vocab import enrich

    prompt = enrich.build_prompt([{"lemma": "Internet", "sources": ["wiktionary"]}])
    assert "glosses_de" in prompt
    assert "KEIN Hinweis auf ein zweifelhaftes" in prompt
    # And the grammar table must reach the model, not just live in Python.
    assert "GRAMMATIK-TABELLE" in prompt
    for key in ("genitiv", "praeteritum", "komparativ", "kasus"):
        assert key in prompt

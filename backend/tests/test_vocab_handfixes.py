"""Hand-adjudicated exceptions to the rules in `forms.py`.

Two things have to hold or the file is decoration. `tag_forms` clears every tag
it did not just write, so an adjudicated tag has to be re-applied by the same
pass rather than written once. And a card field lives in two places — a promoted
column and inside `data` — so a correction that moves only one leaves the list
row and the open card disagreeing about the same word.
"""
from __future__ import annotations

import json
import sqlite3

import pytest
from app.vocab import forms, handfixes


def card(con, lemma, pos="other", article=None, ru="", ru_all=None):
    con.execute(
        "INSERT INTO cards(lemma,pos,article,ru,data) VALUES(?,?,?,?,?)",
        (lemma, pos, article, ru,
         json.dumps({"ru": ru, "ru_all": ru_all or [ru], "article": article},
                    ensure_ascii=False)))


@pytest.fixture
def db(tmp_path):
    """A card table shaped like the real one, plus a `v.words` for tag_forms."""
    con = sqlite3.connect(tmp_path / "enrichment.db")
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE cards(lemma TEXT PRIMARY KEY, pos TEXT, article TEXT,
                   ru TEXT, data TEXT, form_kind TEXT, form_of TEXT)""")
    vocab = tmp_path / "vocab.db"
    v = sqlite3.connect(vocab)
    v.execute("CREATE TABLE words(lemma TEXT UNIQUE, translations TEXT)")
    v.commit()
    v.close()
    con.execute("ATTACH DATABASE ? AS v", (str(vocab),))
    yield con
    con.close()


def _write(monkeypatch, tmp_path, twins: str = "", fixes: str = ""):
    t, f = tmp_path / "not_headwords.tsv", tmp_path / "card_fixes.tsv"
    t.write_text(twins, encoding="utf-8")
    f.write_text(fixes, encoding="utf-8")
    monkeypatch.setattr(handfixes, "TWINS_FILE", t)
    monkeypatch.setattr(handfixes, "FIXES_FILE", f)
    handfixes.load_twins.cache_clear()
    handfixes.load_fixes.cache_clear()


def test_an_adjudicated_tag_survives_tag_forms(db, tmp_path, monkeypatch):
    """`_capitalised_twins` only ever inspects the CAPITALISED half of a pair.

    A spurious lowercase entry beside a real noun — `frieden` next to `der
    Frieden` — is therefore invisible to it, and 32 of the 400 flagged cards
    were exactly that shape.
    """
    card(db, "Frieden", pos="noun", article="der", ru="мир")
    card(db, "frieden", pos="noun", ru="мир")
    db.commit()
    _write(monkeypatch, tmp_path, twins="frieden\tform\tFrieden\tненормативное написание\n")

    forms.tag_forms(db)
    row = db.execute("SELECT form_kind, form_of FROM cards WHERE lemma='frieden'").fetchone()
    assert (row["form_kind"], row["form_of"]) == ("variant", "Frieden")
    # the real noun is untouched
    assert db.execute("SELECT form_kind FROM cards WHERE lemma='Frieden'").fetchone()[0] is None


def test_an_exempt_word_is_never_tagged(db, tmp_path, monkeypatch):
    """`mal` sits at zipf 6.28 and was tagged `abbrev`, so search demoted one of
    the commonest particles in German below every noun that matched it."""
    card(db, "Mal", pos="noun", article="das", ru="раз")
    card(db, "mal", pos="other", ru="раз")
    db.commit()
    _write(monkeypatch, tmp_path, twins="mal\tkeep\t\tчастица, не сокращение\n")

    forms.tag_forms(db)
    assert db.execute("SELECT form_kind FROM cards WHERE lemma='mal'").fetchone()[0] is None


def test_gloss_correction_moves_both_copies(db, tmp_path, monkeypatch):
    card(db, "Ich", pos="noun", article="das", ru="я", ru_all=["я"])
    db.commit()
    _write(monkeypatch, tmp_path, fixes="Ich\tru\tсвоё «я», эго\tфилософский термин\n")

    assert handfixes.apply_fixes(db) == 1
    ru, data = db.execute("SELECT ru, data FROM cards WHERE lemma='Ich'").fetchone()
    stored = json.loads(data)
    assert ru == "своё «я», эго"
    assert stored["ru"] == ru and stored["ru_all"][0] == ru


def test_splitting_ru_all_carries_the_promoted_meaning_with_it(db, tmp_path, monkeypatch):
    """`ru` is `ru_all[0]` by contract; re-splitting moves what that first
    meaning is, so the column has to follow or the row shows a string the card
    no longer contains."""
    card(db, "ankommen", pos="verb", ru="приходить, прибывать",
         ru_all=["приходить, прибывать"])
    db.commit()
    _write(monkeypatch, tmp_path,
           fixes='ankommen\tru_all\t["приходить", "прибывать"]\tдва значения\n')

    assert handfixes.apply_fixes(db) == 1
    ru, data = db.execute("SELECT ru, data FROM cards WHERE lemma='ankommen'").fetchone()
    assert ru == "приходить"
    assert json.loads(data)["ru_all"] == ["приходить", "прибывать"]


def test_article_correction_moves_both_copies(db, tmp_path, monkeypatch):
    card(db, "Eltern", pos="noun", article=None, ru="родители")
    db.commit()
    _write(monkeypatch, tmp_path, fixes="Eltern\tarticle\tdie\tpluralia tantum\n")

    assert handfixes.apply_fixes(db) == 1
    article, data = db.execute(
        "SELECT article, data FROM cards WHERE lemma='Eltern'").fetchone()
    assert article == "die" and json.loads(data)["article"] == "die"


def test_apply_fixes_is_idempotent(db, tmp_path, monkeypatch):
    card(db, "Eltern", pos="noun", article=None, ru="родители")
    db.commit()
    _write(monkeypatch, tmp_path, fixes="Eltern\tarticle\tdie\tpluralia tantum\n")
    assert handfixes.apply_fixes(db) == 1
    assert handfixes.apply_fixes(db) == 0


def test_unknown_fields_are_ignored(db, tmp_path, monkeypatch):
    """The file is a narrow repair channel, not a back door for rewriting cards."""
    card(db, "Haus", pos="noun", article="das", ru="дом")
    db.commit()
    _write(monkeypatch, tmp_path,
           fixes="Haus\tdefinition_de\tetwas ganz anderes\t—\nHaus\tpos\tverb\t—\n")
    assert handfixes.load_fixes() == {}
    assert handfixes.apply_fixes(db) == 0


def test_the_shipped_files_parse_and_point_at_real_cards():
    """The vendored data itself, not a fixture: a typo here is silent."""
    handfixes.load_twins.cache_clear()
    handfixes.load_fixes.cache_clear()
    tag, keep = handfixes.load_twins()
    fixes = handfixes.load_fixes()
    assert tag and keep and fixes
    assert not (set(tag) & keep), "a lemma cannot be both tagged and exempt"
    for lemma, fields in fixes.items():
        assert set(fields) <= set(handfixes._FIELDS), lemma
        if "ru_all" in fields:
            assert isinstance(fields["ru_all"], list) and fields["ru_all"]
        if "article" in fields:
            assert fields["article"] in ("der", "die", "das"), lemma


def test_kind_comes_from_the_relation_not_from_the_capital(db, tmp_path, monkeypatch):
    """`Intensivität` is a misspelling of `Intensität`, not a case twin.

    Both start with a capital, so inferring the kind from the lemma's own first
    letter labelled it «форма от» — which says the word is a form of the other.
    It is a spelling of the other. Only a pair differing by nothing but case is
    a case pair.
    """
    card(db, "Intensität", pos="noun", article="die", ru="интенсивность")
    card(db, "Intensivität", pos="noun", article="die", ru="интенсивность")
    card(db, "Bauen", pos="verb", ru="строить")
    card(db, "bauen", pos="verb", ru="строить")
    db.commit()
    _write(monkeypatch, tmp_path,
           twins="Intensivität\tform\tIntensität\t—\nBauen\tform\tbauen\t—\n")

    forms.tag_forms(db)
    kinds = {r["lemma"]: r["form_kind"] for r in
             db.execute("SELECT lemma, form_kind FROM cards")}
    assert kinds["Intensivität"] == "variant"
    assert kinds["Bauen"] == "capitalised"


def test_a_lowercase_noun_is_a_spelling_not_a_form(db, tmp_path, monkeypatch):
    """German has no lowercase nouns, so `frieden` is a misspelling of `Frieden`.

    It IS a case pair by string comparison, but `capitalised` renders as «форма
    от», and a form is not what it is. `capitalised` stays reserved for the
    direction it was built for: a capital standing in for a real lowercase word.
    """
    card(db, "Frieden", pos="noun", article="der", ru="мир")
    card(db, "frieden", pos="noun", ru="мир")
    db.commit()
    _write(monkeypatch, tmp_path, twins="frieden\tform\tFrieden\t—\n")
    forms.tag_forms(db)
    row = db.execute("SELECT form_kind FROM cards WHERE lemma='frieden'").fetchone()
    assert row["form_kind"] == "variant"


def test_the_kind_can_be_named_outright_when_inference_cannot_see_it(db, tmp_path,
                                                                     monkeypatch):
    """`Spiele` is the plural of `das Spiel`, filed as a headword of its own.

    Nothing about the two strings says "plural" rather than "some other
    spelling", and the UI renders those differently — «форма от» against
    «вариант написания». So the file may name the kind.
    """
    card(db, "Spiel", pos="noun", article="das", ru="игра")
    card(db, "Spiele", pos="noun", article="das", ru="игра")
    db.commit()
    _write(monkeypatch, tmp_path, twins="Spiele\tinflection\tSpiel\t—\n")
    forms.tag_forms(db)
    row = db.execute("SELECT form_kind, form_of FROM cards WHERE lemma='Spiele'").fetchone()
    assert (row["form_kind"], row["form_of"]) == ("inflection", "Spiel")

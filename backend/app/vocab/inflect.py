"""Resolve an inflected form to the headword that carries its card.

The hole this closes. Typing the commonest words in German answered garbage:
`ist` (zipf 7.08) returned `Ist-Wert` "фактическое значение", `mich` returned
`Michelin-Männchen`, `bin` returned `Bingo`, `gibt` returned nothing at all.
Measured against the live search on 2026-07-26, every one of `ist sind war bin
hat hatte wird wurde mich mir ihm ihn kann muss will eine einer diese meine
seine dieses` lied. Nothing matched exactly, so pg_trgm filled the silence with
the nearest string.

Why there is no card to find. The enrichment prompt refuses word forms, and it
is *right* to: `ist` is a cell of `sein`, and `sein` already carries the card.
`vocab/funcwords.py` makes the same argument for the closed class it seeds by
hand. So the fix cannot be "enrich them" — it has to be "know where they point".

We already own both halves of that mapping and have never joined them:

  * `morphology` holds 63 340 paradigms imported from de.wiktionary — six
    present-tense persons, Präteritum, Partizip II, Konjunktiv II, imperatives
    for verbs; all four cases in both numbers for nouns; the two degrees for
    adjectives. Expanded, that is ~173 000 distinct surface forms.
  * `cards` holds the headwords those paradigms belong to.

So this module is a JOIN, not an enrichment: no model call, no tokens, nothing
invented. A form resolves to a lemma we already publish, or it does not resolve.

Two things it deliberately does NOT do.

It does not write cards. 2 220 of these forms happen to sit in `vocab.db` as
lemmas of their own, and giving each a card was the obvious move — but it would
have covered only those 2 220 out of 173 000, inflated the mirror, and put 2 220
more rows into a ranking that `forms.py` spent an entire pass teaching to push
forms DOWN. An index answers the whole class and competes with nothing.

It does not let a verb paradigm claim a pronoun. Wiktionary conjugates reflexive
verbs with the pronoun attached, so `mich` appears as a "form" of `besinnen`,
`erholen`, `verlieben` and 24 others. `mich` is the accusative of `ich` and
nothing else. `_PRONOUNS` blocks the whole closed class from the generated side;
those forms are declined here by hand instead, from tables every A1 textbook
prints.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import NamedTuple

# ── the closed class, by hand ────────────────────────────────────────────────
# Finite, and not derivable from anything we hold: no dump conjugates pronouns,
# and `morphology` covers noun/verb/adj only (50 521 / 8 325 / 4 494 rows, zero
# pronouns). The same argument `funcwords.py` makes for `im = in dem` — A1
# grammar you simply know — applies to `mir` being the dative of `ich`.


class Form(NamedTuple):
    """One surface form and where it points.

    `ru` is filled only for the handwritten closed class, where the cell IS the
    answer: someone typing `mir` wants "мне", and sending them to `ich` "я"
    alone would make them work the paradigm out themselves. For generated forms
    the base card's own `ru` is the answer and this stays empty.
    """

    base: str
    cell_de: str
    cell_ru: str
    ru: str = ""
    pos: str = ""


def _f(base: str, cell_de: str, cell_ru: str, ru: str = "", pos: str = "other") -> Form:
    return Form(base, cell_de, cell_ru, ru, pos)


# Personal pronouns, nominative excluded — those are headwords with cards of
# their own.
#
# The genitive series (`meiner`, `seiner`, `ihrer`, `deiner`) is deliberately
# NOT here, even though the forms exist. In modern German those strings are read
# as possessives — "mit ihrer Mutter", "wegen seiner Arbeit" — and the pronoun
# genitive survives only in fixed literary turns ("gedenke meiner"). Glossing
# `ihrer` at zipf 5.76 as an archaism would answer the rare reading and hide the
# one the learner actually met, so the possessive table below claims them.
_PERSONAL: dict[str, Form] = {
    "mich": _f("ich", "Akkusativ von „ich“", "винительный падеж от ich", "меня"),
    "mir": _f("ich", "Dativ von „ich“", "дательный падеж от ich", "мне"),
    "dich": _f("du", "Akkusativ von „du“", "винительный падеж от du", "тебя"),
    "dir": _f("du", "Dativ von „du“", "дательный падеж от du", "тебе"),
    "ihn": _f("er", "Akkusativ von „er“", "винительный падеж от er", "его"),
    "ihm": _f("er", "Dativ von „er“ und „es“", "дательный падеж от er / es", "ему"),
    "uns": _f("wir", "Akkusativ und Dativ von „wir“", "винительный и дательный от wir",
              "нас, нам"),
    "euch": _f("ihr", "Akkusativ und Dativ von „ihr“", "винительный и дательный от ihr",
               "вас, вам"),
    "ihnen": _f("sie", "Dativ Plural von „sie“", "дательный падеж мн. ч. от sie", "им"),
    "Ihnen": _f("Sie", "Dativ der Höflichkeitsform", "дательный падеж вежливой формы Sie",
                "Вам"),
}

# Reflexives. `sich` has its own card; the other persons borrow the personal
# pronoun and are the reason a verb paradigm must never claim them.
_REFLEXIVE = ("mich", "dich", "sich", "uns", "euch")

# Possessive and determiner endings. One table, because German declines all of
# them the same way — der-words differ only in that the bare stem is not a form.
#
# (ending, cell in German, cell in Russian)
_ENDINGS: tuple[tuple[str, str, str], ...] = (
    ("e", "Nominativ/Akkusativ feminin oder Plural", "им. / вин. п. ж. р. или мн. ч."),
    ("en", "Akkusativ maskulin, Dativ Plural", "вин. п. м. р., дат. п. мн. ч."),
    ("em", "Dativ maskulin oder neutrum", "дат. п. м. или ср. р."),
    ("er", "Nominativ maskulin, Genitiv/Dativ feminin", "им. п. м. р., род./дат. п. ж. р."),
    ("es", "Genitiv maskulin/neutrum, Nominativ neutrum", "род. п. м./ср. р., им. п. ср. р."),
)

# stem -> (base lemma to point at, what the word is, Russian gloss of the stem)
_POSSESSIVE: tuple[tuple[str, str, str, str], ...] = (
    ("mein", "mein", "Possessivartikel „mein“", "мой"),
    ("dein", "dein", "Possessivartikel „dein“", "твой"),
    ("sein", "sein", "Possessivartikel „sein“", "его"),
    ("ihr", "ihr", "Possessivartikel „ihr“", "её, их"),
    ("unser", "unser", "Possessivartikel „unser“", "наш"),
    ("euer", "euer", "Possessivartikel „euer“", "ваш"),
    # Points at `Sie`, not at `Ihr`: only `Sie` carries a card, and the polite
    # possessive is the possessive OF `Sie` anyway.
    ("Ihr", "Sie", "Possessivartikel der Höflichkeitsform („Sie“)", "Ваш"),
)

_DETERMINER: tuple[tuple[str, str, str, str], ...] = (
    ("ein", "ein", "unbestimmter Artikel", "один, неопределённый артикль"),
    ("kein", "kein", "Negationsartikel „kein“", "никакой"),
    ("dies", "dieser", "Demonstrativpronomen „dieser“", "этот"),
    ("jen", "jener", "Demonstrativpronomen „jener“", "тот"),
    ("welch", "welcher", "Interrogativpronomen „welcher“", "какой"),
    ("jed", "jeder", "Indefinitpronomen „jeder“", "каждый"),
    ("all", "alle", "Indefinitpronomen „alle“", "весь, все"),
    ("manch", "mancher", "Indefinitpronomen „mancher“", "некоторый"),
    ("solch", "solcher", "Demonstrativpronomen „solcher“", "такой"),
)


def _stem_form(stem: str, ending: str) -> str:
    """Attach a declension ending. `euer` drops its second e: euer + en -> euren."""
    return ("eur" + ending) if stem == "euer" else (stem + ending)


def _closed_class() -> dict[str, Form]:
    out: dict[str, Form] = dict(_PERSONAL)
    for stem, base, what, gloss in _POSSESSIVE + _DETERMINER:
        for ending, cell_de, cell_ru in _ENDINGS:
            form = _stem_form(stem, ending)
            if form in out:          # a personal pronoun already claimed it
                continue
            out[form] = Form(base, f"{what}, {cell_de}", f"{what} — {cell_ru}",
                             gloss, "other")
    return out


CLOSED_CLASS: dict[str, Form] = _closed_class()

# Every closed-class surface form, plus the reflexives. A generated paradigm may
# never produce any of these: Wiktionary conjugates `sich erholen` as "ich erhole
# mich", so `mich` shows up as a form of 27 different verbs and would outvote the
# one answer that is true.
_PRONOUNS: frozenset[str] = frozenset(CLOSED_CLASS) | frozenset(_REFLEXIVE) | frozenset(
    ("ich", "du", "er", "sie", "es", "wir", "ihr", "Sie", "man",
     "der", "die", "das", "den", "dem", "des", "wer", "was")
)

# ── the generated side ───────────────────────────────────────────────────────
_PERSON_DE = {"ich": "1. Person Singular", "du": "2. Person Singular",
              "er": "3. Person Singular", "wir": "1. Person Plural",
              "ihr": "2. Person Plural", "sie": "3. Person Plural"}
_PERSON_RU = {"ich": "1 л. ед. ч.", "du": "2 л. ед. ч.", "er": "3 л. ед. ч.",
              "wir": "1 л. мн. ч.", "ihr": "2 л. мн. ч.", "sie": "3 л. мн. ч."}

_SCALAR = {
    "praeteritum": ("Präteritum", "прошедшее время (претерит)"),
    "partizip2": ("Partizip II", "причастие II"),
    "konjunktiv2": ("Konjunktiv II", "сослагательное наклонение"),
    "imperativ_du": ("Imperativ (du)", "повелительное наклонение (ты)"),
    "imperativ_ihr": ("Imperativ (ihr)", "повелительное наклонение (вы)"),
    "komparativ": ("Komparativ", "сравнительная степень"),
    "superlativ": ("Superlativ", "превосходная степень"),
}
_CASE_DE = {"nom": "Nominativ", "gen": "Genitiv", "dat": "Dativ", "akk": "Akkusativ"}
_CASE_RU = {"nom": "именительный", "gen": "родительный", "dat": "дательный",
            "akk": "винительный"}
_NUM_DE = {"sg": "Singular", "pl": "Plural"}
_NUM_RU = {"sg": "ед. ч.", "pl": "мн. ч."}


def _surface(value: str, *, kind: str) -> str:
    """The one token in a paradigm cell that a user would actually type.

    Cells are not uniformly single words, and the exceptions do not point the
    same way — which is why this cannot be "take the last token" or "take the
    first". Measured on the live `morphology` table:

        aufstehen  praesens.ich = "stehe auf"      finite verb FIRST
        anfangen   praeteritum  = "fing an"        finite verb FIRST
        gut        superlativ   = "am besten"      the word is LAST

    A separable verb is then dropped rather than indexed under its finite half:
    "steht" is not a form of `aufstehen`, it is a form of `stehen` — which
    carries its own paradigm and its own card. Indexing it here would point
    `steht` at every -stehen compound in the dump and bury the answer.

    ⚠️ `info/CRITICAL-LINKS.md` §6a says these cells arrive "с местоимениями
    (`du gibst`), а не голыми". They do not: `geben` stores `{"du": "gibst"}`.
    The claim is about the dump, not about what `morph.py` stored.
    """
    text = (value or "").strip()
    if not text:
        return ""
    parts = text.split()
    if len(parts) == 1:
        return parts[0]
    if kind == "degree" and len(parts) == 2 and parts[0] in ("am", "der", "die", "das"):
        return parts[1]         # "am besten" -> besten
    return ""                   # separable verb, or a phrase we will not index


def paradigm_forms(paradigm: dict, pos: str) -> Iterator[tuple[str, str, str]]:
    """Expand one `morphology` row into (surface form, cell_de, cell_ru).

    Skips anything that is not a single plain word, and anything the closed
    class already owns.
    """
    if not isinstance(paradigm, dict):
        return
    for person, raw in (paradigm.get("praesens") or {}).items():
        if isinstance(raw, str) and (word := _surface(raw, kind="verb")):
            yield word, f"Präsens, {_PERSON_DE.get(person, person)}", \
                f"настоящее время, {_PERSON_RU.get(person, person)}"
    for key, (de, ru) in _SCALAR.items():
        raw = paradigm.get(key)
        kind = "degree" if key in ("komparativ", "superlativ") else "verb"
        if isinstance(raw, str) and (word := _surface(raw, kind=kind)):
            yield word, de, ru
    if pos == "noun":
        for num in ("sg", "pl"):
            block = paradigm.get(num)
            if not isinstance(block, dict):
                continue
            for case, raw in block.items():
                key = str(case).lower()[:3]
                if key in _CASE_DE and isinstance(raw, str) \
                        and (word := _surface(raw, kind="noun")):
                    yield word, f"{_CASE_DE[key]} {_NUM_DE[num]}", \
                        f"{_CASE_RU[key]} падеж, {_NUM_RU[num]}"


def is_blocked(form: str) -> bool:
    """A generated paradigm may not claim this surface form."""
    return form in _PRONOUNS


def index_rows(cards: Iterator[tuple[str, str, dict]]) -> dict[str, list[Form]]:
    """Build form -> candidate bases from (lemma, pos, paradigm) triples.

    Case is never folded here, for the same reason it is never folded anywhere
    else in this pipeline: `Morgen` and `morgen` are different words, and so are
    `Sagen` (plural of `die Sage`) and `sagen`.
    """
    out: dict[str, list[Form]] = {}
    for lemma, pos, paradigm in cards:
        for word, cell_de, cell_ru in paradigm_forms(paradigm, pos):
            if word == lemma or is_blocked(word) or len(word) < 2:
                continue
            out.setdefault(word, []).append(Form(lemma, cell_de, cell_ru, "", pos))
    return out

"""Tell headwords apart from the word forms the source dictionary also listed.

`vocab.db` is a dump of bilingual dictionaries, and a dictionary lists more than
headwords: it also carries participles (`gemacht`), plurals (`Fakten`), preterite
forms (`gäbe`), combining forms (`Schnell-` "в сл. сл."), abbreviations and bare
cross-references (`alleine` → "разг. см. allein"). Enrichment could not tell
those from real words, so each got a card of its own.

That would be harmless if they sank. They do the opposite. `wordfreq` folds case
and counts surface forms, so `Schnell` is handed the frequency of the adjective
`schnell` (5.51, the 354th most common word in German) and `gemacht` the weight
of every "hat gemacht" ever written. Search ranks by `zipf` right after match
quality, so these are precisely the entries that surface first: measured on the
live base, non-words are 16% of the zipf 4–5 band against 1% of the tail below 2.
Looking up "обманывать" answered `linken` — a rare slang verb wearing the
frequency of `link` — while `täuschen` and `betrügen` sat below it.

So we tag rather than delete, the way Yandex.Dictionary and Linguee do: a form
stays reachable, it just stops pretending to be a headword. Typing `gemacht`
still finds it, now labelled "форма от machen".

**The signal is the lexicographer's, not ours.** Every marker below is the source
dictionary stating in its own text that an entry is not a headword. That matters
because the obvious alternative — running a lemmatiser over the base and dropping
whatever folds — is wrong: `simplemma` maps `bitte`→`bitten`, `danke`→`danken`,
`später`→`spät`, `lieber`→`lieb` and `weiß`→`wissen`, all of which are words a
B1–C1 learner needs in their own right. A lemmatiser cannot see lexicalisation;
the dictionary already did. `simplemma` is used here only to *resolve* a base
form the marker did not name, never to decide that something is a form.
"""
from __future__ import annotations

import json
import logging
import re
import sqlite3

logger = logging.getLogger(__name__)

# A base form has to be a plain German word: Latin letters, no digits, no spaces.
# Markers are prose, so the target is whatever Latin-script token follows them.
_WORD = r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß-]{1,}"

# How far into an entry a marker may sit and still be about the entry itself.
#
# This threshold is the whole difference between a useful pass and a harmful one.
# A dictionary states "this is a form of X" as the entry's opening move, but it
# also drops a trailing note about compounds at the END of a long, ordinary
# entry: `Tag` carries "Tag- дневной в сл. сл." at character 8566 of 8603, after
# eight thousand characters of legitimate senses. Matching anywhere in the body
# tagged 1006 words as combining forms when only ~22 are; the casualties were
# Hand, Weg, Tag, Tod, Grund, Welt, Höhe, Art — some of the most common nouns in
# the language, which search would then have pushed below their own compounds.
_MARKER_HEAD = 40

# kind → (pattern, does the pattern name its base?). Order matters: the first
# match wins, and the participle/plural markers are more specific than "см.".
_MARKERS: tuple[tuple[str, re.Pattern[str], bool], ...] = (
    # "1. part II от verstehen (sich) 2. part adj понятый"
    ("inflection", re.compile(rf"\bpart(?:\.|izip)?\s*I?I\s+от\s+({_WORD})"), True),
    # "pl от Faktum"
    ("inflection", re.compile(rf"\bpl\s+от\s+({_WORD})"), True),
    # "prät conj от geben", "prät от gelten"
    ("inflection", re.compile(rf"\bprät\w*\.?\s*(?:conj\s*)?от\s+({_WORD})"), True),
    # "сокр. от homogenisierte Milch"
    ("abbrev", re.compile(rf"сокр\.\s*от\s+({_WORD})"), True),
    # "Schnell- в сл. сл.: быстроходный" — a combining form, base is its own stem
    ("compound", re.compile(r"в сл\.\s*сл\.|в сложных словах"), False),
    # A whole entry that is nothing but a pointer: "разг. см. allein 1."
    ("variant", re.compile(rf"^\W{{0,6}}(?:разг\.\s*)?см\.\s+({_WORD})\s*\d?\.?\s*$"), True),
)


def _source_bodies(con: sqlite3.Connection) -> dict[str, str]:
    """Every enriched lemma's raw translation text from the attached `v.words`.

    Read in one sweep rather than per-lemma: 76k point lookups across an ATTACHed
    database is minutes, one scan is seconds.
    """
    out: dict[str, str] = {}
    for lemma, raw in con.execute(
        "SELECT w.lemma, w.translations FROM v.words w "
        "JOIN cards c ON c.lemma = w.lemma"
    ):
        try:
            parts = json.loads(raw or "[]")
        except (json.JSONDecodeError, TypeError):
            continue
        out[lemma] = " ".join(str(p) for p in parts)
    return out


def _classify(lemma: str, body: str) -> tuple[str, str | None] | None:
    """(kind, named base) if the source calls this entry a form, else None."""
    head = body.lstrip()
    for kind, rx, names_base in _MARKERS:
        m = rx.search(body)
        if not m or m.start() > _MARKER_HEAD:
            continue
        # A combining form writes itself out: the entry for the stub literally
        # opens "Schnell- в сл. сл.". Ordinary words never do, so this separates
        # the 22 real stubs from the ~980 words that merely mention a compound —
        # measured, not assumed: no buried match passes it.
        if kind == "compound" and not head.startswith(f"{lemma}-"):
            continue
        base = m.group(1) if names_base and m.groups() else None
        # "pl от Faktum" pointing at itself is a mis-parse, not a form.
        return (kind, base) if base != lemma else None
    return None


def _lemmatise(lemma: str) -> str | None:
    """Base form per `simplemma`, or None when it leaves the word alone."""
    try:
        import simplemma
    except ImportError:  # pragma: no cover — declared in pyproject
        return None
    try:
        base = simplemma.lemmatize(lemma, lang="de")
    except Exception:  # noqa: BLE001 — a lemmatiser hiccup must not fail the pass
        return None
    return base if base and base != lemma else None


def _capitalised_twins(con: sqlite3.Connection) -> dict[str, str]:
    """`Schnell` when `schnell` is also a card and the capital one is not a noun.

    Sentence-initial capitals got recorded as separate headwords, and `wordfreq`
    then handed each the lowercase word's frequency — 866 pairs share a zipf
    exactly. A real nominalisation (`das Essen`, `das Können`) is excluded by the
    article test: German gives nominalised infinitives an article, these have none
    even though enrichment guessed `noun`.
    """
    cards = {
        r["lemma"]: (r["pos"], r["article"])
        for r in con.execute("SELECT lemma, pos, article FROM cards")
    }
    out: dict[str, str] = {}
    for lemma, (pos, article) in cards.items():
        lower = lemma.lower()
        if lemma == lower or lower not in cards:
            continue
        if pos == "noun" and article:
            continue  # das Essen — a genuine nominalisation
        out[lemma] = lower
    return out


def tag_forms(con: sqlite3.Connection) -> dict:
    """Fill `cards.form_kind`/`form_of` from the source dictionary's own markers.

    Idempotent and cheap — pure SQL plus regex, no model call. Re-running rewrites
    the same values, so it is safe on every start; the caller only needs to know
    whether anything changed, because an in-place UPDATE does not move
    `created_at` and the mirror cursor would otherwise never see it.
    """
    bodies = _source_bodies(con)
    twins = _capitalised_twins(con)
    have_card = {r[0] for r in con.execute("SELECT lemma FROM cards")}

    updates: list[tuple[str, str | None, str]] = []
    for lemma, body in bodies.items():
        hit = _classify(lemma, body)
        if hit is None:
            continue
        kind, base = hit
        # Prefer the base the dictionary named; fall back to the lemmatiser only
        # to answer "of what?", never to decide that this is a form at all.
        if not base or base not in have_card:
            guess = _lemmatise(lemma)
            base = guess if guess in have_card else (base or None)
        updates.append((kind, base, lemma))

    tagged = {u[2] for u in updates}
    for lemma, lower in twins.items():
        if lemma not in tagged:
            updates.append(("capitalised", lower, lemma))

    con.executemany(
        "UPDATE cards SET form_kind=?, form_of=? WHERE lemma=?", updates)
    # Anything previously tagged that no longer matches must be released, or a
    # loosened marker would leave permanent false positives behind.
    keep = [u[2] for u in updates]
    cleared = 0
    if keep:
        marks = ",".join("?" * len(keep))
        cleared = con.execute(
            f"UPDATE cards SET form_kind=NULL, form_of=NULL "
            f"WHERE form_kind IS NOT NULL AND lemma NOT IN ({marks})", keep).rowcount
    con.commit()

    by_kind: dict[str, int] = {}
    for kind, _, _ in updates:
        by_kind[kind] = by_kind.get(kind, 0) + 1
    logger.info("form tagging: %d cards tagged %s, %d cleared",
                len(updates), by_kind, cleared)
    return {"tagged": len(updates), "cleared": cleared, "by_kind": by_kind}

"""Full inflection paradigms, imported from a German Wiktionary dump.

What the enrichment model gives us is thin: three fields per verb (Präteritum,
Partizip II, Hilfsverb), two per adjective, two per noun. That is enough to
recognise a word and nowhere near enough to use one. The present tense is
missing entirely, so `du gibst` and `er gibt` — the stem change that is the
single most drilled thing at A2–B1 — appear nowhere in the base. Nouns carry
Genitiv and Plural but no Dativ, which hides the n-declension: `Student` stores
"des Studenten / die Studenten" and a learner still cannot tell whether it is
"dem Student" or "dem Studenten".

Wiktionary has all of it, already tabulated, and this is a pure join — no model
call, no tokens. `geben` arrives with 306 clean forms; we keep the dozen a
learner actually conjugates.

Why the German edition and not the English one (both measured 2026-07-19 on the
live base): 153 706 usable lemmas against 78 692, 53 222 of our cards matched
against 39 038, and its forms come with their pronouns ("du gibst",
"er/sie/es gibt") rather than bare stems. It is also a third of the download.

    https://kaikki.org/dictionary/downloads/de/de-extract.jsonl.gz

Import is deliberately an offline step, not something the app does at boot: the
dump is 300 MB and does not belong in the image. `import_dump` fills a table the
mirror then carries to Postgres like any other card column.

⚠️ This module reads Wiktionary for MORPHOLOGY only. Its `form_of` links must
never be used to decide that one of our cards is a word form — see forms.py. It
marks `das`, `es`, `ein`, `aber`, `schon`, `mehr` and `mal` as non-lemmas
because each has some rare homographic parse, and demoting those would gut the
dictionary.
"""
from __future__ import annotations

import gzip
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger(__name__)

# Regional, historical and register variants share the tag space with the plain
# paradigm. They are real German, but a learner card wants one answer per slot.
_NOISE = {"obsolete", "archaic", "variant", "alternative", "rare", "dated",
          "Switzerland", "Liechtenstein", "Austria", "colloquial", "poetic",
          "table-tags", "inflection-template"}

# Forms arrive with their subject ("ich gebe", "er/sie/es gibt"). Store the verb
# alone — the UI already labels the row, and repeating the pronoun in the data
# would put it on screen twice.
_PRONOUNS = ("ich", "du", "er/sie/es", "er", "sie/es", "wir", "ihr", "sie", "Sie")

_PERSONS = (("ich", "first-person", "singular"), ("du", "second-person", "singular"),
            ("er", "third-person", "singular"), ("wir", "first-person", "plural"),
            ("ihr", "second-person", "plural"), ("sie", "third-person", "plural"))
_CASES = (("nom", "nominative"), ("gen", "genitive"),
          ("dat", "dative"), ("akk", "accusative"))


def _strip_subject(form: str) -> str:
    parts = form.strip().split(" ", 1)
    if len(parts) == 2 and parts[0] in _PRONOUNS:
        form = parts[1]
    return form.strip().rstrip("!").strip()


def _pick(forms: list[dict], need: set[str], *, exact: int | None = None) -> str:
    """First form carrying every tag in `need`, cleaned up.

    `exact` caps the tag count, which is how the bare comparative ("besser") is
    told apart from its sixteen declined cells ("besserer", "bessere", …).
    """
    for f in forms:
        tags = set(f.get("tags") or [])
        if need <= tags and (exact is None or len(tags) <= exact):
            value = _strip_subject(str(f.get("form") or ""))
            if value and value != "—":
                return value
    return ""


def _clean_forms(entry: dict) -> list[dict]:
    return [f for f in (entry.get("forms") or [])
            if f.get("tags") and not _NOISE & set(f["tags"])]


def _verb(forms: list[dict]) -> dict[str, Any]:
    present = {label: _pick(forms, {person, number, "present", "active", "indicative"})
               for label, person, number in _PERSONS}
    out: dict[str, Any] = {}
    if any(present.values()):
        out["praesens"] = {k: v for k, v in present.items() if v}
    for key, need in (
        ("praeteritum", {"past", "first-person", "singular", "active", "indicative"}),
        ("partizip2", {"participle-2", "perfect"}),
        ("hilfsverb", {"auxiliary", "perfect"}),
        ("imperativ_du", {"imperative", "second-person", "singular", "present", "active"}),
        ("imperativ_ihr", {"imperative", "plural"}),
        ("konjunktiv2", {"subjunctive-ii", "first-person", "singular", "active"}),
    ):
        value = _pick(forms, need)
        if value:
            out[key] = value
    return out


def _noun(forms: list[dict]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for number, key in (("singular", "sg"), ("plural", "pl")):
        cells = {short: _pick(forms, {case, number}) for short, case in _CASES}
        cells = {k: v for k, v in cells.items() if v}
        if cells:
            out[key] = cells
    return out


def _adj(forms: list[dict]) -> dict[str, Any]:
    # Cap the tag count: the bare degree carries just ("comparative",), while the
    # declined cells add case, gender, number and strength.
    out = {}
    for key, tag in (("komparativ", "comparative"), ("superlativ", "superlative")):
        value = _pick(forms, {tag}, exact=2)
        if value:
            out[key] = value
    return out


_BUILDERS = {"verb": _verb, "noun": _noun, "adj": _adj}


def paradigm_of(entry: dict) -> dict[str, Any]:
    """The learner-sized paradigm for one Wiktionary entry ({} if it has none)."""
    build = _BUILDERS.get(entry.get("pos") or "")
    if not build:
        return {}
    return build(_clean_forms(entry))


def read_dump(path: Path) -> Iterator[dict]:
    """German-language entries from a wiktextract dump, plain or gzipped.

    The German edition describes other languages too (en, it, pl, fr are all in
    there), so the language filter is not optional.
    """
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as fh:  # type: ignore[operator]
        for line in fh:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("lang_code") == "de" and entry.get("word"):
                yield entry


def ensure_table(con: sqlite3.Connection) -> None:
    con.execute("""CREATE TABLE IF NOT EXISTS morphology(
        lemma TEXT NOT NULL,
        pos TEXT NOT NULL,
        data TEXT NOT NULL,               -- the paradigm as JSON
        source TEXT,                      -- which dump it came from
        PRIMARY KEY(lemma, pos))""")
    con.commit()


def import_dump(path: Path, con: sqlite3.Connection, *,
                only_known: bool = True) -> dict:
    """Load paradigms for every card we hold (or for everything, if asked).

    Restricted to known lemmas by default: the dump carries 153k lemmas against
    our 76k cards, and morphology for a word with no card is dead weight the
    mirror would carry around for nothing.

    Case matters. Our base separates homographs by case on purpose (Morgen vs
    morgen), so the lookup is exact; a case-folded match would hand the noun's
    declension to the adverb.
    """
    ensure_table(con)
    known: dict[str, set[str]] = {}
    for lemma, pos in con.execute("SELECT lemma, pos FROM cards"):
        known.setdefault(lemma, set()).add(pos or "other")

    rows: list[tuple] = []
    seen = matched = 0
    for entry in read_dump(path):
        seen += 1
        if seen % 250_000 == 0:
            logger.info("morphology import: %d entries read, %d matched",
                        seen, matched)
        word, pos = entry["word"], entry.get("pos") or ""
        if only_known and (word not in known or pos not in known[word]):
            continue
        paradigm = paradigm_of(entry)
        if not paradigm:
            continue
        matched += 1
        rows.append((word, pos, json.dumps(paradigm, ensure_ascii=False), path.name))

    # An entry can appear more than once (separate etymologies); the richest
    # paradigm wins rather than whichever the dump happened to list last.
    best: dict[tuple[str, str], tuple] = {}
    for row in rows:
        key = (row[0], row[1])
        if key not in best or len(row[2]) > len(best[key][2]):
            best[key] = row
    con.executemany(
        "INSERT INTO morphology(lemma,pos,data,source) VALUES(?,?,?,?) "
        "ON CONFLICT(lemma,pos) DO UPDATE SET data=excluded.data, source=excluded.source",
        list(best.values()))
    con.commit()
    total = con.execute("SELECT COUNT(*) FROM morphology").fetchone()[0]
    logger.info("morphology import: %d entries read, %d paradigms stored (%d total)",
                seen, len(best), total)
    return {"read": seen, "stored": len(best), "total": total}

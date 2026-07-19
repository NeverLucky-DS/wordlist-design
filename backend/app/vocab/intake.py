"""New headwords from a Wiktionary dump, appended to the intake table.

Why this exists. Coverage was measured 2026-07-19 against an external corpus —
18 full de.wikipedia articles on exactly the Goethe Schreiben topics, 21k
tokens — instead of against the base itself. Of 1 088 missed types at zipf ≥ 3.0,
**895 (82 %) were absent from `vocab.db` altogether** and only 193 were
enrichment failures. The bottleneck is the source, not the model.

The source is a dump of bilingual dictionaries that predate 1995, so it has
`Kolchos` and `Fernschreiber` but not `Internet` (zipf 5.23), `online`,
`Digitalisierung`, `Klimawandel`, `Smartphone`, `Privatsphäre` or
`Suchmaschine`. None of those were ever even candidates — they are missing from
`word_status` entirely. For an essay trainer whose whole subject matter is
digitalisation, data protection and social media, that is the product's central
gap. See [[vocab-source-is-pre-1995-dictionary]].

How the words get in. `claim` serves work from `v.words` — vocab.db is the
intake table — so a new lemma becomes a candidate by being appended there, and
the rest of the pipeline (junk filter, batching, prompt, skip rules, mirror)
needs no change at all. Rows are stamped `sources=["wiktionary"]`, which both
tells the model where the data came from and makes the whole intake reversible
with a single DELETE.

⚠️ Two Wiktionary caveats that cost real time when ignored:

  · `pos: "name"` is proper nouns, and they are 9 % of the dump. Letting them in
    would refill the base with the Berlin/München/Peter noise the skip rule
    spent tokens removing. Excluded outright, along with abbreviations, affixes
    and phrases.
  · `form_of` may NOT be used to demote a card we already hold — it calls
    `das`, `es`, `aber` and `schon` non-lemmas (see morph.py). Here the question
    is the opposite one: whether to admit a brand-new word at all. Rejecting an
    entry whose senses are *all* form-of is safe in that direction, because no
    existing card can be lost by declining to add one.
  · Multi-word entries are refused outright. The dump has plenty and the first
    import let 922 through; sorted by frequency the top of that list is
    conjugated phrase forms in both word orders — `war dabei` AND `dabei war`,
    `bin dabei` AND `dabei bin`, `ist dafür` — which are not headwords by any
    definition. The base held exactly ZERO multi-word lemmas across 108 084 rows
    before this, so admitting them would break an invariant the card UI, the
    personal word list and the brush lookup all quietly rely on. The genuinely
    useful ones (`von Zeit zu Zeit`, `recht haben`) are collocations and idioms,
    and the card schema already has fields for those.

The frequency floor is what keeps this honest. Take candidates from the
intersection with Wiktionary lemmas rather than from a frequency list: down at
low zipf `wordfreq.top_n_list` is Swiss spellings (`weiss`, `fussball`),
participles, names and English.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Iterator

from wordfreq import zipf_frequency

from . import enrich, morph

logger = logging.getLogger(__name__)

SOURCE = "wiktionary"

# Wiktionary part of speech → ours. Everything absent here is refused: `name`
# (proper nouns), `abbrev`, `phrase`, `prefix`/`suffix`, `character`, and the
# closed classes, which funcwords.py writes by hand.
POS_MAP = {"noun": "noun", "verb": "verb", "adj": "adj", "adv": "adv"}

_GENDER = {"masculine": "der", "feminine": "die", "neuter": "das"}

# A gloss that only points at another entry carries no meaning of its own.
_REFERENCE_ONLY = ("Alternative Schreibweise", "alternative Schreibweise",
                   "Nebenform", "veraltet für", "Kurzform", "Abkürzung für")

MAX_GLOSSES = 6
MAX_EXAMPLES = 3


def _article(entry: dict) -> str | None:
    for tag in entry.get("tags") or []:
        if tag in _GENDER:
            return _GENDER[tag]
    return None


def _senses(entry: dict) -> tuple[list[str], list[str], bool]:
    """(glosses, example sentences, every-sense-is-a-form-of).

    The form-of flag is deliberately strict — all senses, not any — because a
    real word often carries one incidental form-of reading alongside its own.
    """
    glosses: list[str] = []
    examples: list[str] = []
    senses = entry.get("senses") or []
    real = 0
    forms = 0
    for s in senses:
        if s.get("form_of") or s.get("alt_of"):
            forms += 1
            continue
        for g in s.get("glosses") or []:
            g = str(g).strip()
            if not g or g in glosses:
                continue
            if g.startswith(_REFERENCE_ONLY):
                continue
            real += 1
            if len(glosses) < MAX_GLOSSES:
                glosses.append(g)
        for ex in s.get("examples") or []:
            text = str(ex.get("text") or "").strip()
            if text and len(text) < 200 and len(examples) < MAX_EXAMPLES:
                examples.append(text)
    all_forms = bool(senses) and real == 0 and forms > 0
    return glosses, examples, all_forms


def candidates(dump: Path, *, min_zipf: float, known: set[str],
               limit: int | None = None) -> Iterator[dict]:
    """Rows ready for `vocab.db.words`, newest headwords only.

    `known` is matched case-exactly: the base separates homographs by case on
    purpose (Morgen vs morgen), so a case-folded check would silently refuse a
    genuinely new spelling.
    """
    seen: set[str] = set()
    yielded = 0
    for entry in morph.read_dump(dump):
        word = entry["word"]
        pos = POS_MAP.get(entry.get("pos") or "")
        if not pos or word in known or word in seen:
            continue
        if " " in word or enrich.is_junk(word):
            continue
        if zipf_frequency(word, "de") < min_zipf:
            continue
        glosses, examples, all_forms = _senses(entry)
        if all_forms or not glosses:
            continue
        seen.add(word)
        by_source = {SOURCE: {
            "translations": [],           # no Russian in the dump — the model writes it
            "glosses_de": glosses,        # German definitions stand in as the evidence
            "examples": examples,
            "article": _article(entry),
            "pos": [entry.get("pos_title") or pos],
            "forms": [],
        }}
        yield {
            "lemma": word,
            "article": _article(entry),
            "pos": json.dumps([pos], ensure_ascii=False),
            "forms": "[]",
            "translations": "[]",
            "examples": json.dumps(examples, ensure_ascii=False),
            "synonyms": json.dumps(
                [str(s.get("word")) for s in (entry.get("synonyms") or [])
                 if s.get("word")][:5], ensure_ascii=False),
            "collocations": "[]",
            "idioms": "[]",
            "sources": json.dumps([SOURCE], ensure_ascii=False),
            "by_source": json.dumps(by_source, ensure_ascii=False),
            "zipf": zipf_frequency(word, "de"),
            "freq_rank": None,
            "level": "unlisted",
            "enriched": 0,
        }
        yielded += 1
        if limit and yielded >= limit:
            return


_COLS = ("lemma", "article", "pos", "forms", "translations", "examples",
         "synonyms", "collocations", "idioms", "sources", "by_source",
         "zipf", "freq_rank", "level", "enriched")


def known_lemmas(vocab: Path, enrichment: Path | None = None) -> set[str]:
    """Every lemma we must not re-admit — intake rows AND cards we already hold.

    Cards matter separately because the two tables genuinely disagree. The 1996
    spelling rename files the CARD under the modern form while `word_status`
    stays pinned to the one that was sent, so `Fluss` has a finished card while
    `vocab.db` only ever knew `Fluß`. Keying off vocab.db alone would re-admit
    `Fluss` as brand new, pay for it a second time, and let INSERT OR REPLACE
    overwrite a good card with a fresh roll of the dice.

    A file that exists but has no such table is a MISCONFIGURATION, not a
    transient condition, and it raises. The repo keeps empty stubs at
    `app/vocab/vocab.db` next to the real databases in `app/vocab/vocab_data/`,
    and `VOCAB_DB` defaults to the stub whenever the env var is unset — outside
    the container it always is. Reading the stub silently yields `known = 0`,
    which turns every word we already own back into a "new" candidate: the first
    dry run here reported 36 455 of them, `Mensch` and `Software` included.
    """
    known: set[str] = set()
    for path, sql, table in ((vocab, "SELECT lemma FROM words", "words"),
                             (enrichment, "SELECT lemma FROM cards", "cards")):
        if not path or not Path(path).exists():
            continue
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            known.update(r[0] for r in con.execute(sql))
        except sqlite3.OperationalError as exc:
            if "no such table" in str(exc):
                raise RuntimeError(
                    f"{path} has no `{table}` table — this is almost certainly the "
                    f"empty stub, not the real database. The live ones live in "
                    f"app/vocab/vocab_data/; set VOCAB_DB or pass --vocab-db."
                ) from exc
            logger.warning("known_lemmas: could not read %s (%s)", path, exc)
        finally:
            con.close()
    if not known:
        raise RuntimeError(
            f"no known lemmas read from {vocab} / {enrichment} — refusing to treat "
            f"the entire dump as new. Check the database paths.")
    return known


def append(dump: Path, vocab: Path, *, min_zipf: float,
           enrichment: Path | None = None, limit: int | None = None,
           dry_run: bool = False) -> dict[str, Any]:
    """Append new headwords to vocab.db. Returns a summary.

    Existing rows are never touched — `INSERT OR IGNORE` on the unique lemma —
    so a re-run with a lower floor only adds what the higher floor skipped.
    """
    known = known_lemmas(vocab, enrichment)
    rows = list(candidates(dump, min_zipf=min_zipf, known=known, limit=limit))
    if dry_run:
        return {"known": len(known), "new": len(rows), "written": 0,
                "sample": [r["lemma"] for r in rows[:40]]}

    con = sqlite3.connect(vocab)
    try:
        # `written` counts the words TABLE before and after. It must not be
        # derived from len(known): that set is deliberately wider than the table
        # (it also holds lemmas that have a card but no intake row, 500 of them
        # on the live base), so subtracting it undercounts every insert.
        before = con.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        placeholders = ",".join("?" * len(_COLS))
        con.executemany(
            f"INSERT OR IGNORE INTO words({','.join(_COLS)}) VALUES({placeholders})",
            [tuple(r[c] for c in _COLS) for r in rows])
        con.commit()
        after = con.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    finally:
        con.close()
    logger.info("intake: %d new lemmas, table now %d", after - before, after)
    return {"known": len(known), "new": len(rows), "written": after - before,
            "total": after, "sample": [r["lemma"] for r in rows[:40]]}

"""Hand-adjudicated exceptions to the rules in `forms.py`.

`forms.py` reads signals the source dictionary states about itself, and that is
the right default — it scales to 92 000 cards and cannot be argued with. But a
rule that fires on a signal also misses what the signal does not cover, and
sometimes fires where it should not. Both need somewhere to live that a rerun
will not erase, because `tag_forms()` clears every tag it did not just write.

What is in here comes from the mechanical screen of 2026-07-26. It flagged 400
cards where a capitalised lemma and its lowercase twin carry a byte-identical
`ru` — the signature of one word enriched twice. Reading all 200 pairs by hand
split them three ways:

  * 129 of the 178 real duplicates were **already tagged** by
    `_capitalised_twins`. The rule works; nothing to do.
  * 40 were not, and mostly could not be: the rule only ever inspects the
    CAPITALISED half, so a spurious *lowercase* entry (`frieden` beside `der
    Frieden`, `hering`, `drittel`, `dutzend`) is structurally invisible to it.
  * 11 pairs are two real words whose glosses got copied across the case
    boundary — `das Ich` is the philosophical ego, not the pronoun; `die Elf` is
    a football team, not the numeral.

And four the rules got wrong in the other direction. `mal` — zipf 6.28, one of
the commonest particles in German — was tagged `abbrev` and demoted in search
for it. `Vorletzte`, `Nächstbeste`, `Erstbeste` are ordinary nominalised
adjectives that `_capitalised_twins` read as sentence-initial noise.

Data lives in TSV beside the wordlists rather than in this file: these are
lexicographic judgements about individual words, the list will grow as more of
the base is reviewed, and a reviewer should be able to read and amend it without
touching code.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA = Path(__file__).with_name("data")
TWINS_FILE = _DATA / "case_twins.tsv"
FIXES_FILE = _DATA / "card_fixes.tsv"

# Which card fields may be corrected from the TSV. Deliberately short: these are
# adjudicated single-value repairs, not a back door for rewriting cards by hand.
# `ru` and `ru_all` are stored twice (a promoted column and inside `data`) and
# both copies have to move together, or the list row and the open card disagree.
_FIELDS = ("ru", "ru_all", "article")


def _rows(path: Path) -> list[list[str]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        out.append(line.split("\t"))
    return out


@lru_cache(maxsize=1)
def load_twins() -> tuple[dict[str, str], frozenset[str]]:
    """(lemma -> base to point at, lemmas that must never be tagged)."""
    tag: dict[str, str] = {}
    keep: set[str] = set()
    for cols in _rows(TWINS_FILE):
        cols = (cols + ["", "", ""])[:4]
        lemma, action, base, _why = cols
        if action == "form" and lemma and base:
            tag[lemma] = base
        elif action == "keep" and lemma:
            keep.add(lemma)
    return tag, frozenset(keep)


@lru_cache(maxsize=1)
def load_fixes() -> dict[str, dict[str, object]]:
    """lemma -> {field: value}. `ru_all` is stored as a JSON array."""
    out: dict[str, dict[str, object]] = {}
    for cols in _rows(FIXES_FILE):
        if len(cols) < 3:
            continue
        lemma, field, raw = cols[0], cols[1], cols[2]
        if not lemma or field not in _FIELDS or not raw:
            continue
        value: object = raw
        if field == "ru_all":
            try:
                value = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(value, list) or not value:
                continue
        out.setdefault(lemma, {})[field] = value
    return out


def exempt() -> frozenset[str]:
    """Lemmas `forms.tag_forms` must leave alone whatever its rules say."""
    return load_twins()[1]


def extra_tags(have_card) -> list[tuple[str, str | None, str]]:
    """Adjudicated (kind, base, lemma) triples to merge into `tag_forms`.

    The kind follows the spelling, because that is what the reader sees. A
    capitalised entry beside a real lowercase word is the `capitalised` case the
    UI already labels «форма от …»; a lowercase entry beside a real noun is a
    non-standard spelling, which the UI labels «вариант написания».
    """
    tag, _keep = load_twins()
    out = []
    for lemma, base in tag.items():
        if lemma not in have_card:
            continue
        kind = "capitalised" if lemma[:1].isupper() else "variant"
        out.append((kind, base if base in have_card else None, lemma))
    return out


def apply_fixes(con: sqlite3.Connection) -> int:
    """Write the adjudicated field corrections onto the cards.

    Every affected field is stored TWICE — as a promoted column for the list row
    and inside `data` for the open card — so both copies move together or the
    two views of the same word disagree with each other.

    Runs in place, which means `created_at` does not move and the mirror's
    forward cursor will never see the change: the caller has to trigger a full
    resync, exactly as it already does for `tag_forms` and the `zipf` backfill.

    Idempotent, and the returned count is rows that actually changed — rerunning
    reports zero rather than re-reporting the same work.
    """
    fixes = load_fixes()
    if not fixes:
        return 0
    changed = 0
    for lemma, fields in fixes.items():
        row = con.execute("SELECT ru, article, data FROM cards WHERE lemma=?",
                          (lemma,)).fetchone()
        if row is None:
            continue
        try:
            card = json.loads(row[2]) or {}
        except (TypeError, json.JSONDecodeError):
            card = {}
        ru, article = row[0], row[1]
        touched = False

        if "ru_all" in fields:
            want = [str(x) for x in (fields["ru_all"] or [])]  # type: ignore[union-attr]
            if (card.get("ru_all") or []) != want:
                card["ru_all"] = want
                touched = True
                # The promoted `ru` is the first meaning by contract. Re-splitting
                # a packed entry moves that first meaning, so it has to follow —
                # otherwise the row shows a string no longer present in the card.
                if ru not in want:
                    ru = want[0]
        if "ru" in fields and fields["ru"] != ru:
            ru = str(fields["ru"])
            rest = [x for x in (card.get("ru_all") or []) if x != ru]
            card["ru_all"] = [ru, *rest]
            touched = True
        if "article" in fields and fields["article"] != article:
            article = str(fields["article"])
            card["article"] = article
            touched = True

        if not touched and ru == row[0]:
            continue
        card["ru"] = ru
        con.execute("UPDATE cards SET ru=?, article=?, data=? WHERE lemma=?",
                    (ru, article, json.dumps(card, ensure_ascii=False), lemma))
        changed += 1
    con.commit()
    if changed:
        logger.info("handfixes: corrected %d cards", changed)
    return changed

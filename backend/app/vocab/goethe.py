"""CEFR level assignment from authoritative wordlists (not frequency).

Frequency rank is NOT a reliable CEFR signal (concrete A1 words like
`Doppelzimmer`/`Postleitzahl` are corpus-rare; formal connectors like
`hinsichtlich` are corpus-frequent). So levels come from wordlists, in
priority order:

1. Goethe/ÖSD A1–B1 Wortliste — official, authoritative. Wins every conflict.
   Vendored `data/goethe_levels.tsv` (from ilkermeliksitki/goethe-institute-
   wordlist); also carries article + plural + a level-appropriate example.
2. Supplemental A1–C2 list — fills B2/C1/C2 that Goethe does not cover.
   Vendored `data/cefr_extra.tsv` (from abdullahbutt/deutsch-lernen-goethe).
   Carries article + plural, no example.
3. Anything in neither list → `unlisted` (level not asserted).
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).with_name("data")
GOETHE_FILE = _DATA / "goethe_levels.tsv"      # a1/a2/b1 + example (authoritative)
EXTRA_FILE = _DATA / "cefr_extra.tsv"           # a1..c2 supplemental list
MANUAL_FILE = _DATA / "cefr_manual.tsv"         # a1..c2 hand-classified tail

CEFR_ORDER = {"a1": 0, "a2": 1, "b1": 2, "b2": 3, "c1": 4, "c2": 5}
GOETHE_LEVELS = ("a1", "a2", "b1")
UNLISTED = "unlisted"                            # in no wordlist → level unknown
ALL_LEVELS = ("a1", "a2", "b1", "b2", "c1", "c2", UNLISTED)
OBLIGATORY = ("a1", "a2", "b1")                  # Goethe core

_PAREN = re.compile(r"\([^)]*\)")   # "(pl.)", "(sich)", "(1)"
_NONWORD = re.compile(r"[^a-zäöüß]+")


def norm(lemma: str) -> str:
    """Fold a lemma to a match key: drop parentheticals/markers, casefold."""
    s = _PAREN.sub(" ", lemma or "")
    s = s.replace("ß", "ss").strip().casefold()
    s = _NONWORD.sub(" ", s).strip()   # keep only letters+spaces (drops '-', '/', ',')
    return s


def _read(path: Path, allowed: tuple[str, ...], with_example: bool) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        cols = (line.split("\t") + ["", "", "", ""])[:5]
        lemma, level, article, plural, example = cols
        if not with_example:
            example = ""
        key = norm(lemma)
        if not key or level not in allowed:
            continue
        cur = out.get(key)
        if cur is None or CEFR_ORDER[level] < CEFR_ORDER[cur["level"]]:
            out[key] = {"level": level, "article": article,
                        "plural": plural, "example": example}
        else:  # keep richer metadata from the alternate entry
            for f, v in (("article", article), ("plural", plural), ("example", example)):
                if not cur[f] and v:
                    cur[f] = v
    return out


@lru_cache(maxsize=1)
def load() -> dict[str, dict]:
    """Goethe A1–B1 map (authoritative, carries example). key(norm) -> record."""
    return _read(GOETHE_FILE, GOETHE_LEVELS, with_example=True)


@lru_cache(maxsize=1)
def load_extra() -> dict[str, dict]:
    """Supplemental A1–C2 map (fills B2/C1/C2). key(norm) -> record."""
    return _read(EXTRA_FILE, tuple(CEFR_ORDER), with_example=False)


@lru_cache(maxsize=1)
def load_manual() -> dict[str, dict]:
    """Hand-classified tail (lowest priority). key(norm) -> record."""
    return _read(MANUAL_FILE, tuple(CEFR_ORDER), with_example=False)


def resolve(lemma: str) -> dict:
    """Final CEFR record. Priority: Goethe > supplemental list > manual > unlisted."""
    key = norm(lemma)
    hit = load().get(key) or load_extra().get(key) or load_manual().get(key)
    if hit:
        return hit
    return {"level": UNLISTED, "article": "", "plural": "", "example": ""}


def level_of(lemma: str) -> str:
    return resolve(lemma)["level"]

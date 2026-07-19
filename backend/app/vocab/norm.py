"""Shared normalization for the Wörterbuch mirror, search and word list.

Search has to be forgiving — the user types "gruen" or "grun" for "grün", and
"зависимости" for "зависимость". The stored `lemma`, on the other hand, must
stay verbatim: it is the key of the personal word list, and the enrichment
prompt deliberately relies on case to separate homographs (Morgen/morgen,
Essen/essen). So we keep the lemma exact and index a folded copy beside it.
"""
from __future__ import annotations

import re

# ── text folding ─────────────────────────────────────────────────────────────
# Applied AFTER lower(), so only lowercase keys are needed.
#
# German umlauts get folded TWO ways, because both spellings are things people
# actually type on a keyboard without umlauts, and neither form finds the other:
#   fold_de   ä→ae  — the orthographically correct substitution ("gruen")
#   ascii_de  ä→a   — the lazy one ("grun")
# Storing both and scoring against the better one makes "grün", "gruen" and
# "grun" all resolve to grün exactly. With only one form, whichever spelling the
# user picked that wasn't ours drops out of the ranking — measured: "grun"
# against ae-folding alone put Grund and Grunzen above grün.
_DE_FOLD = str.maketrans({
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "é": "e", "è": "e", "ê": "e", "á": "a", "à": "a", "â": "a",
    "í": "i", "ì": "i", "ó": "o", "ò": "o", "ô": "o", "ú": "u", "ù": "u",
    "ç": "c", "ñ": "n", "å": "a", "ø": "o", "æ": "ae",
})
_DE_ASCII = str.maketrans({
    "ä": "a", "ö": "o", "ü": "u", "ß": "ss",
    "é": "e", "è": "e", "ê": "e", "á": "a", "à": "a", "â": "a",
    "í": "i", "ì": "i", "ó": "o", "ò": "o", "ô": "o", "ú": "u", "ù": "u",
    "ç": "c", "ñ": "n", "å": "a", "ø": "o", "æ": "ae",
})

# ё/е are interchangeable in everyday typing; fold so "всё" finds "все".
_RU_FOLD = str.maketrans({"ё": "е"})

_WS = re.compile(r"\s+")
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")


def fold_de(s: str) -> str:
    """Fold a German string into its search key (ä→ae, ß→ss)."""
    return _WS.sub(" ", (s or "").strip().lower()).translate(_DE_FOLD)


def ascii_de(s: str) -> str:
    """Fold a German string with umlauts flattened to bare vowels (ä→a)."""
    return _WS.sub(" ", (s or "").strip().lower()).translate(_DE_ASCII)


def fold_ru(s: str) -> str:
    """Fold a Russian string into its search key."""
    return _WS.sub(" ", (s or "").strip().lower()).translate(_RU_FOLD)


def detect_lang(q: str) -> str:
    """Which side of the dictionary a query is aimed at.

    Any Cyrillic → the user is typing Russian and wants German back; otherwise
    assume German. Deliberately crude: there is no third option to confuse it
    with, and a stray Latin letter in a Russian query still resolves to `ru`.
    """
    return "ru" if _CYRILLIC.search(q or "") else "de"


# ── level → display band ─────────────────────────────────────────────────────
# The brush set (`js/words-data.js` WASH) only covers B1/B2/C1, and we are not
# drawing more: the app is a B1–C1 product. Everything else is clamped into that
# band so no word can end up without a wash. `unlisted` (~71% of the base — real
# words that simply aren't on a Goethe list) is treated as C1 by decision.
LEVEL_BAND = {
    "a1": "B1", "a2": "B1", "b1": "B1",
    "b2": "B2",
    "c1": "C1", "c2": "C1", "unlisted": "C1",
}
BANDS = ("B1", "B2", "C1")


def band_of(level: str | None) -> str:
    return LEVEL_BAND.get((level or "").strip().lower(), "C1")


# ── frequency band ───────────────────────────────────────────────────────────
# A `level` of "unlisted" covers 95.6% of the base (88 067 of 92 090), so the
# CEFR badge it produces is a placeholder, not information. Frequency is the one
# thing we actually know about those words: `zipf` is filled for 92 090 of
# 92 090.
#
# ⚠️ This is NOT a computed CEFR level, and must never be displayed as one.
# Measured against the 4 023 cards that carry a real Goethe label, zipf orders
# the levels correctly on average (median a1 4.76 → b1 4.16 → c1 3.36 → c2 3.02)
# but cannot separate individual words. At the best available threshold (3.5) it
# still misfiles 398 of 3 312 B1 words as rare and 120 of 331 C1 words as
# common; b1 (4.16) and b2 (4.15) are indistinguishable outright. Rendering that
# as "B2" would swap an honest placeholder for a confident-looking guess the
# user cannot audit — strictly worse. So we report frequency AS frequency.
#
# The häufig cut sits at 4.0 because that is where Goethe's own B1 vocabulary
# centres (median 4.16): "häufig" means "as common as core B1 vocabulary".
FREQ_HAEUFIG = 4.0
FREQ_MITTEL = 3.0
FREQS = ("haeufig", "mittel", "selten")


def freq_of(zipf: float | None) -> str | None:
    """Frequency band from a zipf score, or None when we have no frequency.

    None is a real answer — it means unknown, and the UI shows nothing rather
    than guessing "selten", which would be a claim we cannot support.
    """
    if zipf is None:
        return None
    if zipf >= FREQ_HAEUFIG:
        return "haeufig"
    if zipf >= FREQ_MITTEL:
        return "mittel"
    return "selten"


# ── (pos, article) → brush type ──────────────────────────────────────────────
def type_of(pos: str | None, article: str | None) -> str:
    """Map a card onto one of the five brush types: der/die/das/verb/adj.

    Nouns without an article are nominalized adjectives (der/die Jugendliche,
    Erwachsene, Studierende) — they genuinely have no fixed article, so the
    `adj` wash is the honest answer rather than a fallback. Adverbs and function
    words also take `adj`: in German the adjective/adverb line is thin
    ("schnell" is both), and there is no separate wash to give them.
    """
    p = (pos or "").strip().lower()
    if p == "verb":
        return "verb"
    if p == "noun":
        art = (article or "").strip().lower()
        return art if art in ("der", "die", "das") else "adj"
    return "adj"

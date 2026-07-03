from __future__ import annotations

"""Word normalisation — clean LLM output, strip articles, lemmatise.

Fixes the two biggest sources of pipeline loss:
1. Dirty word strings ("die Anpassung (an + Akk.)") written to DB.
2. Inflected forms ("Emissionen", "nachhaltigen") failing exact
   Wiktionary lookup → word dropped.
"""

import logging
import re

from app.services.topic_pack_service import normalize_article, normalize_german_lemma

from .types import WordCandidate

logger = logging.getLogger(__name__)

try:
    import simplemma

    _HAS_SIMPLEMMA = True
except ImportError:  # pragma: no cover
    _HAS_SIMPLEMMA = False
    logger.warning("simplemma not installed — lemmatisation disabled")


def clean_word(raw: str) -> str:
    """Remove LLM annotations, plural hints, brackets from word strings."""
    w = re.sub(r"\s*\([^)]*\)", "", raw)
    w = re.sub(r"\s*\[[^\]]*\]", "", w)
    w = re.sub(r"\s*\*.*", "", w)
    w = re.sub(r"\s{2,}", " ", w)
    return w.strip(" ,;.:-–—")


def lemmatize_token(token: str) -> str:
    """Lemmatise a single German token (best effort)."""
    if not _HAS_SIMPLEMMA or not token.isalpha():
        return token
    try:
        lemma = simplemma.lemmatize(token, lang="de")
    except Exception:
        return token
    if not lemma or not isinstance(lemma, str):
        return token
    # Preserve noun capitalisation from input
    if token[0].isupper() and lemma[0].islower():
        lemma = lemma[0].upper() + lemma[1:]
    return lemma


def normalize_candidate(candidate: WordCandidate) -> WordCandidate | None:
    """Return candidate with canonical lemma in `.word`, or None if garbage.

    Canonical form (matches seed/topic-pack convention):
    - `word`    — lemma without article ("Klimawandel", "fossile Energieträger")
    - `article` — lowercase 'der'|'die'|'das' or None
    """
    cleaned = clean_word(candidate.word)
    lemma, article = normalize_german_lemma(cleaned, normalize_article(candidate.article))

    if not lemma or len(lemma) < 3 or len(lemma) > 100:
        return None
    if re.search(r"[\d@#%&=<>/\\]", lemma):
        return None

    # Lemmatise single-token words only; keep multi-word collocations as-is
    if " " not in lemma:
        lemma = lemmatize_token(lemma)

    candidate.word = lemma
    candidate.article = article
    return candidate


def dedupe_candidates(candidates: list[WordCandidate]) -> list[WordCandidate]:
    """Deduplicate by lowercase lemma; merge examples."""
    seen: dict[str, WordCandidate] = {}
    for c in candidates:
        key = c.word.lower().strip()
        if key not in seen:
            seen[key] = c
        else:
            kept = seen[key]
            kept.examples = list(dict.fromkeys(kept.examples + c.examples))[:3]
            if not kept.article and c.article:
                kept.article = c.article
    return list(seen.values())

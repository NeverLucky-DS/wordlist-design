from __future__ import annotations

"""Supplement step — close the gap to target_words / min_phrases.

When article extraction yields fewer words than the target, ask Mistral
directly for additional topic-specific essay vocabulary (excluding what we
already have). Generated words are verified against Wiktionary/DWDS during
enrichment (origin="generated" requires a dictionary hit), so hallucinated
words cannot enter the DB.

Same applies to Redemittel: if too few were found in articles, generate a
balanced set across essay parts.
"""

import asyncio
import logging

from .mistral_http import post_mistral_json
from .normalize import dedupe_candidates, normalize_candidate
from .types import PhraseCandidate, PipelineError, WordCandidate

logger = logging.getLogger(__name__)

_GEN_WORDS_PROMPT = """Du bist ein Experte für DaF-Essaytraining (B2-C1).
Thema: "{topic}"

Generiere {n} deutsche Wörter/Kollokationen (Niveau B2-C1), die für argumentative
Essays zu diesem Thema besonders nützlich sind: Fachbegriffe, präzise Verben mit
Rektion, treffende Adjektive, typische Kollokationen.
{focus}
NICHT verwenden (bereits vorhanden): {exclude}

Regeln:
- Nur real existierende, gebräuchliche Wörter (sie werden gegen Wörterbücher geprüft).
- Grundformen: Nomen Singular Nominativ mit Artikel, Verben Infinitiv, Adjektive Grundform.
- Je Wort 1-2 Beispielsätze (B2-C1) zum Thema.

Antworte NUR mit JSON:
{{"words": [{{"word": "die Ressourcenknappheit", "pos": "Noun", "article": "die",
              "examples": ["..."]}}]}}
pos: "Noun" | "Verb" | "Adjective" | "Other"
"""

_GEN_REDEMITTEL_PROMPT = """Du bist ein Experte für DaF-Essaytraining (B2-C1).
Thema: "{topic}"

Generiere Redemittel für argumentative Essays zu diesem Thema, verteilt auf die Teile:
- einleitung: {n_einleitung}
- argument: {n_argument}
- gegenargument: {n_gegenargument}
- beispiel: {n_beispiel}
- schluss: {n_schluss}

Regeln:
- Niveau B2-C1, idiomatisch und präzise (kein Schulbuch-Klischee wie "In der heutigen Zeit...").
- Wo sinnvoll, themenspezifisch formulieren (z.B. mit Bezug auf "{topic}").
- Lücken mit "..." markieren.
- Russische Übersetzung für jedes Redemittel.

NICHT verwenden (bereits vorhanden): {exclude}

Antworte NUR mit JSON:
{{"redemittel": [{{"text_de": "Angesichts der aktuellen Entwicklungen lässt sich ...",
                  "translation_ru": "...", "essay_part": "einleitung", "level": "C1"}}]}}
"""

ESSAY_PARTS = ("einleitung", "argument", "gegenargument", "beispiel", "schluss")

# Per-round focus → balanced large word sets instead of 60 nouns
ROUND_FOCUS: list[str] = [
    "",  # round 1: general
    "Fokus dieser Runde: VERBEN mit Rektion und Verb-Nomen-Kollokationen "
    "(z.B. 'Maßnahmen ergreifen', 'auf etw. zurückführen').",
    "Fokus dieser Runde: präzise ADJEKTIVE und NOMEN-KOMPOSITA "
    "(z.B. 'flächendeckend', 'die Versorgungssicherheit').",
]


def round_focus(round_no: int) -> str:
    if 0 <= round_no < len(ROUND_FOCUS):
        return ROUND_FOCUS[round_no]
    return ""


def _mistral_json_sync(prompt: str, mistral_api_key: str, mistral_model: str) -> dict:
    return post_mistral_json(
        [
            {"role": "system", "content": "Return only a valid JSON object. No markdown."},
            {"role": "user", "content": prompt},
        ],
        mistral_api_key,
        mistral_model,
        temperature=0.4,
        timeout=120,
        delays=[10, 30],
    )


async def generate_words(
    topic: str,
    n: int,
    exclude: list[str],
    mistral_api_key: str,
    mistral_model: str,
    mistral_semaphore: asyncio.Semaphore,
    focus: str = "",
) -> tuple[list[WordCandidate], list[PipelineError]]:
    """Generate n additional word candidates (origin='generated')."""
    errors: list[PipelineError] = []
    exclude_str = ", ".join(sorted(exclude)[:150]) or "-"
    prompt = _GEN_WORDS_PROMPT.format(
        topic=topic, n=n, exclude=exclude_str,
        focus=(focus + "\n") if focus else "",
    )

    async with mistral_semaphore:
        try:
            parsed = await asyncio.to_thread(
                _mistral_json_sync, prompt, mistral_api_key, mistral_model,
            )
        except Exception as exc:
            errors.append(PipelineError("generate", f"words/{topic}", str(exc)))
            return [], errors

    candidates: list[WordCandidate] = []
    excluded_lower = {e.lower() for e in exclude}
    for item in parsed.get("words") or []:
        if not isinstance(item, dict):
            continue
        raw_word = str(item.get("word", "")).strip()
        if not raw_word:
            continue
        candidate = WordCandidate(
            word=raw_word,
            pos=str(item.get("pos", "Other")),
            article=item.get("article") or None,
            examples=[str(e) for e in item.get("examples", []) if e][:3],
            source_url="",
            origin="generated",
        )
        normalized = normalize_candidate(candidate)
        if normalized and normalized.word.lower() not in excluded_lower:
            candidates.append(normalized)

    logger.info("Supplement generated %d word candidates for '%s'", len(candidates), topic)
    return dedupe_candidates(candidates), errors


async def generate_redemittel(
    topic: str,
    needed_per_part: dict[str, int],
    exclude: list[str],
    mistral_api_key: str,
    mistral_model: str,
    mistral_semaphore: asyncio.Semaphore,
) -> tuple[list[PhraseCandidate], list[PipelineError]]:
    """Generate Redemittel to balance essay parts."""
    errors: list[PipelineError] = []
    if not any(needed_per_part.values()):
        return [], errors

    prompt = _GEN_REDEMITTEL_PROMPT.format(
        topic=topic,
        exclude="; ".join(exclude[:60]) or "-",
        n_einleitung=needed_per_part.get("einleitung", 0),
        n_argument=needed_per_part.get("argument", 0),
        n_gegenargument=needed_per_part.get("gegenargument", 0),
        n_beispiel=needed_per_part.get("beispiel", 0),
        n_schluss=needed_per_part.get("schluss", 0),
    )

    async with mistral_semaphore:
        try:
            parsed = await asyncio.to_thread(
                _mistral_json_sync, prompt, mistral_api_key, mistral_model,
            )
        except Exception as exc:
            errors.append(PipelineError("phrases", f"redemittel/{topic}", str(exc)))
            return [], errors

    phrases: list[PhraseCandidate] = []
    excluded_lower = {e.lower() for e in exclude}
    for item in parsed.get("redemittel") or []:
        if not isinstance(item, dict):
            continue
        text_de = str(item.get("text_de", "")).strip()
        if not text_de or len(text_de) < 8 or text_de.lower() in excluded_lower:
            continue
        part = str(item.get("essay_part", "")).strip().lower()
        if part not in ESSAY_PARTS:
            part = "argument"
        level = str(item.get("level", "B2")).strip().upper()
        if level not in ("B1", "B2", "C1"):
            level = "B2"
        phrases.append(PhraseCandidate(
            text_de=text_de,
            translation_ru=str(item.get("translation_ru", "")).strip(),
            essay_part=part,
            level=level,
        ))

    logger.info("Supplement generated %d redemittel for '%s'", len(phrases), topic)
    return phrases, errors

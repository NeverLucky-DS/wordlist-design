from __future__ import annotations

"""Auto-topics — keep the queue filled without manual input.

Strategy (cheap → expensive):
1. Curated catalog of classic B2-C1 exam essay topics (TestDaF / Goethe /
   DSH / telc) — deterministic, free, high quality.
2. When the catalog is exhausted, ask Mistral for fresh topics that are not
   yet covered.

`pick_new_topics` returns topics that exist neither in word_topics nor in
the queue (case-insensitive).
"""

import asyncio
import logging

from .mistral_http import post_mistral_json

logger = logging.getLogger(__name__)

# Classic argumentative-essay topics from German B2-C1 exams
CURATED_TOPICS: list[str] = [
    "Klimawandel",
    "Digitalisierung",
    "Migration",
    "Soziale Medien",
    "Künstliche Intelligenz",
    "Globalisierung",
    "Bildungssystem",
    "Arbeitswelt der Zukunft",
    "Umweltschutz",
    "Energiewende",
    "Demografischer Wandel",
    "Gesundheit und Ernährung",
    "Massentourismus",
    "Urbanisierung",
    "Konsumgesellschaft",
    "Gleichberechtigung",
    "Ehrenamt",
    "Mobilität und Verkehr",
    "Datenschutz",
    "Wissenschaft und Ethik",
    "Kulturelle Vielfalt",
    "Mediennutzung",
    "Studium im Ausland",
    "Homeoffice",
    "Nachhaltiger Konsum",
    "Generationenkonflikt",
    "Sprachenlernen",
    "Armut und Reichtum",
    "Pressefreiheit",
    "Sport und Gesellschaft",
]

_GEN_TOPICS_PROMPT = """Du bist ein Experte für DaF-Prüfungen (TestDaF, Goethe C1, DSH, telc).
Nenne {n} NEUE Themen für argumentative Essays (B2-C1), die in Prüfungen
vorkommen könnten.

Bereits vorhanden (NICHT wiederholen): {exclude}

Regeln:
- Kurze Nominalphrasen (1-4 Wörter), z.B. "Plastikmüll", "Work-Life-Balance".
- Gesellschaftlich relevant, ergiebig für Pro/Contra-Argumentation.

Antworte NUR mit JSON: {{"topics": ["...", "..."]}}
"""


def _norm(t: str) -> str:
    return t.strip().lower()


async def pick_new_topics(
    existing: set[str],
    n: int,
    mistral_api_key: str,
    mistral_model: str,
) -> list[str]:
    """Return up to n topics not present in `existing` (lowercase set)."""
    existing_norm = {_norm(t) for t in existing}

    fresh = [t for t in CURATED_TOPICS if _norm(t) not in existing_norm][:n]
    if len(fresh) >= n or not mistral_api_key:
        if fresh:
            logger.info("Auto-topics from catalog: %s", fresh)
        return fresh

    # Catalog exhausted — generate the remainder
    need = n - len(fresh)
    exclude = sorted(existing_norm | {_norm(t) for t in fresh})
    prompt = _GEN_TOPICS_PROMPT.format(n=need, exclude=", ".join(exclude[:150]))
    try:
        parsed = await asyncio.to_thread(
            post_mistral_json,
            [
                {"role": "system", "content": "Return only a valid JSON object. No markdown."},
                {"role": "user", "content": prompt},
            ],
            mistral_api_key,
            mistral_model,
        )
    except Exception as exc:
        logger.warning("Auto-topic generation failed: %s", exc)
        return fresh

    for raw in parsed.get("topics") or []:
        t = str(raw).strip()
        if t and 2 < len(t) < 60 and _norm(t) not in existing_norm:
            fresh.append(t)
            existing_norm.add(_norm(t))
        if len(fresh) >= n:
            break

    logger.info("Auto-topics (catalog+generated): %s", fresh)
    return fresh

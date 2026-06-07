from __future__ import annotations

"""Step 2 — Article Parsing + Word Extraction.

All HTTPS calls use `requests` + `asyncio.to_thread` because
Python 3.9 / LibreSSL 2.8.3 on macOS breaks httpx async TLS.
"""

import asyncio
import json
import logging
import re
import time

import requests as _requests
from bs4 import BeautifulSoup

from .types import PipelineError, SourceItem, WordCandidate

logger = logging.getLogger(__name__)

MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
_MAX_TEXT_CHARS = 8_000

_EXTRACTION_PROMPT = """Du bekommst einen deutschsprachigen Artikeltext zum Thema "{topic}".
Aufgabe:
1. Finde 15-25 Wörter/Phrasen auf Niveau B2-C1, die typisch für Essays zu diesem Thema sind.
2. Für jedes Wort: 1-3 genaue Beispielsätze AUS DIESEM TEXT (Sätze, die das Wort enthalten).
3. Markiere Wortart und Artikel.
4. Gib saubere Wortformen zurück — KEINE Klammern, Anmerkungen oder Plural-Endungen im "word"-Feld.
   Falsch: "die Emission(en)", "das Szenario (denkbare ~ )"
   Richtig: "die Emission", "das Szenario"

Antworte NUR mit JSON-Array:
[{{"word": "der Klimawandel", "pos": "Noun", "article": "Der", "examples": ["...", "..."]}}]
pos: "Noun" | "Verb" | "Adjective" | "Other"
article: "Der" | "Die" | "Das" | null

Artikeltext:
{text}
"""


# ---------------------------------------------------------------------------
# Article fetching  (sync requests)
# ---------------------------------------------------------------------------

def _fetch_article_text_sync(url: str) -> str:
    try:
        resp = _requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; WordEnricher/1.0)"},
            timeout=15,
            allow_redirects=True,
        )
        resp.raise_for_status()
    except Exception:
        raise

    soup = BeautifulSoup(resp.text, "lxml")
    for tag in soup.find_all(["nav", "footer", "header", "script", "style", "aside", "form"]):
        tag.decompose()
    for tag in soup.find_all(class_=re.compile(r"nav|menu|sidebar|footer|header|cookie|banner", re.I)):
        tag.decompose()
    for tag in soup.find_all(id=re.compile(r"nav|menu|sidebar|footer|header|cookie|banner", re.I)):
        tag.decompose()

    main = (
        soup.find("article")
        or soup.find("main")
        or soup.find(id=re.compile(r"content|main|article|body", re.I))
        or soup.find(class_=re.compile(r"content|main|article|body", re.I))
        or soup.body
    )
    text = (main or soup).get_text(separator=" ", strip=True)
    text = re.sub(r"\s{2,}", " ", text)
    return text[:_MAX_TEXT_CHARS]


# ---------------------------------------------------------------------------
# Word name sanitizer
# ---------------------------------------------------------------------------

def _clean_word(raw: str) -> str:
    """Remove LLM annotations, plural hints, brackets from word strings."""
    # Remove bracketed content: "(en)", "(e)", "(denkbare ~ )", "[als Phrase]"
    w = re.sub(r"\s*\([^)]*\)", "", raw)
    w = re.sub(r"\s*\[[^\]]*\]", "", w)
    # Remove trailing asterisks, hints
    w = re.sub(r"\s*\*.*", "", w)
    w = w.strip(" ,;.")
    return w


# ---------------------------------------------------------------------------
# Mistral word extraction  (sync requests)
# ---------------------------------------------------------------------------

def _mistral_extract_sync(
    text: str,
    topic: str,
    source_url: str,
    mistral_api_key: str,
    mistral_model: str,
) -> list[WordCandidate]:
    if len(text.strip()) < 200:
        return []

    prompt = _EXTRACTION_PROMPT.format(topic=topic, text=text)
    payload = {
        "model": mistral_model,
        "messages": [
            {"role": "system", "content": "Return only a valid JSON array. No markdown."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {mistral_api_key}",
        "Content-Type": "application/json",
    }
    # Retry on 429
    delays = [10, 30]
    for attempt, delay in enumerate(delays):
        resp = _requests.post(MISTRAL_URL, headers=headers, json=payload, timeout=90)
        if resp.status_code == 429:
            if attempt < len(delays) - 1:
                logger.warning("Mistral 429 (extraction), retrying in %ds", delay)
                time.sleep(delay)
                continue
        resp.raise_for_status()
        break

    data = resp.json()
    raw_content = data["choices"][0]["message"]["content"]

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        return []

    if isinstance(parsed, dict):
        items = next((v for v in parsed.values() if isinstance(v, list)), [])
    elif isinstance(parsed, list):
        items = parsed
    else:
        return []

    candidates: list[WordCandidate] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        raw_word = str(item.get("word", "")).strip()
        word = _clean_word(raw_word)
        if not word or len(word) > 100:
            continue
        candidates.append(
            WordCandidate(
                word=word,
                pos=str(item.get("pos", "Other")),
                article=item.get("article") or None,
                examples=[str(e) for e in item.get("examples", []) if e][:3],
                source_url=source_url,
            )
        )
    return candidates


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------

async def process_sources(
    sources: list[SourceItem],
    topic: str,
    mistral_api_key: str,
    mistral_model: str,
    fetch_semaphore: asyncio.Semaphore | None = None,
    mistral_semaphore: asyncio.Semaphore | None = None,
) -> tuple[list[WordCandidate], list[PipelineError]]:
    """Step 2: Fetch all articles in parallel and extract words via Mistral."""
    if fetch_semaphore is None:
        fetch_semaphore = asyncio.Semaphore(5)
    if mistral_semaphore is None:
        mistral_semaphore = asyncio.Semaphore(2)  # conservative for free Mistral tier

    all_candidates: list[WordCandidate] = []
    errors: list[PipelineError] = []

    async def _process_one(source: SourceItem) -> None:
        # --- fetch article ---
        async with fetch_semaphore:
            try:
                text = await asyncio.to_thread(_fetch_article_text_sync, source.url)
            except Exception as exc:
                errors.append(PipelineError("fetch", source.url, str(exc)))
                return

        if not text.strip():
            errors.append(PipelineError("fetch", source.url, "Empty article text"))
            return

        # --- extract words via Mistral ---
        async with mistral_semaphore:
            try:
                words = await asyncio.to_thread(
                    _mistral_extract_sync,
                    text, topic, source.url,
                    mistral_api_key, mistral_model,
                )
                logger.info("Extracted %d words from %s", len(words), source.url)
                all_candidates.extend(words)
            except Exception as exc:
                errors.append(PipelineError("extract", source.url, str(exc)))

    await asyncio.gather(*[_process_one(s) for s in sources])

    # Deduplicate by normalised word form
    seen: dict[str, WordCandidate] = {}
    for c in all_candidates:
        key = c.word.lower().strip()
        if key not in seen:
            seen[key] = c
        else:
            seen[key].examples = list(dict.fromkeys(seen[key].examples + c.examples))[:3]

    return list(seen.values()), errors

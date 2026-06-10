from __future__ import annotations

"""Step 2 — Article Parsing + Word & Redemittel Extraction.

One Mistral call per article returns BOTH essay vocabulary (20-30 words)
and Redemittel (essay clichés) — same API cost as words-only.

All HTTPS calls use `requests` + `asyncio.to_thread` because
Python 3.9 / LibreSSL 2.8.3 on macOS breaks httpx async TLS.
"""

import asyncio
import logging
import re

import requests as _requests
from bs4 import BeautifulSoup

from .mistral_http import post_mistral_json
from .normalize import dedupe_candidates, normalize_candidate
from .types import PhraseCandidate, PipelineError, SourceItem, WordCandidate

logger = logging.getLogger(__name__)

_MAX_TEXT_CHARS = 12_000

ESSAY_PARTS = ("einleitung", "argument", "gegenargument", "beispiel", "schluss")

_EXTRACTION_PROMPT = """Du bekommst einen deutschsprachigen Artikeltext zum Thema "{topic}".

Aufgabe 1 — WÖRTER:
Finde 20-30 Wörter/Kollokationen auf Niveau B2-C1, die typisch für Essays zu diesem Thema sind.
- Für jedes Wort: 1-3 genaue Beispielsätze AUS DIESEM TEXT.
- Wortart und Artikel markieren.
- Saubere GRUNDFORMEN zurückgeben — Nomen im Singular Nominativ, Verben im Infinitiv,
  Adjektive in der Grundform. KEINE Klammern, Anmerkungen oder Plural-Endungen.
  Falsch: "die Emission(en)", "das Szenario (denkbare ~ )", "Emissionen", "nachhaltigen"
  Richtig: "die Emission", "das Szenario", "nachhaltig"

Aufgabe 2 — REDEMITTEL:
Finde 5-10 Redemittel/Satzbausteine für argumentative Essays, die in diesem Text vorkommen
oder von seinen Formulierungen inspiriert sind (B2-C1). Lücken mit "..." markieren.
Ordne jedes einem Essay-Teil zu: einleitung | argument | gegenargument | beispiel | schluss.

Antworte NUR mit einem JSON-Objekt:
{{
  "words": [{{"word": "der Klimawandel", "pos": "Noun", "article": "der", "examples": ["..."]}}],
  "redemittel": [{{"text_de": "Daraus lässt sich schließen, dass ...",
                   "translation_ru": "Из этого можно заключить, что ...",
                   "essay_part": "schluss", "level": "B2"}}]
}}
pos: "Noun" | "Verb" | "Adjective" | "Other"
article: "der" | "die" | "das" | null

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
# Mistral extraction  (sync requests)
# ---------------------------------------------------------------------------

def _mistral_extract_sync(
    text: str,
    topic: str,
    source_url: str,
    mistral_api_key: str,
    mistral_model: str,
) -> tuple[list[WordCandidate], list[PhraseCandidate]]:
    if len(text.strip()) < 200:
        return [], []

    prompt = _EXTRACTION_PROMPT.format(topic=topic, text=text)
    try:
        parsed = post_mistral_json(
            [
                {"role": "system", "content": "Return only a valid JSON object. No markdown."},
                {"role": "user", "content": prompt},
            ],
            mistral_api_key,
            mistral_model,
            temperature=0.1,
            timeout=120,
            delays=[10, 30],
        )
    except ValueError:
        return [], []

    word_items = parsed.get("words")
    if not isinstance(word_items, list):
        word_items = next((v for v in parsed.values() if isinstance(v, list)), [])

    candidates: list[WordCandidate] = []
    for item in word_items:
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
            source_url=source_url,
            origin="article",
        )
        normalized = normalize_candidate(candidate)
        if normalized:
            candidates.append(normalized)

    phrases: list[PhraseCandidate] = []
    for item in parsed.get("redemittel") or []:
        if not isinstance(item, dict):
            continue
        text_de = str(item.get("text_de", "")).strip()
        if not text_de or len(text_de) < 8:
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

    return candidates, phrases


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
) -> tuple[list[WordCandidate], list[PhraseCandidate], list[PipelineError]]:
    """Step 2: Fetch all articles in parallel, extract words + Redemittel."""
    if fetch_semaphore is None:
        fetch_semaphore = asyncio.Semaphore(5)
    if mistral_semaphore is None:
        mistral_semaphore = asyncio.Semaphore(2)

    all_candidates: list[WordCandidate] = []
    all_phrases: list[PhraseCandidate] = []
    errors: list[PipelineError] = []

    async def _process_one(source: SourceItem) -> None:
        async with fetch_semaphore:
            try:
                text = await asyncio.to_thread(_fetch_article_text_sync, source.url)
            except Exception as exc:
                errors.append(PipelineError("fetch", source.url, str(exc)))
                return

        if not text.strip():
            errors.append(PipelineError("fetch", source.url, "Empty article text"))
            return

        async with mistral_semaphore:
            try:
                words, phrases = await asyncio.to_thread(
                    _mistral_extract_sync,
                    text, topic, source.url,
                    mistral_api_key, mistral_model,
                )
                logger.info(
                    "Extracted %d words, %d redemittel from %s",
                    len(words), len(phrases), source.url,
                )
                all_candidates.extend(words)
                all_phrases.extend(phrases)
            except Exception as exc:
                errors.append(PipelineError("extract", source.url, str(exc)))

    await asyncio.gather(*[_process_one(s) for s in sources])

    # Dedupe phrases by lowercase text
    seen_phrases: dict[str, PhraseCandidate] = {}
    for p in all_phrases:
        key = p.text_de.lower().strip()
        if key not in seen_phrases:
            seen_phrases[key] = p

    return dedupe_candidates(all_candidates), list(seen_phrases.values()), errors

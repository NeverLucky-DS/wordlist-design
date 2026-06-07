from __future__ import annotations

"""Step 1 — Source Discovery.

Primary:  Grok (X.ai) with live web search.
Fallback: DuckDuckGo search (no API key required).

Uses `requests` + `asyncio.to_thread` instead of httpx async, because
Python 3.9 / LibreSSL builds have TLS issues with httpx's async transport
against Cloudflare-fronted hosts (api.x.ai, etc.).
"""

import asyncio
import json
import logging
import re
from typing import Any

import requests  # sync — wrapped in asyncio.to_thread

from .types import PipelineError, SourceItem

logger = logging.getLogger(__name__)

GROK_API_URL = "https://api.x.ai/v1/chat/completions"
_REQUESTS_TIMEOUT = 60

_SYSTEM = "You are a research assistant. Return only valid JSON, no markdown fences."

_USER_TMPL = """Find 8-12 high-quality German-language sources (essays, journal articles, academic texts)
on the topic: "{topic}".
Requirements: language level B2–C2, rich vocabulary, essay/argumentative style.
Return ONLY a JSON array (no other text):
[{{"url": "https://...", "title": "...", "type": "essay|article|academic"}}]
"""

_DDG_QUERIES = [
    '"{topic}" Essay Deutsch site:bpb.de OR site:zeit.de OR site:spiegel.de OR site:faz.net',
    '"{topic}" Argumentation Deutsch B2 C1',
    'Klimawandel Umwelt Deutsch Essay Argumente',
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_json_array(text: str) -> list[dict]:
    """Extract first JSON array from possibly-wrapped text."""
    text = text.strip()
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```", "", text)
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        return []
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []


# ---------------------------------------------------------------------------
# Grok discovery (sync, wrapped later)
# ---------------------------------------------------------------------------

def _grok_discover_sync(topic: str, grok_api_key: str) -> tuple[list[SourceItem], str | None]:
    """Synchronous Grok call — run inside asyncio.to_thread."""
    headers = {
        "Authorization": f"Bearer {grok_api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": "grok-3",
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": _USER_TMPL.format(topic=topic)},
        ],
        "temperature": 0.3,
        "search_parameters": {
            "mode": "on",
            "max_search_results": 15,
            "sources": [{"type": "web"}],
        },
    }
    try:
        resp = requests.post(GROK_API_URL, headers=headers, json=payload, timeout=_REQUESTS_TIMEOUT)
    except Exception as exc:
        return [], str(exc)

    if resp.status_code in (401, 403):
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        return [], body.get("error", f"HTTP {resp.status_code}")
    try:
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return [], str(exc)

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

    # Also pull URLs from citations (live search results)
    seen: set[str] = set()
    sources: list[SourceItem] = []

    for raw in _extract_json_array(content):
        url = str(raw.get("url", "")).strip()
        title = str(raw.get("title", url)).strip()
        stype = str(raw.get("type", "article")).strip()
        if url and url.startswith("http") and url not in seen:
            seen.add(url)
            sources.append(SourceItem(url=url, title=title, source_type=stype))

    for choice in data.get("choices", []):
        for citation in choice.get("message", {}).get("citations", []) or []:
            url = citation.get("url") or citation.get("link") or ""
            if url and url not in seen:
                seen.add(url)
                sources.append(SourceItem(url=url, title=url, source_type="article"))

    return sources, None


# ---------------------------------------------------------------------------
# DuckDuckGo fallback (sync, wrapped later)
# ---------------------------------------------------------------------------

def _ddg_discover_sync(topic: str) -> list[SourceItem]:
    """Free fallback: search DuckDuckGo for German essay sources."""
    from duckduckgo_search import DDGS  # lazy import

    queries = [
        f'"{topic}" Essay Deutsch Argumentation',
        f'"{topic}" site:bpb.de OR site:zeit.de OR site:spiegel.de',
        f'"{topic}" Deutsch Analyse Kommentar',
    ]

    seen: set[str] = set()
    results: list[SourceItem] = []

    with DDGS() as ddgs:
        for query in queries:
            try:
                for r in ddgs.text(query, region="de-de", max_results=4):
                    url = r.get("href", "")
                    title = r.get("title", url)
                    if url and url not in seen:
                        seen.add(url)
                        results.append(SourceItem(url=url, title=title, source_type="article"))
                if len(results) >= 10:
                    break
            except Exception:
                continue

    return results


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------

async def discover_sources(
    topic: str,
    grok_api_key: str = "",
) -> tuple[list[SourceItem], list[PipelineError]]:
    """Step 1: Discover German-language sources for *topic*.

    Tries Grok first (if key provided); falls back to DuckDuckGo.
    """
    errors: list[PipelineError] = []

    if grok_api_key:
        sources, grok_error = await asyncio.to_thread(_grok_discover_sync, topic, grok_api_key)
        if grok_error:
            logger.warning("Grok discovery failed (%s), falling back to DuckDuckGo", grok_error)
            errors.append(PipelineError("fetch", f"grok/topic={topic}", grok_error))
        elif sources:
            logger.info("Grok discovered %d sources for '%s'", len(sources), topic)
            return sources, errors

    # DuckDuckGo fallback
    logger.info("Using DuckDuckGo to discover sources for '%s'", topic)
    try:
        ddg_sources = await asyncio.to_thread(_ddg_discover_sync, topic)
    except Exception as exc:
        errors.append(PipelineError("fetch", f"ddg/topic={topic}", str(exc)))
        return [], errors

    if not ddg_sources:
        errors.append(PipelineError("fetch", f"ddg/topic={topic}", "DuckDuckGo returned no results"))

    logger.info("DuckDuckGo found %d sources for '%s'", len(ddg_sources), topic)
    return ddg_sources, errors

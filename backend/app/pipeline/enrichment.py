from __future__ import annotations

"""Step 4 — Word Enrichment.

All HTTPS calls use `requests` + `asyncio.to_thread` because
Python 3.9 / LibreSSL 2.8.3 on macOS breaks httpx async TLS.

Sources (in priority order):
1. de.wiktionary.org  — grammar tables, level, usage notes
2. dwds.de            — example sentences, definitions (fallback / supplement)
"""

import asyncio
import json
import logging
import re
import time

import requests as _requests

from .types import EnrichedWord, PipelineError, WordCandidate

logger = logging.getLogger(__name__)

WIKTIONARY_API = "https://de.wiktionary.org/w/api.php"
DWDS_API       = "https://www.dwds.de/api/wb/snippet/?q={word}"
MISTRAL_URL    = "https://api.mistral.ai/v1/chat/completions"

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_STRUCTURE_PROMPT = """Du bist ein deutsches Lexikon-Extraktionssystem.
Unten stehen Rohdaten für das deutsche Wort "{word}".

Bereits extrahierte Beispielsätze (aus Artikeln): {examples_json}
Anzahl bereits vorhandener Beispiele: {examples_count}

Gib ausschließlich ein JSON-Objekt zurück (KEIN Markdown, KEINE Erklärungen):
{{
  "article": "der|die|das|null",
  "pos": "Noun|Verb|Adjective|Other",
  "level": "A1|A2|B1|B2|C1|C2|null",
  "ru": "точный перевод на русский язык (2-5 слов)",
  "rektion": "управление глагола/существительного, напр. 'auf + Akk.' или ''",
  "ready_phrase": "готовая фраза с управлением, показывающая использование слова, или ''",
  "declension": {{}},
  "examples_generated": []
}}

PFLICHTREGELN — Fehler hier sind inakzeptabel:
- "pos": MUSS "Noun", "Verb", "Adjective" oder "Other" sein.
- "article": MUSS "der", "die", "das" sein wenn Nomen, sonst null.
- "ru": MUSS eine sinnvolle russische Übersetzung enthalten, NICHT leer.
- "level": MUSS ein CEFR-Niveau sein wenn erkennbar, sonst null.
- "declension": MUSS für Verben Konjugation enthalten (Hilfsverb, Partizip II,
  Präteritum, Präsens-Formen). Für Nomen: Kasus-Tabelle. Für Adjektive:
  Steigerungsformen (positiv/komparativ/superlativ). Niemals leer lassen wenn
  die Rohdaten es enthalten.
- "examples_generated": Füge {examples_needed} neue deutsche Beispielsätze hinzu
  (B2-C1 Niveau, mit dem Wort in Fettschrift als **Wort**). Wenn bereits 3+ vorhanden, [].

Für Verben MUSS "declension" folgende Struktur haben:
{{
  "hilfsverb": "haben|sein",
  "Partizip II": "ge...t/ge...en",
  "Präteritum": "...",
  "Präsens": {{"ich":"...", "du":"...", "er/sie/es":"...", "wir":"...", "ihr":"...", "sie/Sie":"..."}}
}}

Rohdaten (Wiktionary + DWDS):
{wikitext}
"""


# ---------------------------------------------------------------------------
# Wiktionary  (sync)
# ---------------------------------------------------------------------------

def _fetch_wikitext_sync(word: str) -> str | None:
    params = {
        "action": "parse", "page": word,
        "prop": "wikitext", "format": "json", "redirects": "1",
    }
    try:
        session = _requests.Session()
        resp = session.get(
            WIKTIONARY_API, params=params,
            headers={"User-Agent": "WordEnricher/1.0 (educational project)"},
            timeout=15,
        )
        session.close()
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("Wiktionary fetch failed for '%s': %s", word, exc)
        return None

    if "error" in data:
        return None

    wikitext: str = data.get("parse", {}).get("wikitext", {}).get("*", "")
    if not wikitext:
        return None

    # Extract German section only
    de_match = re.search(
        r"== [^\n=]+ \({{Sprache\|Deutsch}}\) ==(.+?)(?=\n== [^\n=]+ ==|\Z)",
        wikitext, re.DOTALL,
    )
    section = de_match.group(0) if de_match else wikitext
    return section[:8_000]


# ---------------------------------------------------------------------------
# DWDS  (sync) — secondary source for examples & definitions
# ---------------------------------------------------------------------------

def _fetch_dwds_sync(word: str) -> str | None:
    """Fetch DWDS snippet for a word. Returns plain-text summary or None."""
    try:
        session = _requests.Session()
        resp = session.get(
            DWDS_API.format(word=word),
            headers={"User-Agent": "WordEnricher/1.0 (educational project)", "Accept": "application/json"},
            timeout=10,
        )
        session.close()
        if resp.status_code != 200:
            return None
        payload = resp.json()
    except Exception as exc:
        logger.debug("DWDS fetch failed for '%s': %s", word, exc)
        return None

    lines: list[str] = []

    # DWDS returns a list of word senses
    entries = payload if isinstance(payload, list) else [payload]
    for entry in entries[:2]:
        if not isinstance(entry, dict):
            continue
        # Definition
        for key in ("def", "definition", "kurzdefinition"):
            val = entry.get(key)
            if val and isinstance(val, str):
                clean = re.sub(r"<[^>]+>", "", val).strip()
                if clean:
                    lines.append("Definition: " + clean)
                    break
        # Examples from DWDS
        examples = entry.get("examples") or entry.get("belege") or []
        if isinstance(examples, list):
            for ex in examples[:3]:
                txt = ex if isinstance(ex, str) else ex.get("text", "")
                txt = re.sub(r"<[^>]+>", "", str(txt)).strip()
                if txt:
                    lines.append("Beispiel: " + txt[:200])

    return "\n".join(lines) if lines else None


# ---------------------------------------------------------------------------
# Confidence check — only enrich words we can be sure about
# ---------------------------------------------------------------------------

def _is_confident(candidate: WordCandidate, wikitext: str | None) -> bool:
    """Return True if we have enough data to run the expensive Mistral call."""
    word = candidate.word.strip()
    # Too short or looks like garbage
    if len(word) < 3:
        return False
    # Contains digits or special chars (not a real dictionary word)
    if re.search(r"[\d@#%]", word):
        return False
    # Wiktionary found something — most reliable signal
    if wikitext and len(wikitext) > 100:
        return True
    # Even without Wiktionary, proceed if we have article/pos hint
    if candidate.pos and candidate.pos.lower() not in ("other", "unknown", ""):
        return True
    return False


# ---------------------------------------------------------------------------
# Mistral structuring  (sync)
# ---------------------------------------------------------------------------

def _mistral_structure_sync(
    word: str,
    combined_text: str,
    existing_examples: list[str],
    mistral_api_key: str,
    mistral_model: str,
) -> dict:
    examples_needed = max(0, 3 - len(existing_examples))
    prompt = _STRUCTURE_PROMPT.format(
        word=word,
        wikitext=combined_text,
        examples_json=json.dumps(existing_examples, ensure_ascii=False),
        examples_count=len(existing_examples),
        examples_needed=examples_needed,
    )
    payload = {
        "model": mistral_model,
        "messages": [
            {"role": "system", "content": "Return only a valid JSON object. No markdown, no prose."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {mistral_api_key}",
        "Content-Type": "application/json",
    }
    delays = [5, 15, 30]
    for attempt, delay in enumerate(delays):
        resp = _requests.post(MISTRAL_URL, headers=headers, json=payload, timeout=90)
        if resp.status_code == 429:
            if attempt < len(delays) - 1:
                logger.warning("Mistral 429 for '%s', retrying in %ds", word, delay)
                time.sleep(delay)
                continue
        resp.raise_for_status()
        break

    content = resp.json()["choices"][0]["message"]["content"]
    return json.loads(content)


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------

async def enrich_word(
    candidate: WordCandidate,
    mistral_api_key: str,
    mistral_model: str,
    wiktionary_semaphore: asyncio.Semaphore,
    mistral_semaphore: asyncio.Semaphore,
) -> tuple[EnrichedWord | None, list[PipelineError]]:
    """Step 4: Wiktionary + DWDS → Mistral structuring."""
    errors: list[PipelineError] = []

    # Clean up the lookup word
    lookup_word = candidate.word
    for prefix in ("Der ", "Die ", "Das ", "der ", "die ", "das "):
        if lookup_word.startswith(prefix):
            lookup_word = lookup_word[len(prefix):]
            break
    lookup_word = re.sub(r"\s*\(.*?\)", "", lookup_word).strip()
    lookup_word = re.sub(r"\s*\[.*?\]", "", lookup_word).strip()
    lookup_word = re.sub(r"\(en\)|\(e\)|\(s\)", "", lookup_word).strip()

    # ── 1. Wiktionary ──────────────────────────────────────────────────────
    async with wiktionary_semaphore:
        wikitext = await asyncio.to_thread(_fetch_wikitext_sync, lookup_word)

    if wikitext is None:
        wikitext = await asyncio.to_thread(_fetch_wikitext_sync, lookup_word)

    if wikitext is None:
        errors.append(PipelineError(
            "wiktionary", candidate.word,
            f"Not found: '{lookup_word}' in de.wiktionary.org",
        ))

    # ── 2. DWDS (secondary source, non-blocking) ──────────────────────────
    dwds_text: str | None = None
    try:
        dwds_text = await asyncio.to_thread(_fetch_dwds_sync, lookup_word)
    except Exception:
        pass

    # ── 3. Combine sources ────────────────────────────────────────────────
    parts: list[str] = []
    if wikitext:
        parts.append("=== Wiktionary ===\n" + wikitext)
    else:
        parts.append(f"=== Wiktionary ===\nKein Eintrag für: {lookup_word}")
    if dwds_text:
        parts.append("=== DWDS ===\n" + dwds_text)

    combined = "\n\n".join(parts)

    # ── 4. Confidence check ───────────────────────────────────────────────
    if not _is_confident(candidate, wikitext):
        errors.append(PipelineError(
            "mistral", candidate.word,
            "Low confidence — skipping Mistral enrichment",
        ))
        return None, errors

    # ── 5. Mistral structuring ─────────────────────────────────────────────
    async with mistral_semaphore:
        try:
            parsed = await asyncio.to_thread(
                _mistral_structure_sync,
                candidate.word,
                combined,
                candidate.examples,
                mistral_api_key,
                mistral_model,
            )
        except Exception as exc:
            errors.append(PipelineError("mistral", candidate.word, str(exc)))
            return None, errors

    article_raw = parsed.get("article")
    article = (
        str(article_raw).strip()
        if article_raw and str(article_raw).lower() not in ("null", "none", "")
        else None
    )
    examples_needed = max(0, 3 - len(candidate.examples))

    enriched = EnrichedWord(
        de=candidate.word,
        article=article,
        pos=str(parsed.get("pos", "Other")),
        level=parsed.get("level") or None,
        ru=str(parsed.get("ru", "")),
        rektion=str(parsed.get("rektion", "")),
        ready_phrase=str(parsed.get("ready_phrase", "")),
        declension=parsed.get("declension") if isinstance(parsed.get("declension"), dict) else {},
        examples_generated=[str(e) for e in parsed.get("examples_generated", []) if e][:examples_needed],
    )
    return enriched, errors

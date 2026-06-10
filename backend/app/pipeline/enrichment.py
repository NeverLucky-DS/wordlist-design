from __future__ import annotations

"""Step 4 — Word Enrichment (batched).

Key change vs v1: words are enriched in BATCHES of N per Mistral call
instead of one call per word. 50 words = ~7 calls instead of 50+,
which keeps the free Mistral tier well under its rate limit.

Sources per word (fetched in parallel, condensed before prompting):
1. de.wiktionary.org  — grammar tables, level, usage notes
2. dwds.de            — example sentences, definitions

Words WITHOUT a dictionary hit are no longer dropped if they came from a
real article (origin="article") — Mistral fills the grammar itself.
Generated words (origin="generated") still require a dictionary hit,
to guard against hallucinations.

All HTTPS calls use `requests` + `asyncio.to_thread` because
Python 3.9 / LibreSSL 2.8.3 on macOS breaks httpx async TLS.
"""

import asyncio
import logging
import re

import requests as _requests

from .mistral_http import post_mistral_json
from .types import EnrichedWord, PipelineError, WordCandidate

logger = logging.getLogger(__name__)

WIKTIONARY_API = "https://de.wiktionary.org/w/api.php"
DWDS_API       = "https://www.dwds.de/api/wb/snippet/?q={word}"

_MAX_RAW_PER_WORD = 2_500  # condensed wikitext budget per word in batch prompt

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_BATCH_PROMPT = """Du bist ein deutsches Lexikon-Extraktionssystem.
Unten stehen Rohdaten für {count} deutsche Wörter. Verarbeite ALLE Wörter.

Gib ausschließlich ein JSON-Objekt zurück (KEIN Markdown, KEINE Erklärungen):
{{"words": [
  {{
    "word": "<exakt das Eingabewort>",
    "article": "der|die|das|null",
    "pos": "Noun|Verb|Adjective|Other",
    "level": "A1|A2|B1|B2|C1|C2|null",
    "ru": "точный перевод на русский язык (2-5 слов)",
    "rektion": "управление, напр. 'auf + Akk.' или ''",
    "ready_phrase": "готовая фраза с управлением или ''",
    "declension": {{}},
    "examples_generated": []
  }}
]}}

PFLICHTREGELN — Fehler hier sind inakzeptabel:
- "word": MUSS exakt dem Eingabewort entsprechen (zum Zuordnen).
- "pos": MUSS "Noun", "Verb", "Adjective" oder "Other" sein.
- "article": MUSS "der", "die", "das" sein wenn Nomen, sonst null.
- "ru": MUSS eine sinnvolle russische Übersetzung enthalten, NICHT leer.
- "rektion": Wenn das Wort eine typische Präposition regiert (z.B. "hinweisen auf + Akk."),
  MUSS sie angegeben werden. Nutze dein Wissen, auch ohne Rohdaten.
- "declension": Für Verben Konjugation: {{"hilfsverb": "haben|sein", "Partizip II": "...",
  "Präteritum": "...", "Präsens": {{"ich":"...", "du":"...", "er/sie/es":"...",
  "wir":"...", "ihr":"...", "sie/Sie":"..."}}}}.
  Für Nomen: {{"Genus":"...", "Genitiv Singular":"...", "Plural":"..."}}.
  Für Adjektive: {{"Positiv":"...", "Komparativ":"...", "Superlativ":"..."}}.
  Niemals leer lassen — wenn die Rohdaten nichts enthalten, nutze dein Sprachwissen.
- "examples_generated": So viele NEUE deutsche Beispielsätze (B2-C1, Wort fett als **Wort**)
  wie im Feld "examples_needed" des Wortes angegeben. Wenn 0, dann [].

Eingabewörter mit Rohdaten:
{words_block}
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

    de_match = re.search(
        r"== [^\n=]+ \({{Sprache\|Deutsch}}\) ==(.+?)(?=\n== [^\n=]+ ==|\Z)",
        wikitext, re.DOTALL,
    )
    section = de_match.group(0) if de_match else wikitext
    return _condense_wikitext(section)


_KEEP_BLOCK_RE = re.compile(
    r"{{(Deutsch (?:Substantiv|Verb|Adjektiv) Übersicht)[^}]*}}", re.DOTALL
)


def _condense_wikitext(section: str) -> str:
    """Keep only the parts useful for enrichment, capped per word."""
    parts: list[str] = []

    # Grammar overview tables (Übersicht templates)
    for m in _KEEP_BLOCK_RE.finditer(section):
        parts.append(m.group(0))

    # Wortart line
    wa = re.search(r"=== {{Wortart\|[^\n]+", section)
    if wa:
        parts.append(wa.group(0))

    # Bedeutungen block (first 12 lines)
    bed = re.search(r"{{Bedeutungen}}\n((?::\[\d+\][^\n]*\n?){1,12})", section)
    if bed:
        parts.append("{{Bedeutungen}}\n" + bed.group(1))

    # Russian translation line
    ru = re.search(r"\*{{ru}}[^\n]*", section)
    if ru:
        parts.append(ru.group(0))

    condensed = "\n".join(parts).strip()
    if len(condensed) < 80:  # condensing failed — fall back to raw head
        condensed = section
    return condensed[:_MAX_RAW_PER_WORD]


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
    entries = payload if isinstance(payload, list) else [payload]
    for entry in entries[:2]:
        if not isinstance(entry, dict):
            continue
        for key in ("def", "definition", "kurzdefinition"):
            val = entry.get(key)
            if val and isinstance(val, str):
                clean = re.sub(r"<[^>]+>", "", val).strip()
                if clean:
                    lines.append("Definition: " + clean)
                    break
        examples = entry.get("examples") or entry.get("belege") or []
        if isinstance(examples, list):
            for ex in examples[:2]:
                txt = ex if isinstance(ex, str) else ex.get("text", "")
                txt = re.sub(r"<[^>]+>", "", str(txt)).strip()
                if txt:
                    lines.append("Beispiel: " + txt[:200])

    return "\n".join(lines)[:800] if lines else None


# ---------------------------------------------------------------------------
# Mistral batch structuring  (sync)
# ---------------------------------------------------------------------------

def _mistral_batch_sync(
    words_block: str,
    count: int,
    mistral_api_key: str,
    mistral_model: str,
) -> dict:
    prompt = _BATCH_PROMPT.format(count=count, words_block=words_block)
    return post_mistral_json(
        [
            {"role": "system", "content": "Return only a valid JSON object. No markdown, no prose."},
            {"role": "user", "content": prompt},
        ],
        mistral_api_key,
        mistral_model,
        temperature=0.1,
        timeout=180,
        delays=[5, 15, 30],
    )


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------

def _basic_filter(candidate: WordCandidate) -> bool:
    word = candidate.word.strip()
    if len(word) < 3:
        return False
    if re.search(r"[\d@#%]", word):
        return False
    return True


async def fetch_raw_data(
    candidates: list[WordCandidate],
    wiktionary_semaphore: asyncio.Semaphore,
) -> dict[str, tuple[str | None, str | None]]:
    """Fetch Wiktionary + DWDS for all candidates in parallel.

    Returns {word: (wikitext, dwds_text)}.
    """
    results: dict[str, tuple[str | None, str | None]] = {}

    async def _one(c: WordCandidate) -> None:
        async with wiktionary_semaphore:
            wikitext = await asyncio.to_thread(_fetch_wikitext_sync, c.word)
        dwds_text: str | None = None
        try:
            dwds_text = await asyncio.to_thread(_fetch_dwds_sync, c.word)
        except Exception:
            pass
        results[c.word] = (wikitext, dwds_text)

    await asyncio.gather(*[_one(c) for c in candidates])
    return results


async def enrich_batch(
    candidates: list[WordCandidate],
    mistral_api_key: str,
    mistral_model: str,
    wiktionary_semaphore: asyncio.Semaphore,
    mistral_semaphore: asyncio.Semaphore,
) -> tuple[list[tuple[WordCandidate, EnrichedWord]], list[tuple[WordCandidate, PipelineError]]]:
    """Step 4 (batched): dictionaries → one Mistral call for the whole batch.

    Returns (enriched_pairs, failed_pairs) so the caller can retry failures.
    """
    failed: list[tuple[WordCandidate, PipelineError]] = []

    batch = [c for c in candidates if _basic_filter(c)]
    for c in candidates:
        if c not in batch:
            failed.append((c, PipelineError("extract", c.word, "Garbage word — filtered out")))
    if not batch:
        return [], failed

    raw = await fetch_raw_data(batch, wiktionary_semaphore)

    # Generated words without any dictionary hit → likely hallucination, drop.
    verified: list[WordCandidate] = []
    for c in batch:
        wikitext, dwds_text = raw.get(c.word, (None, None))
        if c.origin == "generated" and not wikitext and not dwds_text:
            failed.append((c, PipelineError(
                "wiktionary", c.word, "Generated word not found in Wiktionary/DWDS — dropped",
            )))
        else:
            verified.append(c)
    if not verified:
        return [], failed

    # Build the words block for the batch prompt
    blocks: list[str] = []
    for i, c in enumerate(verified, 1):
        wikitext, dwds_text = raw.get(c.word, (None, None))
        raw_parts = []
        if wikitext:
            raw_parts.append(wikitext)
        if dwds_text:
            raw_parts.append("DWDS:\n" + dwds_text)
        raw_text = "\n".join(raw_parts) or "(kein Wörterbucheintrag — nutze dein Sprachwissen)"
        examples_needed = max(0, 3 - len(c.examples))
        blocks.append(
            f"--- Wort {i}: {c.word}\n"
            f"pos-Hinweis: {c.pos} | Artikel-Hinweis: {c.article or '-'} | "
            f"examples_needed: {examples_needed}\n"
            f"{raw_text}"
        )
    words_block = "\n\n".join(blocks)

    async with mistral_semaphore:
        try:
            parsed = await asyncio.to_thread(
                _mistral_batch_sync,
                words_block, len(verified),
                mistral_api_key, mistral_model,
            )
        except Exception as exc:
            for c in verified:
                failed.append((c, PipelineError("mistral", c.word, str(exc))))
            return [], failed

    items = parsed.get("words") if isinstance(parsed, dict) else None
    if not isinstance(items, list):
        items = next((v for v in parsed.values() if isinstance(v, list)), []) if isinstance(parsed, dict) else []

    by_word: dict[str, dict] = {}
    for item in items:
        if isinstance(item, dict) and item.get("word"):
            by_word[str(item["word"]).strip().lower()] = item

    enriched_pairs: list[tuple[WordCandidate, EnrichedWord]] = []
    for c in verified:
        item = by_word.get(c.word.strip().lower())
        if item is None:
            failed.append((c, PipelineError("mistral", c.word, "Missing from batch response")))
            continue

        article_raw = item.get("article")
        article = (
            str(article_raw).strip().lower()
            if article_raw and str(article_raw).lower() not in ("null", "none", "")
            else None
        )
        examples_needed = max(0, 3 - len(c.examples))
        enriched = EnrichedWord(
            de=c.word,
            article=article,
            pos=str(item.get("pos", c.pos or "Other")),
            level=item.get("level") or None,
            ru=str(item.get("ru", "")),
            rektion=str(item.get("rektion", "")),
            ready_phrase=str(item.get("ready_phrase", "")),
            declension=item.get("declension") if isinstance(item.get("declension"), dict) else {},
            examples_generated=[str(e) for e in item.get("examples_generated", []) if e][:examples_needed],
        )
        if not enriched.ru.strip():
            failed.append((c, PipelineError("mistral", c.word, "Empty translation in batch response")))
            continue
        enriched_pairs.append((c, enriched))

    return enriched_pairs, failed


async def enrich_word(
    candidate: WordCandidate,
    mistral_api_key: str,
    mistral_model: str,
    wiktionary_semaphore: asyncio.Semaphore,
    mistral_semaphore: asyncio.Semaphore,
) -> tuple[EnrichedWord | None, list[PipelineError]]:
    """Single-word compatibility wrapper around enrich_batch."""
    pairs, failed = await enrich_batch(
        [candidate], mistral_api_key, mistral_model,
        wiktionary_semaphore, mistral_semaphore,
    )
    errors = [err for _, err in failed]
    if pairs:
        return pairs[0][1], errors
    return None, errors

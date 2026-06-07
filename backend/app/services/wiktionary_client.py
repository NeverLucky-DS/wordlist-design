from __future__ import annotations

from urllib.parse import quote

import httpx

WIKTIONARY_PAGE_API = "https://de.wiktionary.org/api/rest_v1/page/definition/{word}"


async def fetch_wiktionary_entry(word: str) -> dict | None:
    url = WIKTIONARY_PAGE_API.format(word=quote(word))
    timeout = httpx.Timeout(8.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(url)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError:
            return None

    de_entries = payload.get("de")
    if not isinstance(de_entries, list) or not de_entries:
        return None

    first = de_entries[0]
    if not isinstance(first, dict):
        return None

    return {
        "title": first.get("word"),
        "lang": "de",
        "pos": first.get("partOfSpeech"),
        "source_url": f"https://de.wiktionary.org/wiki/{quote(word)}",
        # REST endpoint часто не даёт полноценные таблицы склонений/спряжений.
        # Оставляем расширяемую структуру: позже можно добавить парсинг sections/html.
        "forms": [],
        "metadata": {
            "api": "wiktionary-rest-v1",
            "definitions_count": len(de_entries),
        },
    }

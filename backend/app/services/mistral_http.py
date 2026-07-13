from __future__ import annotations

"""Shared Mistral HTTP helper — one place for retries, 429 handling, JSON parsing.

Used by essay analysis and future vocab enrichment. Stability features:

- Honours the `Retry-After` header on 429 (capped at 60s), falls back to
  exponential backoff.
- Module-wide cooldown: after a 429 every caller waits until the cooldown
  expires before firing the next request, so parallel workers don't keep
  hammering an already-throttled API.
- Always returns parsed JSON (dict) or raises — callers never touch raw HTTP.

Sync (`requests`) by design — wrapped in `asyncio.to_thread` by callers,
because Python 3.9 / LibreSSL builds break httpx async TLS.
"""

import json
import logging
import threading
import time

import requests as _requests

logger = logging.getLogger(__name__)

MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"

_DEFAULT_DELAYS = [5, 15, 30]
_MAX_RETRY_AFTER = 60.0

# Module-wide cooldown shared across threads
_cooldown_lock = threading.Lock()
_cooldown_until = 0.0


def _wait_for_cooldown() -> None:
    with _cooldown_lock:
        wait = _cooldown_until - time.monotonic()
    if wait > 0:
        logger.info("Mistral cooldown active — waiting %.1fs", wait)
        time.sleep(wait)


def _set_cooldown(seconds: float) -> None:
    global _cooldown_until
    with _cooldown_lock:
        _cooldown_until = max(_cooldown_until, time.monotonic() + seconds)


def post_mistral_json(
    messages: list[dict],
    api_key: str,
    model: str,
    *,
    temperature: float = 0.1,
    timeout: int = 120,
    delays: list[int] | None = None,
) -> dict:
    """POST a chat request, return the parsed JSON object from the response.

    Raises requests.HTTPError / json.JSONDecodeError on unrecoverable failure.
    """
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    delays = delays or _DEFAULT_DELAYS

    resp = None
    for attempt in range(len(delays) + 1):
        _wait_for_cooldown()
        resp = _requests.post(MISTRAL_URL, headers=headers, json=payload, timeout=timeout)
        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            try:
                delay = min(float(retry_after), _MAX_RETRY_AFTER) if retry_after else float(
                    delays[min(attempt, len(delays) - 1)]
                )
            except ValueError:
                delay = float(delays[min(attempt, len(delays) - 1)])
            _set_cooldown(delay)
            if attempt < len(delays):
                logger.warning("Mistral 429, retrying in %.1fs (attempt %d)", delay, attempt + 1)
                time.sleep(delay)
                continue
        resp.raise_for_status()
        break

    content = resp.json()["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise ValueError(f"Mistral returned non-object JSON: {type(parsed).__name__}")
    return parsed

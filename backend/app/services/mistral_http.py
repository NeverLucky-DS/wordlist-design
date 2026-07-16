from __future__ import annotations

"""Shared Mistral HTTP helper — one place for retries, 429 handling, JSON parsing.

Used by essay analysis and vocab enrichment. Stability features:

- Retries transient failures with exponential backoff: 429 (rate limit),
  5xx (server), and connection drops / timeouts (`RemoteDisconnected` &
  friends — the Mistral edge closes long or unlucky requests without a
  response, and the enrichment workload hits this constantly).
- Honours the `Retry-After` header on 429 (capped at 60s).
- Per-key cooldown: after a 429 every caller *using that key* waits until the
  cooldown expires before firing again — but a 429 on one user's key does NOT
  stall other users' keys. Essential once each account enriches through its own
  key in parallel.
- Always returns parsed JSON (dict) or raises — callers never touch raw HTTP.

Sync (`requests`) by design — wrapped in `asyncio.to_thread` by callers,
because Python 3.9 / LibreSSL builds break httpx async TLS.
"""

import hashlib
import json
import logging
import threading
import time
from typing import Callable

import requests as _requests

logger = logging.getLogger(__name__)

MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODELS_URL = "https://api.mistral.ai/v1/models"

_DEFAULT_DELAYS = [5, 15, 30]
_MAX_RETRY_AFTER = 60.0

# Transient network failures worth retrying (connection reset / dropped
# without a response, read timeout). Mistral drops requests under load, so
# without this a single blip fails an entire enrichment batch.
_TRANSIENT = (
    _requests.exceptions.ConnectionError,
    _requests.exceptions.Timeout,
    _requests.exceptions.ChunkedEncodingError,
)

# Per-key cooldown shared across threads: {key_id: monotonic_deadline}.
# Keyed by a hash, not the raw key — we don't retain secrets in a long-lived
# process-global just to throttle them.
_cooldown_lock = threading.Lock()
_cooldowns: dict[str, float] = {}


def _key_id(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]


def _wait_for_cooldown(api_key: str) -> None:
    kid = _key_id(api_key)
    with _cooldown_lock:
        wait = _cooldowns.get(kid, 0.0) - time.monotonic()
    if wait > 0:
        logger.info("Mistral cooldown active — waiting %.1fs", wait)
        time.sleep(wait)


def _set_cooldown(api_key: str, seconds: float) -> None:
    kid = _key_id(api_key)
    with _cooldown_lock:
        _cooldowns[kid] = max(
            _cooldowns.get(kid, 0.0), time.monotonic() + seconds
        )


def post_mistral_json(
    messages: list[dict],
    api_key: str,
    model: str,
    *,
    temperature: float = 0.1,
    timeout: int = 120,
    delays: list[int] | None = None,
    on_usage: Callable[[dict], None] | None = None,
) -> dict:
    """POST a chat request, return the parsed JSON object from the response.

    Retries 429 / 5xx / connection drops with backoff. Raises
    requests.HTTPError / requests.ConnectionError / json.JSONDecodeError on
    unrecoverable failure.

    `on_usage` receives Mistral's `usage` block ({prompt_tokens, completion_tokens,
    total_tokens}) when the reply carries one. A callback rather than a second
    return value: every caller wants the parsed content and only the enrichment
    fleet wants the token count, and changing the return shape would touch each
    call site for the benefit of one. It fires only on a reply we accepted, so a
    retried request is counted once — for the attempt that actually produced text.
    Never let a bookkeeping failure lose a good response: the callback is called
    inside a try/except by the caller's own contract if it can raise.
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

    def _backoff(attempt: int) -> float:
        return float(delays[min(attempt, len(delays) - 1)])

    resp = None
    for attempt in range(len(delays) + 1):
        _wait_for_cooldown(api_key)
        try:
            resp = _requests.post(
                MISTRAL_URL, headers=headers, json=payload, timeout=timeout
            )
        except _TRANSIENT as exc:
            if attempt < len(delays):
                delay = _backoff(attempt)
                logger.warning(
                    "Mistral connection error (%s), retrying in %.1fs (attempt %d)",
                    type(exc).__name__, delay, attempt + 1,
                )
                time.sleep(delay)
                continue
            raise

        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            try:
                delay = min(float(retry_after), _MAX_RETRY_AFTER) if retry_after else _backoff(attempt)
            except ValueError:
                delay = _backoff(attempt)
            _set_cooldown(api_key, delay)
            if attempt < len(delays):
                logger.warning("Mistral 429, retrying in %.1fs (attempt %d)", delay, attempt + 1)
                time.sleep(delay)
                continue
        elif resp.status_code >= 500 and attempt < len(delays):
            delay = _backoff(attempt)
            logger.warning(
                "Mistral %d, retrying in %.1fs (attempt %d)",
                resp.status_code, delay, attempt + 1,
            )
            time.sleep(delay)
            continue

        resp.raise_for_status()
        break

    try:
        envelope = resp.json()
        content = envelope["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ValueError(f"Unexpected Mistral response shape: {exc}") from exc
    if on_usage is not None:
        usage = envelope.get("usage")
        if isinstance(usage, dict):
            on_usage(usage)
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Mistral returned empty content (likely truncated / filtered)")
    parsed = json.loads(content)  # JSONDecodeError bubbles up (e.g. truncated output)
    if not isinstance(parsed, dict):
        raise ValueError(f"Mistral returned non-object JSON: {type(parsed).__name__}")
    return parsed


def verify_key(api_key: str, timeout: int = 10) -> bool | None:
    """Lightweight key check via GET /v1/models.

    Returns True (accepted), False (explicitly rejected — 401/403), or None
    (couldn't tell: network error / other status) so a transient blip at
    save-time doesn't wrongly reject a good key.
    """
    try:
        resp = _requests.get(
            MISTRAL_MODELS_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )
    except _requests.exceptions.RequestException:
        return None
    if resp.status_code in (401, 403):
        return False
    if resp.ok:
        return True
    return None

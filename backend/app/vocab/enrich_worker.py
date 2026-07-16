"""Server-side enrichment workers — one background thread per authed account.

A worker claims disjoint word batches (`enrich.claim`) and calls Mistral through
the shared, hardened `post_mistral_json` using THAT account's decrypted key, then
persists validated cards. The browser only flips it on/off and polls progress.

Threading (not asyncio) on purpose: `post_mistral_json` is sync `requests`, and
sqlite work is sync — a daemon thread per user keeps it simple and isolates one
account's key/rate-limit from another's.
"""
from __future__ import annotations

import logging
import threading
import time

import requests as _requests

from app.vocab import enrich

logger = logging.getLogger(__name__)

# Stop a worker only after a long run of failures — a flaky uplink (e.g. a phone
# hotspot) drops connections in bursts, and each enrich_call already retries ~50s
# internally. A definitive bad key (401/403) still stops immediately, so a high
# cap here just lets the long-running job ride out a transient outage and resume.
MAX_CONSECUTIVE_FAILURES = 20
_IDLE_BACKOFF = 5.0
_MAX_FAIL_BACKOFF = 90.0        # grow the pause between failing batches, capped

_workers: dict[int, "Worker"] = {}
_registry_lock = threading.Lock()

_plan_lock = threading.Lock()
_plan_result: dict | None = None


def ensure_planned() -> dict:
    """Run the deterministic repair planning once per process, before any worker.

    Ten accounts press Start within seconds of each other, so this has to be
    serialised and done once: `plan_repairs` is idempotent, but scanning 64k cards
    ten times over is waste, and ten writers on one SQLite file is contention for
    no reason. A failure here leaves the flag unset (so the next Start retries)
    and must never block enrichment — a missing repair plan only means the backfill
    runs first, which is the old behaviour, not a broken one.
    """
    global _plan_result
    with _plan_lock:
        if _plan_result is None:
            try:
                _plan_result = enrich.plan_repairs()
                logger.info("enrich repair plan: %s", _plan_result)
            except Exception:  # noqa: BLE001
                logger.exception("enrich repair planning failed; continuing")
                return {}
        return dict(_plan_result)


class Worker:
    def __init__(self, user_id: int, api_key: str, model: str,
                 batch: int = enrich.DEFAULT_BATCH):
        self.user_id = user_id
        self._key = api_key
        self.model = model
        self.batch = batch
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self.stats = {
            "running": True, "started_at": time.time(), "stopped_at": None,
            "done": 0, "failed": 0, "skipped": 0, "renamed": 0, "calls": 0,
            "tokens": 0, "last_error": None, "last_lemmas": [], "reason": None,
        }
        self._thread = threading.Thread(
            target=self._run, name=f"enrich-{user_id}", daemon=True)

    # ── lifecycle ──
    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    @property
    def running(self) -> bool:
        return not self._stop.is_set() and self._thread.is_alive()

    def snapshot(self) -> dict:
        with self._lock:
            s = dict(self.stats)
        s["running"] = self.running
        rate = 0.0
        elapsed = (s["stopped_at"] or time.time()) - s["started_at"]
        if elapsed > 0:
            rate = s["done"] / elapsed
        s["rate"] = round(rate, 3)
        return s

    def _set(self, **kw) -> None:
        with self._lock:
            self.stats.update(kw)

    def _wait(self, seconds: float) -> None:
        self._stop.wait(seconds)   # interruptible sleep

    def _record_usage(self, usage: dict) -> None:
        """Bank what the reply cost. Never let bookkeeping cost us the batch:
        the cards are already paid for, and a write failure here would throw them
        away and re-spend the tokens on a retry."""
        try:
            enrich.record_usage(self.user_id, usage)
        except Exception:  # noqa: BLE001
            logger.exception("token accounting failed (user %s)", self.user_id)
        try:
            spent = int(usage.get("total_tokens") or 0)
        except (TypeError, ValueError):
            spent = 0
        with self._lock:
            self.stats["tokens"] += spent

    @staticmethod
    def _fail_backoff(consecutive: int) -> float:
        """Grow the pause between failing batches so a network outage parks the
        worker (instead of spinning) until it clears — capped so recovery is quick."""
        return min(_IDLE_BACKOFF * consecutive, _MAX_FAIL_BACKOFF)

    # ── loop ──
    def _run(self) -> None:
        consecutive = 0
        try:
            while not self._stop.is_set():
                try:
                    batch = enrich.claim(self.user_id, self.batch)
                except Exception as exc:  # DB hiccup — back off, retry
                    logger.exception("enrich claim failed (user %s)", self.user_id)
                    self._set(last_error=f"claim: {exc}")
                    self._wait(_IDLE_BACKOFF)
                    continue

                if not batch:
                    self._set(reason="done — nothing left to enrich")
                    break

                lemmas = [w["lemma"] for w in batch]
                levels = {w["lemma"]: w["level"] for w in batch}
                zipfs = {w["lemma"]: w["zipf"] for w in batch}
                self._set(last_lemmas=lemmas)

                try:
                    parsed = enrich_call(self._key, self.model, batch,
                                         on_usage=self._record_usage)
                    consecutive = 0
                except _requests.HTTPError as exc:
                    code = getattr(exc.response, "status_code", None)
                    enrich.release(lemmas)
                    if code in (401, 403):
                        self._set(last_error="Mistral rejected the key (401/403)",
                                  reason="invalid key")
                        break
                    consecutive += 1
                    self._set(last_error=f"HTTP {code}")
                    if consecutive >= MAX_CONSECUTIVE_FAILURES:
                        self._set(reason="too many failures")
                        break
                    self._wait(self._fail_backoff(consecutive))
                    continue
                except Exception as exc:
                    # transient network drops (flaky uplink) land here; ride them out
                    enrich.release(lemmas)
                    consecutive += 1
                    self._set(last_error=str(exc)[:200])
                    if consecutive >= MAX_CONSECUTIVE_FAILURES:
                        self._set(reason="too many failures")
                        break
                    self._wait(self._fail_backoff(consecutive))
                    continue

                cards, skipped, unmatched, renamed = enrich.parse_response(
                    lemmas, parsed)
                enrich.save_cards(self.user_id, cards, levels, self.model,
                                  renamed=renamed, zipfs=zipfs)
                if skipped:
                    enrich.skip_words(skipped)
                if unmatched:
                    enrich.fail_words(unmatched)
                with self._lock:
                    self.stats["done"] += len(cards)
                    self.stats["skipped"] += len(skipped)
                    self.stats["failed"] += len(unmatched)
                    self.stats["renamed"] += len(renamed)
                    self.stats["calls"] += 1
        finally:
            # free any still-held lease so a stop doesn't strand words
            with self._lock:
                held = list(self.stats.get("last_lemmas") or [])
            if self._stop.is_set() and held:
                enrich.release(held)
            self._set(running=False, stopped_at=time.time())
            self._key = ""  # drop the plaintext key from memory


def enrich_call(api_key: str, model: str, batch: list[dict],
                on_usage=None) -> dict:
    from app.services.mistral_http import post_mistral_json
    return post_mistral_json(
        [{"role": "user", "content": enrich.build_prompt(batch)}],
        api_key, model, temperature=0.1, timeout=300, on_usage=on_usage,
    )


# ── registry ────────────────────────────────────────────────────────────────
def start_worker(user_id: int, api_key: str, model: str,
                 batch: int = enrich.DEFAULT_BATCH) -> dict:
    with _registry_lock:
        existing = _workers.get(user_id)
        if existing and existing.running:
            return {"already_running": True, **existing.snapshot()}
    plan = ensure_planned()
    with _registry_lock:
        w = Worker(user_id, api_key, model, batch)
        _workers[user_id] = w
    w.start()
    return {"already_running": False, "plan": plan, **w.snapshot()}


def stop_worker(user_id: int) -> dict:
    with _registry_lock:
        w = _workers.get(user_id)
    if not w:
        return {"running": False}
    w.stop()
    return w.snapshot()


def worker_status(user_id: int) -> dict | None:
    with _registry_lock:
        w = _workers.get(user_id)
    return w.snapshot() if w else None


def active_workers() -> list[dict]:
    with _registry_lock:
        workers = list(_workers.values())
    return [w.snapshot() for w in workers if w.running]


def stop_all() -> None:
    with _registry_lock:
        workers = list(_workers.values())
    for w in workers:
        w.stop()

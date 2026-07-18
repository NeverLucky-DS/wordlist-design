"""/api/vocab/* — vocab pipeline dashboard API (Phase 1, server-side key).

Mounted into the main app (nginx already proxies /api/ -> backend:8000) so the
dashboard is reachable from the site. Read endpoints use only sqlite
(app.vocab.store); the heavy ingestion (pyglossary/wordfreq) is imported lazily
inside the build worker, so the app boots and read endpoints work even if those
deps aren't installed yet.
"""
from __future__ import annotations

import asyncio
import logging
import threading
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import Principal, require_admin, require_user
from app.db.session import get_db
from app.vocab import store

router = APIRouter(prefix="/api/vocab", tags=["vocab"])

logger = logging.getLogger(__name__)

# The one-shot replica replay kicked off by the first Start (see _schedule_resync).
_resync_task: asyncio.Task | None = None

_LOCK = threading.Lock()
JOB: dict = {"running": False, "kind": None, "started": None,
             "current": None, "events": [], "summary": None, "error": None}


def _emit(event: dict) -> None:
    with _LOCK:
        event["t"] = round(time.time() - (JOB["started"] or time.time()), 1)
        JOB["current"] = event
        JOB["events"].append(event)
        JOB["events"] = JOB["events"][-60:]
        if event.get("stage") == "done":
            JOB["summary"] = event["summary"]


def _worker(min_zipf: float) -> None:
    try:
        from app.vocab.build import run_build  # heavy: pyglossary + wordfreq
        run_build(min_zipf=min_zipf, progress=_emit)
    except Exception as e:  # noqa: BLE001
        with _LOCK:
            JOB["error"] = f"{type(e).__name__}: {e}"
    finally:
        with _LOCK:
            JOB["running"] = False


@router.post("/build")
def start_build(min_zipf: float = 2.3):
    with _LOCK:
        if JOB["running"]:
            raise HTTPException(409, "job already running")
        JOB.update({"running": True, "kind": "ingest", "started": time.time(),
                    "current": None, "events": [], "summary": None, "error": None})
    threading.Thread(target=_worker, args=(min_zipf,), daemon=True).start()
    return {"ok": True, "min_zipf": min_zipf}


@router.get("/status")
def status():
    with _LOCK:
        return JSONResponse(dict(JOB))


@router.get("/stats")
def stats():
    return store.stats()


@router.get("/words")
def words(q: str = "", level: str = "", limit: int = 40):
    return {"items": store.search(q=q.strip(), level=level, limit=limit)}


@router.get("/word/{lemma}")
def word(lemma: str):
    w = store.get(lemma)
    if not w:
        raise HTTPException(404, "not found")
    return w


# ── server-side LLM enrichment (server calls Mistral with the account's key) ──
# Auth-gated: only a logged-in user who has attached a key can drive a worker,
# and every request goes strictly through THAT account's decrypted key.
class EnrichStartIn(BaseModel):
    batch: int | None = None    # words per Mistral call (default: DEFAULT_BATCH)


@router.post("/enrich/start")
async def enrich_start(
    body: EnrichStartIn,
    principal: Principal = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Start this account's enrichment worker using its own stored Mistral key."""
    from app.services import crypto
    from app.config import settings
    from app.db.models import User
    from app.vocab import enrich, enrich_worker

    if not crypto.is_enabled():
        raise HTTPException(503, "key storage disabled (MISTRAL_KEY_SECRET unset)")
    user = await db.get(User, principal.user_id)
    api_key = crypto.decrypt(user.mistral_key_enc) if user and user.mistral_key_enc else None
    if not api_key:
        raise HTTPException(400, "no Mistral key attached to this account")

    batch = enrich.DEFAULT_BATCH if body.batch is None else max(1, min(body.batch, enrich.MAX_BATCH))
    # Blocking on purpose: repair planning is a few seconds of SQLite work, and it
    # must be finished before the worker claims its first batch — otherwise the
    # first batches come from the backfill and the phase order means nothing.
    state = await asyncio.to_thread(
        enrich_worker.start_worker, principal.user_id, api_key,
        settings.mistral_model, batch)
    plan = state.get("plan") or {}
    # Both of these rewrite existing cards in place, which leaves `created_at`
    # untouched and therefore invisible to the mirror's forward cursor.
    if plan.get("zipf_filled") or plan.get("forms_tagged") or plan.get("forms_cleared"):
        _schedule_resync()
    return {"ok": True, **state}


def _schedule_resync() -> None:
    """Replay the replica after `plan_repairs` rewrote cards in place.

    Detached from the request: it is ~64k upserts and the button should not wait
    for it. Guarded by a module flag so ten accounts starting at once queue one
    resync, not ten concurrent full replays over the same rows.
    """
    global _resync_task
    if _resync_task and not _resync_task.done():
        return

    async def _run() -> None:
        from app.vocab import mirror
        try:
            result = await mirror.full_resync()
            logger.info("vocab mirror resync after repair planning: %s", result)
        except Exception:  # noqa: BLE001 — a stale mirror must not kill enrichment
            logger.exception("vocab mirror resync failed")

    _resync_task = asyncio.create_task(_run())


@router.post("/enrich/stop")
async def enrich_stop(principal: Principal = Depends(require_user)):
    from app.vocab import enrich_worker

    return {"ok": True, **enrich_worker.stop_worker(principal.user_id)}


@router.get("/enrich/progress")
def enrich_progress():
    """Global enrichment progress (DB) + active worker summaries."""
    from app.vocab import enrich, enrich_worker

    out = enrich.progress()
    out["workers"] = enrich_worker.active_workers()
    return out


@router.get("/enrich/cards")
def enrich_cards(q: str = "", confidence: str = "", topic: str = "",
                 level: str = "", limit: int = 40, offset: int = 0):
    """Browse the enriched cards (the OUTPUT the app shows). Public read —
    inspecting the vocabulary base needs no auth, same as /words."""
    from app.vocab import enrich

    return enrich.list_cards(q=q.strip(), confidence=confidence, topic=topic,
                             level=level, limit=limit, offset=offset)


@router.get("/enrich/card/{lemma}")
def enrich_card(lemma: str):
    from app.vocab import enrich

    card = enrich.get_card(lemma)
    if not card:
        raise HTTPException(404, "not found")
    return card


class RequeueIn(BaseModel):
    scope: str | None = None       # "low_confidence" — requeue all low-conf cards
    lemmas: list[str] | None = None  # or an explicit list


@router.post("/enrich/requeue")
async def enrich_requeue(
    body: RequeueIn,
    principal: Principal = Depends(require_user),
):
    """Reset words back to 'raw' so the next run re-enriches them with the current
    prompt. Auth-gated: it mutates the shared enrichment state."""
    from app.vocab import enrich

    if body.lemmas:
        n = enrich.requeue([s.strip() for s in body.lemmas if s.strip()])
    elif body.scope == "low_confidence":
        n = enrich.requeue_low_confidence()
    else:
        raise HTTPException(422, "pass scope='low_confidence' or a lemmas list")
    return {"ok": True, "requeued": n}


# ── fleet: drive every account's worker from one place ───────────────────────
# Ten accounts, ten keys, one operator. Without this the only way to run them all
# is ten browser tabs, each logged into a different account. Admin-gated because
# it starts work on OTHER accounts' keys — it spends their money.
class FleetStartIn(BaseModel):
    batch: int | None = None


def _account_row(user, worker: dict | None, usage: dict) -> dict:
    """One line of the fleet table: who, whether it can work, what it is doing,
    what it has spent. `worker` is None for an account that never started."""
    w = worker or {}
    return {
        "user_id": user.id,
        "email": user.email,
        "has_key": bool(user.mistral_key_enc),
        "running": bool(w.get("running")),
        "done": w.get("done", 0),
        "skipped": w.get("skipped", 0),
        "failed": w.get("failed", 0),
        "calls": w.get("calls", 0),
        "rate": w.get("rate", 0.0),
        "last_error": w.get("last_error"),
        "reason": w.get("reason"),
        # Session counters die with the process; these are the durable ledger.
        "tokens_today": usage.get("today_tokens", 0),
        "tokens_total": usage.get("total_tokens", 0),
        "calls_total": usage.get("calls", 0),
    }


@router.get("/enrich/fleet")
async def enrich_fleet(
    principal: Principal = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Every account, its worker and its token spend, plus global progress."""
    from sqlalchemy import select

    from app.db.models import User
    from app.vocab import enrich, enrich_worker

    users = (await db.execute(select(User).order_by(User.id))).scalars().all()
    usage = await asyncio.to_thread(enrich.usage_by_user)
    accounts = [
        _account_row(u, enrich_worker.worker_status(u.id), usage.get(u.id, {}))
        for u in users
    ]
    progress = await asyncio.to_thread(enrich.progress)
    return {
        "accounts": accounts,
        "running": sum(1 for a in accounts if a["running"]),
        "with_key": sum(1 for a in accounts if a["has_key"]),
        "tokens_today": sum(a["tokens_today"] for a in accounts),
        "tokens_total": sum(a["tokens_total"] for a in accounts),
        "progress": progress,
    }


@router.post("/enrich/fleet/start")
async def enrich_fleet_start(
    body: FleetStartIn,
    principal: Principal = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Start a worker for every account that has a key attached.

    One account's bad key must not stop the other nine: each is decrypted and
    started independently and its failure is reported as a row, not raised.
    """
    from sqlalchemy import select

    from app.config import settings
    from app.db.models import User
    from app.services import crypto
    from app.vocab import enrich, enrich_worker

    if not crypto.is_enabled():
        raise HTTPException(503, "key storage disabled (MISTRAL_KEY_SECRET unset)")
    users = (await db.execute(
        select(User).where(User.mistral_key_enc.isnot(None)).order_by(User.id)
    )).scalars().all()
    if not users:
        raise HTTPException(400, "no account has a Mistral key attached")

    batch = (enrich.DEFAULT_BATCH if body.batch is None
             else max(1, min(body.batch, enrich.MAX_BATCH)))
    started, already, failed, plan = [], [], [], {}
    for user in users:
        try:
            key = crypto.decrypt(user.mistral_key_enc)
        except Exception as exc:  # noqa: BLE001 — e.g. re-keyed server secret
            failed.append({"email": user.email, "error": f"ключ не читается: {exc}"})
            continue
        if not key:
            failed.append({"email": user.email, "error": "ключ не читается"})
            continue
        try:
            state = await asyncio.to_thread(
                enrich_worker.start_worker, user.id, key,
                settings.mistral_model, batch)
        except Exception as exc:  # noqa: BLE001
            logger.exception("fleet: could not start worker for %s", user.email)
            failed.append({"email": user.email, "error": str(exc)[:200]})
            continue
        plan = plan or (state.get("plan") or {})
        (already if state.get("already_running") else started).append(user.email)

    if plan.get("zipf_filled"):
        _schedule_resync()
    return {"ok": True, "started": started, "already_running": already,
            "failed": failed, "plan": plan}


@router.post("/enrich/fleet/stop")
async def enrich_fleet_stop(principal: Principal = Depends(require_admin)):
    """Stop every running worker, whoever started it."""
    from app.vocab import enrich_worker

    running = [w for w in enrich_worker.active_workers()]
    enrich_worker.stop_all()
    return {"ok": True, "stopped": len(running)}


@router.get("/enrich/status")
async def enrich_status(principal: Principal = Depends(require_user)):
    """This account's worker state (running?, done, last_error)."""
    from app.vocab import enrich_worker

    return enrich_worker.worker_status(principal.user_id) or {"running": False}

"""/api/vocab/* — vocab pipeline dashboard API (Phase 1, server-side key).

Mounted into the main app (nginx already proxies /api/ -> backend:8000) so the
dashboard is reachable from the site. Read endpoints use only sqlite
(app.vocab.store); the heavy ingestion (pyglossary/wordfreq) is imported lazily
inside the build worker, so the app boots and read endpoints work even if those
deps aren't installed yet.
"""
from __future__ import annotations

import threading
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.vocab import store

router = APIRouter(prefix="/api/vocab", tags=["vocab"])

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

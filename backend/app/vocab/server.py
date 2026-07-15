"""Dev verify server: serves the real frontend statically + the API routers
needed to exercise the site end-to-end (vocab + auth) without Docker.

Lets us open the real site page (pipeline.html) end-to-end — shared header,
css/pipeline.css, js/pipeline.js, js/enrich.js — and drive the auth-gated,
server-side enrichment control panel. In production the same routers are served
by the main app (app.main) behind nginx's /api/ proxy.

Uses a throwaway local SQLite DB (tables via create_all) and a dev encryption
secret so per-user Mistral keys can be attached. Run:
  ./.venv/bin/uvicorn --app-dir backend app.vocab.server:app --port 8770
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # backend/ on path

# Configure BEFORE importing app.config (pydantic settings read env at import).
_DEV_DB = Path(__file__).resolve().parents[2] / "data" / "vocab_dev.db"
_DEV_DB.parent.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_DEV_DB}")
os.environ.setdefault("MISTRAL_KEY_SECRET", "dev-secret-not-for-prod")

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth as auth_routes
from app.db.models import Base
from app.db.session import engine
from app.vocab.api import router as vocab_router

app = FastAPI(title="Wortschatz-Werk (dev)")
app.include_router(auth_routes.router)
app.include_router(vocab_router)


@app.on_event("startup")
async def _init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# serve the repo frontend (pipeline.html, css/, js/, images/) from the worktree root
FRONTEND = Path(__file__).resolve().parents[3]
app.mount("/", StaticFiles(directory=str(FRONTEND), html=True), name="static")

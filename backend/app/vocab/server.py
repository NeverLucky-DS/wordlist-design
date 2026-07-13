"""Dev verify server: serves the real frontend statically + mounts /api/vocab/*.

Lets us open the real site page (pipeline.html) end-to-end — with the shared
site header, css/pipeline.css and js/pipeline.js — without standing up the full
Docker stack. In production the same /api/vocab/* is served by the main app
(app.vocab.api.router in main.py) behind nginx's existing /api/ proxy.

Run:  ./.venv/bin/uvicorn --app-dir backend app.vocab.server:app --port 8770
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # backend/ on path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.vocab.api import router as vocab_router

app = FastAPI(title="Wortschatz-Werk (dev)")
app.include_router(vocab_router)

# serve the repo frontend (pipeline.html, css/, js/, images/) from the worktree root
FRONTEND = Path(__file__).resolve().parents[3]
app.mount("/", StaticFiles(directory=str(FRONTEND), html=True), name="static")

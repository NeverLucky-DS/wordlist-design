import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, essays, health, phrases, topics, words
from app.auth import cleanup_expired_sessions
from app.vocab.api import router as vocab_router
from app.vocab.dict_api import router as woerterbuch_router
from app.config import settings
from app.db.init_data import ensure_seed_data
from app.db.session import SessionLocal


def _configure_app_logging() -> None:
    """Make our own `app.*` INFO logs visible.

    Uvicorn only configures its own loggers, and Python's last-resort handler
    only emits WARNING+, so `logger.info(...)` from app modules (e.g. the essay
    analyzer / pipeline) was silently dropped. Attach one handler to the `app`
    namespace so those diagnostics actually reach stderr / the container logs.
    """
    app_logger = logging.getLogger("app")
    if not app_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s | %(message)s")
        )
        app_logger.addHandler(handler)
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False


_configure_app_logging()

app = FastAPI(title="Deutsch Essay Trainer")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
# Also accept any private-LAN origin (http://<host>:<port>) so the dashboard works
# when opened from another device on the local network — phones/tablets hit the
# nginx host by its 10./172.16-31./192.168. address, not localhost. Same-origin
# requests through nginx don't need this, but it future-proofs cross-origin calls.
LAN_ORIGIN_RE = (
    r"http://(localhost|127\.0\.0\.1|"
    r"(10|192\.168|172\.(1[6-9]|2\d|3[01]))(\.\d{1,3}){2})"
    r"(:\d+)?"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=LAN_ORIGIN_RE,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(essays.router)
app.include_router(words.router)
app.include_router(phrases.router)
app.include_router(topics.router)
app.include_router(vocab_router)  # /api/vocab/* — dictionary-ingestion dashboard
app.include_router(woerterbuch_router)  # /api/vocab/* — Wörterbuch lookup + word list

# Background replica sync (see app.vocab.mirror). Held in a module global so the
# task isn't garbage-collected mid-flight, and cancelled on shutdown.
_mirror_task: asyncio.Task | None = None


@app.on_event("startup")
async def on_startup() -> None:
    # The database schema is owned by Alembic migrations (backend/alembic/).
    # They are applied by the container entrypoint (`alembic upgrade head`)
    # before this app boots — startup only seeds and tidies data.
    async with SessionLocal() as session:
        await cleanup_expired_sessions(session)
        await ensure_seed_data(session)
        # Idempotent cleanup: dirty lemmas / duplicates left by pipeline v1
        from app.services.topic_pack_service import (
            dedupe_words_by_german,
            fix_word_lemmas,
            normalize_topic_case,
        )

        fixed = await fix_word_lemmas(session)
        deduped = await dedupe_words_by_german(session)
        topics_fixed = await normalize_topic_case(session)
        if fixed or deduped or topics_fixed:
            import logging

            logging.getLogger(__name__).info(
                "Startup cleanup: %d lemmas fixed, %d duplicates merged, %d topic links normalized",
                fixed, deduped, topics_fixed,
            )

    from app.services.analysis_jobs import mark_interrupted_analyses

    await mark_interrupted_analyses()

    # Migrate enrichment.db here, for the same reason alembic runs before the app
    # serves: it is the mirror's source, and the mirror starts reading on boot. A
    # worker would eventually call this itself, but only once someone presses
    # Start — until then every sync pass would fail on a column that is missing.
    global _mirror_task
    from app.vocab import enrich, mirror

    await asyncio.to_thread(enrich.ensure_schema)

    # Pull enriched cards into the searchable Postgres replica, now and then on a
    # timer — the enrichment worker keeps adding to SQLite while we serve.
    _mirror_task = asyncio.create_task(mirror.periodic_sync())


@app.on_event("shutdown")
async def stop_background() -> None:
    from app.services.analysis_jobs import stop_analysis_jobs
    from app.vocab import enrich_worker

    if _mirror_task is not None:
        _mirror_task.cancel()
    await stop_analysis_jobs()
    enrich_worker.stop_all()

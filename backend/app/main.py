import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, essays, health, phrases, topics, words
from app.api.routes import pipeline
from app.auth import cleanup_expired_sessions
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
app.include_router(pipeline.router)


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

    # Autonomous mode: background scheduler over the topic queue
    if settings.pipeline_autorun:
        from app.pipeline.scheduler import start_scheduler

        start_scheduler(SessionLocal)


@app.on_event("shutdown")
async def stop_background() -> None:
    from app.pipeline.scheduler import stop_scheduler
    from app.services.analysis_jobs import stop_analysis_jobs

    stop_scheduler()
    await stop_analysis_jobs()

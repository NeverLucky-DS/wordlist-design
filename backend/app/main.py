from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import essays, health, phrases, topics, words
from app.api.routes import pipeline
from app.config import settings
from app.db.init_data import ensure_seed_data
from app.db.models import Base
from app.db.session import engine
from app.db.session import SessionLocal

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
app.include_router(essays.router)
app.include_router(words.router)
app.include_router(phrases.router)
app.include_router(topics.router)
app.include_router(pipeline.router)


async def _ensure_new_columns(conn) -> None:
    """Lightweight migration: add columns introduced by pipeline v2.

    Works on both SQLite (local dev) and PostgreSQL (docker-compose).
    """
    from sqlalchemy import text

    wanted = {
        "pipeline_runs": {
            "phrases_added": "INTEGER DEFAULT 0",
            "target_words": "INTEGER DEFAULT 0",
        },
    }
    dialect = conn.dialect.name  # 'sqlite' | 'postgresql'
    for table, columns in wanted.items():
        if dialect == "postgresql":
            for col, ddl in columns.items():
                await conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {ddl}"
                ))
        else:
            try:
                rows = (await conn.execute(text(f"PRAGMA table_info({table})"))).fetchall()
            except Exception:
                continue
            existing = {row[1] for row in rows}
            for col, ddl in columns.items():
                if col not in existing:
                    await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))


@app.on_event("startup")
async def init_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _ensure_new_columns(conn)
    async with SessionLocal() as session:
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

    # Autonomous mode: background scheduler over the topic queue
    if settings.pipeline_autorun:
        from app.pipeline.scheduler import start_scheduler

        start_scheduler(SessionLocal)


@app.on_event("shutdown")
async def stop_background() -> None:
    from app.pipeline.scheduler import stop_scheduler

    stop_scheduler()

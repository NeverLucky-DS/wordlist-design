"""Analysis background jobs — startup recovery, timestamps, lifecycle."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.auth import Principal
from app.db.models import EssayAnalysis, User
from app.services import analysis_jobs
from app.services.essays_repo import create_analysis_run, create_essay, create_version
from tests.helpers import essay_payload


def test_now_returns_naive_utc():
    value = analysis_jobs._now()
    assert value.tzinfo is None
    assert isinstance(value, datetime)


async def test_mark_interrupted_analyses_updates_stale_runs(db_session, monkeypatch):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_factory = async_sessionmaker(db_session.bind, expire_on_commit=False)
    monkeypatch.setattr(analysis_jobs, "SessionLocal", session_factory)

    user = User(email="jobs@test.com", password_hash="x")
    db_session.add(user)
    await db_session.flush()
    principal = Principal(user_id=user.id)

    essay = await create_essay(db_session, essay_payload(), principal)
    version = await create_version(db_session, essay, reason="analysis")
    queued = await create_analysis_run(db_session, essay=essay, version=version, part=None)
    running = await create_analysis_run(db_session, essay=essay, version=version, part="einleitung")
    running.status = "running"
    await db_session.commit()

    await analysis_jobs.mark_interrupted_analyses()

    db_session.expire_all()
    rows = (await db_session.execute(select(EssayAnalysis))).scalars().all()
    for row in rows:
        if row.id in {queued.id, running.id}:
            assert row.status == "interrupted"
            assert row.finished_at is not None
            assert row.finished_at.tzinfo is None
            assert "restarted" in (row.error_message or "")


async def test_mark_interrupted_leaves_completed_alone(db_session, monkeypatch):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_factory = async_sessionmaker(db_session.bind, expire_on_commit=False)
    monkeypatch.setattr(analysis_jobs, "SessionLocal", session_factory)

    user = User(email="done@test.com", password_hash="x")
    db_session.add(user)
    await db_session.flush()
    principal = Principal(user_id=user.id)
    essay = await create_essay(db_session, essay_payload(), principal)
    version = await create_version(db_session, essay, reason="analysis")
    done = await create_analysis_run(db_session, essay=essay, version=version, part=None)
    done.status = "completed"
    done.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db_session.commit()

    await analysis_jobs.mark_interrupted_analyses()
    await db_session.refresh(done)
    assert done.status == "completed"

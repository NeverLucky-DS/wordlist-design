"""Tests for autonomy v3: crash recovery, auto-topics, maintenance, overview."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import settings
from app.db.models import PipelineRun, TopicQueueItem, Word, WordTopic
from app.pipeline import scheduler


async def test_recover_stale_resets_queue_and_runs(db_session):
    db_session.add(TopicQueueItem(topic="Hängethema", status="running"))
    stale_run = PipelineRun(topic="Hängethema", status="running")
    db_session.add(stale_run)
    await db_session.commit()
    # backdate started_at beyond the watchdog window
    stale_run.started_at = datetime.utcnow() - timedelta(minutes=settings.pipeline_stale_run_minutes + 5)
    await db_session.commit()

    session_factory = async_sessionmaker(db_session.bind, expire_on_commit=False)
    await scheduler.recover_stale(session_factory)

    async with session_factory() as db:
        item = (await db.execute(select(TopicQueueItem))).scalars().first()
        run = (await db.execute(select(PipelineRun))).scalars().first()
    assert item.status == "pending"
    assert run.status == "failed"
    assert any(e["item"] == "watchdog" for e in run.errors_json)


async def test_ensure_topics_fills_empty_queue_from_catalog(db_session):
    # 'klimawandel' already covered by words → must not be re-queued
    w = Word(german="Testwort", word_type="noun", translation_ru="x", level="B2", examples=[])
    db_session.add(w)
    await db_session.flush()
    db_session.add(WordTopic(word_id=w.id, topic="klimawandel"))
    await db_session.commit()

    session_factory = async_sessionmaker(db_session.bind, expire_on_commit=False)

    with (
        patch.object(settings, "pipeline_auto_topics", True),
        patch.object(settings, "pipeline_auto_topics_batch", 3),
        patch.object(settings, "mistral_api_key", ""),  # catalog only, no LLM
    ):
        added = await scheduler.ensure_topics(session_factory)

    assert added == 3
    async with session_factory() as db:
        topics = [i.topic for i in (await db.execute(select(TopicQueueItem))).scalars().all()]
    assert len(topics) == 3
    assert all(t.lower() != "klimawandel" for t in topics)

    # Queue is non-empty now → second call adds nothing
    with patch.object(settings, "pipeline_auto_topics", True):
        added2 = await scheduler.ensure_topics(session_factory)
    assert added2 == 0


async def test_maintenance_requeues_underfilled_done_topics(db_session):
    db_session.add(TopicQueueItem(topic="Migration", status="done", target_words=5, attempts=1))
    # only 1 word linked — under target 5
    w = Word(german="Zuwanderung", word_type="noun", translation_ru="x", level="B2", examples=[])
    db_session.add(w)
    await db_session.flush()
    db_session.add(WordTopic(word_id=w.id, topic="migration"))
    await db_session.commit()

    session_factory = async_sessionmaker(db_session.bind, expire_on_commit=False)
    requeued = await scheduler.maintenance_requeue(session_factory)

    assert requeued == 1
    async with session_factory() as db:
        item = (await db.execute(select(TopicQueueItem))).scalars().first()
    assert item.status == "pending"


async def test_maintenance_leaves_filled_topics_done(db_session):
    db_session.add(TopicQueueItem(topic="Energie", status="done", target_words=1, attempts=1))
    w = Word(german="Solarstrom", word_type="noun", translation_ru="x", level="B2", examples=[])
    db_session.add(w)
    await db_session.flush()
    db_session.add(WordTopic(word_id=w.id, topic="energie"))
    await db_session.commit()

    session_factory = async_sessionmaker(db_session.bind, expire_on_commit=False)
    requeued = await scheduler.maintenance_requeue(session_factory)

    assert requeued == 0


async def test_overview_endpoint(client, db_session):
    w = Word(german="Treibhausgas", word_type="noun", translation_ru="x", level="B2", examples=[])
    db_session.add(w)
    await db_session.flush()
    db_session.add(WordTopic(word_id=w.id, topic="klimawandel"))
    db_session.add(TopicQueueItem(topic="klimawandel", status="done", attempts=1))
    await db_session.commit()

    res = await client.get("/api/pipeline/overview")
    assert res.status_code == 200
    data = res.json()
    assert "topics" in data and "queue" in data and "settings" in data
    topic_row = next(t for t in data["topics"] if t["topic"] == "klimawandel")
    assert topic_row["words"] == 1
    assert topic_row["queue_status"] == "done"
    assert data["queue"] == {"done": 1}
    assert data["settings"]["target_words"] == settings.pipeline_target_words


async def test_failures_endpoint(client, db_session):
    from app.db.models import WordFailure

    db_session.add(WordFailure(word="Kaputtwort", topic="klimawandel", stage="mistral", error="boom"))
    await db_session.commit()

    res = await client.get("/api/pipeline/failures?topic=klimawandel")
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) == 1
    assert rows[0]["word"] == "Kaputtwort"


async def test_pick_new_topics_catalog_excludes_existing():
    from app.pipeline.topics_catalog import CURATED_TOPICS, pick_new_topics

    existing = {t.lower() for t in CURATED_TOPICS[:5]}
    topics = await pick_new_topics(existing, 3, "", "model")
    assert len(topics) == 3
    assert all(t.lower() not in existing for t in topics)

from __future__ import annotations

"""Autonomous mode — background scheduler over the topic queue.

Runs inside the FastAPI process. Each cycle it:
1. recover_stale  — heals state after crashes/restarts: queue items stuck in
   "running" go back to "pending", pipeline runs stuck in "running" longer
   than `pipeline_stale_run_minutes` are marked "failed".
2. ensure_topics  — if the pending queue is empty, auto-enqueues new topics
   (curated exam catalog first, then LLM-generated) so the word base keeps
   growing without any manual input.
3. maintenance_requeue — topics finished below target get re-queued (until
   `pipeline_max_attempts`), so under-filled topics catch up over time.
4. process_next_topic — runs the pipeline for the oldest pending topic.

No external cron needed: while the backend is up, the queue drains itself.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings
from app.db.models import PipelineRun, TopicQueueItem, WordTopic

from .runner import run_pipeline
from .topics_catalog import pick_new_topics

logger = logging.getLogger(__name__)

_task: asyncio.Task | None = None


# ---------------------------------------------------------------------------
# 1. Crash recovery
# ---------------------------------------------------------------------------

async def recover_stale(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Heal queue/runs left in 'running' by a crash or restart."""
    async with session_factory() as db:
        # Queue items: running → pending (the run itself died with the process)
        result = await db.execute(
            select(TopicQueueItem).where(TopicQueueItem.status == "running")
        )
        for item in result.scalars().all():
            logger.warning("Recovering stale queue item '%s' → pending", item.topic)
            item.status = "pending"

        # Runs: running for too long → failed
        cutoff = datetime.utcnow() - timedelta(minutes=settings.pipeline_stale_run_minutes)
        result = await db.execute(
            select(PipelineRun).where(
                PipelineRun.status == "running",
                PipelineRun.started_at < cutoff,
            )
        )
        for run in result.scalars().all():
            logger.warning("Marking stale run %d ('%s') as failed", run.id, run.topic)
            run.status = "failed"
            run.finished_at = datetime.utcnow()
            run.errors_json = (run.errors_json or []) + [{
                "stage": "fetch", "item": "watchdog",
                "error": f"Run stale for >{settings.pipeline_stale_run_minutes} min — marked failed",
                "timestamp": datetime.utcnow().isoformat(),
            }]
        await db.commit()


# ---------------------------------------------------------------------------
# 2. Auto-topics
# ---------------------------------------------------------------------------

async def ensure_topics(session_factory: async_sessionmaker[AsyncSession]) -> int:
    """Auto-enqueue new topics when the pending queue is empty."""
    if not settings.pipeline_auto_topics:
        return 0

    async with session_factory() as db:
        pending = (await db.execute(
            select(sa_func.count(TopicQueueItem.id)).where(TopicQueueItem.status == "pending")
        )).scalar() or 0
        if pending > 0:
            return 0

        queued = {t for (t,) in (await db.execute(select(TopicQueueItem.topic))).all()}
        covered = {t for (t,) in (await db.execute(select(WordTopic.topic).distinct())).all()}

    new_topics = await pick_new_topics(
        queued | covered,
        settings.pipeline_auto_topics_batch,
        settings.mistral_api_key,
        settings.mistral_model,
    )
    if not new_topics:
        return 0

    async with session_factory() as db:
        for topic in new_topics:
            db.add(TopicQueueItem(topic=topic))
        await db.commit()
    logger.info("Auto-enqueued %d topics: %s", len(new_topics), new_topics)
    return len(new_topics)


# ---------------------------------------------------------------------------
# 3. Maintenance — re-queue under-filled topics
# ---------------------------------------------------------------------------

async def maintenance_requeue(session_factory: async_sessionmaker[AsyncSession]) -> int:
    """Re-queue 'done' topics that are still below their word target."""
    requeued = 0
    async with session_factory() as db:
        result = await db.execute(
            select(TopicQueueItem).where(
                TopicQueueItem.status == "done",
                TopicQueueItem.attempts < settings.pipeline_max_attempts,
            )
        )
        for item in result.scalars().all():
            target = item.target_words or settings.pipeline_target_words
            have = (await db.execute(
                select(sa_func.count(WordTopic.id)).where(
                    WordTopic.topic == item.topic.strip().lower()
                )
            )).scalar() or 0
            if have < target:
                item.status = "pending"
                requeued += 1
                logger.info(
                    "Maintenance: requeue '%s' (%d/%d words, attempt %d)",
                    item.topic, have, target, item.attempts,
                )
        await db.commit()
    return requeued


# ---------------------------------------------------------------------------
# 4. Process one topic
# ---------------------------------------------------------------------------

async def process_next_topic(session_factory: async_sessionmaker[AsyncSession]) -> bool:
    """Pick and process one pending topic. Returns True if something ran."""
    async with session_factory() as db:
        result = await db.execute(
            select(TopicQueueItem)
            .where(TopicQueueItem.status == "pending")
            .order_by(TopicQueueItem.created_at.asc())
            .limit(1)
        )
        item = result.scalars().first()
        if item is None:
            return False

        item.status = "running"
        item.attempts += 1
        run = PipelineRun(topic=item.topic, status="running")
        db.add(run)
        await db.commit()
        await db.refresh(run)
        item_id, topic, target, attempts = item.id, item.topic, item.target_words, item.attempts
        run_id = run.id

    logger.info("Scheduler: processing topic '%s' (attempt %d, run %d)", topic, attempts, run_id)
    try:
        await run_pipeline(run_id, topic, [], session_factory, target_words=target)
    except Exception:
        logger.exception("Scheduler: run %d crashed", run_id)

    # Evaluate outcome and update queue item
    async with session_factory() as db:
        item = await db.get(TopicQueueItem, item_id)
        run = await db.get(PipelineRun, run_id)
        if item is None:
            return True
        item.last_run_id = run_id

        target_n = item.target_words or settings.pipeline_target_words
        count_result = await db.execute(
            select(sa_func.count(WordTopic.id)).where(WordTopic.topic == topic.strip().lower())
        )
        have = int(count_result.scalar() or 0)

        if have >= target_n:
            item.status = "done"
        elif run is not None and run.status == "failed" and item.attempts >= settings.pipeline_max_attempts:
            item.status = "failed"
        elif item.attempts >= settings.pipeline_max_attempts:
            item.status = "done"  # best effort reached
        else:
            item.status = "pending"  # re-queue: catch up next cycle
        logger.info(
            "Scheduler: topic '%s' → %s (%d/%d words, attempt %d)",
            topic, item.status, have, target_n, item.attempts,
        )
        await db.commit()
    return True


# ---------------------------------------------------------------------------
# Loop
# ---------------------------------------------------------------------------

async def scheduler_loop(session_factory: async_sessionmaker[AsyncSession]) -> None:
    await asyncio.sleep(10)  # let the app finish startup
    logger.info(
        "Pipeline scheduler started (interval: %d min, auto-topics: %s)",
        settings.pipeline_interval_minutes, settings.pipeline_auto_topics,
    )
    while True:
        try:
            if settings.pipeline_autorun and settings.mistral_api_key:
                await recover_stale(session_factory)
                await maintenance_requeue(session_factory)
                await ensure_topics(session_factory)
                ran = await process_next_topic(session_factory)
                if ran:
                    # keep draining the queue, but pause between topics
                    # (rate-limit friendly for the free Mistral tier)
                    await asyncio.sleep(300)
                    continue
        except Exception:
            logger.exception("Scheduler loop error")
        await asyncio.sleep(settings.pipeline_interval_minutes * 60)


def start_scheduler(session_factory: async_sessionmaker[AsyncSession]) -> None:
    global _task
    if _task is None or _task.done():
        _task = asyncio.create_task(scheduler_loop(session_factory))


def stop_scheduler() -> None:
    global _task
    if _task is not None:
        _task.cancel()
        _task = None

from __future__ import annotations

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_admin
from app.db.models import PipelineRun
from app.db.session import SessionLocal, get_db
from app.pipeline.runner import run_pipeline

router = APIRouter(
    prefix="/api/pipeline",
    tags=["pipeline"],
    dependencies=[Depends(require_admin)],
)


class PipelineRequest(BaseModel):
    topic: str
    article_urls: list[str] = []
    target_words: int | None = None


class PipelineRunOut(BaseModel):
    run_id: int
    status: str
    topic: str
    words_added: int
    words_linked: int
    phrases_added: int = 0
    target_words: int = 0
    errors: list[dict]
    started_at: str
    finished_at: str | None


class QueueRequest(BaseModel):
    topics: list[str]
    target_words: int | None = None


@router.post("/run", summary="Start word enrichment pipeline for a topic")
async def start_pipeline(
    body: PipelineRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """POST /api/pipeline/run

    Body:
        topic        — German topic name, e.g. "Klimawandel"
        article_urls — optional list of URLs to use instead of Grok discovery
    """
    topic = body.topic.strip()
    if not topic:
        raise HTTPException(status_code=422, detail="topic must not be empty")

    run = PipelineRun(topic=topic, status="running")
    db.add(run)
    await db.commit()
    await db.refresh(run)

    background_tasks.add_task(
        run_pipeline,
        run.id,
        topic,
        body.article_urls,
        SessionLocal,
        body.target_words,
    )

    return {"status": "started", "run_id": run.id, "topic": topic}


@router.post("/queue", summary="Queue topics for autonomous processing")
async def queue_topics(body: QueueRequest, db: AsyncSession = Depends(get_db)):
    """Add topics to the autonomous queue — the background scheduler picks
    them up one by one and tops each up to target_words."""
    from sqlalchemy import select
    from app.db.models import TopicQueueItem

    added, skipped = [], []
    for raw in body.topics:
        topic = raw.strip()
        if not topic:
            continue
        existing = (
            await db.execute(select(TopicQueueItem).where(TopicQueueItem.topic.ilike(topic)))
        ).scalars().first()
        if existing:
            if existing.status in ("done", "failed"):
                existing.status = "pending"
                existing.attempts = 0
                if body.target_words:
                    existing.target_words = body.target_words
                added.append(topic)
            else:
                skipped.append(topic)
            continue
        db.add(TopicQueueItem(topic=topic, target_words=body.target_words))
        added.append(topic)
    await db.commit()
    return {"queued": added, "skipped": skipped}


@router.get("/queue", summary="List topic queue")
async def list_queue(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.db.models import TopicQueueItem

    result = await db.execute(
        select(TopicQueueItem).order_by(TopicQueueItem.created_at.asc())
    )
    return [
        {
            "id": i.id,
            "topic": i.topic,
            "status": i.status,
            "target_words": i.target_words,
            "attempts": i.attempts,
            "last_run_id": i.last_run_id,
        }
        for i in result.scalars().all()
    ]


@router.get("/overview", summary="One-call dashboard: topics, queue, failures")
async def pipeline_overview(db: AsyncSession = Depends(get_db)):
    """Everything the UI needs in a single request."""
    from sqlalchemy import func as sa_func, select
    from app.config import settings
    from app.db.models import Phrase, PipelineRun, TopicQueueItem, WordFailure, WordTopic

    word_counts = {
        topic: count
        for topic, count in (await db.execute(
            select(WordTopic.topic, sa_func.count(WordTopic.id)).group_by(WordTopic.topic)
        )).all()
    }
    phrase_counts = {
        topic: count
        for topic, count in (await db.execute(
            select(Phrase.topic, sa_func.count(Phrase.id)).group_by(Phrase.topic)
        )).all()
    }
    failure_counts = {
        topic: count
        for topic, count in (await db.execute(
            select(WordFailure.topic, sa_func.count(WordFailure.id))
            .where(WordFailure.resolved == False)  # noqa: E712
            .group_by(WordFailure.topic)
        )).all()
    }
    queue_items = {
        i.topic.strip().lower(): i
        for i in (await db.execute(select(TopicQueueItem))).scalars().all()
    }
    last_runs: dict[str, PipelineRun] = {}
    for run in (await db.execute(
        select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(100)
    )).scalars().all():
        key = run.topic.strip().lower()
        if key not in last_runs:
            last_runs[key] = run

    all_topics = sorted(
        set(word_counts) | set(phrase_counts) | set(queue_items),
        key=lambda t: -word_counts.get(t, 0),
    )
    topics_out = []
    for topic in all_topics:
        q = queue_items.get(topic)
        r = last_runs.get(topic)
        topics_out.append({
            "topic": topic,
            "words": word_counts.get(topic, 0),
            "target_words": (q.target_words if q and q.target_words else settings.pipeline_target_words),
            "phrases": phrase_counts.get(topic, 0),
            "failures_open": failure_counts.get(topic, 0),
            "queue_status": q.status if q else None,
            "attempts": q.attempts if q else None,
            "last_run": {
                "run_id": r.id,
                "status": r.status,
                "words_added": r.words_added,
                "phrases_added": r.phrases_added or 0,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            } if r else None,
        })

    queue_summary: dict[str, int] = {}
    for i in queue_items.values():
        queue_summary[i.status] = queue_summary.get(i.status, 0) + 1

    return {
        "topics": topics_out,
        "queue": queue_summary,
        "settings": {
            "target_words": settings.pipeline_target_words,
            "min_phrases": settings.pipeline_min_phrases,
            "autorun": settings.pipeline_autorun,
            "auto_topics": settings.pipeline_auto_topics,
            "interval_minutes": settings.pipeline_interval_minutes,
        },
    }


@router.get("/failures", summary="Open word failures (auto-retried next runs)")
async def list_failures(topic: str | None = None, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.db.models import WordFailure

    stmt = select(WordFailure).where(WordFailure.resolved == False)  # noqa: E712
    if topic:
        stmt = stmt.where(WordFailure.topic == topic.strip().lower())
    result = await db.execute(stmt.order_by(WordFailure.updated_at.desc()).limit(200))
    return [
        {
            "word": f.word,
            "topic": f.topic,
            "stage": f.stage,
            "error": f.error,
            "retry_count": f.retry_count,
        }
        for f in result.scalars().all()
    ]


@router.get("/run/{run_id}", response_model=PipelineRunOut, summary="Poll pipeline run status")
async def get_run_status(run_id: int, db: AsyncSession = Depends(get_db)):
    """GET /api/pipeline/run/{run_id} — returns current status + error report."""
    run = await db.get(PipelineRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    return PipelineRunOut(
        run_id=run.id,
        status=run.status,
        topic=run.topic,
        words_added=run.words_added,
        words_linked=run.words_linked,
        phrases_added=run.phrases_added or 0,
        target_words=run.target_words or 0,
        errors=run.errors_json or [],
        started_at=run.started_at.isoformat(),
        finished_at=run.finished_at.isoformat() if run.finished_at else None,
    )


@router.get("/runs", summary="List all pipeline runs")
async def list_runs(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(
        select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(50)
    )
    runs = result.scalars().all()
    return [
        {
            "run_id": r.id,
            "topic": r.topic,
            "status": r.status,
            "words_added": r.words_added,
            "words_linked": r.words_linked,
            "errors_count": len(r.errors_json or []),
            "started_at": r.started_at.isoformat(),
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        }
        for r in runs
    ]

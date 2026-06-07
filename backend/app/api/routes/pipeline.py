from __future__ import annotations

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PipelineRun
from app.db.session import SessionLocal, get_db
from app.pipeline.runner import run_pipeline

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class PipelineRequest(BaseModel):
    topic: str
    article_urls: list[str] = []


class PipelineRunOut(BaseModel):
    run_id: int
    status: str
    topic: str
    words_added: int
    words_linked: int
    errors: list[dict]
    started_at: str
    finished_at: str | None


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
    )

    return {"status": "started", "run_id": run.id, "topic": topic}


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

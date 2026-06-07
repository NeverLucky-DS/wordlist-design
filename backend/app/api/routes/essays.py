import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas import (
    EssayAnalysisOut,
    EssayAnalysisRecordOut,
    EssayCreate,
    EssayListItemOut,
    EssayOut,
    EssayUpdate,
)
from app.services import essays_repo
from app.config import settings
from app.services.mistral_analyzer import analyze_essay, iter_analyze_events
from app.services.user_stats_service import record_activity

router = APIRouter(prefix="/api/essays", tags=["essays"])


def _row_to_analysis_out(row, essay_id: int, *, is_stale: bool = False) -> dict:
    errors = row.errors_json.get("errors", []) if row.errors_json else []
    part_reports = row.part_reports_json.get("items", []) if row.part_reports_json else []
    final_raw = row.final_summary_json or {}
    final_summary = final_raw if final_raw else None
    return {
        "essay_id": essay_id,
        "overall_score": row.overall_score or 0,
        "grade": row.grade or "D",
        "errors": errors,
        "part_reports": part_reports,
        "final_summary": final_summary,
        "model": row.model or "unknown",
        "created_at": row.created_at,
        "text_snapshot": row.text_snapshot or "",
        "is_stale": is_stale,
    }


async def _persist_analysis(db: AsyncSession, essay, event: dict) -> None:
    await essays_repo.save_analysis(
        db,
        essay_id=essay.id,
        errors=event["errors"],
        overall_score=event["overall_score"],
        grade=event["grade"],
        text_snapshot=essay.text,
        part_reports=event.get("part_reports", []),
        final_summary=event.get("final_summary"),
        model=event.get("model", ""),
    )
    await record_activity(db, user_id=settings.default_user_id)


@router.post("", response_model=EssayOut)
async def create_essay(body: EssayCreate, db: AsyncSession = Depends(get_db)):
    essay = await essays_repo.create_essay(db, body.model_dump())
    return essay


@router.get("", response_model=list[EssayListItemOut])
async def list_essays(db: AsyncSession = Depends(get_db)):
    return await essays_repo.list_essays_with_analysis(db)


@router.get("/{essay_id}", response_model=EssayOut)
async def get_essay(essay_id: int, db: AsyncSession = Depends(get_db)):
    essay = await essays_repo.get_essay(db, essay_id)
    if not essay:
        raise HTTPException(status_code=404, detail="Essay not found")
    return essay


@router.get("/{essay_id}/analysis/latest", response_model=EssayAnalysisRecordOut)
async def get_latest_analysis(essay_id: int, db: AsyncSession = Depends(get_db)):
    essay = await essays_repo.get_essay(db, essay_id)
    if not essay:
        raise HTTPException(status_code=404, detail="Essay not found")
    row = await essays_repo.get_latest_analysis(db, essay_id)
    if not row:
        raise HTTPException(status_code=404, detail="No analysis found")
    is_stale = bool(row.text_snapshot and row.text_snapshot != essay.text)
    return _row_to_analysis_out(row, essay.id, is_stale=is_stale)


@router.patch("/{essay_id}", response_model=EssayOut)
async def update_essay(
    essay_id: int,
    body: EssayUpdate,
    db: AsyncSession = Depends(get_db),
):
    update_data = body.model_dump(exclude_none=True)
    essay = await essays_repo.update_essay(db, essay_id, update_data)
    if not essay:
        raise HTTPException(status_code=404, detail="Essay not found")
    return essay


@router.post("/{essay_id}/analyze", response_model=EssayAnalysisOut)
async def analyze(essay_id: int, db: AsyncSession = Depends(get_db)):
    essay = await essays_repo.get_essay(db, essay_id)
    if not essay:
        raise HTTPException(status_code=404, detail="Essay not found")

    analysis = await analyze_essay(
        text=essay.text,
        essay_type=essay.essay_type,
        level=essay.level,
    )
    await _persist_analysis(db, essay, analysis)
    return {
        "essay_id": essay.id,
        "overall_score": analysis["overall_score"],
        "grade": analysis["grade"],
        "errors": analysis["errors"],
        "part_reports": analysis.get("part_reports", []),
        "final_summary": analysis.get("final_summary"),
        "model": analysis["model"],
    }


@router.post("/{essay_id}/analyze/stream")
async def analyze_stream(essay_id: int, db: AsyncSession = Depends(get_db)):
    essay = await essays_repo.get_essay(db, essay_id)
    if not essay:
        raise HTTPException(status_code=404, detail="Essay not found")

    async def generate():
        async for event in iter_analyze_events(
            text=essay.text,
            essay_type=essay.essay_type,
            level=essay.level,
        ):
            if event.get("type") == "done":
                await _persist_analysis(db, essay, event)
            payload = {"essay_id": essay.id, **event}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

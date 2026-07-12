from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import Principal, get_principal
from app.db.models import EssayAnalysis
from app.db.session import get_db
from app.schemas import (
    AnalysisRunOut,
    AnalysisStartIn,
    EssayAnalysisOut,
    EssayAnalysisRecordOut,
    EssayCreate,
    EssayListItemOut,
    EssayOut,
    EssayUpdate,
    EssayVersionCreate,
    EssayVersionOut,
)
from app.services import essays_repo
from app.services.analysis_jobs import start_analysis_job
from app.services.mistral_analyzer import PART_ORDER, analyze_essay, iter_analyze_events

router = APIRouter(prefix="/api/essays", tags=["essays"])


def _analysis_payload(row: EssayAnalysis, essay_text: str) -> dict:
    final = row.final_summary_json or {}
    return {
        "id": row.id,
        "essay_id": row.essay_id,
        "version_id": row.version_id,
        "scope": row.scope,
        "part": row.part,
        "status": row.status,
        "progress_step": row.progress_step,
        "cancellation_requested": row.cancellation_requested,
        "overall_score": row.overall_score,
        "grade": row.grade,
        "errors": (row.errors_json or {}).get("errors", []),
        "part_reports": (row.part_reports_json or {}).get("items", []),
        "final_summary": final or None,
        "warnings": row.warnings_json or [],
        "model": row.model,
        "schema_version": row.schema_version,
        "prompt_version": row.prompt_version,
        "error_message": row.error_message,
        "created_at": row.created_at,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "text_snapshot": row.text_snapshot or "",
        "is_stale": bool((row.text_snapshot or "") != essay_text),
    }


def _legacy_payload(row: EssayAnalysis, essay_text: str) -> dict:
    payload = _analysis_payload(row, essay_text)
    return {
        key: payload[key]
        for key in (
            "essay_id",
            "overall_score",
            "grade",
            "errors",
            "part_reports",
            "final_summary",
            "model",
            "created_at",
            "text_snapshot",
            "is_stale",
        )
    }


async def _essay_or_404(
    db: AsyncSession, essay_id: int, principal: Principal
):
    essay = await essays_repo.get_essay(db, essay_id, principal)
    if not essay:
        raise HTTPException(status_code=404, detail="Essay not found")
    return essay


@router.post("", response_model=EssayOut)
async def create_essay(
    body: EssayCreate,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    return await essays_repo.create_essay(db, body.model_dump(), principal)


@router.get("", response_model=list[EssayListItemOut])
async def list_essays(
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    return await essays_repo.list_essays_with_analysis(db, principal)


@router.get("/{essay_id}", response_model=EssayOut)
async def get_essay(
    essay_id: int,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    return await _essay_or_404(db, essay_id, principal)


@router.patch("/{essay_id}", response_model=EssayOut)
async def update_essay(
    essay_id: int,
    body: EssayUpdate,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    essay = await essays_repo.update_essay(
        db, essay_id, body.model_dump(exclude_none=True), principal
    )
    if not essay:
        raise HTTPException(status_code=404, detail="Essay not found")
    return essay


@router.delete("/{essay_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_essay(
    essay_id: int,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    if not await essays_repo.delete_essay(db, essay_id, principal):
        raise HTTPException(status_code=404, detail="Essay not found")


@router.post(
    "/{essay_id}/versions",
    response_model=EssayVersionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_version(
    essay_id: int,
    body: EssayVersionCreate,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    essay = await _essay_or_404(db, essay_id, principal)
    reason = body.reason if body.reason in {"manual", "analysis"} else "manual"
    return await essays_repo.create_version(db, essay, reason=reason)


@router.get("/{essay_id}/versions", response_model=list[EssayVersionOut])
async def list_versions(
    essay_id: int,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    rows = await essays_repo.list_versions(db, essay_id, principal)
    if rows is None:
        raise HTTPException(status_code=404, detail="Essay not found")
    return rows


@router.post(
    "/{essay_id}/versions/{version_id}/restore",
    response_model=EssayOut,
)
async def restore_version(
    essay_id: int,
    version_id: int,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    essay = await essays_repo.restore_version(db, essay_id, version_id, principal)
    if not essay:
        raise HTTPException(status_code=404, detail="Essay version not found")
    return essay


@router.post(
    "/{essay_id}/analyses",
    response_model=AnalysisRunOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_analysis(
    essay_id: int,
    body: AnalysisStartIn,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    essay = await _essay_or_404(db, essay_id, principal)
    if body.part is not None and body.part not in PART_ORDER:
        raise HTTPException(status_code=422, detail="Unknown essay part")
    active = await essays_repo.get_active_analysis(db, essay.id)
    if active:
        raise HTTPException(
            status_code=409,
            detail={"message": "Analysis already running", "analysis_id": active.id},
        )
    version = await essays_repo.create_version(db, essay, reason="analysis")
    row = await essays_repo.create_analysis_run(
        db, essay=essay, version=version, part=body.part
    )
    payload = _analysis_payload(row, essay.text)
    start_analysis_job(row.id)
    return payload


@router.get("/{essay_id}/analyses", response_model=list[AnalysisRunOut])
async def list_analyses(
    essay_id: int,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    essay = await _essay_or_404(db, essay_id, principal)
    rows = await essays_repo.list_analyses(db, essay_id, principal)
    return [_analysis_payload(row, essay.text) for row in (rows or [])]


@router.get(
    "/{essay_id}/analyses/active",
    response_model=AnalysisRunOut | None,
)
async def active_analysis(
    essay_id: int,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    essay = await _essay_or_404(db, essay_id, principal)
    row = await essays_repo.get_active_analysis(db, essay_id)
    return _analysis_payload(row, essay.text) if row else None


@router.get("/{essay_id}/analyses/{analysis_id}", response_model=AnalysisRunOut)
async def get_analysis(
    essay_id: int,
    analysis_id: int,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    essay = await _essay_or_404(db, essay_id, principal)
    row = await essays_repo.get_analysis(db, analysis_id, principal)
    if not row or row.essay_id != essay_id:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _analysis_payload(row, essay.text)


@router.post("/{essay_id}/analyses/{analysis_id}/cancel", response_model=AnalysisRunOut)
async def cancel_analysis(
    essay_id: int,
    analysis_id: int,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    essay = await _essay_or_404(db, essay_id, principal)
    row = await essays_repo.request_cancel(db, analysis_id, principal)
    if not row or row.essay_id != essay_id:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _analysis_payload(row, essay.text)


@router.get(
    "/{essay_id}/analysis/latest",
    response_model=EssayAnalysisRecordOut,
)
async def get_latest_analysis(
    essay_id: int,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    essay = await _essay_or_404(db, essay_id, principal)
    row = await essays_repo.get_latest_analysis(db, essay_id)
    if not row:
        raise HTTPException(status_code=404, detail="No analysis found")
    return _legacy_payload(row, essay.text)


@router.post("/{essay_id}/analyze", response_model=EssayAnalysisOut)
async def analyze_legacy(
    essay_id: int,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    essay = await _essay_or_404(db, essay_id, principal)
    result = await analyze_essay(
        text=essay.text,
        essay_type=essay.essay_type,
        level=essay.level,
    )
    version = await essays_repo.create_version(db, essay, reason="analysis")
    row = await essays_repo.create_analysis_run(
        db, essay=essay, version=version, part=None
    )
    row.status = (
        "completed_with_warnings" if result.get("warnings") else "completed"
    )
    row.progress_step = "completed"
    row.errors_json = {"errors": result.get("errors", [])}
    row.part_reports_json = {"items": result.get("part_reports", [])}
    row.final_summary_json = result.get("final_summary") or {}
    row.overall_score = result.get("overall_score")
    row.grade = result.get("grade")
    row.model = result.get("model")
    row.warnings_json = result.get("warnings", [])
    await db.commit()
    payload = _legacy_payload(row, essay.text)
    payload.pop("created_at", None)
    payload.pop("text_snapshot", None)
    payload.pop("is_stale", None)
    return payload


@router.post("/{essay_id}/analyze/stream")
async def analyze_stream_legacy(
    essay_id: int,
    part: str | None = None,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    essay = await _essay_or_404(db, essay_id, principal)

    async def generate():
        async for event in iter_analyze_events(
            text=essay.text,
            essay_type=essay.essay_type,
            level=essay.level,
            only_part=part,
        ):
            yield f"data: {json.dumps({'essay_id': essay.id, **event}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

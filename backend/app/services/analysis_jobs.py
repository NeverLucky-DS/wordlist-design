from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.db.models import Essay, EssayAnalysis, EssayVersion
from app.db.session import SessionLocal
from app.services.mistral_analyzer import iter_analyze_events
from app.services.user_stats_service import record_activity

logger = logging.getLogger(__name__)
_tasks: dict[int, asyncio.Task] = {}


def _now() -> datetime:
    # EssayAnalysis timestamps are naive UTC (DateTime without timezone=True).
    return datetime.now(timezone.utc).replace(tzinfo=None)


def start_analysis_job(analysis_id: int) -> None:
    task = asyncio.create_task(_run(analysis_id), name=f"essay-analysis-{analysis_id}")
    _tasks[analysis_id] = task
    task.add_done_callback(lambda _: _tasks.pop(analysis_id, None))


async def _cancel_requested(db, row: EssayAnalysis) -> bool:
    await db.refresh(row, attribute_names=["cancellation_requested"])
    return bool(row.cancellation_requested)


async def _run(analysis_id: int) -> None:
    async with SessionLocal() as db:
        row = await db.get(EssayAnalysis, analysis_id)
        if not row:
            return
        version = await db.get(EssayVersion, row.version_id)
        essay = await db.get(Essay, row.essay_id)
        if not version or not essay:
            row.status = "failed"
            row.error_message = "Essay version is unavailable"
            row.finished_at = _now()
            await db.commit()
            return

        row.status = "running"
        row.progress_step = "preparing"
        row.started_at = _now()
        await db.commit()

        done_event: dict | None = None
        try:
            async for event in iter_analyze_events(
                text=version.text,
                essay_type=essay.essay_type,
                level=essay.level,
                only_part=row.part,
            ):
                if await _cancel_requested(db, row):
                    row.status = "cancelled"
                    row.progress_step = "cancelled"
                    row.finished_at = _now()
                    await db.commit()
                    return

                event_type = event.get("type")
                if event_type == "part_start":
                    row.progress_step = f"analyzing:{event.get('part', '')}"
                elif event_type == "part_done":
                    row.progress_step = f"reviewed:{event.get('part', '')}"
                    row.errors_json = {"errors": event.get("all_errors", [])}
                    row.part_reports_json = {
                        "items": event.get("part_reports", [])
                    }
                    row.warnings_json = event.get("warnings", [])
                elif event_type == "done":
                    row.progress_step = "saving"
                    done_event = event
                await db.commit()

            if not done_event:
                raise RuntimeError("Analysis ended without a result")

            warnings = done_event.get("warnings", [])
            row.errors_json = {"errors": done_event.get("errors", [])}
            row.part_reports_json = {
                "items": done_event.get("part_reports", [])
            }
            row.final_summary_json = done_event.get("final_summary") or {}
            row.overall_score = done_event.get("overall_score")
            row.grade = done_event.get("grade")
            row.model = done_event.get("model")
            row.warnings_json = warnings
            row.status = "completed_with_warnings" if warnings else "completed"
            row.progress_step = "completed"
            row.finished_at = _now()
            await db.commit()

            if essay.user_id is not None:
                await record_activity(db, user_id=essay.user_id)
        except asyncio.CancelledError:
            row.status = "interrupted"
            row.progress_step = "interrupted"
            row.error_message = "Server stopped while analysis was running"
            row.finished_at = _now()
            await db.commit()
            raise
        except Exception as exc:
            logger.exception("Background essay analysis failed [%s]", analysis_id)
            row.status = "failed"
            row.progress_step = "failed"
            row.error_message = str(exc)[:1000]
            row.finished_at = _now()
            await db.commit()


async def mark_interrupted_analyses() -> None:
    async with SessionLocal() as db:
        await db.execute(
            update(EssayAnalysis)
            .where(EssayAnalysis.status.in_(("queued", "running")))
            .values(
                status="interrupted",
                progress_step="interrupted",
                error_message="Server restarted while analysis was running",
                finished_at=_now(),
            )
        )
        await db.commit()


async def stop_analysis_jobs() -> None:
    tasks = list(_tasks.values())
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Essay, EssayAnalysis


async def create_essay(session: AsyncSession, data: dict) -> Essay:
    essay = Essay(**data)
    session.add(essay)
    await session.commit()
    await session.refresh(essay)
    return essay


async def list_essays(session: AsyncSession) -> list[Essay]:
    result = await session.execute(select(Essay).order_by(Essay.updated_at.desc()))
    return list(result.scalars().all())


async def get_essay(session: AsyncSession, essay_id: int) -> Essay | None:
    result = await session.execute(select(Essay).where(Essay.id == essay_id))
    return result.scalar_one_or_none()


async def update_essay(session: AsyncSession, essay_id: int, data: dict) -> Essay | None:
    essay = await get_essay(session, essay_id)
    if not essay:
        return None
    for key, value in data.items():
        setattr(essay, key, value)
    await session.commit()
    await session.refresh(essay)
    return essay


async def save_analysis(
    session: AsyncSession,
    *,
    essay_id: int,
    errors: list[dict],
    overall_score: int,
    grade: str,
    text_snapshot: str = "",
    part_reports: list | None = None,
    final_summary: dict | None = None,
    model: str = "",
) -> EssayAnalysis:
    row = EssayAnalysis(
        essay_id=essay_id,
        errors_json={"errors": errors},
        overall_score=overall_score,
        grade=grade,
        text_snapshot=text_snapshot,
        part_reports_json={"items": part_reports or []},
        final_summary_json=final_summary or {},
        model=model or None,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def list_essays_with_analysis(session: AsyncSession) -> list[dict]:
    essays = await list_essays(session)
    items: list[dict] = []
    for essay in essays:
        latest = await get_latest_analysis(session, essay.id)
        items.append(
            {
                "id": essay.id,
                "title": essay.title,
                "text": essay.text,
                "essay_type": essay.essay_type,
                "topic": essay.topic,
                "level": essay.level,
                "created_at": essay.created_at,
                "updated_at": essay.updated_at,
                "grade": latest.grade if latest else None,
                "overall_score": latest.overall_score if latest else None,
                "last_analyzed_at": latest.created_at if latest else None,
            }
        )
    return items


async def get_latest_analysis(session: AsyncSession, essay_id: int) -> EssayAnalysis | None:
    result = await session.execute(
        select(EssayAnalysis)
        .where(EssayAnalysis.essay_id == essay_id)
        .order_by(EssayAnalysis.created_at.desc())
        .limit(1),
    )
    return result.scalar_one_or_none()

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import Principal
from app.db.models import Essay, EssayAnalysis, EssayVersion, EssayWordPackage


def _owned(principal: Principal):
    if principal.user_id is not None:
        return Essay.user_id == principal.user_id
    return Essay.guest_session_id == principal.guest_session_id


async def create_essay(
    session: AsyncSession, data: dict, principal: Principal
) -> Essay:
    essay = Essay(
        **data,
        user_id=principal.user_id,
        guest_session_id=principal.guest_session_id,
    )
    session.add(essay)
    await session.commit()
    await session.refresh(essay)
    return essay


async def list_essays(
    session: AsyncSession, principal: Principal
) -> list[Essay]:
    result = await session.execute(
        select(Essay)
        .where(_owned(principal))
        .order_by(Essay.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_essay(
    session: AsyncSession, essay_id: int, principal: Principal
) -> Essay | None:
    result = await session.execute(
        select(Essay).where(Essay.id == essay_id, _owned(principal))
    )
    return result.scalar_one_or_none()


async def update_essay(
    session: AsyncSession,
    essay_id: int,
    data: dict,
    principal: Principal,
) -> Essay | None:
    essay = await get_essay(session, essay_id, principal)
    if not essay:
        return None
    for key, value in data.items():
        setattr(essay, key, value)
    await session.commit()
    await session.refresh(essay)
    return essay


async def delete_essay(
    session: AsyncSession, essay_id: int, principal: Principal
) -> bool:
    essay = await get_essay(session, essay_id, principal)
    if not essay:
        return False
    await session.delete(essay)
    await session.commit()
    return True


async def create_version(
    session: AsyncSession, essay: Essay, *, reason: str
) -> EssayVersion:
    row = EssayVersion(
        essay_id=essay.id,
        title=essay.title,
        text=essay.text,
        content_json=essay.content_json or {},
        reason=reason,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def list_versions(
    session: AsyncSession, essay_id: int, principal: Principal
) -> list[EssayVersion] | None:
    if not await get_essay(session, essay_id, principal):
        return None
    result = await session.execute(
        select(EssayVersion)
        .where(EssayVersion.essay_id == essay_id)
        .order_by(EssayVersion.created_at.desc(), EssayVersion.id.desc())
    )
    return list(result.scalars().all())


async def restore_version(
    session: AsyncSession,
    essay_id: int,
    version_id: int,
    principal: Principal,
) -> Essay | None:
    essay = await get_essay(session, essay_id, principal)
    if not essay:
        return None
    result = await session.execute(
        select(EssayVersion).where(
            EssayVersion.id == version_id,
            EssayVersion.essay_id == essay_id,
        )
    )
    version = result.scalar_one_or_none()
    if not version:
        return None
    session.add(
        EssayVersion(
            essay_id=essay.id,
            title=essay.title,
            text=essay.text,
            content_json=essay.content_json or {},
            reason="pre_restore",
        )
    )
    essay.title = version.title
    essay.text = version.text
    essay.content_json = version.content_json or {}
    await session.commit()
    await session.refresh(essay)
    return essay


async def create_analysis_run(
    session: AsyncSession,
    *,
    essay: Essay,
    version: EssayVersion,
    part: str | None,
) -> EssayAnalysis:
    row = EssayAnalysis(
        essay_id=essay.id,
        version_id=version.id,
        scope="part" if part else "full",
        part=part,
        status="queued",
        progress_step="queued",
        text_snapshot=version.text,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def list_essays_with_analysis(
    session: AsyncSession, principal: Principal
) -> list[dict]:
    essays = await list_essays(session, principal)
    items: list[dict] = []
    for essay in essays:
        latest = await get_latest_analysis(session, essay.id)
        items.append(
            {
                "id": essay.id,
                "title": essay.title,
                "text": essay.text,
                "content_json": essay.content_json or {},
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


async def get_latest_analysis(
    session: AsyncSession, essay_id: int
) -> EssayAnalysis | None:
    result = await session.execute(
        select(EssayAnalysis)
        .where(
            EssayAnalysis.essay_id == essay_id,
            EssayAnalysis.status.in_(("completed", "completed_with_warnings")),
        )
        .order_by(EssayAnalysis.created_at.desc(), EssayAnalysis.id.desc())
        .limit(1),
    )
    return result.scalar_one_or_none()


async def get_analysis(
    session: AsyncSession,
    analysis_id: int,
    principal: Principal,
) -> EssayAnalysis | None:
    result = await session.execute(
        select(EssayAnalysis)
        .join(Essay, Essay.id == EssayAnalysis.essay_id)
        .where(EssayAnalysis.id == analysis_id, _owned(principal))
    )
    return result.scalar_one_or_none()


async def list_analyses(
    session: AsyncSession,
    essay_id: int,
    principal: Principal,
) -> list[EssayAnalysis] | None:
    if not await get_essay(session, essay_id, principal):
        return None
    result = await session.execute(
        select(EssayAnalysis)
        .where(EssayAnalysis.essay_id == essay_id)
        .order_by(EssayAnalysis.created_at.desc(), EssayAnalysis.id.desc())
    )
    return list(result.scalars().all())


async def get_active_analysis(
    session: AsyncSession, essay_id: int
) -> EssayAnalysis | None:
    result = await session.execute(
        select(EssayAnalysis)
        .where(
            EssayAnalysis.essay_id == essay_id,
            EssayAnalysis.status.in_(("queued", "running")),
        )
        .order_by(EssayAnalysis.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def request_cancel(
    session: AsyncSession,
    analysis_id: int,
    principal: Principal,
) -> EssayAnalysis | None:
    row = await get_analysis(session, analysis_id, principal)
    if not row:
        return None
    if row.status in ("queued", "running"):
        row.cancellation_requested = True
        await session.commit()
        await session.refresh(row)
    return row


async def get_wortpaket(
    session: AsyncSession, essay_id: int
) -> EssayWordPackage | None:
    result = await session.execute(
        select(EssayWordPackage).where(EssayWordPackage.essay_id == essay_id)
    )
    return result.scalar_one_or_none()


async def upsert_wortpaket(session: AsyncSession, essay: Essay) -> EssayWordPackage:
    """One package per essay: rebuilding resets the existing row in place.

    Reset rather than insert-a-new-one, and the old lemmas are cleared with it.
    Leaving them visible while a rebuild runs would show a list that belongs to
    the previous topic under a spinner that claims to be building this one.

    `thema` and `niveau` are copied from the essay HERE, at the moment the build
    is asked for. That is what makes a later mismatch detectable: the row says
    what it was built from, not what the essay happens to say now.
    """
    row = await get_wortpaket(session, essay.id)
    if row is None:
        row = EssayWordPackage(essay_id=essay.id)
        session.add(row)

    row.thema = essay.topic or ""
    row.niveau = essay.level or "B1"
    row.status = "pending"
    row.lemmas = []
    row.stats = {}
    row.error_message = None
    row.finished_at = None
    await session.commit()
    await session.refresh(row)
    return row

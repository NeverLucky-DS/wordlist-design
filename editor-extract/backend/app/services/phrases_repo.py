from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Phrase, UserPhraseKnown


async def list_phrases(
    session: AsyncSession,
    *,
    level: str | None = None,
    essay_part: str | None = None,
    topic: str | None = None,
) -> list[Phrase]:
    topic_slug = (topic or "").strip().lower()

    if topic_slug:
        stmt = select(Phrase).where(Phrase.topic == topic_slug).order_by(Phrase.id.asc())
        if level:
            stmt = stmt.where(Phrase.level == level)
        if essay_part:
            stmt = stmt.where(Phrase.essay_part == essay_part)
        result = await session.execute(stmt)
        topic_phrases = list(result.scalars().all())
        if topic_phrases:
            return topic_phrases

    stmt = select(Phrase).where(Phrase.topic.is_(None)).order_by(Phrase.id.asc())
    if level:
        stmt = stmt.where(Phrase.level == level)
    if essay_part:
        stmt = stmt.where(Phrase.essay_part == essay_part)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_phrase_known_map(
    session: AsyncSession,
    *,
    user_id: int,
    phrase_ids: list[int],
) -> dict[int, bool]:
    if not phrase_ids:
        return {}
    stmt = select(UserPhraseKnown).where(
        UserPhraseKnown.user_id == user_id,
        UserPhraseKnown.phrase_id.in_(phrase_ids),
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return {row.phrase_id: row.known for row in rows}


async def set_phrase_known(
    session: AsyncSession,
    *,
    user_id: int,
    phrase_id: int,
    known: bool,
) -> UserPhraseKnown:
    stmt = select(UserPhraseKnown).where(
        UserPhraseKnown.user_id == user_id,
        UserPhraseKnown.phrase_id == phrase_id,
    )
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    if row:
        row.known = known
    else:
        row = UserPhraseKnown(user_id=user_id, phrase_id=phrase_id, known=known)
        session.add(row)
    await session.commit()
    await session.refresh(row)
    return row

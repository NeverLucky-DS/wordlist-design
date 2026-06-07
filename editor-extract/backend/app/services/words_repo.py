from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import UserWordProgress, Word, WordTopic


async def list_words(
    session: AsyncSession,
    *,
    topic: str | None = None,
    level: str | None = None,
    q: str | None = None,
) -> list[Word]:
    stmt = select(Word).options(selectinload(Word.topics)).order_by(Word.german)
    if level:
        stmt = stmt.where(Word.level == level)
    if q:
        stmt = stmt.where(Word.translation_ru.ilike(f"%{q}%"))
    if topic:
        stmt = stmt.join(WordTopic).where(WordTopic.topic == topic)
    result = await session.execute(stmt)
    return list(result.scalars().unique().all())


async def get_word(session: AsyncSession, word_id: int) -> Word | None:
    stmt = (
        select(Word)
        .options(selectinload(Word.topics))
        .where(Word.id == word_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def add_word_to_queue(
    session: AsyncSession,
    *,
    user_id: int,
    word_id: int,
) -> UserWordProgress:
    stmt = select(UserWordProgress).where(
        UserWordProgress.user_id == user_id,
        UserWordProgress.word_id == word_id,
    )
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    if row:
        return row
    row = UserWordProgress(user_id=user_id, word_id=word_id, score=0)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def update_word_grammar_data(
    session: AsyncSession,
    *,
    word_id: int,
    grammar_data: dict | None,
) -> Word | None:
    word = await get_word(session, word_id)
    if not word:
        return None
    word.grammar_data = grammar_data
    await session.commit()
    await session.refresh(word)
    return word

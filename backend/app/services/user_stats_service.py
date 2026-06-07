from __future__ import annotations

from datetime import date, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserStats, UserWordProgress

STREAK_TZ = ZoneInfo("Europe/Berlin")
LEARNED_SCORE_THRESHOLD = 80
DEFAULT_USER_ID = 1


def next_streak(current: int, last_date: date | None, today: date) -> tuple[int, date]:
    """Обновляет streak при активности в календарный день (Europe/Berlin)."""
    if last_date is None:
        return 1, today
    if last_date == today:
        return current, today
    if last_date == today - timedelta(days=1):
        return current + 1, today
    return 1, today


def today_berlin() -> date:
    from datetime import datetime

    return datetime.now(STREAK_TZ).date()


async def get_or_create_stats(session: AsyncSession, user_id: int = DEFAULT_USER_ID) -> UserStats:
    result = await session.execute(select(UserStats).where(UserStats.user_id == user_id))
    row = result.scalar_one_or_none()
    if row:
        return row
    row = UserStats(user_id=user_id)
    session.add(row)
    await session.flush()
    return row


async def count_learned_words(session: AsyncSession, user_id: int = DEFAULT_USER_ID) -> int:
    stmt = (
        select(func.count())
        .select_from(UserWordProgress)
        .where(
            UserWordProgress.user_id == user_id,
            UserWordProgress.score > LEARNED_SCORE_THRESHOLD,
        )
    )
    result = await session.execute(stmt)
    return int(result.scalar_one() or 0)


async def sync_words_learned(session: AsyncSession, user_id: int = DEFAULT_USER_ID) -> int:
    stats = await get_or_create_stats(session, user_id)
    learned = await count_learned_words(session, user_id)
    stats.total_words_learned = learned
    return learned


async def record_activity(session: AsyncSession, user_id: int = DEFAULT_USER_ID) -> UserStats:
    """Фиксирует день активности (тренировка или анализ) и пересчитывает выученные слова."""
    stats = await get_or_create_stats(session, user_id)
    today = today_berlin()
    new_streak, new_date = next_streak(stats.streak_current, stats.streak_last_date, today)
    stats.streak_current = new_streak
    stats.streak_last_date = new_date
    await sync_words_learned(session, user_id)
    await session.commit()
    await session.refresh(stats)
    return stats

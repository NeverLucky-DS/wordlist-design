"""User stats — streak logic and activity recording."""

from __future__ import annotations

from datetime import date, timedelta

from app.services.user_stats_service import LEARNED_SCORE_THRESHOLD, next_streak, record_activity
from app.db.models import User, UserWordProgress


def test_next_streak_first_day():
    today = date(2026, 7, 13)
    streak, last = next_streak(0, None, today)
    assert streak == 1
    assert last == today


def test_next_streak_same_day_keeps_count():
    today = date(2026, 7, 13)
    streak, last = next_streak(5, today, today)
    assert streak == 5
    assert last == today


def test_next_streak_consecutive_day_increments():
    today = date(2026, 7, 13)
    streak, last = next_streak(3, today - timedelta(days=1), today)
    assert streak == 4
    assert last == today


def test_next_streak_gap_resets():
    today = date(2026, 7, 13)
    streak, last = next_streak(10, today - timedelta(days=3), today)
    assert streak == 1
    assert last == today


async def test_record_activity_creates_stats(db_session):
    user = User(email="stats@test.com", password_hash="x")
    db_session.add(user)
    await db_session.flush()

    stats = await record_activity(db_session, user_id=user.id)
    assert stats.streak_current >= 1
    assert stats.streak_last_date is not None
    assert stats.total_words_learned == 0


async def test_learned_words_count_respects_threshold(db_session):
    user = User(email="learned@test.com", password_hash="x")
    db_session.add(user)
    await db_session.flush()

    from app.db.models import Word

    word = Word(
        german="Lernen",
        word_type="verb",
        translation_ru="учиться",
        level="B1",
        examples=[],
        source="test",
    )
    db_session.add(word)
    await db_session.flush()

    db_session.add(
        UserWordProgress(
            user_id=user.id,
            word_id=word.id,
            score=LEARNED_SCORE_THRESHOLD + 1,
        )
    )
    await db_session.commit()

    stats = await record_activity(db_session, user_id=user.id)
    assert stats.total_words_learned == 1

"""Direct repository / DB layer tests (ownership, cascades, idempotency)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.auth import Principal
from app.db.models import Essay, EssayAnalysis, User, UserPhraseKnown, UserWordProgress, Word
from app.services import essays_repo, phrases_repo, words_repo
from tests.helpers import essay_payload, seed_words_and_phrases


async def test_essays_repo_ownership_isolation(db_session):
    user_a = User(email="a@test.com", password_hash="x")
    user_b = User(email="b@test.com", password_hash="x")
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    essay = await essays_repo.create_essay(
        db_session,
        essay_payload(title="A only"),
        Principal(user_id=user_a.id),
    )
    hidden = await essays_repo.get_essay(db_session, essay.id, Principal(user_id=user_b.id))
    assert hidden is None


async def test_essays_repo_guest_ownership(db_session):
    from app.db.models import GuestSession

    guest = GuestSession(
        token_hash="abc",
        expires_at=datetime.now(timezone.utc),
    )
    db_session.add(guest)
    await db_session.flush()

    essay = await essays_repo.create_essay(
        db_session,
        essay_payload(title="Guest"),
        Principal(guest_session_id=guest.id),
    )
    found = await essays_repo.get_essay(
        db_session, essay.id, Principal(guest_session_id=guest.id)
    )
    assert found is not None
    assert found.guest_session_id == guest.id


async def test_create_analysis_run_snapshots_text(db_session):
    user = User(email="snap@test.com", password_hash="x")
    db_session.add(user)
    await db_session.flush()
    principal = Principal(user_id=user.id)

    essay = await essays_repo.create_essay(db_session, essay_payload(), principal)
    version = await essays_repo.create_version(db_session, essay, reason="analysis")
    row = await essays_repo.create_analysis_run(
        db_session, essay=essay, version=version, part="einleitung"
    )
    assert row.text_snapshot == essay.text
    assert row.scope == "part"
    assert row.part == "einleitung"
    assert row.status == "queued"


async def test_get_latest_analysis_ignores_failed_runs(db_session):
    user = User(email="latest@test.com", password_hash="x")
    db_session.add(user)
    await db_session.flush()
    principal = Principal(user_id=user.id)
    essay = await essays_repo.create_essay(db_session, essay_payload(), principal)
    version = await essays_repo.create_version(db_session, essay, reason="analysis")

    failed = await essays_repo.create_analysis_run(
        db_session, essay=essay, version=version, part=None
    )
    failed.status = "failed"
    await db_session.commit()

    ok = await essays_repo.create_analysis_run(
        db_session, essay=essay, version=version, part=None
    )
    ok.status = "completed"
    ok.grade = "B"
    ok.overall_score = 75
    await db_session.commit()

    latest = await essays_repo.get_latest_analysis(db_session, essay.id)
    assert latest.id == ok.id


async def test_words_repo_filters_combined(db_session):
    await seed_words_and_phrases(db_session)
    rows = await words_repo.list_words(db_session, topic="natur", level="A2")
    assert len(rows) == 1
    assert rows[0].german == "Baum"


async def test_words_repo_queue_is_idempotent(db_session):
    user = User(email="queue@test.com", password_hash="x")
    db_session.add(user)
    await db_session.flush()
    word = Word(
        german="Test",
        word_type="noun",
        translation_ru="тест",
        level="B1",
        examples=[],
        source="test",
    )
    db_session.add(word)
    await db_session.commit()

    first = await words_repo.add_word_to_queue(
        db_session, user_id=user.id, word_id=word.id
    )
    second = await words_repo.add_word_to_queue(
        db_session, user_id=user.id, word_id=word.id
    )
    assert first.id == second.id


async def test_phrases_repo_known_toggle(db_session):
    user = User(email="phrase@test.com", password_hash="x")
    db_session.add(user)
    await db_session.flush()
    await seed_words_and_phrases(db_session)
    phrases = await phrases_repo.list_phrases(db_session, topic="technologie")
    phrase_id = phrases[0].id

    row = await phrases_repo.set_phrase_known(
        db_session, user_id=user.id, phrase_id=phrase_id, known=True
    )
    assert row.known is True
    mapping = await phrases_repo.get_phrase_known_map(
        db_session, user_id=user.id, phrase_ids=[phrase_id]
    )
    assert mapping[phrase_id] is True


async def test_delete_essay_cascades_analyses(db_session):
    user = User(email="cascade@test.com", password_hash="x")
    db_session.add(user)
    await db_session.flush()
    principal = Principal(user_id=user.id)
    essay = await essays_repo.create_essay(db_session, essay_payload(), principal)
    version = await essays_repo.create_version(db_session, essay, reason="analysis")
    await essays_repo.create_analysis_run(db_session, essay=essay, version=version, part=None)

    await essays_repo.delete_essay(db_session, essay.id, principal)
    remaining = (
        await db_session.execute(select(EssayAnalysis).where(EssayAnalysis.essay_id == essay.id))
    ).scalars().all()
    assert remaining == []

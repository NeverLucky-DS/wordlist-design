"""Unit tests for pipeline word-routing — Step 3 before enrichment."""

from __future__ import annotations

from app.db.models import Word, WordTopic
from app.pipeline.runner import _route_words
from app.pipeline.types import WordCandidate


async def test_route_words_links_existing_and_queues_new(db_session):
    existing = Word(
        german="Digitalisierung",
        article="die",
        word_type="noun",
        translation_ru="цифровизация",
        level="B2",
        grammar_data=None,
        examples=[],
        source="seed",
    )
    db_session.add(existing)
    await db_session.commit()
    await db_session.refresh(existing)
    db_session.add(WordTopic(word_id=existing.id, topic="technologie"))
    await db_session.commit()

    candidates = [
        WordCandidate(word="Digitalisierung", pos="Noun", article="die"),
        WordCandidate(word="Nachhaltigkeit", pos="Noun", article="die"),
    ]

    new_candidates, linked = await _route_words(candidates, "klimawandel", db_session)

    assert linked == 1
    assert len(new_candidates) == 1
    assert new_candidates[0].word == "Nachhaltigkeit"

    topics = await db_session.execute(
        WordTopic.__table__.select().where(WordTopic.word_id == existing.id)
    )
    topic_names = {row.topic for row in topics}
    assert "technologie" in topic_names
    assert "klimawandel" in topic_names


async def test_route_words_skips_duplicate_topic_link(db_session):
    word = Word(
        german="Energie",
        article="die",
        word_type="noun",
        translation_ru="энергия",
        level="B2",
        grammar_data=None,
        examples=[],
        source="seed",
    )
    db_session.add(word)
    await db_session.commit()
    await db_session.refresh(word)
    db_session.add(WordTopic(word_id=word.id, topic="energie"))
    await db_session.commit()

    candidates = [WordCandidate(word="Energie", pos="Noun", article="die")]

    new_candidates, linked = await _route_words(candidates, "energie", db_session)

    # Link already exists → not counted again, word not re-enriched
    assert linked == 0
    assert new_candidates == []

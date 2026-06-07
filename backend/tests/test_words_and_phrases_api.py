from __future__ import annotations

from app.db.models import Phrase, Word, WordTopic


async def seed_words_and_phrases(db_session):
    w1 = Word(
        german="Baum",
        article="der",
        word_type="noun",
        translation_ru="дерево",
        level="A2",
        grammar_data=None,
        examples=[],
        source="test",
    )
    w2 = Word(
        german="Digitalisierung",
        article="die",
        word_type="noun",
        translation_ru="цифровизация",
        level="B1",
        grammar_data=None,
        examples=[],
        source="test",
    )
    db_session.add_all([w1, w2])
    await db_session.flush()
    db_session.add_all(
        [
            WordTopic(word_id=w1.id, topic="natur"),
            WordTopic(word_id=w2.id, topic="technologie"),
            Phrase(
                text_de="Ich bin der Meinung, dass ...",
                translation_ru="Я считаю, что...",
                essay_part="einleitung",
                topic="technologie",
                level="B1",
            ),
            Phrase(
                text_de="Zusammenfassend kann man sagen, dass ...",
                translation_ru="Подводя итог, можно сказать, что...",
                essay_part="schluss",
                topic="technologie",
                level="B2",
            ),
        ]
    )
    await db_session.commit()


async def test_words_filters(client, db_session):
    await seed_words_and_phrases(db_session)

    all_words = await client.get("/api/words")
    assert all_words.status_code == 200
    assert len(all_words.json()) >= 2

    by_level = await client.get("/api/words?level=A2")
    assert by_level.status_code == 200
    assert all(word["level"] == "A2" for word in by_level.json())

    by_topic = await client.get("/api/words?topic=natur")
    assert by_topic.status_code == 200
    assert all("natur" in word["topics"] for word in by_topic.json())

    by_q = await client.get("/api/words?q=дерево")
    assert by_q.status_code == 200
    assert any(word["german"] == "Baum" for word in by_q.json())


async def test_phrases_filters_and_known_toggle(client, db_session):
    await seed_words_and_phrases(db_session)

    by_part = await client.get("/api/phrases?part=einleitung&topic=technologie")
    assert by_part.status_code == 200
    payload = by_part.json()
    assert len(payload) == 1
    phrase_id = payload[0]["id"]
    assert payload[0]["known"] is False

    set_known = await client.post(f"/api/phrases/{phrase_id}/known", json={"known": True})
    assert set_known.status_code == 200
    assert set_known.json()["known"] is True

    after = await client.get("/api/phrases?part=einleitung&topic=technologie")
    assert after.status_code == 200
    assert after.json()[0]["known"] is True

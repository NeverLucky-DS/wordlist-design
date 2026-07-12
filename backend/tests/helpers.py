from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Phrase, Word, WordTopic


def essay_payload(**overrides) -> dict:
    base = {
        "title": "Technologie",
        "text": (
            "Einleitung:\nTechnologie ist wichtig.\n\n"
            "Argument Eins:\nSie spart Zeit.\n\n"
            "Argument Zwei:\nSie schafft auch Risiken.\n\n"
            "Schluss:\nWir brauchen Balance."
        ),
        "essay_type": "argumentativ",
        "topic": "technologie",
        "level": "B1",
    }
    base.update(overrides)
    return base


async def seed_words_and_phrases(db_session: AsyncSession) -> None:
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

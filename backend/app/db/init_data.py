from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Phrase, Word, WordTopic


async def ensure_seed_data(session: AsyncSession) -> None:
    words_count = await session.scalar(select(func.count()).select_from(Word))
    phrases_count = await session.scalar(select(func.count()).select_from(Phrase))

    if (words_count or 0) == 0:
        seed_words = [
            {
                "german": "Technologie",
                "article": "die",
                "word_type": "noun",
                "translation_ru": "технология",
                "level": "B1",
            },
            {
                "german": "Fortschritt",
                "article": "der",
                "word_type": "noun",
                "translation_ru": "прогресс",
                "level": "B1",
            },
            {
                "german": "Digitalisierung",
                "article": "die",
                "word_type": "noun",
                "translation_ru": "цифровизация",
                "level": "B2",
            },
        ]
        created_words: list[Word] = []
        for item in seed_words:
            row = Word(
                german=item["german"],
                article=item["article"],
                word_type=item["word_type"],
                translation_ru=item["translation_ru"],
                level=item["level"],
                grammar_data=None,
                examples=[],
                source="seed",
            )
            session.add(row)
            created_words.append(row)
        await session.flush()
        for row in created_words:
            session.add(WordTopic(word_id=row.id, topic="technologie"))
            session.add(WordTopic(word_id=row.id, topic="wissenschaft"))

    if (phrases_count or 0) == 0:
        seed_phrases = [
            {
                "text_de": "In der heutigen Zeit ist ... ein wichtiges Thema.",
                "translation_ru": "В наше время ... — важная тема.",
                "essay_part": "einleitung",
                "topic": "technologie",
                "level": "B1",
            },
            {
                "text_de": "Ein wichtiges Argument dafür ist, dass ...",
                "translation_ru": "Важный аргумент в пользу этого — что ...",
                "essay_part": "argument1",
                "topic": "technologie",
                "level": "B1",
            },
            {
                "text_de": "Zusammenfassend lässt sich sagen, dass ...",
                "translation_ru": "Подводя итог, можно сказать, что ...",
                "essay_part": "schluss",
                "topic": "technologie",
                "level": "B1",
            },
        ]
        for item in seed_phrases:
            session.add(
                Phrase(
                    text_de=item["text_de"],
                    translation_ru=item["translation_ru"],
                    essay_part=item["essay_part"],
                    topic=item["topic"],
                    level=item["level"],
                )
            )

    await session.commit()

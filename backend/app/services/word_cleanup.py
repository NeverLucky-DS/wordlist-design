"""Идемпотентная уборка таблицы `words` — то, что зовётся на старте контейнера.

Раньше это была нижняя половина `topic_pack_service.py`, файла на 444 строки, из
которых 354 обслуживали загрузку тем из YAML-пакетов (`*.topic.yaml`). Ни одного
такого файла не осталось ни в репозитории, ни в образе, поэтому загрузчик мог
ответить только `[]` и 404 — проверено на живом стенде 2026-07-26. Загрузчик
удалён вместе с роутером `/api/topics`; здесь осталось то, что реально работает.

Работает оно из `main.py` on_startup: чинит леммы, слепленные ещё пайплайном v1
(артикль внутри `german`, скобки, LLM-аннотации), сливает дубликаты и приводит
`topic` к нижнему регистру. Всё три идемпотентны: повторный запуск возвращает 0.
"""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Phrase, Word, WordTopic


def normalize_article(raw) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip().lower()
    if not text or text == "null":
        return None
    return text


def normalize_german_lemma(german: str, article: str | None) -> tuple[str, str | None]:
    """german в БД — лемма без артикля; article отдельно."""
    lemma = german.strip()
    art = normalize_article(article)
    for candidate in ("der", "die", "das"):
        prefix = f"{candidate} "
        if lemma.lower().startswith(prefix):
            if not art:
                art = candidate
            lemma = lemma[len(prefix) :].strip()
            break
    return lemma, art


async def ensure_word_topic(session: AsyncSession, word_id: int, topic: str) -> bool:
    """Добавляет связь слово↔тема. True — если связь создана впервые."""
    exists = await session.execute(
        select(WordTopic).where(WordTopic.word_id == word_id, WordTopic.topic == topic)
    )
    if exists.scalar_one_or_none():
        return False
    session.add(WordTopic(word_id=word_id, topic=topic))
    return True


_BRACKETS_RE = re.compile(r"\s*\([^)]*\)|\s*\[[^\]]*\]")


async def fix_word_lemmas(session: AsyncSession) -> int:
    """Приводит german к лемме: без артикля, скобок и LLM-аннотаций."""
    result = await session.execute(select(Word))
    fixed = 0
    for word in result.scalars().all():
        cleaned = _BRACKETS_RE.sub("", word.german).strip(" ,;.:-–—")
        new_german, new_article = normalize_german_lemma(cleaned, word.article)
        if new_german != word.german or new_article != word.article:
            word.german = new_german
            word.article = new_article
            fixed += 1
    if fixed:
        await session.commit()
    return fixed


async def normalize_topic_case(session: AsyncSession) -> int:
    """Приводит topic в word_topics/phrases к lowercase (наследие v1)."""
    changed = 0
    result = await session.execute(select(WordTopic))
    for link in result.scalars().all():
        lower = link.topic.strip().lower()
        if link.topic == lower:
            continue
        dup = await session.execute(
            select(WordTopic).where(
                WordTopic.word_id == link.word_id, WordTopic.topic == lower
            )
        )
        if dup.scalar_one_or_none():
            await session.delete(link)  # lowercase link already exists
        else:
            link.topic = lower
        changed += 1

    result = await session.execute(select(Phrase))
    for phrase in result.scalars().all():
        if phrase.topic and phrase.topic != phrase.topic.strip().lower():
            phrase.topic = phrase.topic.strip().lower()
            changed += 1

    if changed:
        await session.commit()
    return changed


async def dedupe_words_by_german(session: AsyncSession) -> int:
    """Сливает дубликаты с одинаковой леммой (после нормализации артикля)."""
    result = await session.execute(
        select(Word).options(selectinload(Word.topics)).order_by(Word.id.asc())
    )
    words = list(result.scalars().all())
    by_lemma: dict[str, Word] = {}
    removed = 0

    for word in words:
        key = word.german.strip().lower()
        keeper = by_lemma.get(key)
        if not keeper:
            by_lemma[key] = word
            continue

        for link in list(word.topics):
            await ensure_word_topic(session, keeper.id, link.topic)
            await session.delete(link)
        await session.flush()
        await session.delete(word)
        removed += 1

    if removed:
        await session.commit()
    return removed

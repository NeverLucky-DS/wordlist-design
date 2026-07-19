from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Phrase, UserPhraseKnown

# A reusable cliché keeps a gap for the writer to fill: "Zusammenfassend lässt
# sich sagen, dass ...". That ellipsis is what separates a template from a
# finished sentence about one particular essay prompt — measured 2026-07-19,
# 1 713 of the 1 806 distinct texts carry it, and the 93 that do not are
# content ("Ein Blick auf die Niederlande zeigt: Seit der Einführung …").
# Repetition is the weaker signal: the commonest template is stored 120 times,
# once per topic, but plenty of equally reusable ones appear only once.
_PLACEHOLDER = "%...%"


async def list_templates(
    session: AsyncSession,
    *,
    level: str | None = None,
    essay_part: str | None = None,
) -> list[Phrase]:
    """Topic-independent templates, one row per distinct wording.

    The table stores every template once per essay prompt it was generated for,
    so a plain query returns "Zusammenfassend lässt sich sagen, dass ..." 120
    times. DISTINCT ON collapses that back to the 1 806 real phrasings.
    """
    # Deduplicate within an essay part, not across the whole table. A wording
    # like "Daraus ergibt sich die Frage, ob ..." is filed under both
    # `einleitung` and `argument`, and both are right — collapsing globally
    # handed it to whichever id sorted first and silently shortened the other
    # part's list (einleitung came back 366 unfiltered against 374 filtered).
    inner = (
        select(Phrase)
        .where(Phrase.text_de.like(_PLACEHOLDER))
        .distinct(Phrase.text_de, Phrase.essay_part)
        .order_by(Phrase.text_de.asc(), Phrase.essay_part.asc(), Phrase.id.asc())
    )
    if level:
        inner = inner.where(Phrase.level == level)
    if essay_part:
        inner = inner.where(Phrase.essay_part == essay_part)

    # Shortest first. The table was generated per essay prompt, so alongside
    # "Daraus ergibt sich die Frage, ob ..." it holds thirty-word openers that
    # name their original topic ("Angesichts der rasanten Fortschritte im
    # Bereich der künstlichen Intelligenz rückt die Frage in den Fokus, ob ...").
    # Both are templates, but only the short one transplants into any essay, and
    # length separates them without having to guess at topicality.
    sub = inner.subquery()
    stmt = (
        select(Phrase)
        .join(sub, Phrase.id == sub.c.id)
        .order_by(func.length(Phrase.text_de).asc(), Phrase.text_de.asc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


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

    # Fall back to the topic-independent templates rather than to `topic IS
    # NULL`. Every one of the 4 021 rows carries a topic, so the old fallback
    # matched nothing and `GET /api/phrases` answered `[]` for anyone who did
    # not already know an exact topic slug — which is why this table sat unused.
    return await list_templates(session, level=level, essay_part=essay_part)


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

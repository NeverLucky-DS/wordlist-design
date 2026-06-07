from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.schemas import PhraseKnownUpdate, PhraseOut
from app.services import phrases_repo

router = APIRouter(prefix="/api/phrases", tags=["phrases"])


@router.get("", response_model=list[PhraseOut])
async def list_phrases(
    level: str | None = None,
    part: str | None = None,
    topic: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    phrases = await phrases_repo.list_phrases(
        db,
        level=level,
        essay_part=part,
        topic=topic,
    )
    known_map = await phrases_repo.get_phrase_known_map(
        db,
        user_id=settings.default_user_id,
        phrase_ids=[p.id for p in phrases],
    )
    result = []
    for phrase in phrases:
        result.append(
            PhraseOut(
                id=phrase.id,
                text_de=phrase.text_de,
                translation_ru=phrase.translation_ru,
                essay_part=phrase.essay_part,
                topic=phrase.topic,
                level=phrase.level,
                known=known_map.get(phrase.id, False),
            )
        )
    return result


@router.post("/{phrase_id}/known")
async def set_known(
    phrase_id: int,
    body: PhraseKnownUpdate,
    db: AsyncSession = Depends(get_db),
):
    row = await phrases_repo.set_phrase_known(
        db,
        user_id=settings.default_user_id,
        phrase_id=phrase_id,
        known=body.known,
    )
    return {"phrase_id": row.phrase_id, "known": row.known}

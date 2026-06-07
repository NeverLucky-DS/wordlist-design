from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.schemas import WordOut
from app.services import words_repo
from app.services.grammar_parser import normalize_wiktionary_entry
from app.services.topic_pack_service import normalize_german_lemma
from app.services.wiktionary_client import fetch_wiktionary_entry

router = APIRouter(prefix="/api/words", tags=["words"])


def word_to_out(word) -> WordOut:
    return WordOut(
        id=word.id,
        german=word.german,
        article=word.article,
        word_type=word.word_type,
        translation_ru=word.translation_ru,
        level=word.level,
        grammar_data=word.grammar_data,
        examples=word.examples or [],
        source=word.source,
        topics=[t.topic for t in word.topics],
    )


@router.get("", response_model=list[WordOut])
async def list_words(
    topic: str | None = None,
    level: str | None = None,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    words = await words_repo.list_words(db, topic=topic, level=level, q=q)
    return [word_to_out(w) for w in words]


@router.get("/{word_id}", response_model=WordOut)
async def get_word(word_id: int, db: AsyncSession = Depends(get_db)):
    word = await words_repo.get_word(db, word_id)
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    return word_to_out(word)


@router.post("/{word_id}/queue")
async def queue_word(word_id: int, db: AsyncSession = Depends(get_db)):
    word = await words_repo.get_word(db, word_id)
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    progress = await words_repo.add_word_to_queue(
        db,
        user_id=settings.default_user_id,
        word_id=word_id,
    )
    return {"word_id": word_id, "score": progress.score}


@router.post("/{word_id}/refresh-grammar", response_model=WordOut)
async def refresh_grammar(word_id: int, db: AsyncSession = Depends(get_db)):
    word = await words_repo.get_word(db, word_id)
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")

    lookup, _ = normalize_german_lemma(word.german, word.article)
    raw = await fetch_wiktionary_entry(lookup)
    grammar_data = normalize_wiktionary_entry(raw, word=lookup)
    updated = await words_repo.update_word_grammar_data(
        db,
        word_id=word_id,
        grammar_data=grammar_data,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Word not found")
    return word_to_out(updated)

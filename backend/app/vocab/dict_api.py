"""/api/vocab/* — the Wörterbuch product API: lookup + personal word list.

Split from `api.py` on purpose. That module is the ops dashboard for dictionary
ingestion (build/enrich/progress); this one is what the Wörterbuch page talks to.
Both mount under the same prefix, which is fine — FastAPI merges them.

Reads are public, matching the existing convention that inspecting the base needs
no account. Everything touching a personal list requires one: the list is the
user's own data and, by decision, has no guest mode (unlike essays).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import Principal, get_optional_user, require_user
from app.db.models import UserWordList, VocabCard
from app.db.session import get_db
from app.vocab import mirror, norm, search as search_mod

router = APIRouter(prefix="/api/vocab", tags=["woerterbuch"])

LIST_PAGE = 20      # the page shows the most recent words; the rest is paged
LIST_MAX = 100


# ── helpers ──────────────────────────────────────────────────────────────────
async def _lemmas_in_list(db: AsyncSession, user_id: int | None,
                          lemmas: list[str]) -> set[str]:
    """Which of `lemmas` this user already learns — drives the add/added button."""
    if not user_id or not lemmas:
        return set()
    rows = await db.execute(
        select(UserWordList.lemma).where(
            UserWordList.user_id == user_id, UserWordList.lemma.in_(lemmas)
        )
    )
    return {r[0] for r in rows}


def _list_item(row: UserWordList) -> dict:
    return {
        "lemma": row.lemma,
        "ru": row.ru,
        "level": row.level,
        "band": row.band,
        "type": norm.type_of(row.pos, row.article),
        "pos": row.pos,
        "article": row.article,
        "topic": row.topic,
        "status": row.status,
        "added_at": row.added_at.isoformat() if row.added_at else None,
    }


# ── lookup ───────────────────────────────────────────────────────────────────
@router.get("/search")
async def search(
    q: str = "",
    limit: int = 20,
    principal: Principal | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Dictionary lookup. Latin input searches German, Cyrillic searches Russian.

    An empty `items` means exactly that — we do not have the word yet. The base
    is still being enriched, so that answer is honest rather than final.
    """
    q = (q or "").strip()
    if not q:
        return {"lang": "de", "query": "", "items": []}

    result = await search_mod.search(db, q, limit)
    known = await _lemmas_in_list(
        db,
        principal.user_id if principal else None,
        [i["lemma"] for i in result["items"]],
    )
    for item in result["items"]:
        item["in_list"] = item["lemma"] in known
    return result


@router.get("/entry/{lemma:path}")
async def entry(
    lemma: str,
    principal: Principal | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """One full card from the mirror, by exact lemma."""
    card = await db.get(VocabCard, lemma)
    if not card:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")
    out = search_mod.card_out(card)
    known = await _lemmas_in_list(
        db, principal.user_id if principal else None, [lemma]
    )
    out["in_list"] = lemma in known
    return out


# ── personal word list ───────────────────────────────────────────────────────
class AddWordIn(BaseModel):
    lemma: str = Field(min_length=1, max_length=128)


@router.get("/list")
async def get_list(
    limit: int = LIST_PAGE,
    offset: int = 0,
    principal: Principal = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """The user's words, newest first."""
    limit = max(1, min(int(limit), LIST_MAX))
    offset = max(0, int(offset))
    total = (
        await db.execute(
            select(func.count())
            .select_from(UserWordList)
            .where(UserWordList.user_id == principal.user_id)
        )
    ).scalar_one()
    rows = (
        await db.execute(
            select(UserWordList)
            .where(UserWordList.user_id == principal.user_id)
            .order_by(UserWordList.added_at.desc(), UserWordList.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()
    return {
        "items": [_list_item(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/list/stats")
async def list_stats(
    principal: Principal = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Counts per band — the donut on the page."""
    rows = await db.execute(
        select(UserWordList.band, func.count())
        .where(UserWordList.user_id == principal.user_id)
        .group_by(UserWordList.band)
    )
    counts = {band: 0 for band in norm.BANDS}
    for band, n in rows:
        if band in counts:
            counts[band] = n
    return {"total": sum(counts.values()), "bands": counts}


@router.post("/list", status_code=status.HTTP_201_CREATED)
async def add_word(
    body: AddWordIn,
    principal: Principal = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Put a word on the learning list, snapshotting it for cheap rendering.

    Idempotent: adding a word twice refreshes the snapshot instead of failing,
    so a double click (or a retry from the future extension) is harmless.
    """
    lemma = body.lemma.strip()
    card = await db.get(VocabCard, lemma)
    if not card:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "unknown word")

    values = {
        "user_id": principal.user_id,
        "lemma": card.lemma,
        "ru": card.ru,
        "level": card.level,
        "band": card.band,
        "pos": card.pos,
        "article": card.article,
        "topic": card.topic,
        "status": "learning",
    }
    stmt = pg_insert(UserWordList).values(values)
    await db.execute(
        stmt.on_conflict_do_update(
            constraint="uq_user_word_list",
            set_={k: stmt.excluded[k] for k in
                  ("ru", "level", "band", "pos", "article", "topic")},
        )
    )
    await db.commit()

    row = (
        await db.execute(
            select(UserWordList).where(
                UserWordList.user_id == principal.user_id,
                UserWordList.lemma == lemma,
            )
        )
    ).scalar_one()
    return _list_item(row)


@router.delete("/list/{lemma:path}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_word(
    lemma: str,
    principal: Principal = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(UserWordList).where(
            UserWordList.user_id == principal.user_id,
            UserWordList.lemma == lemma.strip(),
        )
    )
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── mirror ───────────────────────────────────────────────────────────────────
@router.post("/mirror/sync")
async def mirror_sync(
    principal: Principal = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Pull newly enriched cards into the searchable replica.

    Runs on a timer too (see `mirror.periodic_sync`); this is the manual nudge
    for when you don't want to wait for the next pass.
    """
    result = await mirror.sync_cards(db)
    if not result.get("ok"):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            result.get("reason", "sync unavailable"))
    return result

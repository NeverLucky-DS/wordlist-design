"""Incremental replica: enrichment.db (SQLite) → Postgres `vocab_cards`.

Why a replica exists at all: the enrichment worker owns `enrichment.db` as its
durable scratch space and writes to it around the clock — we must not disturb
it. But fuzzy search (pg_trgm) and the personal word list have to be queryable
*together*, in one database. So finished cards are copied across incrementally.
Nothing here ever writes back to SQLite; it is opened read-only.

The cursor is the `(created_at, lemma)` pair of the last copied row. `save_cards`
persists with INSERT OR REPLACE and a fresh `created_at`, so a re-enriched card
moves to the end of the cursor order and is picked up again — updates ride the
same path as inserts, and no separate change feed is needed.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import VocabCard, VocabCardTranslation
from app.vocab import norm

logger = logging.getLogger(__name__)

SYNC_BATCH = 2000       # cards per round trip
SYNC_INTERVAL = 300.0   # s between background passes — enrichment adds ~1k/10min
_MAX_RU_CHARS = 255     # matches the column; longer meanings are noise anyway


# ── SQLite side (sync, read-only) ────────────────────────────────────────────
def _read_since(after_ts: float, after_lemma: str, limit: int) -> list[dict]:
    """Cards strictly after the `(created_at, lemma)` cursor, in cursor order.

    Row-value comparison keeps the pass terminating even though a whole batch of
    cards shares one `created_at` (the worker stamps `time.time()` once per save).
    """
    from app.vocab.enrich import ENRICH_DB

    if not ENRICH_DB.exists():
        return []
    con = sqlite3.connect(f"file:{ENRICH_DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            "SELECT lemma, level, topic, pos, article, ru, confidence, register, "
            "       data, zipf, created_at "
            "FROM cards WHERE (created_at, lemma) > (?, ?) "
            "ORDER BY created_at, lemma LIMIT ?",
            (after_ts, after_lemma, limit),
        ).fetchall()
    finally:
        con.close()
    return [dict(r) for r in rows]


def _read_lemmas() -> set[str]:
    """Every lemma that currently has a card. Used to find rows the replica kept
    after the source dropped them."""
    from app.vocab.enrich import ENRICH_DB

    if not ENRICH_DB.exists():
        return set()
    con = sqlite3.connect(f"file:{ENRICH_DB}?mode=ro", uri=True)
    try:
        return {r[0] for r in con.execute("SELECT lemma FROM cards")}
    finally:
        con.close()


def _ru_meanings(row: dict) -> list[str]:
    """All Russian meanings of a card, most important first, deduped.

    `ru` is the promoted primary meaning and `ru_all` the full list; they usually
    agree, but the card is model output so neither is guaranteed present.
    """
    try:
        data = json.loads(row.get("data") or "{}")
    except json.JSONDecodeError:
        data = {}
    raw: list[Any] = data.get("ru_all") if isinstance(data.get("ru_all"), list) else []
    values = [str(v).strip()[:_MAX_RU_CHARS] for v in raw]
    primary = str(row.get("ru") or "").strip()[:_MAX_RU_CHARS]
    if primary:
        values.insert(0, primary)
    out: list[str] = []
    for v in values:
        if v and v not in out:
            out.append(v)
    return out


def _card_values(row: dict) -> dict:
    return {
        "lemma": row["lemma"],
        "lemma_norm": norm.fold_de(row["lemma"]),
        "lemma_ascii": norm.ascii_de(row["lemma"]),
        "level": (row.get("level") or "unlisted").lower(),
        "band": norm.band_of(row.get("level")),
        "topic": row.get("topic"),
        "pos": (row.get("pos") or "other").lower(),
        "article": row.get("article"),
        "ru": row.get("ru") or "",
        "confidence": row.get("confidence") or "high",
        "register": row.get("register"),
        "data": json.loads(row["data"]) if row.get("data") else {},
        "zipf": row.get("zipf"),
        "source_created_at": float(row.get("created_at") or 0.0),
    }


# ── Postgres side ────────────────────────────────────────────────────────────
def is_supported(db: AsyncSession) -> bool:
    """The replica only makes sense on Postgres — pg_trgm is the whole point."""
    try:
        return db.get_bind().dialect.name == "postgresql"
    except Exception:  # noqa: BLE001 — an unbound session is simply unsupported
        return False


async def _cursor(db: AsyncSession) -> tuple[float, str]:
    row = (
        await db.execute(
            select(VocabCard.source_created_at, VocabCard.lemma)
            .order_by(VocabCard.source_created_at.desc(), VocabCard.lemma.desc())
            .limit(1)
        )
    ).first()
    return (row[0], row[1]) if row else (0.0, "")


async def _write_batch(db: AsyncSession, rows: list[dict]) -> None:
    cards = [_card_values(r) for r in rows]
    stmt = pg_insert(VocabCard).values(cards)
    await db.execute(
        stmt.on_conflict_do_update(
            index_elements=[VocabCard.lemma],
            set_={
                c: stmt.excluded[c]
                for c in ("lemma_norm", "lemma_ascii", "level", "band", "topic",
                          "pos", "article", "ru", "confidence", "register", "data",
                          "zipf", "source_created_at")
            }
            | {"synced_at": func.now()},
        )
    )

    lemmas = [c["lemma"] for c in cards]
    # Re-enrichment can shrink `ru_all`, so replace the set rather than upsert it;
    # a stale idx would otherwise linger and pollute search.
    await db.execute(
        delete(VocabCardTranslation).where(VocabCardTranslation.lemma.in_(lemmas))
    )
    translations = [
        {"lemma": row["lemma"], "idx": i, "ru": ru, "ru_norm": norm.fold_ru(ru)}
        for row in rows
        for i, ru in enumerate(_ru_meanings(row))
    ]
    if translations:
        await db.execute(pg_insert(VocabCardTranslation).values(translations))


async def prune_orphans(db: AsyncSession) -> int:
    """Drop replica rows whose card no longer exists in the source.

    The sync is a forward cursor, so it can only ever add. Deletions do happen:
    a repair pass that the model answers with `skip` removes the card (the noun
    wrongly filed under "nacht"), and a pre-1996 lemma is re-filed under its
    modern spelling. Without this the replica would keep serving exactly the
    entries we just decided were wrong — permanently, since nothing would ever
    touch them again.

    Bails out if the source reads back empty: that means enrichment.db is missing
    or unreadable, and deleting "everything not in an empty set" would wipe the
    dictionary. A stale replica is recoverable; an empty one is an outage.
    """
    live = await asyncio.to_thread(_read_lemmas)
    if not live:
        return 0
    mirrored = {r[0] for r in (await db.execute(select(VocabCard.lemma))).all()}
    gone = sorted(mirrored - live)
    if not gone:
        return 0
    for i in range(0, len(gone), SYNC_BATCH):
        await db.execute(
            delete(VocabCard).where(VocabCard.lemma.in_(gone[i:i + SYNC_BATCH]))
        )
        await db.commit()
    logger.info("vocab mirror: pruned %d orphaned cards", len(gone))
    return len(gone)


async def sync_cards(db: AsyncSession, *, batch: int = SYNC_BATCH,
                     max_rows: int | None = None,
                     since: tuple[float, str] | None = None,
                     prune: bool = True) -> dict:
    """Copy new/updated cards across. Idempotent; safe to run concurrently
    with the enrichment worker (SQLite is read-only here).

    `since=(0.0, "")` replays every card instead of resuming from the watermark.
    Needed when a column is added or backfilled on the SQLite side: that does not
    move `created_at`, so the cursor would never revisit those rows. Upserts make
    the replay harmless, and search keeps serving throughout — no drop-and-rebuild.
    """
    if not is_supported(db):
        return {"ok": False, "reason": "mirror requires postgresql", "synced": 0}

    ts, lemma = since if since is not None else await _cursor(db)
    synced = 0
    while True:
        take = batch if max_rows is None else min(batch, max_rows - synced)
        if take <= 0:
            break
        rows = await asyncio.to_thread(_read_since, ts, lemma, take)
        if not rows:
            break
        await _write_batch(db, rows)
        await db.commit()
        synced += len(rows)
        ts, lemma = float(rows[-1]["created_at"] or 0.0), rows[-1]["lemma"]
        if len(rows) < take:
            break

    pruned = await prune_orphans(db) if prune else 0
    total = (await db.execute(select(func.count()).select_from(VocabCard))).scalar_one()
    return {"ok": True, "synced": synced, "pruned": pruned, "total": total}


async def full_resync() -> dict:
    """Replay every card into the replica on a session of our own.

    Used by the enrichment start-up once `plan_repairs` has backfilled `zipf` on
    cards that were written before the column existed — the cursor cannot see
    those, so ranking would stay broken until each card happened to be re-enriched.
    """
    from app.db.session import SessionLocal

    async with SessionLocal() as db:
        return await sync_cards(db, since=(0.0, ""))


async def periodic_sync(interval: float = SYNC_INTERVAL) -> None:
    """Keep the replica tracking the still-running enrichment.

    Syncs once on boot (so a fresh container serves a current dictionary), then
    every `interval`. Never lets a failure escape: a stale mirror only degrades
    search quality, whereas a crashed background task would be invisible and
    permanent.
    """
    from app.db.session import SessionLocal

    while True:
        try:
            async with SessionLocal() as db:
                if not is_supported(db):
                    return  # nothing to mirror onto — e.g. the SQLite test setup
                result = await sync_cards(db)
            if result.get("synced") or result.get("pruned"):
                logger.info("vocab mirror: +%d −%d cards (total %d)",
                            result["synced"], result["pruned"], result["total"])
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            logger.exception("vocab mirror sync failed; retrying next pass")
        await asyncio.sleep(interval)

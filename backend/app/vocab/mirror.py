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

from app.db.models import VocabCard, VocabCardTranslation, VocabForm
from app.vocab import inflect, norm

logger = logging.getLogger(__name__)

SYNC_BATCH = 2000       # cards per round trip
SYNC_INTERVAL = 300.0   # s between background passes — enrichment adds ~1k/10min
_MAX_RU_CHARS = 255     # matches the column; longer meanings are noise anyway

# The wire protocol caps a single statement at 2^15-1 bind parameters, and a
# multi-row INSERT spends one per column per row. Adding `form_kind`, `form_of`
# and `morphology` took the card insert from 14 columns to 17, and 17 × 2000
# crossed the line — the resync died with "the number of query arguments cannot
# exceed 32767" after the schema had already migrated. Deriving the chunk from
# the column count instead of hard-coding a smaller batch means the next column
# shrinks the chunk by itself rather than breaking production again.
_PG_MAX_PARAMS = 32767


def _chunks(rows: list[dict], columns: int):
    """Slices of `rows` that fit under the bind-parameter ceiling."""
    per_statement = max(1, _PG_MAX_PARAMS // max(columns, 1))
    for i in range(0, len(rows), per_statement):
        yield rows[i:i + per_statement]


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
        # LEFT JOIN, not a second pass: morphology is filled by an offline import
        # that does not touch `cards.created_at`, so the cursor would never
        # revisit a card to pick its paradigm up. Riding along on the card's own
        # row means a re-import is published by the same full resync as any other
        # in-place rewrite.
        # `level_est` is added by `levels.apply_estimates`, which may never have
        # run against this file — a fresh enrichment.db, or the fixtures the test
        # suite builds. Naming a missing column is a hard error in SQLite and
        # would take the whole mirror down, so ask the schema rather than assume.
        has_est = any(r[1] == "level_est"
                      for r in con.execute("PRAGMA table_info(cards)"))
        est = "c.level_est, " if has_est else "NULL AS level_est, "
        rows = con.execute(
            "SELECT c.lemma, c.level, " + est + "c.topic, c.pos, c.article, c.ru, "
            "       c.confidence, "
            "       c.register, c.data, c.zipf, c.form_kind, c.form_of, "
            "       m.data AS morphology, c.created_at "
            "FROM cards c "
            "LEFT JOIN morphology m ON m.lemma = c.lemma AND m.pos = c.pos "
            "WHERE (c.created_at, c.lemma) > (?, ?) "
            "ORDER BY c.created_at, c.lemma LIMIT ?",
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
        "level_est": (row.get("level_est") or None),
        "band": norm.band_of(row.get("level")),
        "topic": row.get("topic"),
        "pos": (row.get("pos") or "other").lower(),
        "article": row.get("article"),
        "ru": row.get("ru") or "",
        "confidence": row.get("confidence") or "high",
        "register": row.get("register"),
        "data": json.loads(row["data"]) if row.get("data") else {},
        "zipf": row.get("zipf"),
        "form_kind": row.get("form_kind"),
        "form_of": row.get("form_of"),
        "morphology": json.loads(row["morphology"]) if row.get("morphology") else None,
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
    for chunk in _chunks(cards, len(cards[0]) if cards else 1):
        stmt = pg_insert(VocabCard).values(chunk)
        await db.execute(
            stmt.on_conflict_do_update(
                index_elements=[VocabCard.lemma],
                set_={
                    c: stmt.excluded[c]
                    for c in ("lemma_norm", "lemma_ascii", "level", "level_est",
                              "band", "topic",
                              "pos", "article", "ru", "confidence", "register", "data",
                              "zipf", "form_kind", "form_of", "morphology",
                              "source_created_at")
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
    # Same ceiling: a card averages ~2.4 meanings, so this list runs well past
    # the card count even though it is only four columns wide.
    for chunk in _chunks(translations, 4):
        await db.execute(pg_insert(VocabCardTranslation).values(chunk))


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


async def rebuild_forms(db: AsyncSession) -> dict:
    """Regenerate `vocab_forms` from paradigms already in the replica.

    No new read of SQLite: `vocab_cards.morphology` is the same paradigm the
    `morphology` table holds, carried across by the card's own row. So this is a
    pure derivation from data we have, and it costs one pass over the mirror.

    Three filters decide what becomes an entry, and each one is load-bearing:

    * a form that already HAS a card of its own is dropped. `alle`, `aller` and
      `alles` are cards, and shadowing a real entry with a pointer to `all-`
      would answer a good query with a redirect.
    * a form equal to its own base is dropped — `dieser` generates `dieser`.
    * `inflect.is_blocked` keeps verb paradigms off the closed class. The German
      Wiktionary conjugates reflexives with the pronoun attached, so `mich`
      arrives as a "form" of 27 verbs (`besinnen`, `erholen`, `verlieben`); it is
      the accusative of `ich` and nothing else.

    Ambiguity is kept rather than resolved. `stand` is the Präteritum of `stehen`
    AND a present of `standhalten`; both rows stay, and search shows the base
    whose card ranks best. Choosing one here would be guessing with less
    information than the ranking already has.
    """
    if not is_supported(db):
        return {"ok": False, "reason": "mirror requires postgresql", "forms": 0}

    lemmas = {r[0] for r in (await db.execute(select(VocabCard.lemma))).all()}
    rows = (
        await db.execute(
            select(VocabCard.lemma, VocabCard.pos, VocabCard.morphology)
            .where(VocabCard.morphology.isnot(None))
        )
    ).all()

    index = inflect.index_rows((lemma, pos, para) for lemma, pos, para in rows)
    values: list[dict] = []
    seen: set[tuple[str, str]] = set()

    # The closed class is kept even when the form ALSO has a card of its own,
    # and that exception is the point. `einen` has a card — the rare verb "to
    # unite" — so a query for the accusative of `ein`, one of the commonest
    # words in German, answered "объединять". Same for `meinen`: the card is the
    # verb "to think". Dropping these on collision would leave exactly the lie
    # PLANS A1 measured. The card still wins the result list; the form link
    # rides alongside it as `form_of` and says what the reader actually typed.
    for form, record in inflect.CLOSED_CLASS.items():
        if record.base not in lemmas:
            continue
        seen.add((form, record.base))
        values.append({"form": form, "form_norm": norm.fold_de(form),
                       "base_lemma": record.base, "cell_de": record.cell_de[:96],
                       "cell_ru": record.cell_ru[:96], "ru": record.ru,
                       "pos": record.pos, "source": "closed"})

    for form, candidates in index.items():
        if form in lemmas:
            continue
        for record in candidates:
            key = (form, record.base)
            if key in seen or record.base not in lemmas:
                continue
            seen.add(key)
            values.append({"form": form, "form_norm": norm.fold_de(form),
                           "base_lemma": record.base, "cell_de": record.cell_de[:96],
                           "cell_ru": record.cell_ru[:96], "ru": "",
                           "pos": record.pos, "source": "paradigm"})

    await db.execute(delete(VocabForm))
    for chunk in _chunks(values, 9):
        await db.execute(pg_insert(VocabForm).values(chunk))
    await db.commit()
    logger.info("vocab mirror: rebuilt %d form links", len(values))
    return {"ok": True, "forms": len(values),
            "closed": sum(1 for v in values if v["source"] == "closed")}


async def full_resync() -> dict:
    """Replay every card into the replica on a session of our own.

    Used by the enrichment start-up once `plan_repairs` has backfilled `zipf` on
    cards that were written before the column existed — the cursor cannot see
    those, so ranking would stay broken until each card happened to be re-enriched.
    """
    from app.db.session import SessionLocal

    async with SessionLocal() as db:
        result = await sync_cards(db, since=(0.0, ""))
        result["forms"] = (await rebuild_forms(db)).get("forms", 0)
        return result


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
                # Only when something moved. The rebuild is a full table replace
                # of ~170 000 rows; running it every five minutes to discover
                # nothing changed would be the most expensive no-op in the app.
                if result.get("synced") or result.get("pruned"):
                    await rebuild_forms(db)
            if result.get("synced") or result.get("pruned"):
                logger.info("vocab mirror: +%d −%d cards (total %d)",
                            result["synced"], result["pruned"], result["total"])
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            logger.exception("vocab mirror sync failed; retrying next pass")
        await asyncio.sleep(interval)

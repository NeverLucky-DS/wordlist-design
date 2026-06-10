from __future__ import annotations

"""Step-3 DB cleanup. DRY-RUN by default; pass 'apply' to execute.

1. Merge duplicate topics into a canonical one (move links + phrases, dedupe).
2. Delete junk topics entirely.
3. Cap Redemittel (phrases) to <=10 per topic (balanced across essay parts).
4. Cap words to <=80 per topic — removing the MOST generic words first
   (those linked to the most other topics), which also de-inflates cross-linking
   and avoids orphaning topic-specific vocabulary.
5. Delete words left with zero topics (orphans).

    python scripts/cleanup_db.py            # dry-run report
    python scripts/cleanup_db.py apply      # execute
"""

import asyncio
import os
import sys
from collections import defaultdict

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import Phrase, Word, WordTopic

MERGES = {
    "migrationspolitik": "migration",
    "umwelt": "umweltschutz",
    "wissenschaft": "wissenschaft und ethik",
}
DELETE_TOPICS = ["technologie"]
PHRASE_CAP = 10
WORD_CAP = 80
ESSAY_PARTS = ("einleitung", "argument", "gegenargument", "beispiel", "schluss")


async def main(apply: bool) -> None:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    Session = async_sessionmaker(engine, expire_on_commit=False)
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"=== DB cleanup [{mode}] ===\n")

    async with Session() as db:
        # ---- 1. Merges ----------------------------------------------------
        for src, dst in MERGES.items():
            links = list((await db.execute(select(WordTopic).where(WordTopic.topic == src))).scalars())
            dst_word_ids = set((await db.execute(
                select(WordTopic.word_id).where(WordTopic.topic == dst))).scalars())
            moved = sum(1 for l in links if l.word_id not in dst_word_ids)
            ph = list((await db.execute(select(Phrase).where(Phrase.topic == src))).scalars())
            dst_ph = set((await db.execute(
                select(Phrase.text_de).where(Phrase.topic == dst))).scalars())
            ph_moved = sum(1 for p in ph if p.text_de not in dst_ph)
            print(f"MERGE  {src!r} → {dst!r}: {len(links)} links ({moved} new), "
                  f"{len(ph)} phrases ({ph_moved} new)")
            if apply:
                for l in links:
                    if l.word_id in dst_word_ids:
                        await db.delete(l)
                    else:
                        l.topic = dst
                        dst_word_ids.add(l.word_id)
                for p in ph:
                    if p.text_de in dst_ph:
                        await db.delete(p)
                    else:
                        p.topic = dst
                        dst_ph.add(p.text_de)
        if apply:
            await db.commit()

        # ---- 2. Junk topic deletion --------------------------------------
        for t in DELETE_TOPICS:
            nlinks = await db.scalar(select(func.count(WordTopic.id)).where(WordTopic.topic == t))
            nph = await db.scalar(select(func.count(Phrase.id)).where(Phrase.topic == t))
            print(f"DELETE topic {t!r}: {nlinks} links, {nph} phrases removed")
            if apply:
                await db.execute(delete(WordTopic).where(WordTopic.topic == t))
                await db.execute(delete(Phrase).where(Phrase.topic == t))
        if apply:
            await db.commit()

        # ---- 3. Phrase cap ------------------------------------------------
        print()
        topics = list((await db.execute(select(Phrase.topic).distinct())).scalars())
        ph_deleted = 0
        for t in topics:
            if not t:
                continue
            rows = list((await db.execute(select(Phrase).where(Phrase.topic == t))).scalars())
            if len(rows) <= PHRASE_CAP:
                continue
            # balanced keep: round-robin across essay parts
            by_part = defaultdict(list)
            for p in rows:
                by_part[p.essay_part or "argument"].append(p)
            keep, idx = [], 0
            parts = list(by_part.keys())
            while len(keep) < PHRASE_CAP and any(by_part[p] for p in parts):
                part = parts[idx % len(parts)]
                if by_part[part]:
                    keep.append(by_part[part].pop(0))
                idx += 1
            keep_ids = {p.id for p in keep}
            drop = [p for p in rows if p.id not in keep_ids]
            ph_deleted += len(drop)
            print(f"PHRASE cap {t!r}: {len(rows)} → {PHRASE_CAP}  (drop {len(drop)})")
            if apply:
                for p in drop:
                    await db.delete(p)
        print(f"  total phrases dropped: {ph_deleted}")
        if apply:
            await db.commit()

        # ---- 4. Word cap (drop most-generic first) ------------------------
        print()
        # how many topics each word belongs to
        topic_count: dict[int, int] = dict((await db.execute(
            select(WordTopic.word_id, func.count(WordTopic.id)).group_by(WordTopic.word_id))).all())
        word_topics = defaultdict(list)
        for l in (await db.execute(select(WordTopic))).scalars():
            word_topics[l.topic].append(l)
        links_dropped = 0
        for t, links in word_topics.items():
            if len(links) <= WORD_CAP:
                continue
            # most generic (highest other-topic count) removed first
            links_sorted = sorted(links, key=lambda l: topic_count.get(l.word_id, 1), reverse=True)
            drop = links_sorted[:len(links) - WORD_CAP]
            links_dropped += len(drop)
            print(f"WORD cap {t!r}: {len(links)} → {WORD_CAP}  (drop {len(drop)})")
            if apply:
                for l in drop:
                    topic_count[l.word_id] = topic_count.get(l.word_id, 1) - 1
                    await db.delete(l)
        print(f"  total word-links dropped: {links_dropped}")
        if apply:
            await db.commit()

        # ---- 5. Orphan words ---------------------------------------------
        print()
        orphan_ids = list((await db.execute(
            select(Word.id).outerjoin(WordTopic, WordTopic.word_id == Word.id)
            .where(WordTopic.id.is_(None)))).scalars())
        print(f"ORPHAN words (0 topics): {len(orphan_ids)}"
              + (" — deleting" if apply else " — would delete"))
        if apply and orphan_ids:
            await db.execute(delete(Word).where(Word.id.in_(orphan_ids)))
            await db.commit()

    print(f"\n=== {mode} done ===")


if __name__ == "__main__":
    asyncio.run(main(apply=(len(sys.argv) > 1 and sys.argv[1] == "apply")))

from __future__ import annotations

"""Trial: enrich ONE topic's words with LLM content + verification.

Grammar/IPA already come from the Wiktionary backfill. This adds the "expensive"
half for the words of a single topic:
  - German definition (Bedeutung), ru translation, rektion, ready_phrase,
  - examples with Russian translations,
  - a per-word verification pass that fixes/flags each entry.

Usage (inside backend container, MISTRAL_API_KEY in env):
    python scripts/reprocess_topic.py datenschutz
"""

import asyncio
import json
import os
import re
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models import Word, WordFailure, WordTopic
from app.pipeline.content_llm import generate_content
from app.pipeline.verify import verify_words
from scripts.backfill_grammar import _fetch_wikitext_batch

POS_HINT = {"noun": "Noun", "verb": "Verb", "adjective": "Adjective", "other": "Other"}


def _extract_bedeutungen(wikitext: str) -> str:
    m = re.search(r"\{\{Bedeutungen\}\}\n((?::\[\d+\][^\n]*\n?){1,8})", wikitext)
    if not m:
        return ""
    raw = m.group(1)
    raw = re.sub(r"\{\{[^}]*\}\}", "", raw)            # drop templates
    raw = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]", r"\1", raw)  # links → text
    raw = re.sub(r":\[\d+\]\s*", "", raw)              # sense markers
    raw = raw.replace("'''", "").replace("''", "")
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    return " | ".join(lines[:4])


def _chunk(items, n):
    return [items[i:i + n] for i in range(0, len(items), n)]


async def main(topic: str) -> None:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    Session = async_sessionmaker(engine, expire_on_commit=False)
    key, model = settings.mistral_api_key, settings.mistral_model

    async with Session() as db:
        rows = list((await db.execute(
            select(Word.id, Word.german, Word.word_type, Word.article, Word.examples)
            .join(WordTopic, WordTopic.word_id == Word.id)
            .where(WordTopic.topic == topic)
        )).all())
    print(f"topic '{topic}': {len(rows)} words", flush=True)
    if not rows:
        return

    # fetch Bedeutungen (batched, single-word lemmas only)
    titles = [r.german.strip() for r in rows if " " not in r.german.strip()]
    wt_map: dict[str, str] = {}
    for batch in _chunk(titles, 50):
        wt_map.update(await asyncio.to_thread(_fetch_wikitext_batch, batch))

    stats = {"written": 0, "fixed": 0, "failed": 0}

    for batch in _chunk(rows, 6):
        # build content input
        inp = []
        for r in batch:
            src_ex = [(e.get("text_de") if isinstance(e, dict) else str(e)) for e in (r.examples or [])]
            inp.append({
                "word": r.german,
                "pos": POS_HINT.get(r.word_type, "Other"),
                "article": r.article,
                "definitions": _extract_bedeutungen(wt_map.get(r.german.strip(), "")),
                "examples": [x for x in src_ex if x][:3],
            })
        try:
            content = await asyncio.to_thread(generate_content, inp, key, model)
        except Exception as exc:
            print("  content failed:", exc, flush=True)
            content = {}

        # assemble entries for verification
        entries, assembled = [], {}
        async with Session() as db:
            for r in batch:
                c = content.get(r.german.strip().lower())
                if not c:
                    continue
                w = await db.get(Word, r.id)
                gd = dict(w.grammar_data or {})
                a = {
                    "id": r.id, "word": r.german, "pos": r.word_type, "article": r.article,
                    "ru": c["ru"] or w.translation_ru,
                    "definition": c["definition"],
                    "rektion": c["rektion"],
                    "ready_phrase": c["ready_phrase"],
                    "declension": gd.get("declension") or {},
                    "examples": c["examples"] or (w.examples or []),
                }
                assembled[r.german.strip().lower()] = a
                entries.append(a)

        # verify
        try:
            checks = await asyncio.to_thread(verify_words, entries, key, model)
        except Exception as exc:
            print("  verify failed:", exc, flush=True)
            checks = {}

        # apply + write
        async with Session() as db:
            for key_l, a in assembled.items():
                chk = checks.get(key_l, {"ok": True, "issues": [], "fix": {}})
                fix = chk.get("fix", {})
                ru = fix.get("ru") or a["ru"]
                definition = fix.get("definition") or a["definition"]
                rektion = fix.get("rektion", a["rektion"])
                article = fix.get("article") or a["article"]
                if chk.get("fix"):
                    stats["fixed"] += 1

                if not ru.strip() or not definition.strip():
                    db.add(WordFailure(
                        word=a["word"], topic=topic, pos=POS_HINT.get(a["pos"], "Other"),
                        article=a["article"], examples=[],
                        stage="verify", error="; ".join(chk.get("issues") or ["leeres Pflichtfeld"]),
                    ))
                    stats["failed"] += 1
                    continue

                w = await db.get(Word, a["id"])
                gd = dict(w.grammar_data or {})
                gd["definition"] = definition
                gd["rektion"] = rektion
                gd["ready_phrase"] = a["ready_phrase"]
                w.grammar_data = gd
                w.translation_ru = ru
                if article in ("der", "die", "das"):
                    w.article = article
                if a["examples"]:
                    w.examples = a["examples"]
                w.source = "pipeline_v4"
                stats["written"] += 1
            await db.commit()
        print(f"  batch done — {json.dumps(stats)}", flush=True)

    print("DONE", json.dumps(stats, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    topic = (sys.argv[1] if len(sys.argv) > 1 else "datenschutz").strip().lower()
    asyncio.run(main(topic))

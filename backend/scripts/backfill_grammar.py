from __future__ import annotations

"""One-off maintenance: refresh every word's grammar from de.wiktionary.org.

Free (no LLM). For each word:
- fetch raw wikitext (BATCHED: up to 50 titles per API call via action=query, so
  ~37 requests for the whole DB instead of ~1800 — stays well under Wikimedia's
  rate limit; bursts of per-word requests get 429'd),
- parse the Übersicht template + Lautschrift,
- replace `grammar_data.declension` with the authoritative table
  (merged so verb wir/ihr/sie from the old LLM data are preserved),
- set `grammar_data.ipa`, fix the noun article.

definition / rektion / ready_phrase are left untouched.

Run inside the backend container:
    docker exec -e PYTHONPATH=/app -w /app <backend> python scripts/backfill_grammar.py
"""

import asyncio
import json
import os
import time

import requests
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import Word
from app.pipeline.grammar_schema import merge_declension
from app.pipeline.wiktionary_grammar import parse_grammar

WIKI = "https://de.wiktionary.org/w/api.php"
# Wikimedia asks for a descriptive UA with contact info; bursts/anon UAs get 429'd.
UA = "DeutschEssayWoerterbuch/1.0 (educational project; contact: yondo565@gmail.com)"
BATCH = 50          # titles per query request (API max for non-bots)
PAUSE = 0.6         # seconds between requests — polite, avoids 429


def _fetch_wikitext_batch(titles: list[str], _tries: int = 4) -> dict[str, str]:
    """Return {requested_title: wikitext} for up to 50 titles in one request."""
    params = {
        "action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
        "format": "json", "redirects": "1", "titles": "|".join(titles),
    }
    for attempt in range(_tries):
        try:
            r = requests.get(WIKI, params=params, headers={"User-Agent": UA}, timeout=40)
        except Exception:
            time.sleep(2 * (attempt + 1))
            continue
        if r.status_code == 429:
            wait = float(r.headers.get("Retry-After", 5) or 5)
            time.sleep(min(wait, 30) + 1)
            continue
        if r.status_code != 200:
            time.sleep(2)
            continue
        try:
            data = r.json()
        except Exception:
            return {}
        q = data.get("query", {})
        norm = {n["from"]: n["to"] for n in q.get("normalized", [])}
        redir = {x["from"]: x["to"] for x in q.get("redirects", [])}
        title_wt: dict[str, str] = {}
        for p in q.get("pages", {}).values():
            title = p.get("title", "")
            if "missing" in p:
                title_wt[title] = ""
                continue
            revs = p.get("revisions", [])
            wt = ""
            if revs:
                slot = revs[0].get("slots", {}).get("main", {})
                wt = slot.get("*", "") or revs[0].get("*", "")
            title_wt[title] = wt
        out: dict[str, str] = {}
        for t in titles:
            final = redir.get(norm.get(t, t), norm.get(t, t))
            out[t] = title_wt.get(final, "")
        return out
    return {t: "" for t in titles}


def _chunk(items, n):
    return [items[i:i + n] for i in range(0, len(items), n)]


async def main() -> None:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        words = list((await db.execute(select(Word.id, Word.german, Word.word_type))).all())
    print(f"words: {len(words)}", flush=True)

    stats = {"declension_updated": 0, "article_fixed": 0, "ipa_set": 0,
             "no_page": 0, "multiword_skip": 0, "pos_mismatch": 0}

    # single-word lemmas only (compounds with spaces have no Wiktionary page)
    targets = [(wid, g, wt) for (wid, g, wt) in words if " " not in g.strip()]
    stats["multiword_skip"] = len(words) - len(targets)

    grammar_by_id: dict[int, object] = {}
    batches = _chunk(targets, BATCH)
    for bi, batch in enumerate(batches):
        title_to_ids: dict[str, list[int]] = {}
        for wid, german, _wt in batch:
            title_to_ids.setdefault(german.strip(), []).append(wid)
        wt_map = await asyncio.to_thread(_fetch_wikitext_batch, list(title_to_ids.keys()))
        for title, ids in title_to_ids.items():
            wt = wt_map.get(title, "")
            if not wt:
                stats["no_page"] += len(ids)
                continue
            g = parse_grammar(wt)
            for wid in ids:
                grammar_by_id[wid] = g
        if (bi + 1) % 10 == 0:
            print(f"  ...{(bi + 1) * BATCH}/{len(targets)} fetched", flush=True)
        time.sleep(PAUSE)

    async with Session() as db:
        for wid, g in grammar_by_id.items():
            w = await db.get(Word, wid)
            if not w:
                continue
            gd = dict(w.grammar_data or {})
            if g.ipa and gd.get("ipa") != g.ipa:
                gd["ipa"] = g.ipa
                stats["ipa_set"] += 1
            if g.pos == "noun" and g.article and w.article != g.article:
                w.article = g.article
                stats["article_fixed"] += 1
            if g.declension and g.pos == w.word_type:
                gd["declension"] = merge_declension(g.declension, gd.get("declension") or {}, w.word_type)
                stats["declension_updated"] += 1
            elif g.pos and w.word_type in ("noun", "verb", "adjective") and g.pos != w.word_type:
                stats["pos_mismatch"] += 1
            w.grammar_data = gd
        await db.commit()

    print(json.dumps(stats, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    asyncio.run(main())

"""Deterministic ingestion run: dictionaries -> SQLite (stage [1]-[3] w/o LLM).

- reads every configured source once,
- general sources define coverage; enrichment sources only augment existing lemmas,
- keeps a per-source breakdown so we can inspect what each dictionary contributed,
- ranks with wordfreq and assigns a CEFR-ish level by frequency rank,
- writes backend/app/vocab/vocab.db.

Callable as a background job via run_build(progress=...); CLI prints the same
milestones.  CLI:  MIN_ZIPF=2.3 ./.venv/bin/python backend/app/vocab/build.py
"""
from __future__ import annotations

import bisect
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # backend/ on path

import wordfreq

from app.vocab import readers
from app.vocab.sources import SOURCES

DB_PATH = Path(os.environ.get("VOCAB_DB") or Path(__file__).with_name("vocab.db"))
IS_WORD = re.compile(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß\-]+\Z")

# level bands by frequency rank (heuristic until Goethe lists are wired in)
BANDS = [("b1_core", 2500), ("b2_core", 6000), ("c1_core", 12000)]


def level_for(rank: int) -> str:
    for name, upper in BANDS:
        if rank <= upper:
            return name
    return "extended"


def merge(agg: dict, key: str, src_key: str, can_create: bool, contrib: dict) -> None:
    rec = agg.get(key)
    if rec is None:
        if not can_create:
            return  # enrichment sources never mint a new headword
        rec = agg[key] = {"by_source": {}}
    bs = rec["by_source"].setdefault(src_key, {})
    for field, val in contrib.items():
        if val is None:
            continue
        if isinstance(val, list):
            bs.setdefault(field, [])
            for v in val:
                if v and v not in bs[field]:
                    bs[field].append(v)
        else:
            bs.setdefault(field, val)


def collapse(rec: dict) -> dict:
    out = {"article": None, "forms": [], "pos": [], "translations": [],
           "examples": [], "synonyms": [], "collocations": [], "idioms": []}
    for bs in rec["by_source"].values():
        if bs.get("article") and not out["article"]:
            out["article"] = bs["article"]
        for f in ("forms", "pos", "translations", "examples",
                  "synonyms", "collocations", "idioms"):
            for v in bs.get(f, []):
                if v not in out[f]:
                    out[f].append(v)
    out["translations"] = out["translations"][:20]
    out["examples"] = out["examples"][:12]
    return out


def run_build(min_zipf: float = 0.0, db_path: Path = DB_PATH, progress=None) -> dict:
    """Full ingestion. `progress(event: dict)` is called at each milestone."""
    emit = progress or (lambda e: None)
    t0 = time.time()
    agg: dict[str, dict] = {}

    emit({"stage": "start", "sources": [s.key for s in SOURCES]})
    for phase_cov in (True, False):
        for src in SOURCES:
            if src.coverage != phase_cov:
                continue
            n, ts = 0, time.time()
            try:
                for key, contrib in readers.iter_source(src):
                    merge(agg, key, src.key, src.coverage, contrib)
                    n += 1
            except Exception as e:
                emit({"stage": "source_error", "source": src.key, "error": str(e)})
            emit({"stage": "source", "source": src.key, "role": src.role,
                  "coverage": src.coverage, "entries": n, "agg": len(agg),
                  "secs": round(time.time() - ts, 1)})

    emit({"stage": "aggregate_done", "agg": len(agg), "secs": round(time.time() - t0, 1)})

    rows = []
    for lemma, rec in agg.items():
        if not IS_WORD.match(lemma):
            continue
        merged = collapse(rec)
        if not merged["translations"]:
            continue
        z = wordfreq.zipf_frequency(lemma, "de")
        if z <= 0:
            continue
        rows.append((lemma, z, merged, rec["by_source"]))

    zs = sorted(r[1] for r in rows)
    hist = {str(thr): len(zs) - bisect.bisect_left(zs, thr)
            for thr in (1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5)}
    emit({"stage": "coverage", "count": len(rows), "hist": hist})

    if min_zipf > 0:
        rows = [r for r in rows if r[1] >= min_zipf]
        emit({"stage": "cap", "min_zipf": min_zipf, "kept": len(rows)})
    rows.sort(key=lambda r: r[1], reverse=True)

    db_path.unlink(missing_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("""CREATE TABLE words(
        id INTEGER PRIMARY KEY, lemma TEXT UNIQUE, article TEXT, pos TEXT,
        forms TEXT, translations TEXT, examples TEXT, synonyms TEXT,
        collocations TEXT, idioms TEXT, sources TEXT, by_source TEXT,
        zipf REAL, freq_rank INTEGER, level TEXT)""")
    emit({"stage": "writing", "total": len(rows)})
    for rank, (lemma, z, m, by_source) in enumerate(rows, 1):
        con.execute(
            "INSERT INTO words(lemma,article,pos,forms,translations,examples,"
            "synonyms,collocations,idioms,sources,by_source,zipf,freq_rank,level)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (lemma, m["article"], json.dumps(m["pos"], ensure_ascii=False),
             json.dumps(m["forms"], ensure_ascii=False),
             json.dumps(m["translations"], ensure_ascii=False),
             json.dumps(m["examples"], ensure_ascii=False),
             json.dumps(m["synonyms"], ensure_ascii=False),
             json.dumps(m["collocations"], ensure_ascii=False),
             json.dumps(m["idioms"], ensure_ascii=False),
             json.dumps(sorted(by_source), ensure_ascii=False),
             json.dumps(by_source, ensure_ascii=False),
             z, rank, level_for(rank)))
        if rank % 5000 == 0:
            emit({"stage": "writing", "total": len(rows), "written": rank})
    con.execute("CREATE INDEX ix_level ON words(level)")
    con.execute("CREATE INDEX ix_lemma ON words(lemma)")
    con.commit()

    def c(where=""):
        return con.execute("SELECT COUNT(*) FROM words " + where).fetchone()[0]
    summary = {
        "total": c(), "secs": round(time.time() - t0, 1),
        "levels": {lvl: c("WHERE level='%s'" % lvl)
                   for lvl in ("b1_core", "b2_core", "c1_core", "extended")},
        "obligatory": c("WHERE level IN ('b1_core','b2_core')"),
        "with_article": c("WHERE article IS NOT NULL"),
        "with_examples": c("WHERE examples!='[]'"),
        "with_synonyms": c("WHERE synonyms!='[]'"),
        "with_idioms": c("WHERE idioms!='[]'"),
    }
    con.close()
    emit({"stage": "done", "summary": summary})
    return summary


def main() -> None:
    def show(e):
        print("  " + json.dumps(e, ensure_ascii=False)[:160])
    summary = run_build(float(os.environ.get("MIN_ZIPF", "0")), progress=show)
    print("\n=== STORED %d in %.1fs | obligatory=%d ===" % (
        summary["total"], summary["secs"], summary["obligatory"]))


if __name__ == "__main__":
    main()

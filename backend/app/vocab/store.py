"""Read helpers over vocab.db for the dashboard API."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("VOCAB_DB") or Path(__file__).with_name("vocab.db"))

_JSON_FIELDS = ("pos", "forms", "translations", "examples",
                "synonyms", "collocations", "idioms", "sources", "by_source")


def _conn(db_path: Path) -> sqlite3.Connection | None:
    if not Path(db_path).exists():
        return None
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con


def _card(row: sqlite3.Row) -> dict:
    d = dict(row)
    for f in _JSON_FIELDS:
        if f in d and isinstance(d[f], str):
            try:
                d[f] = json.loads(d[f])
            except json.JSONDecodeError:
                d[f] = []
    return d


def stats(db_path: Path = DB_PATH) -> dict:
    con = _conn(db_path)
    if con is None:
        return {"exists": False, "total": 0}

    def c(where=""):
        return con.execute("SELECT COUNT(*) FROM words " + where).fetchone()[0]

    out = {
        "exists": True,
        "total": c(),
        "levels": {lvl: c("WHERE level='%s'" % lvl)
                   for lvl in ("b1_core", "b2_core", "c1_core", "extended")},
        "obligatory": c("WHERE level IN ('b1_core','b2_core')"),
        "fields": {
            "article": c("WHERE article IS NOT NULL"),
            "examples": c("WHERE examples!='[]'"),
            "synonyms": c("WHERE synonyms!='[]'"),
            "idioms": c("WHERE idioms!='[]'"),
            "collocations": c("WHERE collocations!='[]'"),
        },
        "sources": {},
    }
    for key in ("universal", "langenscheidt", "lein", "allgemein",
                "advanced", "duden_syn", "collocations", "idioms"):
        out["sources"][key] = c("WHERE sources LIKE '%\"" + key + "\"%'")
    con.close()
    return out


def search(q: str = "", level: str = "", limit: int = 40,
           db_path: Path = DB_PATH) -> list[dict]:
    con = _conn(db_path)
    if con is None:
        return []
    where, params = [], []
    if q:
        where.append("lemma LIKE ?")
        params.append(q + "%")
    if level:
        where.append("level = ?")
        params.append(level)
    sql = "SELECT * FROM words"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY freq_rank LIMIT ?"
    params.append(min(limit, 200))
    rows = [_card(r) for r in con.execute(sql, params).fetchall()]
    con.close()
    return rows


def get(lemma: str, db_path: Path = DB_PATH) -> dict | None:
    con = _conn(db_path)
    if con is None:
        return None
    row = con.execute("SELECT * FROM words WHERE lemma=?", (lemma,)).fetchone()
    con.close()
    return _card(row) if row else None

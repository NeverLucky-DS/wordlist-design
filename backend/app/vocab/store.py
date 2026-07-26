"""Read helpers over vocab.db for the dashboard API."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from app.vocab import goethe

DB_PATH = Path(os.environ.get("VOCAB_DB") or Path(__file__).with_name("vocab.db"))

_JSON_FIELDS = ("pos", "forms", "translations", "examples",
                "synonyms", "collocations", "idioms", "sources", "by_source")


def _conn(db_path: Path) -> sqlite3.Connection | None:
    """Соединение с `vocab.db` — или None, если базы фактически нет.

    «Фактически» — это не только отсутствие файла. Рядом с боевыми БД в
    `app/vocab/vocab_data/` лежат пустышки `app/vocab/vocab.db`, и путь по
    умолчанию (вне контейнера `VOCAB_DB` не задан никогда) резолвится именно в
    них — ловушка, уже описанная в CRITICAL-LINKS §6a. Файл при этом
    существует, а таблицы `words` в нём нет, и `stats`/`search`/`get` роняли
    наружу `sqlite3.OperationalError: no such table: words` — то есть 500 там,
    где задумано `{"exists": false}` / `[]` / `None`. Воспроизведено
    Schemathesis 2026-07-26 на `/api/vocab/words`, `/word/{lemma}`, `/stats`.
    """
    if not Path(db_path).exists():
        return None
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    has_words = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='words'"
    ).fetchone()
    if not has_words:
        con.close()
        return None
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

    obligatory = ",".join(f"'{lvl}'" for lvl in goethe.OBLIGATORY)
    out = {
        "exists": True,
        "total": c(),
        "levels": {lvl: c(f"WHERE level='{lvl}'") for lvl in goethe.ALL_LEVELS},
        "obligatory": c(f"WHERE level IN ({obligatory})"),
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

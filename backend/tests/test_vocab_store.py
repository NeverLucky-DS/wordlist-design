"""Чтение `vocab.db` для ops-панели — и то, что бывает вместо базы.

`VOCAB_DB` по умолчанию указывает на пустышку `app/vocab/vocab.db`, лежащую
рядом с боевой базой: вне контейнера переменная не задана никогда. Это уже
описанная ловушка (CRITICAL-LINKS §6a), и `store` попадал в неё хуже прочих —
файл существует, значит соединение открывается, а таблицы `words` в нём нет, и
`sqlite3.OperationalError: no such table: words` уходил наружу нетронутым.
Ручки `/api/vocab/stats`, `/words`, `/word/{lemma}` отвечали на это 500.
Найдено Schemathesis 2026-07-26.

Задуманный ответ на «базы нет» тут уже был — `{"exists": False}`, `[]`, `None`.
Файл без схемы теперь считается тем же самым «базы нет».
"""
from __future__ import annotations

import sqlite3

from app.vocab import store


def _empty_db(tmp_path):
    """Файл есть, схемы нет — ровно то, чем оказывается пустышка."""
    path = tmp_path / "vocab.db"
    sqlite3.connect(path).close()
    assert path.exists()
    return path


def test_stats_on_a_schemaless_file_reports_absent(tmp_path):
    assert store.stats(db_path=_empty_db(tmp_path)) == {"exists": False, "total": 0}


def test_search_on_a_schemaless_file_returns_nothing(tmp_path):
    assert store.search(q="Haus", db_path=_empty_db(tmp_path)) == []


def test_get_on_a_schemaless_file_returns_none(tmp_path):
    assert store.get("Haus", db_path=_empty_db(tmp_path)) is None


def test_a_real_schema_is_still_read(tmp_path):
    """Страховка на сам фикс: проверка наличия таблицы не должна глушить базу,
    в которой таблица есть."""
    path = tmp_path / "vocab.db"
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE words (lemma TEXT PRIMARY KEY, article TEXT, pos TEXT, "
        "level TEXT, zipf REAL, freq_rank INTEGER, translations TEXT, "
        "examples TEXT, synonyms TEXT, idioms TEXT, collocations TEXT, sources TEXT)"
    )
    con.execute(
        "INSERT INTO words VALUES ('Haus', 'das', '[\"noun\"]', 'a1', 5.5, 1, "
        "'[]', '[]', '[]', '[]', '[]', '[]')"
    )
    con.commit()
    con.close()

    assert store.stats(db_path=path)["exists"] is True
    assert [row["lemma"] for row in store.search(q="Haus", db_path=path)] == ["Haus"]

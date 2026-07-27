"""Read-only MCP-сервер над золотыми SQLite — проверка, что он именно read-only.

`scripts/mcp/sqlite_ro.py` даёт запросный доступ к `enrichment.db` и `vocab.db`.
Эти два файла невосстановимы: `vocab.db` содержит июльский интейк на 19 152
слова, которого нет ни в одном бэкапе, а `enrichment.db` — 92 090 оплаченных
карточек. Плюс воркер обогащения пишет в `enrichment.db` круглосуточно, и
читатель, способный взять write-lock, обрывает прогон, идущий часами.

Read-only держат четыре независимых слоя, и тесты бьют по каждому отдельно —
иначе нельзя заметить, что три из них отвалились, пока четвёртый прикрывает:

  1. URI открывает файл `mode=ro`;
  2. `PRAGMA query_only`;
  3. authorizer отклоняет всё, что не чтение (единственный, кто ловит ATTACH);
  4. гейт по первому слову — только SELECT/WITH/EXPLAIN.

Отдельно закреплена асимметрия режимов открытия. Проблема A4 из `info/PLANS.md`
описана там как свойство файла («`vocab.db` не открывается голым `mode=ro`») —
на самом деле это свойство версии SQLite, и оба возможных исхода для золотой
базы плохи: 3.51.0 отказывает с SQLITE_CANTOPEN(14), 3.53.1 открывает, создавая
рядом `-shm` и `-wal`. Отсюда `immutable=1` — единственный режим, который и
работает везде, и не оставляет следов.

Большая часть тестов работает на временных базах, поэтому идёт и в CI, где
золотых файлов нет (они gitignored, 320 МБ на двоих). Те, что требуют настоящих
баз, помечены и пропускаются.
"""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SERVER = REPO / "scripts" / "mcp" / "sqlite_ro.py"


def _load():
    spec = importlib.util.spec_from_file_location("sqlite_ro", SERVER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["sqlite_ro"] = module
    spec.loader.exec_module(module)
    return module


mod = pytest.importorskip("sqlite_ro") if "sqlite_ro" in sys.modules else _load()


# ── фикстуры: две крошечные базы вместо золотых ────────────────────────────
@pytest.fixture
def golden(tmp_path, monkeypatch):
    enrich = tmp_path / "enrichment.db"
    con = sqlite3.connect(enrich)
    con.execute("CREATE TABLE cards (lemma TEXT PRIMARY KEY, ru TEXT, data TEXT, zipf REAL)")
    con.executemany(
        "INSERT INTO cards VALUES (?,?,?,?)",
        [
            ("Morgen", "утро", "x" * 500, 5.1),
            ("morgen", "завтра", "y" * 500, 5.1),
            ("Haus", "дом; здание", "z" * 500, 4.9),
        ],
    )
    con.commit()
    con.close()

    vocab = tmp_path / "vocab.db"
    con = sqlite3.connect(vocab)
    con.execute("CREATE TABLE words (lemma TEXT PRIMARY KEY, sources TEXT)")
    con.executemany(
        "INSERT INTO words VALUES (?,?)",
        [("Morgen", '["duden"]'), ("morgen", '["duden"]'), ("Haus", '["wiktionary"]')],
    )
    con.commit()
    con.close()

    g = mod.Golden(enrich, vocab, {})
    monkeypatch.setattr(mod, "GOLDEN", g)
    yield g
    if g._con is not None:
        g._con.close()


# ── слой 4: гейт по первому слову ──────────────────────────────────────────
@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE cards SET ru='x'",
        "DELETE FROM cards",
        "DROP TABLE cards",
        "INSERT INTO cards VALUES ('a','b','c',1.0)",
        "CREATE TABLE evil (x TEXT)",
        "ALTER TABLE cards RENAME TO gone",
        "PRAGMA journal_mode = DELETE",
        "VACUUM",
    ],
)
def test_write_statements_are_refused(golden, sql):
    assert "only SELECT, WITH and EXPLAIN" in mod.sqlite_query(sql)


def test_multiple_statements_are_refused(golden):
    # Проходит гейт по первому слову — ловится тем, что execute() принимает
    # ровно одну команду.
    assert mod.sqlite_query("SELECT 1; DROP TABLE cards") == "one statement per call"


# ── слой 3: authorizer ─────────────────────────────────────────────────────
def test_authorizer_catches_write_hidden_behind_with(golden):
    """Единственный слой, который здесь работает.

    `WITH t AS (...) DELETE FROM cards` начинается со слова `with`, то есть
    гейт первого слова его пропускает. Если этот тест позеленел на «only
    SELECT» — значит authorizer сняли, и защита стала на слой тоньше, чем
    написано в докстринге сервера.
    """
    out = mod.sqlite_query("WITH t AS (SELECT 1) DELETE FROM cards")
    assert "not authorized" in out


def test_attach_of_a_foreign_file_is_denied(golden, tmp_path):
    outsider = tmp_path / "outsider.db"
    con = sqlite3.connect(outsider)
    con.execute("CREATE TABLE secrets (v TEXT)")
    con.execute("INSERT INTO secrets VALUES ('token')")
    con.commit()
    con.close()
    out = mod.sqlite_query(f"ATTACH DATABASE '{outsider}' AS x")
    assert "only SELECT, WITH and EXPLAIN" in out


def test_load_extension_is_denied(golden):
    assert "not authorized" in mod.sqlite_query("SELECT load_extension('/tmp/x.so')")


def test_writes_are_impossible_even_bypassing_the_gate(golden):
    """Слои 1–2 без слоёв 3–4: идём в соединение напрямую."""
    con = golden.connect()
    with pytest.raises(sqlite3.DatabaseError):
        con.execute("UPDATE cards SET ru='sabotage'")


# ── чтение работает ────────────────────────────────────────────────────────
def test_semicolon_inside_a_string_literal_is_allowed(golden):
    """Регрессия: запрет на ';' отвергал `LIKE '%;%'`, а точка с запятой
    встречается внутри переводов (`дом; здание`)."""
    out = mod.sqlite_query("SELECT count(*) AS n FROM cards WHERE ru LIKE '%;%'")
    assert '{"n": 1}' in out


def test_cross_database_join(golden):
    out = mod.sqlite_query(
        "SELECT c.lemma, w.sources FROM cards c JOIN v.words w ON w.lemma = c.lemma "
        "WHERE w.sources LIKE '%wiktionary%'"
    )
    assert '"lemma": "Haus"' in out


def test_case_is_never_folded(golden):
    """`Morgen` и `morgen` — разные слова, и на этом стоит весь конвейер."""
    out = mod.sqlite_query("SELECT lemma, ru FROM cards WHERE lemma = 'morgen'")
    assert '"ru": "завтра"' in out
    assert "утро" not in out


def test_limit_caps_rows_and_says_so(golden):
    out = mod.sqlite_query("SELECT lemma FROM cards", limit=2)
    assert out.splitlines()[0].startswith("2 row(s)")
    assert "more rows available" in out


def test_limit_cannot_exceed_the_hard_cap(golden):
    out = mod.sqlite_query("SELECT lemma FROM cards", limit=10**9)
    assert out.startswith("3 row(s)")


def test_long_cells_are_truncated(golden):
    out = mod.sqlite_query("SELECT data FROM cards WHERE lemma='Haus'", max_cell=10)
    assert "(+490 chars)" in out
    assert "cells over 10 chars truncated" in out


def test_schema_reports_both_databases(golden):
    out = mod.sqlite_schema()
    assert "CREATE TABLE cards" in out
    assert "CREATE TABLE words" in out


def test_databases_lists_paths_and_counts(golden):
    out = mod.sqlite_databases()
    assert "enrichment.db" in out and "vocab.db" in out
    assert "cards" in out and "3" in out


def test_an_all_empty_database_is_flagged_as_a_stub(tmp_path, monkeypatch):
    """Ловушка из CRITICAL-LINKS §6a: путь по умолчанию резолвится в пустышку,
    скрипт «успешно» отрабатывает вхолостую. Признак — ноль в знаменателе."""
    stub = tmp_path / "enrichment.db"
    con = sqlite3.connect(stub)
    con.execute("CREATE TABLE cards (lemma TEXT)")
    con.commit()
    con.close()
    g = mod.Golden(stub, None, {})
    monkeypatch.setattr(mod, "GOLDEN", g)
    assert "EVERY TABLE EMPTY" in mod.sqlite_databases()
    g._con.close()


# ── A4: почему режимы открытия разные ──────────────────────────────────────
def _wal_db_without_companions(tmp_path: Path) -> Path:
    """WAL-база без спутников `-wal`/`-shm` — состояние золотой `vocab.db`."""
    db = tmp_path / "wal.db"
    con = sqlite3.connect(db)
    con.execute("PRAGMA journal_mode = WAL")
    con.execute("CREATE TABLE t (x INTEGER)")
    con.execute("INSERT INTO t VALUES (1)")
    con.commit()
    con.close()
    for sputnik in (f"{db}-wal", f"{db}-shm"):
        Path(sputnik).unlink(missing_ok=True)
    # Заголовок по-прежнему объявляет WAL, хотя спутников нет.
    assert db.open("rb").read(19)[18] == 2
    return db


def test_immutable_reads_a_wal_database_and_leaves_no_trace(tmp_path):
    """Почему `vocab.db` открывается именно `immutable=1`.

    Золотой файл обязан оставаться инертным: после чтения рядом с ним не должно
    появиться ничего. Это свойство `immutable` и не зависит от версии SQLite.
    """
    db = _wal_db_without_companions(tmp_path)
    con = sqlite3.connect(mod._uri(db, immutable=True), uri=True)
    assert con.execute("SELECT x FROM t").fetchone() == (1,)
    con.close()
    assert not Path(f"{db}-shm").exists()
    assert not Path(f"{db}-wal").exists()


def test_plain_readonly_on_a_wal_database_either_fails_or_writes(tmp_path):
    """Исполняемая версия A4 — и поправка к её формулировке в info/PLANS.md.

    Там сказано «`vocab.db` не открывается голым `mode=ro`», как будто дело в
    файле. Дело в версии SQLite, и оба исхода одинаково неприемлемы для золотой
    базы. Замер на этой машине, один и тот же файл:

        3.51.0 (системный CLI, /usr/bin/python3)  SQLITE_CANTOPEN(14)
        3.53.1 (этот venv)                        открывает, создав -shm и -wal

    Тест не фиксирует конкретный исход — он фиксирует, что «просто mode=ro»
    безвредным не бывает, а значит выбор immutable в сервере не вкусовой.
    """
    db = _wal_db_without_companions(tmp_path)
    try:
        con = sqlite3.connect(mod._uri(db, immutable=False), uri=True)
        con.execute("SELECT x FROM t").fetchone()
        opened = True
    except sqlite3.OperationalError:
        opened = False
    else:
        con.close()

    if opened:
        assert Path(f"{db}-shm").exists(), (
            "mode=ro прочитал WAL-базу, не создав -shm — поведение SQLite "
            "изменилось, и обоснование immutable надо перемерить"
        )
    else:
        assert not Path(f"{db}-shm").exists()


def test_uri_escapes_paths_with_spaces(tmp_path):
    """Репозиторий лежит в каталоге с пробелом («Wordlist design»)."""
    spaced = tmp_path / "с пробелом"
    spaced.mkdir()
    db = spaced / "a.db"
    sqlite3.connect(db).close()
    assert "%20" in mod._uri(db, immutable=True)
    sqlite3.connect(mod._uri(db, immutable=True), uri=True).close()


# ── золотые базы: пропускаются там, где их нет ─────────────────────────────
GOLDEN_PRESENT = (mod.VOCAB_DATA / "enrichment.db").exists() and (
    mod.VOCAB_DATA / "vocab.db"
).exists()
golden_only = pytest.mark.skipif(
    not GOLDEN_PRESENT, reason="золотые базы не выкачаны (gitignored, 320 МБ)"
)


@golden_only
def test_real_databases_open_and_are_not_stubs(monkeypatch):
    g = mod.Golden(mod.VOCAB_DATA / "enrichment.db", mod.VOCAB_DATA / "vocab.db", {})
    monkeypatch.setattr(mod, "GOLDEN", g)
    out = mod.sqlite_databases()
    assert "EVERY TABLE EMPTY" not in out
    # vocab.db открывается только immutable — см. тест про WAL выше.
    assert g.modes["v"] == "mode=ro&immutable=1"
    g._con.close()


@golden_only
def test_real_cross_database_join(monkeypatch):
    g = mod.Golden(mod.VOCAB_DATA / "enrichment.db", mod.VOCAB_DATA / "vocab.db", {})
    monkeypatch.setattr(mod, "GOLDEN", g)
    out = mod.sqlite_query(
        "SELECT c.lemma, c.zipf FROM cards c JOIN v.words w ON w.lemma = c.lemma "
        "WHERE c.lemma = 'Haus'"
    )
    assert '"lemma": "Haus"' in out
    g._con.close()

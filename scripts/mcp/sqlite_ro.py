#!/usr/bin/env python
"""Read-only MCP access to the golden SQLite pair — `enrichment.db` + `vocab.db`.

Why this exists. The postgres MCP server reaches the *mirror* (`vocab_cards`,
`user_word_list`, `users`, `essays`, `phrases`) — but the mirror is derived and
carries only what a search result row needs. Everything the measurements in
`info/PLANS.md` actually talk about lives in SQLite: `word_status.phase` and its
terminal `failed`/`skipped`, `cards.form_kind`, `morphology`, `token_usage`, the
raw dictionary bodies in `v.words`. Before this server those numbers cost a
throwaway script per question; now they cost a query.

Read-only is not a preference here. The enrichment worker owns `enrichment.db`
as its durable scratch space and writes to it around the clock, so a reader that
can take a write lock can stall a run that has been going for hours. Four
independent layers say no: the URI opens the file read-only, `query_only` blocks
writes at the engine, an authorizer denies every action that is not a read, and
the statement gate accepts only SELECT/WITH/EXPLAIN. Any one of them would do;
together they mean no future edit to this file can quietly turn it writable.

Open mode is *per database*, and that asymmetry is the subtle part. Both files
are WAL (header byte 18 == 2), and a read-only connection to a WAL database needs
the `-shm` companion. `enrichment.db` always has one, because the worker keeps
the file open. `vocab.db` has none — and what happens then depends on the SQLite
build, which is the part `info/PLANS.md` A4 got wrong by reading it as a corrupt
file. Measured on this machine, same file, same directory:

    sqlite 3.51.0 (macOS `sqlite3` CLI, /usr/bin/python3)   SQLITE_CANTOPEN(14)
    sqlite 3.53.1 (this venv)                               opens, and *creates*
                                                            `-shm` + `-wal`

Neither outcome is wanted for a golden artifact: one is an error that reads like
data loss, the other silently writes two files next to a database that is
supposed to be inert. So `vocab.db` opens `immutable=1` — it sidesteps WAL and
locking, works on every build, and leaves nothing behind (verified: no
`vocab.db-shm` exists after a session). The same flag would be *wrong* for
`enrichment.db`, where ignoring the WAL means serving a stale page image while
reporting success. The mode follows the file's writer, and the fallback path
says so out loud instead of downgrading in silence.

Defaults point at `backend/app/vocab/vocab_data/`, never at
`backend/app/vocab/`. The latter holds 4 KB and 64 KB stubs that
`enrich.py:39` resolves to whenever `VOCAB_DB` is unset — the trap that once had
a dry run report 36 455 "new" words including `Mensch`. `sqlite_databases`
prints the resolved path every time and flags a database whose tables are all
empty, because the signature of that trap is a zero in the *denominator*.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

REPO = Path(__file__).resolve().parents[2]
VOCAB_DATA = REPO / "backend" / "app" / "vocab" / "vocab_data"

# `enrichment.db` is `main` and `vocab.db` attaches as `v` — the same layout
# `enrich.py:480` and `backend/scripts/qa_cards.py:257` already use, so a query
# written against one works verbatim in the others.
VOCAB_ALIAS = "v"

QUERY_TIMEOUT = 20.0    # s; a mistyped join over 126k rows should fail, not hang
MAX_LIMIT = 1000
MAX_RESPONSE = 200_000  # chars; a full `cards` row averages ~920

# Only reads. Everything absent from this set is denied, which is what keeps
# ATTACH — the one remaining way to reach a file nobody asked for — out.
_ALLOWED_ACTIONS = {
    getattr(sqlite3, name)
    for name in ("SQLITE_SELECT", "SQLITE_READ", "SQLITE_FUNCTION", "SQLITE_RECURSIVE")
    if hasattr(sqlite3, name)
}
# Pragma functions (`select * from pragma_table_info('cards')`) are read-only by
# construction, but only in their no-argument form: `PRAGMA journal_mode = WAL`
# arrives through the same action code with a value in arg2.
_ALLOWED_PRAGMAS = {
    "table_info", "table_xinfo", "index_list", "index_info", "index_xinfo",
    "foreign_key_list", "database_list", "collation_list", "function_list",
    "page_count", "page_size", "freelist_count", "encoding", "compile_options",
}
_STATEMENT_HEADS = ("select", "with", "explain")


def _uri(path: Path, *, immutable: bool) -> str:
    """Percent-encode the path — this repo lives under a directory with a space."""
    quoted = urllib.parse.quote(str(path))
    query = "mode=ro&immutable=1" if immutable else "mode=ro"
    return f"file:{quoted}?{query}"


def _authorizer(action: int, arg1: Any, arg2: Any, _db_name: Any, _trigger: Any) -> int:
    if action in _ALLOWED_ACTIONS:
        return sqlite3.SQLITE_OK
    if (
        hasattr(sqlite3, "SQLITE_PRAGMA")
        and action == sqlite3.SQLITE_PRAGMA
        and arg2 is None
        and str(arg1 or "").lower() in _ALLOWED_PRAGMAS
    ):
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


class Golden:
    """One connection with both databases attached, opened once and kept."""

    def __init__(self, enrich: Path, vocab: Path | None, extra: dict[str, Path]):
        self.enrich = enrich
        self.vocab = vocab
        self.extra = extra
        self.notes: list[str] = []
        self.modes: dict[str, str] = {}
        self._con: sqlite3.Connection | None = None

    # ── opening ────────────────────────────────────────────────────────────
    def _connect_main(self) -> sqlite3.Connection:
        try:
            con = sqlite3.connect(_uri(self.enrich, immutable=False), uri=True, timeout=10)
            self.modes["main"] = "mode=ro"
        except sqlite3.OperationalError as exc:
            # No `-shm` and nothing holding the file open. Falling back to
            # immutable keeps the server usable, but the read now ignores any
            # WAL content, so it must be said out loud rather than absorbed.
            con = sqlite3.connect(_uri(self.enrich, immutable=True), uri=True, timeout=10)
            self.modes["main"] = "mode=ro&immutable=1"
            self.notes.append(
                f"main opened with immutable=1 after mode=ro failed ({exc}). "
                "No writer holds the file, so there is no -shm to attach; if the "
                "enrichment worker is running, uncommitted WAL rows are invisible "
                "to this connection."
            )
        return con

    def _attach(self, con: sqlite3.Connection, alias: str, path: Path, *, immutable: bool) -> None:
        con.execute("ATTACH DATABASE ? AS " + alias, (_uri(path, immutable=immutable),))
        self.modes[alias] = "mode=ro&immutable=1" if immutable else "mode=ro"

    def connect(self) -> sqlite3.Connection:
        if self._con is not None:
            return self._con
        con = self._connect_main()
        if self.vocab is not None:
            # Static at runtime and carrying no -shm — immutable is the only
            # mode that opens it at all. See the module docstring.
            self._attach(con, VOCAB_ALIAS, self.vocab, immutable=True)
        for alias, path in self.extra.items():
            self._attach(con, alias, path, immutable=True)
        con.execute("PRAGMA query_only = ON")
        con.set_authorizer(_authorizer)
        self._con = con
        return con

    # ── introspection ──────────────────────────────────────────────────────
    def schemas(self) -> list[tuple[str, Path]]:
        out = [("main", self.enrich)]
        if self.vocab is not None:
            out.append((VOCAB_ALIAS, self.vocab))
        out.extend(self.extra.items())
        return out

    def tables(self, schema: str) -> list[tuple[str, int]]:
        con = self.connect()
        names = [
            r[0]
            for r in con.execute(
                f"SELECT name FROM {schema}.sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        rows = []
        for name in names:
            (count,) = con.execute(f'SELECT count(*) FROM {schema}."{name}"').fetchone()
            rows.append((name, count))
        return rows


GOLDEN: Golden | None = None
# WARNING, not the default INFO: every tool call would otherwise write a banner
# to stderr, and stderr is where the resolved database paths go — the one line
# per start that has to stay easy to find.
mcp = FastMCP("sqlite-ro", log_level="WARNING")


def _golden() -> Golden:
    assert GOLDEN is not None, "server started without databases"
    return GOLDEN


@mcp.tool()
def sqlite_databases() -> str:
    """List the attached golden SQLite databases: schema alias, resolved path,
    size, open mode and per-table row counts.

    Call this first. The row counts are the guard against the stub-path trap
    documented in CRITICAL-LINKS §6a — a database serving zeros in the
    *denominator* is a wrong file, not an empty result.
    """
    g = _golden()
    out: list[str] = []
    for alias, path in g.schemas():
        tables = g.tables(alias)
        total = sum(c for _, c in tables)
        size_mb = path.stat().st_size / 1024 / 1024 if path.exists() else 0.0
        head = f"{alias}  {path}  ({size_mb:.1f} MB, {g.modes.get(alias, '?')})"
        if total == 0:
            head += "  ⚠️ EVERY TABLE EMPTY — almost certainly a stub, not the golden file"
        out.append(head)
        out.extend(f"    {name:<14} {count:>9,}" for name, count in tables)
    for note in g.notes:
        out.append(f"⚠️ {note}")
    return "\n".join(out)


@mcp.tool()
def sqlite_schema(table: str = "") -> str:
    """Show CREATE statements for tables and indexes.

    With no argument, every object in every attached database. With a table
    name, just that table and its indexes. Accepts a bare name (`cards`) or a
    qualified one (`v.words`).
    """
    g = _golden()
    con = g.connect()
    want_schema, _, want_table = table.rpartition(".")
    out: list[str] = []
    for alias, _ in g.schemas():
        if want_schema and alias != want_schema:
            continue
        sql = (
            f"SELECT sql FROM {alias}.sqlite_master "
            "WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'"
        )
        params: tuple[Any, ...] = ()
        if want_table:
            sql += " AND (name = ? OR tbl_name = ?)"
            params = (want_table, want_table)
        rows = [r[0] for r in con.execute(sql + " ORDER BY tbl_name, type DESC, name", params)]
        if rows:
            out.append(f"── {alias} ──")
            out.extend(f"{r};" for r in rows)
    return "\n".join(out) or f"no such table: {table}"


@mcp.tool()
def sqlite_query(sql: str, limit: int = 100, max_cell: int = 200) -> str:
    """Run one read-only SELECT against the golden databases and return JSONL rows.

    `enrichment.db` is `main` (tables `cards`, `word_status`, `morphology`,
    `enriched`, `token_usage`); `vocab.db` attaches as `v` (table `v.words`), so
    the two join directly:

        SELECT c.lemma, c.zipf, c.form_kind, w.sources
        FROM cards c JOIN v.words w ON w.lemma = c.lemma
        WHERE c.zipf > 5.0 AND c.form_kind IS NOT NULL

    Case is never folded: `Morgen` and `morgen` are different words and the
    whole enrichment pipeline depends on that staying true.

    Only SELECT / WITH / EXPLAIN, one statement per call. `limit` caps returned
    rows (max 1000); `max_cell` truncates long cells — set it higher to read a
    full `cards.data` JSON blob.
    """
    g = _golden()
    con = g.connect()

    statement = sql.strip().rstrip(";").strip()
    if not statement:
        return "empty query"
    # Multiple statements are rejected by `Connection.execute` itself, so there
    # is no hand-rolled ';' scan here — one would also refuse the legitimate
    # `WHERE ru LIKE '%;%'`, and semicolons do occur inside translations.
    if not statement.lower().startswith(_STATEMENT_HEADS):
        return (
            "read-only server: only SELECT, WITH and EXPLAIN are accepted "
            f"(got {statement.split(None, 1)[0]!r}). The golden databases are "
            "never written from here."
        )

    limit = max(1, min(int(limit), MAX_LIMIT))
    deadline = time.monotonic() + QUERY_TIMEOUT
    con.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 20_000)
    started = time.monotonic()
    try:
        cur = con.execute(statement)
        rows = cur.fetchmany(limit)
        more = cur.fetchone() is not None
        columns = [d[0] for d in cur.description] if cur.description else []
    except sqlite3.OperationalError as exc:
        if "interrupted" in str(exc):
            return f"query exceeded {QUERY_TIMEOUT:.0f}s and was aborted — narrow it or add a WHERE"
        return f"sqlite error: {exc}"
    except sqlite3.ProgrammingError:
        return "one statement per call"
    except sqlite3.DatabaseError as exc:
        return f"sqlite error: {exc}"
    finally:
        con.set_progress_handler(None, 0)
    elapsed = (time.monotonic() - started) * 1000

    truncated = False
    lines: list[str] = []
    budget = MAX_RESPONSE
    for row in rows:
        record: dict[str, Any] = {}
        # strict=True: both sides come off the same cursor, so a length mismatch
        # would be a driver bug, not data — better a loud error than a silently
        # dropped column.
        for name, value in zip(columns, row, strict=True):
            if isinstance(value, str) and len(value) > max_cell:
                value = value[:max_cell] + f"… (+{len(value) - max_cell} chars)"
                truncated = True
            elif isinstance(value, bytes):
                value = f"<{len(value)} bytes>"
            record[name] = value
        line = json.dumps(record, ensure_ascii=False, default=str)
        budget -= len(line) + 1
        if budget < 0:
            lines.append(f"… response cap reached after {len(lines)} rows")
            break
        lines.append(line)

    header = f"{len(rows)} row(s) · {elapsed:.0f} ms"
    if more:
        header += f" · more rows available (limit={limit})"
    if truncated:
        header += f" · cells over {max_cell} chars truncated"
    return "\n".join([header, *lines])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enrich-db", type=Path, default=VOCAB_DATA / "enrichment.db")
    parser.add_argument("--vocab-db", type=Path, default=VOCAB_DATA / "vocab.db")
    parser.add_argument(
        "--attach",
        action="append",
        default=[],
        metavar="ALIAS=PATH",
        help="extra read-only database, e.g. golden=./enrichment-GOLDEN-2026-07-19.db",
    )
    parser.add_argument("--self-test", action="store_true", help="open, report, exit")
    args = parser.parse_args(argv)

    extra: dict[str, Path] = {}
    for spec in args.attach:
        alias, _, path = spec.partition("=")
        if not alias.isidentifier() or not path:
            parser.error(f"--attach expects ALIAS=PATH with an identifier alias, got {spec!r}")
        extra[alias] = Path(path).resolve()

    enrich = args.enrich_db.resolve()
    vocab = args.vocab_db.resolve() if args.vocab_db else None
    if not enrich.exists():
        parser.error(f"enrichment database not found: {enrich}")
    if vocab is not None and not vocab.exists():
        print(f"vocab database not found, continuing without it: {vocab}", file=sys.stderr)
        vocab = None

    global GOLDEN
    GOLDEN = Golden(enrich, vocab, extra)
    # Resolved paths go to stderr on every start: the stub trap is silent by
    # nature, and the only cheap defence is never having to guess which file
    # answered.
    print(f"sqlite-ro: main={enrich}", file=sys.stderr)
    print(f"sqlite-ro: {VOCAB_ALIAS}={vocab}", file=sys.stderr)

    if args.self_test:
        print(sqlite_databases())
        return 0

    mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

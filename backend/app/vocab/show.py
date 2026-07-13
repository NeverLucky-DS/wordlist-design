"""Inspect the built vocab.db: overall stats + per-word cards showing what each
dictionary contributed (the "touch the real result" view).

  ./.venv/bin/python backend/app/vocab/show.py                 # stats + samples
  ./.venv/bin/python backend/app/vocab/show.py Haus Umwelt gehen

(named show.py, not inspect.py, to avoid shadowing the stdlib `inspect` module
that wordfreq depends on when this dir is on sys.path.)
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).with_name("vocab.db")


def _c(con, where=""):
    return con.execute("SELECT COUNT(*) FROM words " + where).fetchone()[0]


def stats(con) -> None:
    total = _c(con)
    print("╭─ vocab.db — %d lemmas ─────────────────────────" % total)
    levels = " ".join(
        "%s=%d" % (lvl, _c(con, "WHERE level='%s'" % lvl))
        for lvl in ("a1", "a2", "b1", "b2", "c1", "c2", "unlisted"))
    print("│ levels:  " + levels)
    print("│ obligatory (Goethe A1–B1): %d"
          % _c(con, "WHERE level IN ('a1','a2','b1')"))
    print("│ fields:  article=%d  examples=%d  synonyms=%d  idioms=%d  collocations=%d" % (
        _c(con, "WHERE article IS NOT NULL"), _c(con, "WHERE examples!='[]'"),
        _c(con, "WHERE synonyms!='[]'"), _c(con, "WHERE idioms!='[]'"),
        _c(con, "WHERE collocations!='[]'")))
    print("╰────────────────────────────────────────────────────")


def card(con, lemma: str) -> None:
    cur = con.execute("SELECT * FROM words WHERE lemma=?", (lemma,))
    row = cur.fetchone()
    if not row:
        print(f"\n'{lemma}' — not in coverage")
        return
    r = dict(zip([d[0] for d in cur.description], row))
    art = (r["article"] + " ") if r["article"] else ""
    print(f"\n┏━ {art}{r['lemma']}  ·  {r['level']}  ·  rank #{r['freq_rank']}  ·  zipf {r['zipf']:.2f}")
    pos = ", ".join(json.loads(r["pos"])) or "—"
    forms = ", ".join(json.loads(r["forms"])) or "—"
    print(f"┃ pos: {pos}   forms: {forms}")
    tr = json.loads(r["translations"])
    print(f"┃ переводы ({len(tr)}): " + "; ".join(tr[:8]))
    syn = json.loads(r["synonyms"])
    if syn:
        print("┃ синонимы (de): " + " | ".join(syn[:4]))
    idi = json.loads(r["idioms"])
    if idi:
        print("┃ идиомы: " + " | ".join(idi[:4]))
    col = json.loads(r["collocations"])
    if col:
        print("┃ коллокации: " + " | ".join(col[:3]))
    print("┃ — вклад по источникам —")
    for src, bs in json.loads(r["by_source"]).items():
        bits = []
        if bs.get("translations"):
            bits.append("перев: " + "; ".join(bs["translations"][:3]))
        if bs.get("synonyms"):
            bits.append("син: " + "; ".join(bs["synonyms"][:2]))
        if bs.get("examples"):
            bits.append("прим: " + bs["examples"][0][:60])
        if bs.get("idioms"):
            bits.append("идиом: " + "; ".join(bs["idioms"][:2]))
        if bs.get("collocations"):
            bits.append("коллок: " + bs["collocations"][0][:60])
        print(f"┃   [{src}] " + ("  ·  ".join(bits) if bits else "(grammar/forms)"))
    print("┗━")


def main(words: list[str]) -> None:
    con = sqlite3.connect(DB_PATH)
    stats(con)
    for w in (words or ["Haus", "Umwelt", "gehen", "nachhaltig", "Verantwortung"]):
        card(con, w)
    con.close()


if __name__ == "__main__":
    main(sys.argv[1:])

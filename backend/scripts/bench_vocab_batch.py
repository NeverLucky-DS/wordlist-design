"""Live benchmark: how many vocab.db words (full raw metadata) fit per Mistral call.

Uses MISTRAL_API_KEY from backend/.env. Sends by_source + all merged fields as-is.

Usage (from repo root):
    uv run python backend/scripts/bench_vocab_batch.py
    uv run python backend/scripts/bench_vocab_batch.py --sizes 5,10,15,20
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import settings
from app.services.mistral_http import post_mistral_json

DB = Path(__file__).resolve().parents[1] / "app" / "vocab" / "vocab_data" / "vocab.db"

_JSON = (
    "pos", "forms", "translations", "examples", "synonyms",
    "collocations", "idioms", "sources", "by_source",
)

_PROMPT = """Du bist ein zweisprachiges (Deutsch–Russisch) Lexikon-Redaktionssystem für DaF (B2–C1).
Unten stehen {count} deutsche Wörter mit VOLLSTÄNDIGEN Rohdaten aus unserer Wörterbuch-Datenbank
(jedes Wort: lemma, level, zipf, alle Felder und by_source pro Quelle — unverkürzt).
Bearbeite ALLE Wörter.

Gib AUSSCHLIESSLICH ein JSON-Objekt zurück (kein Markdown):
{{"words": [
  {{
    "word": "<exakt lemma aus den Rohdaten>",
    "ru": "точный перевод на русский (2-5 слов)",
    "definition": "Kurze deutsche Definition in EINEM Satz (B2).",
    "rektion": "Rektion wie 'auf + Akk.' oder leerer String",
    "ready_phrase": "typische Kollokation oder leerer String",
    "examples": [
      {{"de": "Beispiel mit **Wort** fett.", "ru": "русский перевод."}}
    ]
  }}
]}}

REGELN:
- "word" MUSS exakt dem lemma entsprechen (zum Zuordnen).
- "ru" und "definition" sind PFLICHT.
- "examples": GENAU 3 Stück; vorhandene Quell-Beispiele zuerst übersetzen, dann ergänzen.
- Nutze die Rohdaten (by_source, translations, collocations) — erfinde nichts Widersprüchliches.

Eingabewörter (Roh-JSON pro Wort):
{words_block}
"""


def _parse_row(row: sqlite3.Row) -> dict:
    d = dict(row)
    for f in _JSON:
        if isinstance(d.get(f), str):
            d[f] = json.loads(d[f])
    return {
        "lemma": d["lemma"],
        "level": d["level"],
        "article": d["article"],
        "zipf": d["zipf"],
        "freq_rank": d["freq_rank"],
        "pos": d["pos"],
        "forms": d["forms"],
        "translations": d["translations"],
        "examples": d["examples"],
        "synonyms": d["synonyms"],
        "collocations": d["collocations"],
        "idioms": d["idioms"],
        "sources": d["sources"],
        "by_source": d["by_source"],
    }


def _stratified_sample(con: sqlite3.Connection, n: int = 40) -> list[dict]:
    """Mix of small / median / heavy by_source payloads."""
    rows = con.execute(
        "SELECT *, length(by_source) AS bs FROM words ORDER BY bs"
    ).fetchall()
    picks: list[sqlite3.Row] = []
    for frac in (0.15, 0.35, 0.5, 0.65, 0.85, 0.97):
        picks.append(rows[int(len(rows) * frac)])
    # fill with random distinct lemmas
    seen = {r["lemma"] for r in picks}
    for r in con.execute("SELECT * FROM words ORDER BY RANDOM() LIMIT ?", (n * 2,)):
        if r["lemma"] not in seen:
            picks.append(r)
            seen.add(r["lemma"])
        if len(picks) >= n:
            break
    return [_parse_row(r) for r in picks[:n]]


def _build_block(words: list[dict]) -> str:
    parts = []
    for i, w in enumerate(words, 1):
        raw = json.dumps(w, ensure_ascii=False, indent=None)
        parts.append(f"--- Wort {i}: {w['lemma']} ---\n{raw}")
    return "\n\n".join(parts)


def _score_response(sent: list[dict], parsed: dict) -> dict:
    items = parsed.get("words")
    if not isinstance(items, list):
        return {"parse_ok": False, "matched": 0, "total": len(sent), "field_score": 0.0}

    by_lemma = {str(x.get("word", "")).strip().lower(): x for x in items if isinstance(x, dict)}
    matched = 0
    field_hits = 0
    field_total = 0
    required = ("ru", "definition", "examples")

    for w in sent:
        item = by_lemma.get(w["lemma"].lower())
        if not item:
            continue
        matched += 1
        for f in required:
            field_total += 1
            val = item.get(f)
            if f == "examples":
                ok = isinstance(val, list) and len(val) >= 1
            else:
                ok = isinstance(val, str) and val.strip()
            if ok:
                field_hits += 1

    return {
        "parse_ok": True,
        "matched": matched,
        "total": len(sent),
        "match_rate": matched / len(sent) if sent else 0,
        "field_score": field_hits / field_total if field_total else 0,
        "returned_count": len(items),
    }


def _est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def run_benchmark(sizes: list[int], pool: list[dict], margin: float) -> None:
    key = settings.mistral_api_key.strip()
    if not key:
        sys.exit("MISTRAL_API_KEY missing in backend/.env")

    model = settings.mistral_model
    print(f"Model: {model}")
    print(f"DB: {DB} ({len(pool)} words in pool)")
    print(f"Safety margin: {margin:.0%} → operational batch = floor(max_ok × {1 - margin:.2f})")
    print()

    results = []
    for n in sizes:
        batch = pool[:n]
        block = _build_block(batch)
        prompt = _PROMPT.format(count=n, words_block=block)
        input_chars = len(prompt)
        est_in = _est_tokens(prompt)
        # rough output budget: ~350 tokens/word
        est_out = n * 350
        print(f"=== batch={n}  in≈{est_in} tok ({input_chars} chars)  out≈{est_out} tok ===")

        t0 = time.monotonic()
        try:
            parsed = post_mistral_json(
                [{"role": "user", "content": prompt}],
                key,
                model,
                temperature=0.1,
                timeout=300,
            )
            elapsed = time.monotonic() - t0
            sc = _score_response(batch, parsed)
            ok = sc["parse_ok"] and sc["match_rate"] >= 1.0 and sc["field_score"] >= 0.85
            status = "OK" if ok else "WARN"
        except Exception as exc:
            elapsed = time.monotonic() - t0
            sc = {"parse_ok": False, "error": str(exc)[:200]}
            ok = False
            status = "FAIL"

        words_per_sec = n / elapsed if elapsed > 0 else 0
        print(
            f"  {status}  {elapsed:.1f}s  ({words_per_sec:.2f} w/s)  "
            f"match={sc.get('match_rate', 0):.0%}  fields={sc.get('field_score', 0):.0%}  "
            f"returned={sc.get('returned_count', '?')}/{n}"
        )
        if sc.get("error"):
            print(f"  error: {sc['error']}")
        print()

        results.append({"n": n, "ok": ok, "elapsed": elapsed, "input_chars": input_chars,
                        "est_in": est_in, "est_out": est_out, **sc})
        if not ok:
            break
        time.sleep(2)

    ok_sizes = [r["n"] for r in results if r.get("ok")]
    max_ok = max(ok_sizes) if ok_sizes else 0
    operational = int(max_ok * (1 - margin)) if max_ok else 0

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        flag = "✓" if r.get("ok") else "✗"
        print(
            f"  {flag} n={r['n']:3d}  {r['elapsed']:6.1f}s  "
            f"in~{r['est_in']:5d}tok  match={r.get('match_rate', 0):.0%}  "
            f"fields={r.get('field_score', 0):.0%}"
        )

    if max_ok:
        print()
        print(f"Max reliable batch (100% match, ≥85% fields): {max_ok} words/call")
        print(f"With {margin:.0%} headroom → use **{operational} words/call** in production")
        print(f"500-word job units → ~{(500 + operational - 1) // operational} Mistral calls per batch")
        # context ceiling estimate
        avg_chars = sum(r["input_chars"] / r["n"] for r in results if r.get("ok")) / len(ok_sizes)
        ctx_words = int(120_000 * 4 / (avg_chars + 350 * 4))  # 120k tok budget rough
        print(f"Avg input per word: ~{avg_chars:.0f} chars (~{avg_chars/4:.0f} tok in + ~350 tok out)")
        print(f"Theoretical context ceiling (quality not guaranteed): ~{ctx_words} words/call")
    else:
        print("\nNo batch passed quality gate — try smaller sizes or shorter payloads.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="1,3,5,8,10,12,15,18,20,25,30")
    ap.add_argument("--margin", type=float, default=0.35, help="Safety margin (0.35 = 35%%)")
    ap.add_argument("--pool", type=int, default=35)
    args = ap.parse_args()
    sizes = [int(x) for x in args.sizes.split(",") if x.strip()]

    if not DB.exists():
        sys.exit(f"vocab.db not found: {DB}")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    pool = _stratified_sample(con, args.pool)
    con.close()

    run_benchmark(sizes, pool, args.margin)


if __name__ == "__main__":
    main()

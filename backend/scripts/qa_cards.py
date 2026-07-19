"""Quality control for enriched cards: a free mechanical screen, then a review queue.

Two passes on purpose. Most defects a bad batch produces are *structural* and
need no judgement at all — a noun with no article, `ru` disagreeing with
`ru_all[0]`, several meanings crammed into one entry, an example that never uses
the word. Those are found here for nothing, over 100 % of the cards.

What is left needs someone who reads German and Russian: is «чип
(полупроводниковый)» a plausible reading of `Die`? That residue is what gets
handed to a reviewing model, and it is a fraction of the whole — which is the
entire point, because paying a model to re-read 19 000 good cards buys nothing.

Usage (from repo root):
    uv run python backend/scripts/qa_cards.py --source wiktionary --report
    uv run python backend/scripts/qa_cards.py --source wiktionary --batches out/
    uv run python backend/scripts/qa_cards.py --requeue suspects.jsonl --apply
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.vocab import enrich  # noqa: E402

logger = logging.getLogger(__name__)

_LATIN = re.compile(r"[A-Za-zÄÖÜäöüß]")
_CYR = re.compile(r"[А-Яа-яЁё]")
_PAREN = re.compile(r"\([^)]*\)")


def _packed(entry: str) -> bool:
    """Several meanings crammed into one `ru_all` entry.

    The prompt forbids it because search scores each entry whole: "приходить"
    matches the entry "приходить" at 1.00 but "приходить, прибывать" at 0.63, so
    the commonest word loses to any rarer rival that splits its senses.

    Parentheses are stripped FIRST. A qualifier is allowed and routinely holds a
    comma of its own — "последний (в очереди, соревновании)" is one meaning, and
    matching the raw string flagged it along with every card whose gloss reads
    "вопрос, требующий ответа «да» или «нет»".
    """
    bare = _PAREN.sub("", entry or "")
    parts = [p.strip() for p in re.split(r"[,;]", bare) if p.strip()]
    if len(parts) < 2:
        return False
    # Two full-word alternatives, not a subordinate clause: "приходить,
    # прибывать" packs meanings, "вопрос, требующий ответа" is a phrase.
    return all(re.fullmatch(r"[а-яё\- ]{3,}", p, re.I) and len(p.split()) <= 2
               for p in parts)


def _load(con: sqlite3.Connection, source: str | None) -> list[dict]:
    sql = ("SELECT c.lemma, c.pos, c.article, c.ru, c.zipf, c.data, c.prompt_version "
           "FROM cards c")
    params: tuple = ()
    if source:
        sql += (" JOIN v.words w ON w.lemma = c.lemma "
                " WHERE w.sources = ?")
        params = (json.dumps([source], ensure_ascii=False),)
    out = []
    for lemma, pos, article, ru, zipf, data, pv in con.execute(sql, params):
        try:
            card = json.loads(data)
        except (TypeError, json.JSONDecodeError):
            card = {}
        out.append({"lemma": lemma, "pos": pos, "article": article, "ru": ru,
                    "zipf": zipf, "card": card, "prompt_version": pv})
    return out


def check(row: dict, twins: dict[str, list[dict]]) -> list[str]:
    """Structural faults in one card. Empty list means nothing mechanical is wrong.

    Only faults worth acting on. `ru` disagreeing with `ru_all[0]` is a prompt
    violation but not a defect — `Schloss` stores ru "замок" against ru_all[0]
    "замок (дверной)", and the bare form is the better search key of the two. It
    is counted separately as cosmetic rather than queued for re-enrichment.
    """
    faults: list[str] = []
    c, lemma, pos = row["card"], row["lemma"], row["pos"]
    ru, ru_all = row["ru"] or "", c.get("ru_all") or []

    if not ru:
        faults.append("ru-empty")
    if not ru_all:
        faults.append("ru_all-empty")
    if any(_packed(x) for x in ru_all):
        faults.append("ru_all-packed")           # several meanings in one entry
    if ru and not _CYR.search(ru):
        faults.append("ru-not-russian")          # left untranslated

    if pos == "noun" and not row["article"]:
        faults.append("noun-without-article")
    if pos in ("noun", "verb") and not c.get("grammar"):
        faults.append("grammar-empty")
    if not (c.get("definition_de") or "").strip():
        faults.append("definition_de-empty")

    examples = c.get("examples") or []
    if len(examples) < 3:
        faults.append("examples-under-3")
    # The example must actually use the word. Compare on a prefix so inflection
    # ("Häuser" for "Haus") still counts; German compounds make a bare
    # substring test too permissive the other way.
    stem = lemma[:max(4, len(lemma) - 3)].lower()
    if examples and not any(stem in (e.get("de") or "").lower() for e in examples):
        faults.append("examples-miss-the-word")
    if any(not (e.get("ru") or "").strip() for e in examples):
        faults.append("example-without-translation")

    # The pair-collapse signature: two spellings differing only in case, handed
    # byte-identical meanings. 635 such pairs were found once before, when
    # `parse_response` case-folded its lookup and gave both halves one card.
    # Compare against the OTHER card under this spelling, not against a lookup
    # that can return the card itself.
    for other in twins.get(lemma.lower(), ()):
        if other["lemma"] != lemma and ru and (other["ru"] or "") == ru:
            faults.append("case-twin-identical-ru")
            break
    return faults


def cosmetic(row: dict) -> list[str]:
    """Prompt violations that are not worth re-enriching a card over."""
    ru_all = row["card"].get("ru_all") or []
    if ru_all and row["ru"] and ru_all[0] != row["ru"]:
        return ["ru-not-first-of-ru_all"]
    return []


def screen(rows: list[dict]) -> tuple[list[dict], list[dict], Counter, Counter]:
    twins: dict[str, list[dict]] = {}
    for r in rows:
        twins.setdefault(r["lemma"].lower(), []).append(r)

    flagged, clean, tally, cosmetics = [], [], Counter(), Counter()
    for r in rows:
        cosmetics.update(cosmetic(r))
        faults = check(r, twins)
        if faults:
            tally.update(faults)
            flagged.append(r | {"faults": faults})
        else:
            clean.append(r)
    return flagged, clean, tally, cosmetics


def _review_line(r: dict) -> str:
    """One card, trimmed to what a reviewer needs — nothing else costs tokens."""
    c = r["card"]
    return json.dumps({
        "lemma": r["lemma"],
        "pos": r["pos"],
        "article": r["article"],
        "zipf": round(r["zipf"], 2) if r["zipf"] is not None else None,
        "ru_all": (c.get("ru_all") or [])[:4],
        "de": (c.get("definition_de") or "")[:160],
        "ex": [(e.get("de") or "")[:90] for e in (c.get("examples") or [])[:1]],
    }, ensure_ascii=False)


def _requeue(args) -> int:
    """Queue the cards named in verdict files for re-enrichment.

    The stale card is DROPPED rather than kept. The repair phases keep theirs
    because a stale entry beats a hole in search — but these cards are not
    merely stale, they are wrong in a way that misleads: `Die` glossed as a
    semiconductor chip answers a search for the commonest word in German.
    Nothing is lost, `vocab.db` still holds the raw entry.
    """
    if args.enrich_db:
        enrich.ENRICH_DB = args.enrich_db
    if args.vocab_db:
        enrich.VOCAB_DB = args.vocab_db

    lemmas, reasons, missing = [], Counter(), 0
    for path in args.requeue:
        if not path.exists():
            print(f"missing verdict file: {path}", file=sys.stderr)
            return 1
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                v = json.loads(line)
            except json.JSONDecodeError:
                missing += 1
                continue
            lemma = v.get("lemma")
            if not lemma:
                missing += 1
                continue
            lemmas.append(lemma)
            reasons[v.get("verdict") or ",".join(v.get("faults") or []) or "?"] += 1

    lemmas = list(dict.fromkeys(lemmas))          # de-duplicate, keep order
    print(f"verdict files      : {len(args.requeue)}")
    print(f"cards to requeue   : {len(lemmas):,}")
    if missing:
        print(f"unparseable lines  : {missing}")
    print("\nby reason:")
    for name, n in reasons.most_common(15):
        print(f"  {n:>6}  {name}")

    if not args.apply:
        print("\nDRY RUN — pass --apply to actually requeue")
        return 0

    n = enrich.requeue(lemmas, drop_card=True, phase=enrich.QA)
    print(f"\nrequeued {n:,} cards into phase '{enrich.QA}'")
    print("They are served BEFORE the remaining backfill — press Start to run them.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--enrich-db", type=Path, default=None)
    ap.add_argument("--vocab-db", type=Path, default=None)
    ap.add_argument("--source", default=None,
                    help="only cards whose vocab.db row has this single source")
    ap.add_argument("--report", action="store_true", help="print the fault tally")
    ap.add_argument("--batches", type=Path, default=None,
                    help="write review batches (JSONL) into this directory")
    ap.add_argument("--batch-size", type=int, default=60)
    ap.add_argument("--sort-by-zipf", action="store_true", default=True,
                    help="most frequent first — a bad card at zipf 7 outranks everything")
    ap.add_argument("--requeue", type=Path, nargs="*", default=None,
                    help="JSONL verdict files (each line needs a `lemma`); queues "
                         "those cards for re-enrichment")
    ap.add_argument("--apply", action="store_true",
                    help="actually requeue — without it --requeue only reports")
    args = ap.parse_args()

    if args.requeue is not None:
        return _requeue(args)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    if args.enrich_db:
        enrich.ENRICH_DB = args.enrich_db
    if args.vocab_db:
        enrich.VOCAB_DB = args.vocab_db

    con = sqlite3.connect(f"file:{enrich.ENRICH_DB}?mode=ro", uri=True)
    con.execute("ATTACH DATABASE ? AS v", (f"file:{enrich.VOCAB_DB}?mode=ro",))
    try:
        rows = _load(con, args.source)
    finally:
        con.close()

    flagged, clean, tally, cosmetics = screen(rows)
    print(f"cards examined      : {len(rows):,}")
    print(f"mechanically faulty : {len(flagged):,} ({len(flagged)/max(len(rows),1):.1%})")
    print(f"need human/LLM eye  : {len(clean):,}")
    if args.report:
        print("\nfaults by kind:")
        for name, n in tally.most_common():
            print(f"  {n:>7}  {name}")
        print("\ncosmetic (not requeued):")
        for name, n in cosmetics.most_common():
            print(f"  {n:>7}  {name}")
        print("\nworst offenders by frequency:")
        for r in sorted(flagged, key=lambda x: -(x["zipf"] or 0))[:20]:
            print(f"  zipf {r['zipf'] or 0:.2f}  {r['lemma']:<20} {','.join(r['faults'])}")

    if args.batches:
        args.batches.mkdir(parents=True, exist_ok=True)
        pool = sorted(clean, key=lambda r: -(r["zipf"] or 0)) if args.sort_by_zipf else clean
        n = 0
        for i in range(0, len(pool), args.batch_size):
            chunk = pool[i:i + args.batch_size]
            path = args.batches / f"batch-{i // args.batch_size:04d}.jsonl"
            path.write_text("\n".join(_review_line(r) for r in chunk) + "\n",
                            encoding="utf-8")
            n += 1
        # The mechanical finds need no review — they are already verdicts.
        (args.batches / "mechanical-faults.jsonl").write_text(
            "\n".join(json.dumps({"lemma": r["lemma"], "faults": r["faults"],
                                  "zipf": r["zipf"]}, ensure_ascii=False)
                      for r in flagged) + "\n", encoding="utf-8")
        print(f"\nwrote {n} review batches of {args.batch_size} into {args.batches}")
        print(f"plus mechanical-faults.jsonl ({len(flagged):,} cards, no review needed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

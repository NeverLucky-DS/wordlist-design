"""Append new headwords from a Wiktionary dump to vocab.db (the intake table).

Offline on purpose, like the morphology import: the dump is ~300 MB and has no
business in the container image.

    curl -L -o de-extract.jsonl.gz \\
      https://kaikki.org/dictionary/downloads/de/de-extract.jsonl.gz

Look before writing — the dry run costs one pass and nothing else:

    uv run python backend/scripts/import_new_words.py de-extract.jsonl.gz --dry-run
    uv run python backend/scripts/import_new_words.py de-extract.jsonl.gz --min-zipf 2.5

⚠️ BACK UP vocab.db FIRST. It is the intake source for the whole pipeline, and
while this only ever appends (INSERT OR IGNORE on a unique lemma), a source file
is not something to write to without a copy on disk. `--backup` does it for you.

Once the rows are in, the words are ordinary candidates: press Start on the
enrichment page and the workers pick them up like anything else. Enrich a small
batch with `--limit` first and read the cards before committing tokens to the
full intake — new rows carry no Russian translations and only one source, and
the prompt's skip rules treat thin evidence as a reason to doubt a word.
"""
from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.vocab import enrich, intake  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dump", type=Path, help="de-extract.jsonl(.gz) from kaikki.org")
    ap.add_argument("--min-zipf", type=float, default=2.5,
                    help="frequency floor (default 2.5; 2.0 roughly doubles the intake)")
    ap.add_argument("--limit", type=int, default=None,
                    help="stop after N new lemmas — use for a trial batch")
    ap.add_argument("--vocab-db", type=Path, default=None,
                    help="target vocab.db (default: the configured one)")
    ap.add_argument("--dry-run", action="store_true",
                    help="count and sample without writing")
    ap.add_argument("--backup", action="store_true",
                    help="copy vocab.db to vocab.db.bak before writing")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    if not args.dump.exists():
        print(f"dump not found: {args.dump}", file=sys.stderr)
        return 1

    vocab = args.vocab_db or enrich.VOCAB_DB
    if not vocab.exists():
        print(f"vocab.db not found: {vocab}", file=sys.stderr)
        return 1

    # Printed, not assumed: VOCAB_DB defaults to an empty stub beside the real
    # database whenever the env var is unset, which outside the container it
    # always is. Seeing the resolved paths is what catches that in one glance.
    print(f"vocab.db     : {vocab}")
    print(f"enrichment.db: {enrich.ENRICH_DB}")

    if args.backup and not args.dry_run:
        bak = vocab.with_suffix(vocab.suffix + ".bak")
        print(f"backing up {vocab} → {bak}")
        shutil.copy2(vocab, bak)

    stats = intake.append(args.dump, vocab, min_zipf=args.min_zipf,
                          enrichment=enrich.ENRICH_DB,
                          limit=args.limit, dry_run=args.dry_run)

    print(f"\nknown already      : {stats['known']:,} lemmas (vocab.db + cards)")
    print(f"new candidates     : {stats['new']:,}  (zipf >= {args.min_zipf})")
    if args.dry_run:
        print("DRY RUN — nothing written")
    else:
        print(f"written            : {stats['written']:,}")
        print(f"vocab.db now holds : {stats['total']:,}")
    print("\nsample:")
    print("  " + ", ".join(stats["sample"]))
    if not args.dry_run:
        print("\nThese are ordinary candidates now — press Start on the enrichment "
              "page and the workers will pick them up.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

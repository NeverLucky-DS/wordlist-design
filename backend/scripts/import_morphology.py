"""Load full inflection paradigms into enrichment.db from a Wiktionary dump.

Offline on purpose. The dump is ~300 MB and has no business in the container
image, and the import is a one-off join rather than something the app should
redo at boot. Once it has run, the mirror carries the paradigms into Postgres on
its next pass like any other card column.

Get the dump (German edition — measured against the English one at roughly twice
the usable lemmas and with pronouns already attached to verb forms):

    curl -L -o de-extract.jsonl.gz \\
      https://kaikki.org/dictionary/downloads/de/de-extract.jsonl.gz

Usage (from repo root):
    uv run python backend/scripts/import_morphology.py de-extract.jsonl.gz
    uv run python backend/scripts/import_morphology.py dump.jsonl.gz --enrich-db /tmp/copy.db

Roughly 75 s over 1M entries on the live base, and it is re-runnable: a second
pass rewrites the same rows. Nothing is deleted, so a card that Wiktionary has
no entry for simply keeps whatever grammar the model gave it.

⚠️ Run this against a COPY first if enrichment workers are live — this writes to
enrichment.db, which they own.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.vocab import enrich, morph  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dump", type=Path, help="de-extract.jsonl(.gz) from kaikki.org")
    ap.add_argument("--enrich-db", type=Path, default=None,
                    help="target enrichment.db (default: the configured one)")
    ap.add_argument("--all", action="store_true",
                    help="store paradigms for every lemma, not just ones we have "
                         "cards for (3x the rows, useful before a big intake)")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    if not args.dump.exists():
        print(f"dump not found: {args.dump}", file=sys.stderr)
        return 1
    if args.enrich_db:
        enrich.ENRICH_DB = args.enrich_db

    enrich.ensure_schema()
    con = enrich._conn()
    try:
        stats = morph.import_dump(args.dump, con, only_known=not args.all)
        covered = con.execute(
            "SELECT COUNT(*) FROM cards c JOIN morphology m "
            "ON m.lemma = c.lemma AND m.pos = c.pos").fetchone()[0]
        cards = con.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
    finally:
        con.close()

    print(f"\nread {stats['read']:,} entries, stored {stats['stored']:,} paradigms")
    print(f"cards with a paradigm: {covered:,} of {cards:,} "
          f"({covered / max(cards, 1) * 100:.1f}%)")
    print("\nThe mirror publishes these on its next full resync — pressing Start "
          "on the enrichment page triggers one.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

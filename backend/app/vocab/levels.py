"""Estimated CEFR level for the 95.6 % of the base no published list covers.

`goethe.py` resolves a level from two wordlists and answers `unlisted` for
88 067 of 92 090 cards, because Goethe publishes A1–B1 only and no official
B2/C1 list exists at all. The UI already handles that honestly — it shows a
frequency band instead — but frequency is not difficulty, and the app is a
B1–C1 trainer whose whole point is knowing which words are still ahead of you.

So this is an estimate, and the word is load-bearing. `info/PLANS.md` pt.3
rejected computing CEFR from zipf *after measuring it*, on the grounds that a
computed level looks like knowledge the reader cannot audit. Any replacement had
to clear the same bar, so it was measured the same way before it was written:
420 cards that DO carry a published level, judged blind by six independent
raters, scored against the list.

    exact CEFR step        38 %   (zipf rule: 26 %)
    within one step        91 %   (zipf rule: 76 %)
    app's own B1/B2/C1     76 %   (zipf rule: 67 %)
    core (≤B1) vs above    91 %   (zipf rule: 71 %)
    …of that, against the official Goethe list alone:   96 %

Read that shape carefully, because it decides how this may be used. The exact
step is weak — b2 against c1 is close to a coin toss, and the raters lean about
a third of a level EASY, most at the top of the scale. What is strong is the one
boundary an official list actually attests: is this core vocabulary a B1 learner
should already have, or is it beyond that. On the Goethe half of the sample the
estimate never once called a word "core" that the list placed above it.

⚠️ Not every step is equally trustworthy, and the shape is counter-intuitive.
Measured on the 235 calibration words that are absent from the official Goethe
list — exactly the population this file labels — precision per predicted level:

    a1  5/6   83 %        b2  39/100  39 %
    a2  8/11  73 %        c1  20/76   26 %
    b1  4/31  13 %        c2  4/11    36 %

`b1` is the dumping ground: when a rater says b1 about a word no list covers, it
is right one time in eight. The confident calls are at the ends of the scale.

**Tried and rejected: clamping a1/a2 up to b1.** The argument was that Goethe's
A1 list is a closed published set of 673 words, so calling an unlisted word "a1"
claims something no list says. It is a good argument and the data says no:
clamping drops exact accuracy from 34.0 % to 28.5 % and within-one from 90.6 %
to 88.1 %, because a1/a2 are the raters' *best* calls, not their worst. Recorded
here because the argument will look convincing again next time.

Three consequences, all deliberate:

  * A published level always wins. `resolve()` never runs where `goethe.py`
    already answered — a citation is not improved by an estimate.
  * `band` — the key that picks one of 15 hand-painted brushes — is NOT derived
    from this. It stays a function of the published `level`. Repainting the
    visual language of the whole dictionary on a 38 %-exact signal is exactly
    the trade PLANS pt.3 refused.
  * The UI must render it as ours and not as a citation, the way it already
    separates the boxed Goethe chip from the painted frequency meter.

Estimates live in `data/cefr_estimated.tsv` and are applied in place, so a
re-enrichment cannot quietly drop them.
"""
from __future__ import annotations

import logging
import sqlite3
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA = Path(__file__).with_name("data")
ESTIMATES_FILE = _DATA / "cefr_estimated.tsv"

LEVELS = ("a1", "a2", "b1", "b2", "c1", "c2")
# Measured on 420 held-out cards with a published level, six independent raters.
# Kept in code because the API ships them to the browser: a claim the reader
# cannot audit is the thing this module exists to avoid making.
ACCURACY = {
    "exact": 0.38,          # the precise CEFR step
    "within_one": 0.91,     # off by at most one step
    "core_boundary": 0.91,  # "≤B1 or above" — the only boundary a list attests
    "sample": 420,
}


@lru_cache(maxsize=1)
def load() -> dict[str, str]:
    """lemma -> estimated level. Case is significant, as everywhere else here."""
    out: dict[str, str] = {}
    if not ESTIMATES_FILE.exists():
        return out
    for line in ESTIMATES_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) >= 2 and cols[0] and cols[1] in LEVELS:
            out[cols[0]] = cols[1]
    return out


def apply_estimates(con: sqlite3.Connection) -> int:
    """Write `cards.level_est` for every card we have an estimate for.

    Only where `level` is still `unlisted`: a published level is a citation and
    an estimate must never sit next to it pretending to be a second opinion.
    Runs in place, so the caller has to resync the mirror — same contract as
    `tag_forms`, `apply_fixes` and the `zipf` backfill.
    """
    estimates = load()
    if not estimates:
        return 0
    cols = {r[1] for r in con.execute("PRAGMA table_info(cards)")}
    if "level_est" not in cols:
        con.execute("ALTER TABLE cards ADD COLUMN level_est TEXT")
        con.commit()

    changed = 0
    for lemma, level in estimates.items():
        cur = con.execute(
            "UPDATE cards SET level_est=? WHERE lemma=? AND level='unlisted' "
            "AND COALESCE(level_est,'') != ?", (level, lemma, level))
        changed += cur.rowcount
    con.commit()
    if changed:
        logger.info("levels: wrote %d estimated CEFR levels", changed)
    return changed

"""Wortpaket — the vocabulary for one essay's topic.

The user writes a concrete prompt ("Sollten Smartphones an Schulen verboten
werden?") and picks a level; this builds the ~100 words worth having open while
writing it. Two model calls, and neither of them invents a word: every lemma
that reaches the user already has an enriched card. The model only ever *picks*
from what we send it.

    topic catalog (147 slugs + candidate counts)
              |
        call 1: which topics is this prompt close to?
              |
    candidates from those topics (~1000 rows, zipf >= 2.5, headwords only)
              |
        call 2: the 100 most useful for THIS prompt
              |
    byte-exact validation against what we sent + backfill by frequency

Three things here are load-bearing and were each decided against a measurement
(the numbers live in `info/PLANS.md` A13):

1. **The catalog carries counts.** Topic sizes run from 3 words to 2 695
   (mean 225; 43 of 147 hold fewer than fifty). Without the counts the model
   happily calls a three-word topic "close" and the package has nothing to draw
   from.

2. **Level does not filter candidates — it goes into the prompt.** A level
   exists for 18 542 of 92 090 cards, because `level_est` is only computed for
   zipf >= 3.0. That threshold marks where we measured, NOT where quality
   drops: just under it sit `Endlager`, `Hochwasserschutz`, `Verunreinigung`
   and `Ladestation` — mixed in with `Unix`, `Standby` and `Copy-and-Paste`.
   Filtering by level takes both groups. Telling the difference needs the
   topic, and a level threshold has no topic.

3. **No per-topic quotas.** We merge the chosen topics into one pool and ask
   for the best hundred overall. If ninety of them come from one topic, that
   topic was the answer. Asking a language model to split "40 here, 35 there"
   across pools of 3 and 2 695 produces a number with nothing behind it.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserWordList, VocabCard
from app.services.mistral_http import post_mistral_json
from app.vocab.topics import TOPICS

log = logging.getLogger(__name__)

_TOPIC_DE = {t["slug"]: t["de"] for t in TOPICS}

# Candidates start at zipf 2.5. Measured on the Technologie cluster (4 slugs):
# >=3.0 gives 863 rows, >=2.5 gives 1 661, >=2.0 gives 2 910. 2.5 lands on the
# ~1000-word pool the design asks for while still reaching the specific nouns an
# essay actually needs — `Hochwasserschutz` sits at 2.96.
CANDIDATE_MIN_ZIPF = 2.5
# How many topics may contribute. Eight, not three, and the number comes from a
# measurement rather than taste: for "Sollten Smartphones an Schulen verboten
# werden?" the words a writer needs are spread over at least six topics —
# `Verbot` and `Jugendschutz` in `recht_gesetz`, `Sucht` in `sucht_psyche`,
# `Datenschutz` in `datenschutz_privatsphaere`, `Ablenkung` in
# `gefuehle_emotionen`, `Altersgrenze` in `gesellschaft_zusammenleben` — while
# only the subject nouns sit in `digitalisierung_computer` and
# `schule_unterricht`. Subject vocabulary and argument vocabulary do not share a
# topic, and the argument half is what an essay is actually made of.
MAX_TOPICS = 8
# ...which is why the budget is PER TOPIC and not on the pool as a whole. An
# earlier version stopped adding topics once the pool passed 1 000 rows; two big
# subject topics reached that alone and every small, specific topic below them
# was cut off. Measured on the live base: all five argument words above were
# absent from the pool.
#
# This is a budget on the PROMPT, not the quota this design deliberately refused
# to hand the model — the model still picks its hundred from the merged pool
# with no per-topic allowance.
#
# 500 is measured, not chosen. Inside its own topic the argument vocabulary of a
# real prompt sits well down the frequency order: for the smartphone-ban prompt
# `Jugendschutz` (zipf 3.12) is 357th of 798 in `recht_gesetz` and
# `Altersgrenze` (3.13) is 448th of 928 in `gesellschaft_zusammenleben`. A cap
# of 300 cut both. These are mid-frequency compounds by nature — that is what a
# precise argument word looks like — so the cap has to clear their rank, not
# their zipf.
#
# ⚠️ It does not clear every such word, and the failure is silent: a term at
# rank 600 in a big topic still never reaches the model. If packages come back
# generic, this constant is the first thing to measure, not the prompt.
PER_TOPIC_CAP = 500
# Below this the model is guessing. The top topic is always kept regardless —
# a package built from a weak match beats an empty drawer.
MIN_CLOSENESS = 0.25
PACKAGE_SIZE = 100
# Ceiling on the whole prompt regardless of topic count: 8 × 300 = 2 400 rows
# is roughly 29k tokens, and this stops a future taxonomy change from silently
# making it more.
MAX_CANDIDATES = MAX_TOPICS * PER_TOPIC_CAP

PROMPT_VERSION = "wortpaket-2026-07-28a"


# --------------------------------------------------------------------------
# catalog
# --------------------------------------------------------------------------

# Counting candidates per topic is a full pass over `vocab_cards`, and the
# answer only moves when the mirror syncs. Cache it keyed by the card count, so
# a resync invalidates the cache by itself and nothing has to remember to.
_counts_cache: tuple[int, dict[str, int]] | None = None


async def catalog_counts(session: AsyncSession) -> dict[str, int]:
    """slug -> number of candidate words, for every topic that has any."""
    global _counts_cache

    total = int((await session.execute(select(func.count(VocabCard.lemma)))).scalar_one())
    if _counts_cache is not None and _counts_cache[0] == total:
        return _counts_cache[1]

    rows = (
        await session.execute(
            select(VocabCard.topic, func.count(VocabCard.lemma))
            .where(
                VocabCard.topic.is_not(None),
                VocabCard.form_kind.is_(None),
                VocabCard.zipf >= CANDIDATE_MIN_ZIPF,
            )
            .group_by(VocabCard.topic)
        )
    ).all()

    counts = {slug: int(n) for slug, n in rows if slug in _TOPIC_DE and n}
    _counts_cache = (total, counts)
    log.info(
        "wortpaket: catalog rebuilt — %d topics with candidates, %d cards total",
        len(counts), total,
    )
    return counts


def reset_catalog_cache() -> None:
    """Drop the memoised counts. For tests and for a forced rebuild."""
    global _counts_cache
    _counts_cache = None


# --------------------------------------------------------------------------
# call 1 — which topics
# --------------------------------------------------------------------------

_TOPICS_SYSTEM = (
    "Du ordnest ein Aufsatzthema den Themenfeldern eines Lernwörterbuchs zu.\n"
    "Du bekommst das Thema des Lernenden und eine Liste von Themenfeldern, "
    "jedes mit einem Slug und der Anzahl verfügbarer Wörter.\n"
    "Wähle die Themenfelder, deren Wortschatz man zum Schreiben dieses Aufsatzes "
    "wirklich braucht — höchstens sechs, nach Nähe absteigend.\n"
    "Nähe ist eine Zahl zwischen 0 und 1.\n"
    'Antworte NUR mit JSON: {"topics": [{"slug": "...", "closeness": 0.9}]}\n'
    "Verwende ausschliesslich Slugs aus der Liste."
)


def _topics_user_msg(thema: str, niveau: str, counts: dict[str, int]) -> str:
    lines = [f"{slug}\t{_TOPIC_DE[slug]}\t{n}" for slug, n in sorted(counts.items())]
    return (
        f"Aufsatzthema: {thema}\n"
        f"Niveau: {niveau}\n\n"
        "Themenfelder (slug, Bezeichnung, Anzahl Wörter):\n" + "\n".join(lines)
    )


def parse_topics(reply: dict, counts: dict[str, int]) -> list[tuple[str, float]]:
    """Pull (slug, closeness) pairs, dropping anything not in the catalog.

    A slug we did not send is not a near miss to be repaired — it is a topic
    that does not exist, and resolving it by similarity would silently invent a
    category. Same for a topic with no candidates: keeping it would only make
    the pool arithmetic lie.
    """
    out: list[tuple[str, float]] = []
    seen: set[str] = set()
    for item in reply.get("topics") or []:
        if not isinstance(item, dict):
            continue
        slug = item.get("slug")
        if not isinstance(slug, str) or slug in seen or slug not in counts:
            continue
        try:
            closeness = float(item.get("closeness", 0.0))
        except (TypeError, ValueError):
            continue
        seen.add(slug)
        out.append((slug, max(0.0, min(1.0, closeness))))
    out.sort(key=lambda p: p[1], reverse=True)
    return out


def choose_topics(
    ranked: list[tuple[str, float]], counts: dict[str, int]
) -> list[tuple[str, float]]:
    """Take every topic the model rated close enough, up to the cap.

    Closeness is the only stopping rule. Size deliberately is not: the small
    topics are where the argument vocabulary lives, and a rule that stops when
    the pool is "big enough" always drops them, because the big subject topics
    are sorted in first and fill it on their own.

    The first topic is kept whatever its closeness: the alternative to a weak
    match is no package at all, and the second call still gets to reject every
    word in it.
    """
    chosen: list[tuple[str, float]] = []
    for slug, closeness in ranked:
        if chosen and (closeness < MIN_CLOSENESS or len(chosen) >= MAX_TOPICS):
            break
        if counts.get(slug):
            chosen.append((slug, closeness))
    return chosen


# --------------------------------------------------------------------------
# candidates
# --------------------------------------------------------------------------

async def candidates(
    session: AsyncSession,
    slugs: list[str],
    *,
    exclude: set[str] | None = None,
    limit: int = MAX_CANDIDATES,
    per_topic: int = PER_TOPIC_CAP,
) -> list[dict[str, Any]]:
    """Rows the model may choose from: headwords only, frequent enough, unseen.

    Each topic contributes at most `per_topic` rows, taken by frequency.

    `exclude` is the user's own list. A word they already saved belongs in the
    other tab, and offering it again as a discovery is just noise.
    """
    if not slugs:
        return []

    # Rank inside each topic, then keep the head of every one. A plain global
    # `ORDER BY zipf DESC LIMIT n` lets the largest topic eat the budget: on the
    # live base `digitalisierung_computer` and `schule_unterricht` filled a
    # 1 000-row pool between them and `recht_gesetz`, which holds `Verbot` and
    # `Jugendschutz`, contributed nothing at all.
    ranked = (
        select(
            VocabCard.lemma, VocabCard.ru, VocabCard.level, VocabCard.level_est,
            VocabCard.zipf, VocabCard.pos, VocabCard.article, VocabCard.topic,
            func.row_number()
            .over(partition_by=VocabCard.topic, order_by=VocabCard.zipf.desc())
            .label("rn"),
        )
        .where(
            VocabCard.topic.in_(slugs),
            VocabCard.form_kind.is_(None),
            VocabCard.zipf >= CANDIDATE_MIN_ZIPF,
        )
        .subquery()
    )
    rows = (
        await session.execute(
            select(ranked)
            .where(ranked.c.rn <= per_topic)
            .order_by(ranked.c.zipf.desc())
            .limit(limit)
        )
    ).all()

    skip = exclude or set()
    return [
        {
            "lemma": r.lemma,
            "ru": r.ru or "",
            "level": (r.level if r.level and r.level != "unlisted" else r.level_est) or "",
            "zipf": r.zipf,
            "pos": r.pos,
            "article": r.article,
            "topic": r.topic,
        }
        for r in rows
        if r.lemma not in skip
    ]


async def saved_lemmas(session: AsyncSession, user_id: int) -> set[str]:
    rows = (
        await session.execute(
            select(UserWordList.lemma).where(UserWordList.user_id == user_id)
        )
    ).scalars().all()
    return set(rows)


# --------------------------------------------------------------------------
# call 2 — the hundred
# --------------------------------------------------------------------------

_RANK_SYSTEM = (
    "Du stellst die Wortliste für einen Aufsatz zusammen.\n"
    "Du bekommst das Thema, das Niveau des Lernenden und eine Kandidatenliste "
    "(Wort | Übersetzung | Niveau, leer wenn unbekannt).\n"
    "Wähle die Wörter, die man zum Schreiben DIESES Aufsatzes wirklich braucht — "
    "Sachwortschatz, Argumentationswortschatz, typische Kollokationen.\n"
    "Ordne nach Nützlichkeit, das Wichtigste zuerst. Höchstens $N Wörter.\n"
    "Richte dich am Niveau aus: das Niveau des Lernenden und eine Stufe darüber. "
    "Wörter weit darunter kennt er schon, Wörter weit darüber nützen ihm nicht.\n"
    "Eigennamen, Markennamen und Fachjargon ohne Bezug zum Thema gehören nicht "
    "in die Liste.\n"
    'Antworte NUR mit JSON: {"lemmas": ["...", "..."]}\n'
    "Übernimm jedes Wort ZEICHENGENAU aus der Kandidatenliste, "
    "Gross- und Kleinschreibung eingeschlossen. Erfinde nichts dazu."
)
# `$N`, not `{n}`: the prompt itself contains a JSON example, and `str.format`
# reads `{"lemmas": ...}` as a replacement field and raises KeyError on it. The
# tests caught this before the first real call did.
_RANK_SIZE_TOKEN = "$N"


def _rank_user_msg(thema: str, niveau: str, cands: list[dict]) -> str:
    lines = [f"{c['lemma']} | {c['ru']} | {c['level']}" for c in cands]
    return (
        f"Aufsatzthema: {thema}\n"
        f"Niveau: {niveau}\n\n"
        "Kandidaten:\n" + "\n".join(lines)
    )


def parse_ranking(
    reply: dict, cands: list[dict], *, size: int = PACKAGE_SIZE
) -> tuple[list[str], list[str]]:
    """Validate the returned lemmas against what we sent. Returns (kept, dropped).

    Matching is byte-exact and case is significant. This is not pedantry: the
    enrichment pipeline already paid for folding case once — 635 pairs in the
    base came out byte-identical because `parse_response` indexed by
    `word.lower()`, and `morgen` (tomorrow) stopped existing. `Morgen` and
    `morgen` are different words, and a package that quietly resolves one to the
    other puts the wrong card in front of the reader.

    Anything unmatched is dropped rather than repaired. A model that returns a
    word we never sent is not offering a near miss; it is offering a word with
    no card, which is the one thing this whole path exists to prevent.
    """
    by_lemma = {c["lemma"]: c for c in cands}
    kept: list[str] = []
    dropped: list[str] = []
    seen: set[str] = set()

    for item in reply.get("lemmas") or []:
        if not isinstance(item, str) or item in seen:
            continue
        seen.add(item)
        if item in by_lemma:
            kept.append(item)
        else:
            dropped.append(item)
        if len(kept) >= size:
            break
    return kept, dropped


def backfill(kept: list[str], cands: list[dict], *, size: int = PACKAGE_SIZE) -> list[str]:
    """Top the list up from the most frequent candidates the model left out.

    Frequency is a weak signal for topical usefulness — that is the whole reason
    call 2 exists — but it beats handing back a short list because the model
    misspelled fifteen words.
    """
    if len(kept) >= size:
        return kept[:size]
    chosen = set(kept)
    out = list(kept)
    for c in sorted(cands, key=lambda c: (c["zipf"] is None, -(c["zipf"] or 0.0))):
        if len(out) >= size:
            break
        if c["lemma"] not in chosen:
            out.append(c["lemma"])
            chosen.add(c["lemma"])
    return out


# --------------------------------------------------------------------------
# orchestration
# --------------------------------------------------------------------------

def _default_call(messages: list[dict], api_key: str, model: str) -> dict:
    return post_mistral_json(messages, api_key, model, temperature=0.2)


class WortpaketError(RuntimeError):
    """The package could not be built. Carries the stage that failed."""

    def __init__(self, stage: str, detail: str):
        super().__init__(f"{stage}: {detail}")
        self.stage = stage
        self.detail = detail


async def build(
    session: AsyncSession,
    *,
    thema: str,
    niveau: str,
    api_key: str,
    model: str,
    exclude: set[str] | None = None,
    size: int = PACKAGE_SIZE,
    call: Callable[[list[dict], str, str], dict] | None = None,
) -> dict[str, Any]:
    """Build one package. Returns the lemmas plus everything needed to audit it.

    `call` is injectable so tests can drive both model steps without a network
    or a key; production passes nothing and gets `post_mistral_json`.
    """
    call = call or _default_call
    thema = (thema or "").strip()
    if not thema:
        raise WortpaketError("input", "empty thema")

    started = time.monotonic()
    stats: dict[str, Any] = {"prompt_version": PROMPT_VERSION, "thema": thema, "niveau": niveau}

    counts = await catalog_counts(session)
    if not counts:
        raise WortpaketError("catalog", "no topic has any candidate word")

    # ---- call 1
    t0 = time.monotonic()
    msgs = [
        {"role": "system", "content": _TOPICS_SYSTEM},
        {"role": "user", "content": _topics_user_msg(thema, niveau, counts)},
    ]
    try:
        reply = await asyncio.to_thread(call, msgs, api_key, model)
    except Exception as exc:  # noqa: BLE001 — every failure here is the same failure
        raise WortpaketError("topics", f"{type(exc).__name__}: {exc}") from exc
    stats["topics_ms"] = int((time.monotonic() - t0) * 1000)

    ranked = parse_topics(reply, counts)
    if not ranked:
        raise WortpaketError("topics", "model named no known topic")
    chosen = choose_topics(ranked, counts)
    stats["topics"] = [{"slug": s, "closeness": c, "words": counts[s]} for s, c in chosen]
    log.info(
        "wortpaket[%s]: topics %s in %d ms",
        thema[:40],
        ", ".join(f"{s}={c:.2f}({counts[s]})" for s, c in chosen),
        stats["topics_ms"],
    )

    # ---- candidates
    cands = await candidates(session, [s for s, _ in chosen], exclude=exclude)
    stats["pool"] = len(cands)
    stats["excluded"] = len(exclude or ())
    if not cands:
        raise WortpaketError("candidates", "pool is empty after exclusions")

    # ---- call 2
    t0 = time.monotonic()
    msgs = [
        {"role": "system", "content": _RANK_SYSTEM.replace(_RANK_SIZE_TOKEN, str(size))},
        {"role": "user", "content": _rank_user_msg(thema, niveau, cands)},
    ]
    try:
        reply = await asyncio.to_thread(call, msgs, api_key, model)
    except Exception as exc:  # noqa: BLE001
        raise WortpaketError("rank", f"{type(exc).__name__}: {exc}") from exc
    stats["rank_ms"] = int((time.monotonic() - t0) * 1000)

    kept, dropped = parse_ranking(reply, cands, size=size)
    lemmas = backfill(kept, cands, size=size)
    stats["returned"] = len(kept) + len(dropped)
    stats["matched"] = len(kept)
    stats["dropped"] = len(dropped)
    stats["backfilled"] = len(lemmas) - len(kept)
    stats["total_ms"] = int((time.monotonic() - started) * 1000)

    # The dropped words are the early warning that the prompt or the model
    # drifted, so name a few rather than only counting them.
    if dropped:
        log.warning(
            "wortpaket[%s]: %d of %d returned lemmas are not ours, e.g. %s",
            thema[:40], len(dropped), stats["returned"], ", ".join(dropped[:5]),
        )
    log.info(
        "wortpaket[%s]: pool %d → matched %d, backfilled %d, %d ms total",
        thema[:40], len(cands), len(kept), stats["backfilled"], stats["total_ms"],
    )

    return {"lemmas": lemmas, "stats": stats}


def stats_line(stats: dict[str, Any]) -> str:
    """One-line human summary, for ops output and for the failure path."""
    topics = ", ".join(f"{t['slug']} {t['closeness']:.2f}" for t in stats.get("topics", []))
    return (
        f"{stats.get('thema', '?')[:60]} [{stats.get('niveau', '?')}] "
        f"topics={topics or '—'} pool={stats.get('pool', 0)} "
        f"matched={stats.get('matched', 0)} dropped={stats.get('dropped', 0)} "
        f"backfilled={stats.get('backfilled', 0)} {stats.get('total_ms', 0)}ms"
    )


__all__ = [
    "CANDIDATE_MIN_ZIPF", "PACKAGE_SIZE", "PROMPT_VERSION", "WortpaketError",
    "backfill", "build", "candidates", "catalog_counts", "choose_topics",
    "parse_ranking", "parse_topics", "reset_catalog_cache", "saved_lemmas",
    "stats_line",
]

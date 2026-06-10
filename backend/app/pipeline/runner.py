from __future__ import annotations

"""Pipeline runner — orchestrates all steps with a target-driven control loop.

v2 changes:
- Words are written as clean lemmas (lowercase article separate) — matches
  seed/topic-pack convention; routing matches case-insensitively.
- Enrichment runs in batches (settings.pipeline_batch_size words per Mistral
  call) instead of one call per word.
- Control loop: after the article pass, if the topic has fewer than
  target_words words, additional vocabulary is generated directly by Mistral
  (verified against Wiktionary/DWDS) — up to pipeline_max_supplement_rounds.
- Redemittel are extracted from articles and topped up to
  pipeline_min_phrases, balanced across essay parts.
- Failed words are stored in word_failures and retried on the next run.
"""

import asyncio
import logging
from datetime import datetime

from sqlalchemy import func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings
from app.db.models import Phrase, PipelineRun, Word, WordFailure, WordTopic
from app.services.topic_pack_service import ensure_word_topic, normalize_article

from .discovery import discover_sources
from .enrichment import enrich_batch
from .extraction import ESSAY_PARTS, process_sources
from .normalize import dedupe_candidates
from .supplement import generate_redemittel, generate_words
from .types import EnrichedWord, PhraseCandidate, PipelineError, SourceItem, WordCandidate

logger = logging.getLogger(__name__)

_WIKTIONARY_SEM = asyncio.Semaphore(5)
_MISTRAL_SEM = asyncio.Semaphore(1)  # conservative: free Mistral tier has low RPM limit


# ---------------------------------------------------------------------------
# Step 3 — Word Router
# ---------------------------------------------------------------------------

async def _route_words(
    candidates: list[WordCandidate],
    topic: str,
    db: AsyncSession,
) -> tuple[list[WordCandidate], int]:
    """Split candidates into new (to enrich) vs existing (just link topic).

    Matching is case-insensitive on the lemma. Returns (new, linked_count).
    """
    new_candidates: list[WordCandidate] = []
    linked = 0

    for candidate in candidates:
        result = await db.execute(
            select(Word).where(Word.german.ilike(candidate.word)).order_by(Word.id.asc())
        )
        existing = result.scalars().first()

        if existing is not None:
            if await ensure_word_topic(db, existing.id, topic):
                linked += 1
            # Top up examples from the article if the word has few
            if candidate.examples and len(existing.examples or []) < 3:
                current = list(existing.examples or [])
                seen_texts = {
                    (e.get("text_de", "") if isinstance(e, dict) else str(e)).strip().lower()
                    for e in current
                }
                for ex in candidate.examples:
                    if len(current) >= 3:
                        break
                    if ex.strip().lower() not in seen_texts:
                        current.append({"text_de": ex, "is_ai": False})
                        seen_texts.add(ex.strip().lower())
                existing.examples = current
        else:
            new_candidates.append(candidate)

    await db.commit()
    return new_candidates, linked


# ---------------------------------------------------------------------------
# Step 5 — DB Write
# ---------------------------------------------------------------------------

def _pos_to_word_type(pos: str) -> str:
    mapping = {
        "Noun": "noun",
        "Verb": "verb",
        "Adjective": "adjective",
        "Other": "other",
    }
    return mapping.get(pos, "other")


async def _write_word(
    enriched: EnrichedWord,
    topic: str,
    candidate_examples: list[str],
    db: AsyncSession,
) -> None:
    """Insert enriched word (clean lemma) and link to topic."""
    all_examples = candidate_examples + enriched.examples_generated
    examples_payload = []
    for ex in all_examples[:3]:
        examples_payload.append({
            "text_de": ex,
            "is_ai": ex in enriched.examples_generated,
        })

    grammar_payload = {
        "rektion": enriched.rektion,
        "ready_phrase": enriched.ready_phrase,
        "declension": enriched.declension,
    }

    word = Word(
        german=enriched.de,
        article=normalize_article(enriched.article),
        word_type=_pos_to_word_type(enriched.pos),
        translation_ru=enriched.ru,
        level=enriched.level or "B2",
        grammar_data=grammar_payload,
        examples=examples_payload,
        source="pipeline",
    )
    db.add(word)
    await db.flush()  # get word.id

    await ensure_word_topic(db, word.id, topic)
    await db.commit()


async def _write_phrases(
    phrases: list[PhraseCandidate],
    topic: str,
    db: AsyncSession,
) -> int:
    """Insert Redemittel, deduped by (topic, text_de)."""
    added = 0
    for p in phrases:
        exists = await db.execute(
            select(Phrase).where(
                Phrase.topic == topic,
                Phrase.text_de == p.text_de,
            )
        )
        if exists.scalars().first():
            continue
        db.add(Phrase(
            text_de=p.text_de,
            translation_ru=p.translation_ru,
            essay_part=p.essay_part,
            topic=topic,
            level=p.level,
        ))
        added += 1
    await db.commit()
    return added


# ---------------------------------------------------------------------------
# Failure bookkeeping (word_failures)
# ---------------------------------------------------------------------------

async def _load_retry_candidates(topic: str, db: AsyncSession) -> list[WordCandidate]:
    result = await db.execute(
        select(WordFailure).where(
            WordFailure.topic == topic,
            WordFailure.resolved == False,  # noqa: E712
            WordFailure.retry_count < settings.pipeline_max_attempts,
        )
    )
    rows = list(result.scalars().all())
    return [
        WordCandidate(
            word=r.word,
            pos=r.pos,
            article=r.article,
            examples=list(r.examples or []),
            origin="retry",
        )
        for r in rows
    ]


async def _record_failures(
    failed: list[tuple[WordCandidate, PipelineError]],
    topic: str,
    db: AsyncSession,
) -> None:
    for candidate, err in failed:
        result = await db.execute(
            select(WordFailure).where(
                WordFailure.word == candidate.word,
                WordFailure.topic == topic,
            )
        )
        row = result.scalars().first()
        if row:
            row.retry_count += 1
            row.stage = err.stage
            row.error = err.error
        else:
            db.add(WordFailure(
                word=candidate.word,
                topic=topic,
                pos=candidate.pos,
                article=candidate.article,
                examples=candidate.examples,
                stage=err.stage,
                error=err.error,
            ))
    await db.commit()


async def _resolve_failures(words: list[str], topic: str, db: AsyncSession) -> None:
    if not words:
        return
    result = await db.execute(
        select(WordFailure).where(
            WordFailure.topic == topic,
            WordFailure.word.in_(words),
        )
    )
    for row in result.scalars().all():
        row.resolved = True
    await db.commit()


# ---------------------------------------------------------------------------
# Helpers for the control loop
# ---------------------------------------------------------------------------

async def _topic_word_count(topic: str, db: AsyncSession) -> int:
    result = await db.execute(
        select(sa_func.count(WordTopic.id)).where(WordTopic.topic == topic)
    )
    return int(result.scalar() or 0)

async def _topic_lemmas(topic: str, db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(Word.german).join(WordTopic).where(WordTopic.topic == topic)
    )
    return [row[0] for row in result.all()]


async def _topic_phrases(topic: str, db: AsyncSession) -> list[Phrase]:
    result = await db.execute(select(Phrase).where(Phrase.topic == topic))
    return list(result.scalars().all())


def _chunk(items: list, size: int) -> list[list]:
    return [items[i : i + size] for i in range(0, len(items), size)]


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

async def run_pipeline(
    run_id: int,
    topic: str,
    article_urls: list[str],
    session_factory: async_sessionmaker[AsyncSession],
    target_words: int | None = None,
) -> None:
    """Full pipeline run with target-driven control loop."""
    topic = topic.strip().lower()
    target = target_words or settings.pipeline_target_words
    errors: list[PipelineError] = []
    words_added = 0
    words_linked = 0
    phrases_added = 0

    async def _update_run(status: str) -> None:
        async with session_factory() as db:
            run = await db.get(PipelineRun, run_id)
            if run:
                run.status = status
                run.words_added = words_added
                run.words_linked = words_linked
                run.phrases_added = phrases_added
                run.target_words = target
                run.errors_json = [e.to_dict() for e in errors]
                if status in ("completed", "failed"):
                    run.finished_at = datetime.utcnow()
                await db.commit()

    async def _enrich_and_write(candidates: list[WordCandidate]) -> list[str]:
        """Batch-enrich candidates, write successes, record failures.

        Returns list of successfully written lemmas.
        """
        nonlocal words_added
        written: list[str] = []
        for batch in _chunk(candidates, settings.pipeline_batch_size):
            pairs, failed = await enrich_batch(
                batch,
                settings.mistral_api_key,
                settings.mistral_model,
                _WIKTIONARY_SEM,
                _MISTRAL_SEM,
            )
            errors.extend(err for _, err in failed)

            async with session_factory() as db:
                for candidate, enriched in pairs:
                    try:
                        await _write_word(enriched, topic, candidate.examples, db)
                        words_added += 1
                        written.append(candidate.word)
                    except Exception as exc:
                        await db.rollback()
                        errors.append(PipelineError("db", candidate.word, str(exc)))
                        failed.append((candidate, PipelineError("db", candidate.word, str(exc))))
                # bookkeeping
                real_failed = [(c, e) for c, e in failed if c.word not in written]
                if real_failed:
                    await _record_failures(real_failed, topic, db)
                if written:
                    await _resolve_failures(written, topic, db)
        return written

    try:
        # ── Step 0: retry previously failed words ─────────────────────────
        async with session_factory() as db:
            retry_candidates = await _load_retry_candidates(topic, db)
        if retry_candidates:
            logger.info("Retrying %d previously failed words for '%s'", len(retry_candidates), topic)

        # ── Step 1: Source Discovery ──────────────────────────────────────
        sources: list[SourceItem] = []
        if article_urls:
            sources = [SourceItem(url=u, title=u, source_type="article") for u in article_urls]
            logger.info("Using %d user-provided URLs for topic '%s'", len(sources), topic)
        elif settings.grok_api_key:
            sources, disc_errors = await discover_sources(topic, settings.grok_api_key)
            errors.extend(disc_errors)

        if not sources and not settings.mistral_api_key:
            errors.append(PipelineError(
                "fetch", "discovery",
                "No sources (GROK_API_KEY/article_urls) and no MISTRAL_API_KEY for generation",
            ))
            await _update_run("failed")
            return

        # ── Step 2: Article Parsing + Word & Redemittel Extraction ───────
        candidates: list[WordCandidate] = []
        article_phrases: list[PhraseCandidate] = []
        if sources:
            candidates, article_phrases, ext_errors = await process_sources(
                sources,
                topic,
                settings.mistral_api_key,
                settings.mistral_model,
                fetch_semaphore=asyncio.Semaphore(5),
                mistral_semaphore=asyncio.Semaphore(2),
            )
            errors.extend(ext_errors)
            logger.info(
                "Extracted %d candidates, %d redemittel for '%s'",
                len(candidates), len(article_phrases), topic,
            )

        candidates = dedupe_candidates(retry_candidates + candidates)

        # ── Step 3: Word Router ───────────────────────────────────────────
        async with session_factory() as db:
            new_candidates, linked = await _route_words(candidates, topic, db)
        words_linked = linked
        logger.info("Routing: %d new, %d linked for '%s'", len(new_candidates), linked, topic)
        await _update_run("running")

        # ── Step 4+5: Batch enrichment + DB write ─────────────────────────
        await _enrich_and_write(new_candidates)
        await _update_run("running")

        # ── Step 6: Control loop — top up to target_words ────────────────
        for round_no in range(settings.pipeline_max_supplement_rounds):
            async with session_factory() as db:
                have = await _topic_word_count(topic, db)
                existing_lemmas = await _topic_lemmas(topic, db)
            if have >= target:
                break
            need = target - have
            logger.info(
                "Supplement round %d for '%s': have %d, need %d more",
                round_no + 1, topic, have, need,
            )
            from .supplement import round_focus

            gen_candidates, gen_errors = await generate_words(
                topic,
                min(need + 5, 30),  # small overshoot — some will fail verification
                existing_lemmas,
                settings.mistral_api_key,
                settings.mistral_model,
                _MISTRAL_SEM,
                focus=round_focus(round_no),
            )
            errors.extend(gen_errors)
            if not gen_candidates:
                break
            async with session_factory() as db:
                gen_new, gen_linked = await _route_words(gen_candidates, topic, db)
            words_linked += gen_linked
            await _enrich_and_write(gen_new)
            await _update_run("running")

        # ── Step 7: Redemittel — write + top up to min_phrases ───────────
        async with session_factory() as db:
            phrases_added += await _write_phrases(article_phrases, topic, db)
            existing_phrases = await _topic_phrases(topic, db)

        if len(existing_phrases) < settings.pipeline_min_phrases:
            per_part = {p: 0 for p in ESSAY_PARTS}
            for ph in existing_phrases:
                if ph.essay_part in per_part:
                    per_part[ph.essay_part] += 1
            # aim for an even spread
            base = max(2, settings.pipeline_min_phrases // len(ESSAY_PARTS))
            needed = {part: max(0, base - count) for part, count in per_part.items()}
            gen_phrases, ph_errors = await generate_redemittel(
                topic,
                needed,
                [p.text_de for p in existing_phrases],
                settings.mistral_api_key,
                settings.mistral_model,
                _MISTRAL_SEM,
            )
            errors.extend(ph_errors)
            if gen_phrases:
                async with session_factory() as db:
                    phrases_added += await _write_phrases(gen_phrases, topic, db)

    except Exception as exc:
        logger.exception("Pipeline run %d failed: %s", run_id, exc)
        errors.append(PipelineError("fetch", "pipeline", str(exc)))
        await _update_run("failed")
        return

    # Failed if nothing at all was produced
    if words_added == 0 and words_linked == 0:
        await _update_run("failed")
        return

    await _update_run("completed")
    logger.info(
        "Pipeline run %d done: +%d words, %d linked, +%d phrases, %d errors",
        run_id, words_added, words_linked, phrases_added, len(errors),
    )

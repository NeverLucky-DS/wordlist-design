from __future__ import annotations

"""Pipeline runner — orchestrates all 5 steps and writes results to DB."""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import PipelineRun, Word, WordTopic
from app.config import settings

from .discovery import discover_sources
from .enrichment import enrich_word
from .extraction import process_sources
from .types import EnrichedWord, PipelineError, SourceItem, WordCandidate

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

    Returns (new_candidates, linked_count).
    """
    new_candidates: list[WordCandidate] = []
    linked = 0

    for candidate in candidates:
        result = await db.execute(
            select(Word).where(Word.german == candidate.word)
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            # Link topic if not already linked
            try:
                db.add(WordTopic(word_id=existing.id, topic=topic))
                await db.flush()
            except IntegrityError:
                await db.rollback()
            linked += 1
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
    """Upsert word into DB and link to topic."""
    all_examples = candidate_examples + enriched.examples_generated
    examples_payload = []
    for i, ex in enumerate(all_examples[:3]):
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
        article=enriched.article,
        word_type=_pos_to_word_type(enriched.pos),
        translation_ru=enriched.ru,
        level=enriched.level or "B2",
        grammar_data=grammar_payload,
        examples=examples_payload,
        source="pipeline",
    )
    db.add(word)
    await db.flush()  # get word.id

    try:
        db.add(WordTopic(word_id=word.id, topic=topic))
        await db.commit()
    except IntegrityError:
        await db.rollback()
        await db.commit()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

async def run_pipeline(
    run_id: int,
    topic: str,
    article_urls: list[str],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Full pipeline run: discovery → extraction → routing → enrichment → DB write."""
    errors: list[PipelineError] = []
    words_added = 0
    words_linked = 0

    async def _update_run(status: str) -> None:
        async with session_factory() as db:
            run = await db.get(PipelineRun, run_id)
            if run:
                run.status = status
                run.words_added = words_added
                run.words_linked = words_linked
                run.errors_json = [e.to_dict() for e in errors]
                if status in ("completed", "failed"):
                    from datetime import datetime
                    run.finished_at = datetime.utcnow()
                await db.commit()

    try:
        # ── Step 1: Source Discovery ──────────────────────────────────────
        if article_urls:
            # User provided URLs — skip Grok
            sources = [SourceItem(url=u, title=u, source_type="article") for u in article_urls]
            logger.info("Using %d user-provided URLs for topic '%s'", len(sources), topic)
        elif settings.grok_api_key:
            sources, disc_errors = await discover_sources(topic, settings.grok_api_key)
            errors.extend(disc_errors)
        else:
            errors.append(PipelineError("fetch", "discovery", "No GROK_API_KEY and no article_urls provided"))
            await _update_run("failed")
            return

        if not sources:
            await _update_run("failed")
            return

        # ── Step 2: Article Parsing + Word Extraction ─────────────────────
        candidates, ext_errors = await process_sources(
            sources,
            topic,
            settings.mistral_api_key,
            settings.mistral_model,
            fetch_semaphore=asyncio.Semaphore(5),
            mistral_semaphore=asyncio.Semaphore(3),
        )
        errors.extend(ext_errors)
        logger.info("Extracted %d unique word candidates for '%s'", len(candidates), topic)

        if not candidates:
            await _update_run("failed")
            return

        # ── Step 3: Word Router ───────────────────────────────────────────
        async with session_factory() as db:
            new_candidates, linked = await _route_words(candidates, topic, db)
        words_linked = linked
        logger.info("Routing: %d new, %d linked for topic '%s'", len(new_candidates), linked, topic)

        # ── Step 4+5: Enrich new words and write to DB ────────────────────
        async def _enrich_and_write(candidate: WordCandidate) -> None:
            nonlocal words_added
            enriched, enr_errors = await enrich_word(
                candidate,
                settings.mistral_api_key,
                settings.mistral_model,
                _WIKTIONARY_SEM,
                _MISTRAL_SEM,
            )
            errors.extend(enr_errors)

            if enriched is None:
                return

            async with session_factory() as db:
                try:
                    await _write_word(enriched, topic, candidate.examples, db)
                    words_added += 1
                except Exception as exc:
                    errors.append(PipelineError("db", candidate.word, str(exc)))

        await asyncio.gather(*[_enrich_and_write(c) for c in new_candidates])

    except Exception as exc:
        logger.exception("Pipeline run %d failed: %s", run_id, exc)
        errors.append(PipelineError("fetch", "pipeline", str(exc)))
        await _update_run("failed")
        return

    await _update_run("completed")
    logger.info(
        "Pipeline run %d done: +%d words, %d linked, %d errors",
        run_id, words_added, words_linked, len(errors),
    )

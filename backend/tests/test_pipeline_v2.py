"""Tests for pipeline v2: control loop, redemittel, failure retry."""

from __future__ import annotations

from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import settings
from app.db.models import Phrase, PipelineRun, Word, WordFailure, WordTopic
from app.pipeline.types import EnrichedWord, PhraseCandidate, PipelineError, WordCandidate


def _mk_enriched(c: WordCandidate) -> EnrichedWord:
    return EnrichedWord(
        de=c.word,
        article=c.article,
        pos=c.pos or "Noun",
        level="B2",
        ru="перевод",
        rektion="",
        ready_phrase="",
        declension={"Genus": "x"},
        examples_generated=[f"Beispiel mit {c.word}."],
    )


async def _fake_enrich_batch(candidates, *args, **kwargs):
    return [(c, _mk_enriched(c)) for c in candidates], []


async def _run(db_session, topic="klimatest", target=8, **patches):
    from app.pipeline.runner import run_pipeline

    run = PipelineRun(topic=topic, status="running")
    db_session.add(run)
    await db_session.commit()
    await db_session.refresh(run)

    session_factory = async_sessionmaker(db_session.bind, expire_on_commit=False)
    await run_pipeline(run.id, topic, ["http://example.test/a"], session_factory, target_words=target)
    return run.id, session_factory


async def test_control_loop_tops_up_to_target(db_session):
    article_words = [
        WordCandidate(word=f"Artikelwort{i}", pos="Noun", article="das", examples=["S."])
        for i in range(1, 5)
    ]
    gen_words = [
        WordCandidate(word=f"Generiert{i}", pos="Noun", article="die", origin="generated")
        for i in range(1, 7)
    ]

    async def fake_process_sources(*a, **kw):
        return article_words, [PhraseCandidate(text_de="Daraus folgt, dass ...", essay_part="schluss")], []

    async def fake_generate_words(topic, n, exclude, *a, **kw):
        return gen_words, []

    async def fake_generate_redemittel(topic, needed, exclude, *a, **kw):
        return [
            PhraseCandidate(text_de=f"Redemittel {i} ...", essay_part="argument")
            for i in range(1, 6)
        ], []

    with (
        patch("app.pipeline.runner.process_sources", side_effect=fake_process_sources),
        patch("app.pipeline.runner.enrich_batch", side_effect=_fake_enrich_batch),
        patch("app.pipeline.runner.generate_words", side_effect=fake_generate_words),
        patch("app.pipeline.runner.generate_redemittel", side_effect=fake_generate_redemittel),
        patch.object(settings, "mistral_api_key", "test-key"),
        patch.object(settings, "pipeline_min_phrases", 4),
    ):
        run_id, session_factory = await _run(db_session, target=8)

    async with session_factory() as db:
        run = await db.get(PipelineRun, run_id)
        n_words = len((await db.execute(
            select(WordTopic).where(WordTopic.topic == "klimatest")
        )).scalars().all())
        n_phrases = len((await db.execute(
            select(Phrase).where(Phrase.topic == "klimatest")
        )).scalars().all())

    assert run.status == "completed"
    # 4 article words + supplement up to target 8
    assert n_words >= 8
    assert run.words_added >= 8
    # 1 article redemittel + generated up to min_phrases
    assert n_phrases >= 4
    assert run.phrases_added >= 4


async def test_words_written_as_clean_lemmas(db_session):
    dirty = [WordCandidate(word="die Anpassung (an + Akk.)", pos="Noun")]

    async def fake_process_sources(*a, **kw):
        # runner receives candidates already normalised by extraction;
        # here we emulate extraction by normalising manually
        from app.pipeline.normalize import normalize_candidate
        return [normalize_candidate(c) for c in dirty], [], []

    with (
        patch("app.pipeline.runner.process_sources", side_effect=fake_process_sources),
        patch("app.pipeline.runner.enrich_batch", side_effect=_fake_enrich_batch),
        patch("app.pipeline.runner.generate_words", return_value=([], [])),
        patch("app.pipeline.runner.generate_redemittel", return_value=([], [])),
        patch.object(settings, "mistral_api_key", "test-key"),
        patch.object(settings, "pipeline_min_phrases", 0),
        patch.object(settings, "pipeline_max_supplement_rounds", 0),
    ):
        _, session_factory = await _run(db_session, topic="lemmatest", target=1)

    async with session_factory() as db:
        word = (await db.execute(
            select(Word).where(Word.german == "Anpassung")
        )).scalars().first()
    assert word is not None
    assert word.article == "die"
    assert "(" not in word.german


async def test_failed_words_recorded_and_retried(db_session):
    failing = WordCandidate(word="Schwierigwort", pos="Noun", article="das")

    async def enrich_fail_all(candidates, *a, **kw):
        return [], [
            (c, PipelineError("mistral", c.word, "boom")) for c in candidates
        ]

    async def fake_process_sources(*a, **kw):
        return [failing], [], []

    common = dict(
        mistral_api_key="test-key",
        pipeline_min_phrases=0,
        pipeline_max_supplement_rounds=0,
    )

    # Run 1 — everything fails → word_failures row, run failed (nothing added)
    with (
        patch("app.pipeline.runner.process_sources", side_effect=fake_process_sources),
        patch("app.pipeline.runner.enrich_batch", side_effect=enrich_fail_all),
        patch("app.pipeline.runner.generate_words", return_value=([], [])),
        patch("app.pipeline.runner.generate_redemittel", return_value=([], [])),
        patch.object(settings, "mistral_api_key", common["mistral_api_key"]),
        patch.object(settings, "pipeline_min_phrases", 0),
        patch.object(settings, "pipeline_max_supplement_rounds", 0),
    ):
        _, session_factory = await _run(db_session, topic="retrytest", target=1)

    async with session_factory() as db:
        failure = (await db.execute(
            select(WordFailure).where(WordFailure.topic == "retrytest")
        )).scalars().first()
    assert failure is not None
    assert failure.word == "Schwierigwort"
    assert failure.resolved is False

    # Run 2 — no new sources, retry candidate gets enriched → resolved
    async def empty_sources(*a, **kw):
        return [], [], []

    with (
        patch("app.pipeline.runner.process_sources", side_effect=empty_sources),
        patch("app.pipeline.runner.enrich_batch", side_effect=_fake_enrich_batch),
        patch("app.pipeline.runner.generate_words", return_value=([], [])),
        patch("app.pipeline.runner.generate_redemittel", return_value=([], [])),
        patch.object(settings, "mistral_api_key", common["mistral_api_key"]),
        patch.object(settings, "pipeline_min_phrases", 0),
        patch.object(settings, "pipeline_max_supplement_rounds", 0),
    ):
        _, session_factory = await _run(db_session, topic="retrytest", target=1)

    async with session_factory() as db:
        word = (await db.execute(
            select(Word).where(Word.german == "Schwierigwort")
        )).scalars().first()
        failure = (await db.execute(
            select(WordFailure).where(WordFailure.topic == "retrytest")
        )).scalars().first()
    assert word is not None
    assert failure.resolved is True


async def test_scheduler_processes_queue_item(db_session):
    from app.db.models import TopicQueueItem
    from app.pipeline import scheduler

    db_session.add(TopicQueueItem(topic="Queuethema", target_words=2))
    await db_session.commit()

    session_factory = async_sessionmaker(db_session.bind, expire_on_commit=False)

    async def fake_run_pipeline(run_id, topic, urls, factory, target_words=None):
        async with factory() as db:
            run = await db.get(PipelineRun, run_id)
            run.status = "completed"
            run.words_added = 2
            await db.commit()
            # satisfy the word-count check
            w1 = Word(german="Qw1", word_type="noun", translation_ru="x", level="B2", examples=[])
            w2 = Word(german="Qw2", word_type="noun", translation_ru="x", level="B2", examples=[])
            db.add_all([w1, w2])
            await db.flush()
            db.add_all([
                WordTopic(word_id=w1.id, topic="queuethema"),
                WordTopic(word_id=w2.id, topic="queuethema"),
            ])
            await db.commit()

    with patch.object(scheduler, "run_pipeline", side_effect=fake_run_pipeline):
        ran = await scheduler.process_next_topic(session_factory)

    assert ran is True
    async with session_factory() as db:
        item = (await db.execute(select(TopicQueueItem))).scalars().first()
    assert item.status == "done"
    assert item.last_run_id is not None

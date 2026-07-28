"""Running a Wortpaket build in the background — and always leaving a trace.

The failure this guards against is not a wrong package; it is a package that
never happens and never says so. `PLANS.md` 0d records a week spent unable to
answer whether `mirror.periodic_sync` had died, precisely because a live
background task and a dead one look identical from outside. So every exit from
the job has to be a row in the database, and the tests below are mostly about
the exits nobody wants to think about: no key, the model refusing, an exception
nobody predicted.
"""
from __future__ import annotations

from collections.abc import Callable

import pytest
from app.db.models import Essay, EssayWordPackage, User, VocabCard
from app.vocab import norm, wortpaket, wortpaket_jobs


@pytest.fixture(autouse=True)
def _clear_caches():
    wortpaket.reset_catalog_cache()
    yield
    wortpaket.reset_catalog_cache()


async def _setup(session, *, with_key: bool = True) -> tuple[int, int]:
    """One user, one essay, one pending package, three candidate cards."""
    user = User(email="w@example.com", password_hash="x")
    if with_key:
        from app.services import crypto
        user.mistral_key_enc = crypto.encrypt("test-key")
    session.add(user)
    await session.flush()

    essay = Essay(user_id=user.id, title="Smartphoneverbot", topic="smartphoneverbot",
                  level="B2")
    session.add(essay)
    await session.flush()

    for lemma, ru, zipf in [("Verbot", "запрет", 4.4), ("Sucht", "зависимость", 5.0),
                            ("Ablenkung", "отвлечение", 3.7)]:
        session.add(VocabCard(
            lemma=lemma, lemma_norm=norm.fold_de(lemma), lemma_ascii=norm.ascii_de(lemma),
            level="unlisted", band="C1", pos="noun", article="die", ru=ru,
            confidence="high", data={"ru_all": [ru]}, zipf=zipf,
            topic="recht_gesetz", source_created_at=0.0,
        ))

    pkg = EssayWordPackage(
        essay_id=essay.id, thema="Sollten Smartphones an Schulen verboten werden?",
        niveau="B2", status="pending")
    session.add(pkg)
    await session.commit()
    return pkg.id, user.id


class _Replies:
    def __init__(self, topics: dict, rank: dict):
        self.topics, self.rank, self.n = topics, rank, 0

    def __call__(self, messages, api_key, model):
        self.n += 1
        return self.topics if self.n == 1 else self.rank


async def _run_with(monkeypatch, session, replies, **kw) -> Callable:
    """Drive `_run` directly against the test session.

    The job normally opens its own `SessionLocal`; the tests hand it the one the
    fixtures already populated, because a second engine would not see them.
    """
    import contextlib

    @contextlib.asynccontextmanager
    async def _session_factory():
        yield session

    monkeypatch.setattr(wortpaket_jobs, "SessionLocal", _session_factory)

    real_build = wortpaket.build

    async def build(db, **kwargs):
        return await real_build(db, call=replies, **{**kwargs, **kw})

    monkeypatch.setattr(wortpaket_jobs.wortpaket, "build", build)
    return real_build


async def test_a_finished_build_lands_in_the_row(db_session, monkeypatch):
    pkg_id, user_id = await _setup(db_session)
    replies = _Replies({"topics": [{"slug": "recht_gesetz", "closeness": 0.9}]},
                       {"lemmas": ["Sucht", "Verbot"]})
    await _run_with(monkeypatch, db_session, replies, size=2)

    await wortpaket_jobs._run(pkg_id, user_id)

    row = await db_session.get(EssayWordPackage, pkg_id)
    await db_session.refresh(row)
    assert row.status == "ready"
    assert row.lemmas == ["Sucht", "Verbot"]
    assert row.prompt_version == wortpaket.PROMPT_VERSION
    assert row.finished_at is not None
    assert row.error_message is None
    assert row.stats["matched"] == 2, "the audit trail is stored, not only logged"


async def test_a_missing_key_is_a_failed_row_not_a_silent_stop(db_session, monkeypatch):
    """The account looked configured and the worker died quietly — that exact
    pairing already shipped once, after a MISTRAL_KEY_SECRET rotation."""
    pkg_id, user_id = await _setup(db_session, with_key=False)
    await _run_with(monkeypatch, db_session, _Replies({}, {}))

    await wortpaket_jobs._run(pkg_id, user_id)

    row = await db_session.get(EssayWordPackage, pkg_id)
    await db_session.refresh(row)
    assert row.status == "failed"
    assert "key" in (row.error_message or "")
    assert row.finished_at is not None


async def test_a_refused_topic_names_the_stage_that_broke(db_session, monkeypatch):
    pkg_id, user_id = await _setup(db_session)
    replies = _Replies({"topics": [{"slug": "kein_solches_thema", "closeness": 1.0}]}, {})
    await _run_with(monkeypatch, db_session, replies)

    await wortpaket_jobs._run(pkg_id, user_id)

    row = await db_session.get(EssayWordPackage, pkg_id)
    await db_session.refresh(row)
    assert row.status == "failed"
    assert "[topics]" in row.error_message, "the stage is in the row, not only in a log"


async def test_an_unexpected_exception_still_writes_the_row(db_session, monkeypatch):
    """Anything that escapes is still a state. A background task that ends on an
    uncaught exception leaves the drawer spinning forever."""
    pkg_id, user_id = await _setup(db_session)

    import contextlib

    @contextlib.asynccontextmanager
    async def _session_factory():
        yield db_session

    monkeypatch.setattr(wortpaket_jobs, "SessionLocal", _session_factory)

    async def boom(db, **kwargs):
        raise ValueError("something nobody predicted")

    monkeypatch.setattr(wortpaket_jobs.wortpaket, "build", boom)

    await wortpaket_jobs._run(pkg_id, user_id)

    row = await db_session.get(EssayWordPackage, pkg_id)
    await db_session.refresh(row)
    assert row.status == "failed"
    assert "unexpected ValueError" in row.error_message


async def test_a_vanished_row_does_not_raise(db_session, monkeypatch):
    """The essay can be deleted while its package is still being built."""
    import contextlib

    @contextlib.asynccontextmanager
    async def _session_factory():
        yield db_session

    monkeypatch.setattr(wortpaket_jobs, "SessionLocal", _session_factory)
    await wortpaket_jobs._run(999_999, 1)   # must not raise


async def test_the_build_excludes_words_the_user_already_saved(db_session, monkeypatch):
    from app.db.models import UserWordList

    pkg_id, user_id = await _setup(db_session)
    db_session.add(UserWordList(user_id=user_id, lemma="Sucht", ru="зависимость"))
    await db_session.commit()

    seen: dict = {}
    real_build = wortpaket.build

    import contextlib

    @contextlib.asynccontextmanager
    async def _session_factory():
        yield db_session

    monkeypatch.setattr(wortpaket_jobs, "SessionLocal", _session_factory)

    async def build(db, **kwargs):
        seen.update(kwargs)
        return await real_build(
            db, call=_Replies({"topics": [{"slug": "recht_gesetz", "closeness": 0.9}]},
                              {"lemmas": []}),
            **{**kwargs, "size": 5})

    monkeypatch.setattr(wortpaket_jobs.wortpaket, "build", build)
    await wortpaket_jobs._run(pkg_id, user_id)

    assert seen["exclude"] == {"Sucht"}
    row = await db_session.get(EssayWordPackage, pkg_id)
    await db_session.refresh(row)
    assert "Sucht" not in row.lemmas


def test_starting_the_same_package_twice_does_not_double_run():
    """Two clicks on refresh must not spend two pairs of model calls."""
    assert not wortpaket_jobs.is_running(4242)
    wortpaket_jobs._tasks[4242] = object()  # type: ignore[assignment]
    try:
        assert wortpaket_jobs.is_running(4242)
        wortpaket_jobs.start_package_job(4242, 1)
        assert len(wortpaket_jobs._tasks) == 1, "no second task was created"
    finally:
        wortpaket_jobs._tasks.pop(4242, None)

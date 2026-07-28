"""Running a Wortpaket build off the request path.

Two model calls take seconds, and the one thing this must never do is make
someone wait to start writing. So the row is created `pending`, the request
returns, and the build happens here.

Shaped after `services/analysis_jobs.py` — same task registry, same "write the
outcome into the row" contract — because a second, subtly different way of
running background work in one codebase is how one of them stops being watched.

**Every exit writes the row.** A background task whose exception goes nowhere is
already a known failure mode in this project: `PLANS.md` 0d spent a week
suspecting `mirror.periodic_sync` had died silently, and the reason it was hard
to answer was that a healthy task and a dead one looked identical from outside.
Here `ready` and `failed` are both states in the database, `failed` carries the
stage that broke, and the drawer can say so without anyone reading logs.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from app.config import settings
from app.db.models import EssayWordPackage, User
from app.db.session import SessionLocal
from app.services import crypto
from app.vocab import wortpaket

log = logging.getLogger(__name__)

# Strong references to running tasks. Without this the event loop is free to
# garbage-collect a task nobody holds, and the build would vanish mid-flight
# with no error anywhere.
_tasks: dict[int, asyncio.Task] = {}


def _now() -> datetime:
    # `finished_at` is a naive-UTC column, like every other timestamp here.
    return datetime.now(UTC).replace(tzinfo=None)


def start_package_job(package_id: int, user_id: int) -> None:
    """Kick off one build. Returns immediately; the row carries the outcome."""
    if package_id in _tasks:
        log.info("wortpaket job %s already running, not starting a second", package_id)
        return
    task = asyncio.create_task(_run(package_id, user_id), name=f"wortpaket-{package_id}")
    _tasks[package_id] = task
    task.add_done_callback(lambda _: _tasks.pop(package_id, None))


def is_running(package_id: int) -> bool:
    return package_id in _tasks


async def stop_package_jobs() -> None:
    """Cancel everything in flight, for shutdown.

    Rows left `running` are not repaired here on purpose: a package that was
    interrupted by a restart should look interrupted, and the refresh button is
    one click. Silently marking them failed would hide how often restarts land
    mid-build.
    """
    for task in list(_tasks.values()):
        task.cancel()
    if _tasks:
        await asyncio.gather(*_tasks.values(), return_exceptions=True)
    _tasks.clear()


async def _fail(db, row: EssayWordPackage, message: str) -> None:
    row.status = "failed"
    row.error_message = message[:2000]
    row.finished_at = _now()
    await db.commit()
    log.warning("wortpaket %s failed: %s", row.id, message)


async def _run(package_id: int, user_id: int) -> None:
    async with SessionLocal() as db:
        row = await db.get(EssayWordPackage, package_id)
        if row is None:
            log.warning("wortpaket job %s: row is gone, nothing to build", package_id)
            return

        user = await db.get(User, user_id)
        # The build spends the account's own Mistral key, so "has a key" has to
        # mean "we can decrypt it", not "the column is not NULL" — the weaker
        # test already shipped a bug once, after a MISTRAL_KEY_SECRET rotation
        # left every account looking configured and every worker failing.
        api_key = crypto.decrypt(user.mistral_key_enc) if user and user.mistral_key_enc else None
        if not api_key:
            await _fail(db, row, "no usable Mistral key on this account")
            return

        row.status = "running"
        await db.commit()

        try:
            exclude = await wortpaket.saved_lemmas(db, user_id)
            result = await wortpaket.build(
                # The model is configured once (`config.mistral_model`) and read
                # here rather than named again: a second literal is a second
                # thing to remember on the day it changes.
                db, thema=row.thema, niveau=row.niveau,
                api_key=api_key, model=settings.mistral_model, exclude=exclude,
            )
        except wortpaket.WortpaketError as exc:
            await _fail(db, row, f"[{exc.stage}] {exc.detail}")
            return
        except asyncio.CancelledError:
            log.info("wortpaket %s cancelled mid-build", package_id)
            raise
        except Exception as exc:  # noqa: BLE001 — an unexpected break is still a state
            await _fail(db, row, f"unexpected {type(exc).__name__}: {exc}")
            return

        row.lemmas = result["lemmas"]
        row.stats = result["stats"]
        row.prompt_version = wortpaket.PROMPT_VERSION
        row.status = "ready"
        row.error_message = None
        row.finished_at = _now()
        await db.commit()
        log.info("wortpaket %s ready: %s", package_id, wortpaket.stats_line(result["stats"]))

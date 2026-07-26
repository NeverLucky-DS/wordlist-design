"""The gate on POST /api/vocab/build.

`run_build` opens with `db_path.unlink()` on the live, bind-mounted vocab.db, so
this is not an expensive endpoint — it is a destructive one. Until 2026-07-26 it
carried no dependency at all while every enrichment route beside it did, and the
backend listens on 0.0.0.0 with CORS widened to the LAN. One anonymous POST
deleted the ingestion table and rebuilt it from the dictionary dumps alone,
dropping the 19 152 rows the Wiktionary intake had written straight into it; the
newest backup predated that intake by five days.

These tests exist so the dependency cannot be dropped again by accident. They
never let the real worker start: the admin case replaces it, and the two refusal
cases short-circuit inside the dependency, before the thread is ever spawned.
"""

from __future__ import annotations

import pytest

ADMIN_EMAIL = "regular@example.com"   # the non_admin_client fixture's account


@pytest.fixture(autouse=True)
def _never_build(monkeypatch):
    """Stand in for the worker and hand back a pristine JOB to the next test."""
    from app.vocab import api

    calls: list[float] = []

    def _fake_worker(min_zipf: float) -> None:
        calls.append(min_zipf)
        with api._LOCK:
            api.JOB["running"] = False

    monkeypatch.setattr(api, "_worker", _fake_worker)
    monkeypatch.setattr(api, "JOB", dict(api.JOB))
    return calls


def _as_admin(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "admin_emails", ADMIN_EMAIL)


async def test_build_is_closed_to_guests(guest_client, monkeypatch, _never_build):
    _as_admin(monkeypatch)
    assert (await guest_client.post("/api/vocab/build")).status_code == 401
    assert _never_build == [], "the worker must not start for an unauthenticated caller"


async def test_build_is_closed_to_non_admins(non_admin_client, monkeypatch, _never_build):
    from app.config import settings

    monkeypatch.setattr(settings, "admin_emails", "someone-else@example.com")
    assert (await non_admin_client.post("/api/vocab/build")).status_code == 403
    assert _never_build == [], "a logged-in non-admin must not rebuild the dictionary"


async def test_build_still_works_for_an_admin(non_admin_client, monkeypatch, _never_build):
    """The gate must not have turned `principal` into a query parameter."""
    _as_admin(monkeypatch)
    r = await non_admin_client.post("/api/vocab/build?min_zipf=3.5")
    assert r.status_code == 200, r.text
    assert r.json() == {"ok": True, "min_zipf": 3.5}
    assert _never_build == [3.5], "min_zipf must still reach the worker"

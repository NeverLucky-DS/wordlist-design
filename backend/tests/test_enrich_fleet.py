"""Admin fleet control — the gate, and the blast radius of one bad account."""

from __future__ import annotations

import pytest

from app.db.models import User

ADMIN_EMAIL = "regular@example.com"   # the non_admin_client fixture's account


@pytest.fixture(autouse=True)
def _isolate_workers(monkeypatch, tmp_path):
    """Never touch the real worker registry or the real enrichment.db."""
    from app.vocab import enrich, enrich_worker

    monkeypatch.setattr(enrich, "ENRICH_DB", tmp_path / "enrichment.db")
    monkeypatch.setattr(enrich, "VOCAB_DB", tmp_path / "vocab.db")
    monkeypatch.setattr(enrich_worker, "_workers", {})
    monkeypatch.setattr(enrich_worker, "_plan_result", None)


def _as_admin(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "admin_emails", ADMIN_EMAIL)


async def _attach_key(db_session, email: str, key: str = "sk-test-key") -> User:
    from sqlalchemy import select

    from app.services import crypto

    user = (await db_session.execute(
        select(User).where(User.email == email))).scalars().one()
    user.mistral_key_enc = crypto.encrypt(key)
    await db_session.commit()
    return user


# ── the gate ────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("path", ["/api/vocab/enrich/fleet",
                                  "/api/vocab/enrich/fleet/start",
                                  "/api/vocab/enrich/fleet/stop"])
async def test_fleet_is_closed_to_non_admins(non_admin_client, monkeypatch, path):
    """These routes spend other people's keys. A logged-in account is not enough."""
    from app.config import settings

    monkeypatch.setattr(settings, "admin_emails", "someone-else@example.com")
    method = non_admin_client.get if path.endswith("fleet") else non_admin_client.post
    assert (await method(path)).status_code == 403


@pytest.mark.parametrize("path", ["/api/vocab/enrich/fleet",
                                  "/api/vocab/enrich/fleet/start",
                                  "/api/vocab/enrich/fleet/stop"])
async def test_fleet_is_closed_to_guests(guest_client, monkeypatch, path):
    _as_admin(monkeypatch)
    method = guest_client.get if path.endswith("fleet") else guest_client.post
    assert (await method(path)).status_code == 401


async def test_fleet_is_closed_when_no_admin_is_configured(non_admin_client,
                                                           monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "admin_emails", "")
    assert (await non_admin_client.get("/api/vocab/enrich/fleet")).status_code == 403


# ── listing ─────────────────────────────────────────────────────────────────
async def test_fleet_lists_accounts_and_flags_missing_keys(
        non_admin_client, db_session, monkeypatch):
    _as_admin(monkeypatch)
    body = (await non_admin_client.get("/api/vocab/enrich/fleet")).json()
    rows = {a["email"]: a for a in body["accounts"]}
    assert ADMIN_EMAIL in rows
    assert rows[ADMIN_EMAIL]["has_key"] is False   # keyless accounts stay visible
    assert rows[ADMIN_EMAIL]["running"] is False
    assert body["with_key"] == 0 and body["running"] == 0


async def test_fleet_reports_token_spend_per_account(
        non_admin_client, db_session, monkeypatch):
    from app.vocab import enrich

    _as_admin(monkeypatch)
    user = await _attach_key(db_session, ADMIN_EMAIL)
    enrich.record_usage(user.id, {"total_tokens": 1234})

    body = (await non_admin_client.get("/api/vocab/enrich/fleet")).json()
    row = next(a for a in body["accounts"] if a["email"] == ADMIN_EMAIL)
    assert row["tokens_total"] == 1234 and row["has_key"] is True
    assert body["tokens_total"] == 1234 and body["with_key"] == 1


# ── starting ────────────────────────────────────────────────────────────────
async def test_fleet_start_needs_at_least_one_key(non_admin_client, monkeypatch):
    _as_admin(monkeypatch)
    res = await non_admin_client.post("/api/vocab/enrich/fleet/start", json={})
    assert res.status_code == 400


async def test_fleet_start_launches_every_keyed_account(
        non_admin_client, db_session, monkeypatch):
    from app.vocab import enrich_worker

    _as_admin(monkeypatch)
    await _attach_key(db_session, ADMIN_EMAIL)
    calls = []
    monkeypatch.setattr(enrich_worker, "start_worker",
                        lambda uid, key, model, batch: calls.append((uid, key)) or
                        {"already_running": False, "plan": {}})

    res = await non_admin_client.post("/api/vocab/enrich/fleet/start", json={})
    assert res.status_code == 200
    assert res.json()["started"] == [ADMIN_EMAIL]
    assert calls and calls[0][1] == "sk-test-key"   # the account's OWN key


async def test_one_unreadable_key_does_not_stop_the_rest(
        non_admin_client, db_session, monkeypatch):
    """Ten accounts run overnight. If account #4's key was encrypted under an old
    server secret, the other nine must still start — and the panel must say which
    one failed rather than the whole call blowing up."""
    from app.services import crypto
    from app.vocab import enrich_worker

    _as_admin(monkeypatch)
    await _attach_key(db_session, ADMIN_EMAIL)
    monkeypatch.setattr(crypto, "decrypt",
                        lambda _: (_ for _ in ()).throw(ValueError("bad secret")))
    monkeypatch.setattr(enrich_worker, "start_worker",
                        lambda *a, **k: {"already_running": False, "plan": {}})

    res = await non_admin_client.post("/api/vocab/enrich/fleet/start", json={})
    assert res.status_code == 200                    # not a 500
    body = res.json()
    assert body["started"] == []
    assert body["failed"][0]["email"] == ADMIN_EMAIL
    assert "bad secret" in body["failed"][0]["error"]


async def test_fleet_start_reports_an_already_running_account(
        non_admin_client, db_session, monkeypatch):
    from app.vocab import enrich_worker

    _as_admin(monkeypatch)
    await _attach_key(db_session, ADMIN_EMAIL)
    monkeypatch.setattr(enrich_worker, "start_worker",
                        lambda *a, **k: {"already_running": True})

    body = (await non_admin_client.post(
        "/api/vocab/enrich/fleet/start", json={})).json()
    assert body["already_running"] == [ADMIN_EMAIL] and body["started"] == []


async def test_fleet_stop_stops_everything(non_admin_client, monkeypatch):
    from app.vocab import enrich_worker

    _as_admin(monkeypatch)
    stopped = []
    monkeypatch.setattr(enrich_worker, "stop_all", lambda: stopped.append(True))
    monkeypatch.setattr(enrich_worker, "active_workers", lambda: [{"a": 1}, {"b": 2}])

    body = (await non_admin_client.post("/api/vocab/enrich/fleet/stop")).json()
    assert body["stopped"] == 2 and stopped == [True]

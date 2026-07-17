"""Extended auth API tests — registration, login, sessions, admin gate."""

from __future__ import annotations

import pytest

from tests.helpers import seed_words_and_phrases


# ── admin gate ──────────────────────────────────────────────────────────────
def test_nobody_is_admin_when_the_list_is_empty(monkeypatch):
    """The default. An admin can spend other accounts' Mistral keys, so an unset
    ADMIN_EMAILS must grant nothing — never everything."""
    from app.auth import is_admin_email
    from app.config import settings

    monkeypatch.setattr(settings, "admin_emails", "")
    assert is_admin_email("anyone@example.com") is False
    assert is_admin_email("") is False
    assert is_admin_email(None) is False


def test_admin_list_ignores_case_and_padding(monkeypatch):
    from app.auth import is_admin_email
    from app.config import settings

    monkeypatch.setattr(settings, "admin_emails", " Boss@Example.COM , two@x.io ")
    assert is_admin_email("boss@example.com") is True
    assert is_admin_email("BOSS@EXAMPLE.COM") is True
    assert is_admin_email("two@x.io") is True
    assert is_admin_email("three@x.io") is False


async def test_me_reports_admin_status(non_admin_client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "admin_emails", "someone-else@example.com")
    assert (await non_admin_client.get("/api/auth/me")).json()["is_admin"] is False

    monkeypatch.setattr(settings, "admin_emails", "regular@example.com")
    assert (await non_admin_client.get("/api/auth/me")).json()["is_admin"] is True


async def test_guest_is_never_admin(guest_client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "admin_emails", "regular@example.com")
    me = (await guest_client.get("/api/auth/me")).json()
    assert me["authenticated"] is False and me["is_admin"] is False


@pytest.mark.parametrize("bad_email", ["not-an-email", "@missing.com", "a@"])
async def test_register_rejects_invalid_email(guest_client, bad_email):
    res = await guest_client.post(
        "/api/auth/register",
        json={"email": bad_email, "password": "password123"},
    )
    assert res.status_code == 422


async def test_register_rejects_short_password(guest_client):
    res = await guest_client.post(
        "/api/auth/register",
        json={"email": "short@example.com", "password": "abc"},
    )
    assert res.status_code == 422


async def test_register_duplicate_email_returns_409(guest_client):
    payload = {"email": "dup@example.com", "password": "password123"}
    assert (await guest_client.post("/api/auth/register", json=payload)).status_code == 201
    dup = await guest_client.post("/api/auth/register", json=payload)
    assert dup.status_code == 409


async def test_login_wrong_password_returns_401(guest_client):
    await guest_client.post(
        "/api/auth/register",
        json={"email": "login@example.com", "password": "password123"},
    )
    await guest_client.post("/api/auth/logout")
    bad = await guest_client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "wrongpass"},
    )
    assert bad.status_code == 401


async def test_login_unknown_email_returns_401(guest_client):
    res = await guest_client.post(
        "/api/auth/login",
        json={"email": "ghost@example.com", "password": "password123"},
    )
    assert res.status_code == 401


async def test_guest_me_shows_unauthenticated(guest_client):
    res = await guest_client.get("/api/auth/me")
    assert res.status_code == 200
    data = res.json()
    assert data["authenticated"] is False
    assert data.get("guest_expires_at")


async def test_authenticated_me_returns_user(client):
    res = await client.get("/api/auth/me")
    assert res.status_code == 200
    data = res.json()
    assert data["authenticated"] is True
    assert data["user"]["email"] == "tester@example.com"


async def test_logout_clears_session(guest_client):
    await guest_client.post(
        "/api/auth/register",
        json={"email": "logout@example.com", "password": "password123"},
    )
    assert (await guest_client.post("/api/auth/logout")).status_code == 204
    me = (await guest_client.get("/api/auth/me")).json()
    assert me["authenticated"] is False


async def test_phrase_known_requires_auth(guest_client, db_session):
    await seed_words_and_phrases(db_session)
    phrases = (await guest_client.get("/api/phrases?topic=technologie")).json()
    res = await guest_client.post(
        f"/api/phrases/{phrases[0]['id']}/known",
        json={"known": True},
    )
    assert res.status_code == 401


async def test_word_queue_requires_auth(guest_client, db_session):
    await seed_words_and_phrases(db_session)
    words = (await guest_client.get("/api/words")).json()
    res = await guest_client.post(f"/api/words/{words[0]['id']}/queue")
    assert res.status_code == 401

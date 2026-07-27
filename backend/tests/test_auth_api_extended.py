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


@pytest.fixture
def rotating_secret(monkeypatch):
    """Swap the server secret the way an operator rotation does.

    `monkeypatch` restores the setting itself, but the derived Fernet key lives
    in an `lru_cache` that no fixture knows about — so clear it on the way in
    and on the way out, or the next test inherits whichever secret this one
    happened to finish on.
    """
    from app.services import crypto

    def _set(secret: str) -> None:
        monkeypatch.setattr(crypto.settings, "mistral_key_secret", secret)
        crypto._fernet.cache_clear()

    yield _set
    crypto._fernet.cache_clear()


async def test_me_reports_no_key_once_the_server_secret_is_rotated(
    client, db_session, rotating_secret
):
    """`has_mistral_key` must mean "we can still read it", not "the column is set".

    Rotating `MISTRAL_KEY_SECRET` leaves every row present and every row
    undecryptable. Answering "yes" then is the worst of the two answers: the
    account looks equipped, so nobody re-enters the key, and the worker dies on
    `decrypt` returning None with no hint of why.
    """
    from app.db.models import User
    from app.services import crypto
    from sqlalchemy import select, update

    rotating_secret("secret-before-rotation")
    token = crypto.encrypt("sk-live-key")
    await db_session.execute(
        update(User).where(User.email == "tester@example.com").values(mistral_key_enc=token)
    )
    await db_session.commit()

    assert (await client.get("/api/auth/me")).json()["has_mistral_key"] is True

    rotating_secret("secret-after-rotation")
    assert (await client.get("/api/auth/me")).json()["has_mistral_key"] is False

    # ...and the column is untouched, so what changed is readability, not storage.
    stored = (
        await db_session.execute(
            select(User.mistral_key_enc).where(User.email == "tester@example.com")
        )
    ).scalar_one()
    assert stored == token


async def test_logout_clears_session(guest_client):
    await guest_client.post(
        "/api/auth/register",
        json={"email": "logout@example.com", "password": "password123"},
    )
    assert (await guest_client.post("/api/auth/logout")).status_code == 204
    me = (await guest_client.get("/api/auth/me")).json()
    assert me["authenticated"] is False


async def test_phrase_known_requires_auth(guest_client, db_session):
    from app.db.models import Phrase
    from sqlalchemy import select

    await seed_words_and_phrases(db_session)
    # id берётся из БД, а не из ручки: `GET /api/phrases` удалён 2026-07-26
    # (0 потребителей во фронте), а `/templates` стоит на `DISTINCT ON`,
    # которого в sqlite нет. `POST /api/words/{id}/queue` уехал туда же вместе
    # со всем роутером `/api/words`, поэтому его гостевого теста больше нет.
    phrase = (await db_session.execute(select(Phrase))).scalars().first()
    res = await guest_client.post(
        f"/api/phrases/{phrase.id}/known",
        json={"known": True},
    )
    assert res.status_code == 401

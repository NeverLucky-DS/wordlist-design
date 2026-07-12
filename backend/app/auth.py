from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, Response, status
from pwdlib import PasswordHash
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import AuthSession, GuestSession, User
from app.db.session import get_db

AUTH_COOKIE = "essay_auth"
GUEST_COOKIE = "essay_guest"
AUTH_DAYS = 30
GUEST_DAYS = 30
password_hash = PasswordHash.recommended()


@dataclass(frozen=True)
class Principal:
    user_id: int | None = None
    guest_session_id: int | None = None
    email: str | None = None
    guest_expires_at: datetime | None = None

    @property
    def authenticated(self) -> bool:
        return self.user_id is not None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _naive_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _is_expired(value: datetime) -> bool:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value <= _now()


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _set_cookie(response: Response, name: str, token: str, days: int) -> None:
    response.set_cookie(
        name,
        token,
        max_age=days * 24 * 60 * 60,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )


async def create_auth_session(
    db: AsyncSession, response: Response, user_id: int
) -> AuthSession:
    token = secrets.token_urlsafe(32)
    row = AuthSession(
        user_id=user_id,
        token_hash=_digest(token),
        expires_at=_now() + timedelta(days=AUTH_DAYS),
    )
    db.add(row)
    await db.flush()
    _set_cookie(response, AUTH_COOKIE, token, AUTH_DAYS)
    return row


async def _authenticated_principal(
    request: Request, db: AsyncSession
) -> Principal | None:
    token = request.cookies.get(AUTH_COOKIE)
    if not token:
        return None
    result = await db.execute(
        select(AuthSession, User)
        .join(User, User.id == AuthSession.user_id)
        .where(AuthSession.token_hash == _digest(token))
    )
    pair = result.first()
    if not pair:
        return None
    session, user = pair
    if _is_expired(session.expires_at):
        await db.delete(session)
        await db.commit()
        return None
    return Principal(user_id=user.id, email=user.email)


async def get_optional_user(
    request: Request, db: AsyncSession = Depends(get_db)
) -> Principal | None:
    return await _authenticated_principal(request, db)


async def get_principal(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Principal:
    authenticated = await _authenticated_principal(request, db)
    if authenticated:
        return authenticated

    token = request.cookies.get(GUEST_COOKIE)
    guest = None
    if token:
        result = await db.execute(
            select(GuestSession).where(GuestSession.token_hash == _digest(token))
        )
        guest = result.scalar_one_or_none()
        if guest and _is_expired(guest.expires_at):
            await db.delete(guest)
            guest = None

    if not guest:
        token = secrets.token_urlsafe(32)
        guest = GuestSession(
            token_hash=_digest(token),
            expires_at=_now() + timedelta(days=GUEST_DAYS),
        )
        db.add(guest)
        await db.commit()
        await db.refresh(guest)
        _set_cookie(response, GUEST_COOKIE, token, GUEST_DAYS)
    else:
        guest.last_seen_at = _naive_now()
        guest.expires_at = _now() + timedelta(days=GUEST_DAYS)
        await db.commit()

    return Principal(
        guest_session_id=guest.id,
        guest_expires_at=guest.expires_at,
    )


async def require_user(
    principal: Principal = Depends(get_principal),
) -> Principal:
    if not principal.authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return principal


async def require_admin(
    principal: Principal = Depends(require_user),
) -> Principal:
    allowed = {
        email.strip().lower()
        for email in settings.admin_emails.split(",")
        if email.strip()
    }
    if not principal.email or principal.email.lower() not in allowed:
        raise HTTPException(status_code=403, detail="Admin access required")
    return principal


async def revoke_cookie_session(
    db: AsyncSession, request: Request, response: Response
) -> None:
    token = request.cookies.get(AUTH_COOKIE)
    if token:
        await db.execute(
            delete(AuthSession).where(AuthSession.token_hash == _digest(token))
        )
        await db.commit()
    response.delete_cookie(AUTH_COOKIE, path="/")


async def cleanup_expired_sessions(db: AsyncSession) -> None:
    now = _now()
    await db.execute(delete(AuthSession).where(AuthSession.expires_at <= now))
    await db.execute(delete(GuestSession).where(GuestSession.expires_at <= now))
    await db.commit()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    return password_hash.verify(password, encoded)

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    GUEST_COOKIE,
    Principal,
    create_auth_session,
    get_principal,
    hash_password,
    is_admin_email,
    require_user,
    revoke_cookie_session,
    verify_password,
)
from app.db.models import Essay, User
from app.db.session import get_db
from app.schemas import (
    AuthStateOut,
    DeleteAccountIn,
    LoginIn,
    MistralKeyIn,
    RegisterIn,
    UserOut,
)
from app.services import crypto

router = APIRouter(prefix="/api/auth", tags=["auth"])
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _email(value: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) > 320 or not EMAIL_RE.match(normalized):
        raise HTTPException(status_code=422, detail="Invalid email address")
    return normalized


@router.get("/me", response_model=AuthStateOut)
async def me(
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    if principal.authenticated:
        user = await db.get(User, principal.user_id)
        return {
            "authenticated": True,
            "user": user,
            "has_mistral_key": bool(user and user.mistral_key_enc),
            "key_storage_enabled": crypto.is_enabled(),
            "is_admin": is_admin_email(principal.email),
        }
    return {
        "authenticated": False,
        "guest_expires_at": principal.guest_expires_at,
        "key_storage_enabled": crypto.is_enabled(),
    }


@router.put("/mistral-key", status_code=status.HTTP_204_NO_CONTENT)
async def set_mistral_key(
    body: MistralKeyIn,
    principal: Principal = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Attach/replace this account's Mistral key (stored encrypted, never
    returned). Rejects a key Mistral explicitly refuses (401/403)."""
    import asyncio

    from app.services.mistral_http import verify_key

    if not crypto.is_enabled():
        raise HTTPException(status_code=503, detail="Key storage is disabled on this server")
    key = body.key.strip()
    if await asyncio.to_thread(verify_key, key) is False:
        raise HTTPException(status_code=400, detail="Mistral rejected this key")
    await db.execute(
        update(User).where(User.id == principal.user_id).values(
            mistral_key_enc=crypto.encrypt(key)
        )
    )
    await db.commit()


@router.delete("/mistral-key", status_code=status.HTTP_204_NO_CONTENT)
async def clear_mistral_key(
    principal: Principal = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove the stored key and stop any running worker for this account."""
    from app.vocab import enrich_worker

    enrich_worker.stop_worker(principal.user_id)
    await db.execute(
        update(User).where(User.id == principal.user_id).values(mistral_key_enc=None)
    )
    await db.commit()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterIn,
    response: Response,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
):
    email = _email(body.email)
    existing = await db.execute(select(User.id).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email is already registered")

    user = User(email=email, password_hash=hash_password(body.password))
    db.add(user)
    await db.flush()

    if principal.guest_session_id is not None:
        await db.execute(
            update(Essay)
            .where(Essay.guest_session_id == principal.guest_session_id)
            .values(user_id=user.id, guest_session_id=None)
        )
    await create_auth_session(db, response, user.id)
    await db.commit()
    await db.refresh(user)
    response.delete_cookie(GUEST_COOKIE, path="/")
    return user


@router.post("/login", response_model=UserOut)
async def login(
    body: LoginIn,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    email = _email(body.email)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await create_auth_session(db, response, user.id)
    await db.commit()
    response.delete_cookie(GUEST_COOKIE, path="/")
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    await revoke_cookie_session(db, request, response)


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    body: DeleteAccountIn,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, principal.user_id)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=403, detail="Password is incorrect")
    await db.delete(user)
    await db.commit()
    response.delete_cookie("essay_auth", path="/")

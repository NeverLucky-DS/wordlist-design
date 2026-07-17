"""Symmetric encryption for secrets at rest (per-user Mistral API keys).

A Fernet key is DERIVED from `settings.mistral_key_secret` so the operator only
manages one server secret (any string) — we turn it into a valid 32-byte Fernet
key via SHA-256. If the secret is unset the feature is DISABLED: we never fall
back to storing keys in plaintext.
"""
from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


class KeyStorageDisabled(RuntimeError):
    """Raised when encryption is requested but no server secret is configured."""


def is_enabled() -> bool:
    return bool(settings.mistral_key_secret.strip())


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    secret = settings.mistral_key_secret.strip()
    if not secret:
        raise KeyStorageDisabled(
            "MISTRAL_KEY_SECRET is not set — per-user key storage is disabled"
        )
    derived = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(derived)


def encrypt(plaintext: str) -> str:
    """Encrypt a secret → token string safe to store in a DB column."""
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt(token: str) -> str | None:
    """Decrypt a stored token. Returns None if it can't be decrypted (wrong
    secret / corrupted / rotated key) rather than raising, so a bad row degrades
    to 'no key' instead of crashing the worker."""
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, KeyStorageDisabled):
        return None

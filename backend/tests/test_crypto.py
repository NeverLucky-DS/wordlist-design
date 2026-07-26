"""Encryption for per-user Mistral keys at rest."""
from __future__ import annotations

import pytest
from app.services import crypto


@pytest.fixture(autouse=True)
def _reset_fernet():
    crypto._fernet.cache_clear()
    yield
    crypto._fernet.cache_clear()


def _with_secret(monkeypatch, secret: str):
    monkeypatch.setattr(crypto.settings, "mistral_key_secret", secret)
    crypto._fernet.cache_clear()


def test_round_trip(monkeypatch):
    _with_secret(monkeypatch, "server-secret-xyz")
    token = crypto.encrypt("sk-my-mistral-key")
    assert token != "sk-my-mistral-key"        # actually encrypted
    assert crypto.decrypt(token) == "sk-my-mistral-key"


def test_decrypt_garbage_returns_none(monkeypatch):
    _with_secret(monkeypatch, "server-secret-xyz")
    assert crypto.decrypt("not-a-valid-token") is None


def test_wrong_secret_cannot_decrypt(monkeypatch):
    _with_secret(monkeypatch, "secret-A")
    token = crypto.encrypt("sk-key")
    _with_secret(monkeypatch, "secret-B")
    assert crypto.decrypt(token) is None        # different secret → None, not crash


def test_usable_asks_whether_the_key_still_reads_not_whether_it_exists(monkeypatch):
    """`usable` is deliberately not `bool(token)` — that is the bug it replaces.

    A stored token survives a secret rotation; the ability to decrypt it does
    not. Callers that only checked NOT NULL reported "key attached" for a row
    nobody could use.
    """
    _with_secret(monkeypatch, "secret-A")
    token = crypto.encrypt("sk-key")
    assert crypto.usable(token) is True

    _with_secret(monkeypatch, "secret-B")            # ротация
    assert bool(token) is True                       # колонка по-прежнему NOT NULL...
    assert crypto.usable(token) is False             # ...а ключа у нас больше нет


def test_usable_on_nothing_stored(monkeypatch):
    _with_secret(monkeypatch, "secret-A")
    assert crypto.usable(None) is False
    assert crypto.usable("") is False
    assert crypto.usable("not-a-valid-token") is False


def test_disabled_without_secret(monkeypatch):
    _with_secret(monkeypatch, "")
    assert crypto.is_enabled() is False
    with pytest.raises(crypto.KeyStorageDisabled):
        crypto.encrypt("sk-key")

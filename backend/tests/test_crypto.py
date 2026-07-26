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


def test_disabled_without_secret(monkeypatch):
    _with_secret(monkeypatch, "")
    assert crypto.is_enabled() is False
    with pytest.raises(crypto.KeyStorageDisabled):
        crypto.encrypt("sk-key")


def test_has_usable_key_says_no_after_the_secret_was_rotated(monkeypatch):
    """Заполненная колонка ≠ рабочий ключ.

    `/api/auth/me` и панель флота считали `has_mistral_key` как
    `bool(user.mistral_key_enc)`, то есть проверяли NOT NULL. После смены
    `MISTRAL_KEY_SECRET` расшифровка перестаёт работать молча (так задумано),
    и интерфейс всех 17 аккаунтов продолжал показывать «ключ привязан» — а
    первый же запуск воркера отвечал `400 no Mistral key attached`.
    """
    _with_secret(monkeypatch, "secret-A")
    token = crypto.encrypt("sk-key")
    assert crypto.has_usable_key(token) is True

    _with_secret(monkeypatch, "secret-B")           # ротация
    assert bool(token) is True                       # колонка по-прежнему не пуста
    assert crypto.has_usable_key(token) is False     # но ключом уже не воспользуешься


def test_has_usable_key_on_nothing(monkeypatch):
    _with_secret(monkeypatch, "server-secret-xyz")
    assert crypto.has_usable_key(None) is False
    assert crypto.has_usable_key("") is False
    assert crypto.has_usable_key("not-a-valid-token") is False

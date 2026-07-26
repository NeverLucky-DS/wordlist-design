"""Гейт на `POST /api/vocab/mirror/sync`.

Ручка стояла на `require_user`, то есть любой заведённый аккаунт мог запускать
полный проход курсора по 92 000 карточек плюс `prune_orphans` — общий ресурс, а
не свой. Соседние ручки того же класса (`build`, `enrich/fleet/*`) закрыты
админом именно поэтому; эта осталась не закрытой по недосмотру.

Разрушительной она при этом не является: проход идемпотентен, тот же самый
идёт по таймеру каждые 5 минут. Гейт тут про нагрузку, а не про данные — но
правило «общий ресурс дёргает админ» должно быть одно на все ручки, иначе
следующая такая же появится незамеченной.
"""

from __future__ import annotations

import pytest

ADMIN_EMAIL = "regular@example.com"   # аккаунт фикстуры non_admin_client


@pytest.fixture(autouse=True)
def _never_sync(monkeypatch):
    """Подменяет сам проход: тест про право вызова, а не про зеркало."""
    from app.vocab import mirror

    calls: list[int] = []

    async def _fake_sync(db, **kw):
        calls.append(1)
        return {"ok": True, "synced": 0, "pruned": 0}

    monkeypatch.setattr(mirror, "sync_cards", _fake_sync)
    return calls


async def test_mirror_sync_is_closed_to_guests(guest_client, monkeypatch, _never_sync):
    from app.config import settings

    monkeypatch.setattr(settings, "admin_emails", ADMIN_EMAIL)
    assert (await guest_client.post("/api/vocab/mirror/sync")).status_code == 401
    assert _never_sync == [], "гость не должен запускать проход зеркала"


async def test_mirror_sync_is_closed_to_non_admins(non_admin_client, monkeypatch, _never_sync):
    from app.config import settings

    monkeypatch.setattr(settings, "admin_emails", "someone-else@example.com")
    assert (await non_admin_client.post("/api/vocab/mirror/sync")).status_code == 403
    assert _never_sync == []


async def test_mirror_sync_still_works_for_an_admin(non_admin_client, monkeypatch, _never_sync):
    from app.config import settings

    monkeypatch.setattr(settings, "admin_emails", ADMIN_EMAIL)
    r = await non_admin_client.post("/api/vocab/mirror/sync")
    assert r.status_code == 200, r.text
    assert _never_sync == [1]

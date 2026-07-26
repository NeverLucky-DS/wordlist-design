"""Публичные ручки, не привязанные к аккаунту.

Здесь было ещё девять тестов на `/api/topics` и `/api/words`. Оба роутера
удалены 2026-07-26: во фронте их не звал никто, а YAML-пакетов тем, ради
которых существовал загрузчик, нет ни в репозитории, ни в образе — `GET
/api/topics` на живом стенде отвечал `[]`, `GET /api/topics/{slug}` — 404 при
любом слаге. Тесты, проверявшие эти ответы, проверяли пустоту.
"""

from __future__ import annotations


async def test_health_ok(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

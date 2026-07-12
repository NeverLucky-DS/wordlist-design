from __future__ import annotations

import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app


def payload(title: str = "Gast") -> dict:
    return {
        "title": title,
        "text": "Einleitung:\nText",
        "content_json": {"drafts": {"einleitung": "Text"}},
        "level": "B1",
    }


async def test_guest_essays_are_claimed_on_registration(guest_client):
    assert (await guest_client.get("/api/auth/me")).status_code == 200
    assert (await guest_client.get("/api/auth/me")).status_code == 200
    created = await guest_client.post("/api/essays", json=payload())
    assert created.status_code == 200

    registered = await guest_client.post(
        "/api/auth/register",
        json={"email": "new@example.com", "password": "password123"},
    )
    assert registered.status_code == 201

    listed = await guest_client.get("/api/essays")
    assert [item["title"] for item in listed.json()] == ["Gast"]


async def test_login_does_not_claim_current_guest_data(guest_client):
    await guest_client.post("/api/essays", json=payload("Account essay"))
    await guest_client.post(
        "/api/auth/register",
        json={"email": "owner@example.com", "password": "password123"},
    )
    await guest_client.post("/api/auth/logout")
    await guest_client.post("/api/essays", json=payload("Temporary guest essay"))

    logged_in = await guest_client.post(
        "/api/auth/login",
        json={"email": "owner@example.com", "password": "password123"},
    )
    assert logged_in.status_code == 200
    listed = await guest_client.get("/api/essays")
    assert [item["title"] for item in listed.json()] == ["Account essay"]


async def test_account_deletion_removes_owned_essays(guest_client):
    await guest_client.post(
        "/api/auth/register",
        json={"email": "delete@example.com", "password": "password123"},
    )
    await guest_client.post("/api/essays", json=payload("Delete me"))
    deleted = await guest_client.request(
        "DELETE",
        "/api/auth/account",
        json={"password": "password123"},
    )
    assert deleted.status_code == 204
    state = (await guest_client.get("/api/auth/me")).json()
    assert state["authenticated"] is False
    assert (await guest_client.get("/api/essays")).json() == []


async def test_manual_version_restore_preserves_current_text(client):
    essay = (await client.post("/api/essays", json=payload("Versioned"))).json()
    version = (
        await client.post(
            f"/api/essays/{essay['id']}/versions",
            json={"reason": "manual"},
        )
    ).json()
    await client.patch(
        f"/api/essays/{essay['id']}",
        json={"text": "Einleitung:\nChanged"},
    )

    restored = await client.post(
        f"/api/essays/{essay['id']}/versions/{version['id']}/restore"
    )
    assert restored.json()["text"] == "Einleitung:\nText"
    versions = (await client.get(f"/api/essays/{essay['id']}/versions")).json()
    assert any(item["reason"] == "pre_restore" for item in versions)


async def test_background_analysis_history_and_cancel_contract(client):
    essay = (await client.post("/api/essays", json=payload("Analyze"))).json()
    started = await client.post(
        f"/api/essays/{essay['id']}/analyses",
        json={"part": None},
    )
    assert started.status_code == 202
    analysis_id = started.json()["id"]

    final = None
    for _ in range(30):
        response = await client.get(
            f"/api/essays/{essay['id']}/analyses/{analysis_id}"
        )
        final = response.json()
        if final["status"] not in {"queued", "running"}:
            break
        await asyncio.sleep(0.02)

    assert final["status"] == "completed_with_warnings"
    assert final["version_id"] is not None
    history = (await client.get(f"/api/essays/{essay['id']}/analyses")).json()
    assert history[0]["id"] == analysis_id


async def test_user_cannot_read_another_users_essay(client):
    essay = (await client.post("/api/essays", json=payload("Private"))).json()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as other:
        await other.post(
            "/api/auth/register",
            json={"email": "other@example.com", "password": "password123"},
        )
        response = await other.get(f"/api/essays/{essay['id']}")
    assert response.status_code == 404


async def test_running_analysis_can_be_cancelled(client, monkeypatch):
    from app.services import analysis_jobs

    async def slow_events(**_):
        yield {"type": "part_start", "part": "einleitung", "label": "Einleitung"}
        await asyncio.sleep(0.2)
        yield {
            "type": "done",
            "overall_score": 80,
            "grade": "B",
            "errors": [],
            "part_reports": [],
            "final_summary": None,
            "model": "test",
        }

    monkeypatch.setattr(analysis_jobs, "iter_analyze_events", slow_events)
    essay = (await client.post("/api/essays", json=payload("Cancel"))).json()
    started = (
        await client.post(
            f"/api/essays/{essay['id']}/analyses",
            json={"part": None},
        )
    ).json()
    await asyncio.sleep(0.03)
    await client.post(
        f"/api/essays/{essay['id']}/analyses/{started['id']}/cancel"
    )
    await asyncio.sleep(0.25)
    final = (
        await client.get(
            f"/api/essays/{essay['id']}/analyses/{started['id']}"
        )
    ).json()
    assert final["status"] == "cancelled"

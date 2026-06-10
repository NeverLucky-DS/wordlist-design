"""Tests for /api/pipeline — the «новая тема» flow used by pipeline.html."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch  # noqa: F401 — patch used as decorator

import pytest
from app.db.models import PipelineRun


async def test_start_pipeline_creates_run(client):
    """POST /api/pipeline/run — same call pipeline.html makes on «Запустить»."""
    with patch("app.api.routes.pipeline.run_pipeline", new=AsyncMock()):
        res = await client.post(
            "/api/pipeline/run",
            json={"topic": "Klimawandel", "article_urls": []},
        )

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "started"
    assert body["topic"] == "Klimawandel"
    assert isinstance(body["run_id"], int)


@pytest.mark.parametrize("bad_topic", ["", "   "])
async def test_start_pipeline_rejects_empty_topic(client, bad_topic):
    res = await client.post("/api/pipeline/run", json={"topic": bad_topic})
    assert res.status_code == 422


async def test_poll_pipeline_run_while_running(client):
    """GET /api/pipeline/run/{id} — polling endpoint from pipeline.html (every 3s)."""
    with patch("app.api.routes.pipeline.run_pipeline", new=AsyncMock()):
        started = await client.post(
            "/api/pipeline/run",
            json={"topic": "Digitalisierung", "article_urls": []},
        )
    run_id = started.json()["run_id"]

    polled = await client.get(f"/api/pipeline/run/{run_id}")
    assert polled.status_code == 200
    data = polled.json()
    assert data["run_id"] == run_id
    assert data["topic"] == "Digitalisierung"
    assert data["status"] == "running"
    assert data["words_added"] == 0
    assert data["words_linked"] == 0
    assert data["errors"] == []
    assert data["finished_at"] is None


async def test_poll_pipeline_run_not_found(client):
    res = await client.get("/api/pipeline/run/99999")
    assert res.status_code == 404


async def test_list_pipeline_runs(client):
    with patch("app.api.routes.pipeline.run_pipeline", new=AsyncMock()):
        await client.post("/api/pipeline/run", json={"topic": "Migration"})
        await client.post("/api/pipeline/run", json={"topic": "Energiewende"})

    res = await client.get("/api/pipeline/runs")
    assert res.status_code == 200
    runs = res.json()
    assert len(runs) >= 2
    topics = {r["topic"] for r in runs}
    assert {"Migration", "Energiewende"}.issubset(topics)
    assert all("run_id" in r and "status" in r for r in runs)


async def test_pipeline_ui_poll_flow_until_completed(client, db_session):
    """Simulates pipeline.html: POST → poll until status=completed."""

    async def _complete_run(run_id: int, topic: str, article_urls: list[str], session_factory, target_words=None):
        run = await db_session.get(PipelineRun, run_id)
        run.status = "completed"
        run.words_added = 3
        run.words_linked = 1
        run.errors_json = []
        run.finished_at = datetime.utcnow()
        await db_session.commit()

    with patch("app.api.routes.pipeline.run_pipeline", side_effect=_complete_run):
        started = await client.post(
            "/api/pipeline/run",
            json={"topic": "Künstliche Intelligenz", "article_urls": []},
        )
    run_id = started.json()["run_id"]

    polled = await client.get(f"/api/pipeline/run/{run_id}")
    data = polled.json()
    assert data["status"] == "completed"
    assert data["words_added"] == 3
    assert data["words_linked"] == 1
    assert data["finished_at"] is not None


async def test_run_pipeline_fails_without_discovery_inputs(db_session):
    """Without GROK_API_KEY and article_urls=[] the UI run ends as failed — no silent hang."""
    from app.db.session import async_sessionmaker
    from app.pipeline.runner import run_pipeline

    run = PipelineRun(topic="Testthema", status="running")
    db_session.add(run)
    await db_session.commit()
    await db_session.refresh(run)
    run_id = run.id

    session_factory = async_sessionmaker(db_session.bind, expire_on_commit=False)

    with patch("app.pipeline.runner.settings.grok_api_key", ""):
        await run_pipeline(run_id, "Testthema", [], session_factory)

    async with session_factory() as db:
        finished = await db.get(PipelineRun, run_id)
    assert finished.status == "failed"
    assert finished.finished_at is not None
    assert any(e["stage"] == "fetch" for e in (finished.errors_json or []))

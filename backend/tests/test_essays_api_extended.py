"""Extended essays API — CRUD edge cases, versions, analyses, streaming."""

from __future__ import annotations

import asyncio
import json

import pytest

from tests.helpers import essay_payload, seed_words_and_phrases


async def test_delete_essay(client):
    created = await client.post("/api/essays", json=essay_payload())
    essay_id = created.json()["id"]
    deleted = await client.delete(f"/api/essays/{essay_id}")
    assert deleted.status_code == 204
    assert (await client.get(f"/api/essays/{essay_id}")).status_code == 404


async def test_delete_missing_essay_returns_404(client):
    assert (await client.delete("/api/essays/99999")).status_code == 404


async def test_list_shows_grade_after_legacy_analyze(client, monkeypatch):
    from app.api.routes import essays as essays_routes

    async def fake_analyze(**kwargs):
        return {
            "overall_score": 88,
            "grade": "A",
            "errors": [],
            "part_reports": [],
            "final_summary": None,
            "model": "test",
        }

    monkeypatch.setattr(essays_routes, "analyze_essay", fake_analyze)
    essay_id = (await client.post("/api/essays", json=essay_payload())).json()["id"]
    await client.post(f"/api/essays/{essay_id}/analyze")
    listed = (await client.get("/api/essays")).json()
    assert listed[0]["grade"] == "A"
    assert listed[0]["overall_score"] == 88


async def test_start_analysis_rejects_unknown_part(client):
    essay_id = (await client.post("/api/essays", json=essay_payload())).json()["id"]
    res = await client.post(
        f"/api/essays/{essay_id}/analyses",
        json={"part": "intro"},
    )
    assert res.status_code == 422


async def test_cannot_start_second_analysis_while_running(client, monkeypatch):
    from app.services import analysis_jobs

    async def slow(**_):
        yield {"type": "part_start", "part": "einleitung", "label": "Einleitung"}
        await asyncio.sleep(0.3)
        yield {
            "type": "done",
            "overall_score": 70,
            "grade": "B",
            "errors": [],
            "part_reports": [],
            "final_summary": None,
            "model": "test",
        }

    monkeypatch.setattr(analysis_jobs, "iter_analyze_events", slow)
    essay_id = (await client.post("/api/essays", json=essay_payload())).json()["id"]
    first = await client.post(f"/api/essays/{essay_id}/analyses", json={"part": None})
    assert first.status_code == 202
    second = await client.post(f"/api/essays/{essay_id}/analyses", json={"part": None})
    assert second.status_code == 409
    await asyncio.sleep(0.35)


async def test_active_analysis_endpoint(client, monkeypatch):
    from app.services import analysis_jobs

    async def slow(**_):
        yield {"type": "part_start", "part": "einleitung", "label": "Einleitung"}
        await asyncio.sleep(0.25)
        yield {
            "type": "done",
            "overall_score": 72,
            "grade": "B",
            "errors": [],
            "part_reports": [],
            "final_summary": None,
            "model": "test",
            "warnings": [{"code": "ai_not_configured"}],
        }

    monkeypatch.setattr(analysis_jobs, "iter_analyze_events", slow)
    essay_id = (await client.post("/api/essays", json=essay_payload())).json()["id"]
    started = await client.post(f"/api/essays/{essay_id}/analyses", json={"part": None})
    analysis_id = started.json()["id"]
    active = await client.get(f"/api/essays/{essay_id}/analyses/active")
    assert active.status_code == 200
    assert active.json()["id"] == analysis_id
    await asyncio.sleep(0.3)
    inactive = await client.get(f"/api/essays/{essay_id}/analyses/active")
    assert inactive.json() is None


async def test_version_create_and_list(client):
    essay_id = (await client.post("/api/essays", json=essay_payload())).json()["id"]
    v = await client.post(f"/api/essays/{essay_id}/versions", json={"reason": "manual"})
    assert v.status_code == 201
    versions = (await client.get(f"/api/essays/{essay_id}/versions")).json()
    assert len(versions) >= 1
    assert versions[0]["reason"] in {"manual", "analysis"}


async def test_latest_analysis_404_when_none(client):
    essay_id = (await client.post("/api/essays", json=essay_payload())).json()["id"]
    assert (await client.get(f"/api/essays/{essay_id}/analysis/latest")).status_code == 404


async def test_stream_single_part(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "mistral_api_key", "")

    essay_id = (await client.post("/api/essays", json=essay_payload())).json()["id"]
    res = await client.post(
        f"/api/essays/{essay_id}/analyze/stream",
        params={"part": "schluss"},
    )
    assert res.status_code == 200
    frames = [f for f in res.text.split("\n\n") if f.strip()]
    payloads = [json.loads(f.removeprefix("data: ")) for f in frames if f.startswith("data: ")]
    assert any(p.get("type") == "done" for p in payloads)
    done = next(p for p in payloads if p.get("type") == "done")
    assert done.get("only_part") == "schluss" or all(
        r.get("part") == "schluss" for r in done.get("part_reports", [])
    )


async def test_analysis_payload_includes_schema_metadata(client, monkeypatch):
    from app.services import analysis_jobs

    async def instant(**_):
        yield {
            "type": "done",
            "overall_score": 77,
            "grade": "B",
            "errors": [],
            "part_reports": [],
            "final_summary": {"structure_feedback_ru": "x", "topic_feedback_ru": "y",
                              "strengths_ru": [], "next_steps_ru": [], "overall_comment_ru": "z"},
            "model": "mistral-large-latest",
            "warnings": [],
        }

    monkeypatch.setattr(analysis_jobs, "iter_analyze_events", instant)
    essay_id = (await client.post("/api/essays", json=essay_payload())).json()["id"]
    started = await client.post(f"/api/essays/{essay_id}/analyses", json={"part": None})
    analysis_id = started.json()["id"]
    await asyncio.sleep(0.05)
    row = (await client.get(f"/api/essays/{essay_id}/analyses/{analysis_id}")).json()
    assert row["schema_version"] >= 1
    assert row["prompt_version"]
    assert row["status"] in {"completed", "completed_with_warnings"}


@pytest.mark.parametrize("field", ["title", "level", "topic"])
async def test_patch_single_field(client, field):
    essay_id = (await client.post("/api/essays", json=essay_payload())).json()["id"]
    new_value = "C1" if field == "level" else f"Neu-{field}"
    patched = await client.patch(f"/api/essays/{essay_id}", json={field: new_value})
    assert patched.status_code == 200
    assert patched.json()[field] == new_value

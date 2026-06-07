from __future__ import annotations

from app.config import settings


def essay_payload() -> dict:
    return {
        "title": "Technologie",
        "text": (
            "Einleitung:\nTechnologie ist wichtig.\n\n"
            "Argument Eins:\nSie spart Zeit.\n\n"
            "Argument Zwei:\nSie schafft auch Risiken.\n\n"
            "Schluss:\nWir brauchen Balance."
        ),
        "essay_type": "argumentativ",
        "topic": "technologie",
        "level": "B1",
    }


async def test_stream_analyze_fallback_when_no_mistral_key(client, monkeypatch):
    monkeypatch.setattr(settings, "mistral_api_key", "")

    created = await client.post("/api/essays", json=essay_payload())
    essay_id = created.json()["id"]

    response = await client.post(f"/api/essays/{essay_id}/analyze/stream")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    raw = response.text
    frames = [x.strip() for x in raw.split("\n\n") if x.strip()]
    assert len(frames) >= 1
    assert frames[-1].startswith("data: ")

    payload = frames[-1][6:]
    assert '"type": "done"' in payload
    assert '"essay_id":' in payload


async def test_sync_analyze_fallback_when_no_key(client, monkeypatch):
    monkeypatch.setattr(settings, "mistral_api_key", "")

    created = await client.post("/api/essays", json=essay_payload())
    essay_id = created.json()["id"]
    response = await client.post(f"/api/essays/{essay_id}/analyze")
    assert response.status_code == 200
    data = response.json()
    assert data["grade"] in {"A", "B", "C", "D"}
    assert isinstance(data["overall_score"], int)
    assert "model" in data

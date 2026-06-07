from __future__ import annotations

from app.api.routes import essays as essays_routes


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


async def test_essays_crud_flow(client):
    created = await client.post("/api/essays", json=essay_payload())
    assert created.status_code == 200
    created_json = created.json()
    assert created_json["id"] >= 1
    assert created_json["title"] == "Technologie"

    listed = await client.get("/api/essays")
    assert listed.status_code == 200
    listed_json = listed.json()
    assert len(listed_json) == 1
    assert listed_json[0]["grade"] is None

    essay_id = created_json["id"]
    fetched = await client.get(f"/api/essays/{essay_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == essay_id

    patched = await client.patch(f"/api/essays/{essay_id}", json={"title": "Neu"})
    assert patched.status_code == 200
    assert patched.json()["title"] == "Neu"

    missing = await client.get("/api/essays/9999")
    assert missing.status_code == 404


async def test_analysis_latest_and_stale_flag(client, monkeypatch):
    created = await client.post("/api/essays", json=essay_payload())
    essay_id = created.json()["id"]

    async def _fake_analyze_essay(*, text: str, essay_type: str, level: str) -> dict:
        return {
            "overall_score": 76,
            "grade": "B",
            "errors": [],
            "part_reports": [],
            "final_summary": None,
            "model": "mistral-large-latest",
        }

    monkeypatch.setattr(essays_routes, "analyze_essay", _fake_analyze_essay)

    analyzed = await client.post(f"/api/essays/{essay_id}/analyze")
    assert analyzed.status_code == 200
    assert analyzed.json()["overall_score"] == 76

    latest = await client.get(f"/api/essays/{essay_id}/analysis/latest")
    assert latest.status_code == 200
    assert latest.json()["is_stale"] is False

    updated_text = essay_payload()["text"] + "\nNoch ein Satz."
    patched = await client.patch(f"/api/essays/{essay_id}", json={"text": updated_text})
    assert patched.status_code == 200

    latest_after_patch = await client.get(f"/api/essays/{essay_id}/analysis/latest")
    assert latest_after_patch.status_code == 200
    assert latest_after_patch.json()["is_stale"] is True

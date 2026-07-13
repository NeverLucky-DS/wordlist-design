"""Health, topics, words — useful public endpoints."""

from __future__ import annotations

from tests.helpers import seed_words_and_phrases


async def test_health_ok(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


async def test_topics_list_returns_array(client):
    res = await client.get("/api/topics")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


async def test_unknown_topic_returns_404(client):
    res = await client.get("/api/topics/nonexistent-slug-xyz")
    assert res.status_code == 404


async def test_import_unknown_topic_returns_404(client):
    res = await client.post("/api/topics/nonexistent-slug-xyz/import")
    assert res.status_code == 404


async def test_words_get_by_id(client, db_session):
    await seed_words_and_phrases(db_session)
    listed = (await client.get("/api/words")).json()
    word_id = next(w["id"] for w in listed if w["german"] == "Baum")
    fetched = await client.get(f"/api/words/{word_id}")
    assert fetched.status_code == 200
    assert fetched.json()["german"] == "Baum"
    assert "natur" in fetched.json()["topics"]


async def test_words_get_missing_returns_404(client):
    assert (await client.get("/api/words/99999")).status_code == 404


async def test_word_queue_for_authenticated_user(client, db_session):
    await seed_words_and_phrases(db_session)
    word_id = (await client.get("/api/words?q=дерево")).json()[0]["id"]
    queued = await client.post(f"/api/words/{word_id}/queue")
    assert queued.status_code == 200
    assert queued.json()["word_id"] == word_id
    assert queued.json()["score"] == 0


async def test_phrases_fallback_to_global_when_topic_empty(client, db_session):
    from app.db.models import Phrase

    db_session.add(
        Phrase(
            text_de="Global phrase ...",
            translation_ru="Глобальная фраза",
            essay_part="einleitung",
            topic=None,
            level="B1",
        )
    )
    await db_session.commit()
    res = await client.get("/api/phrases?part=einleitung&topic=unknown_topic_xyz")
    assert res.status_code == 200
    assert any(p["text_de"].startswith("Global") for p in res.json())


async def test_refresh_grammar_endpoint(client, db_session, monkeypatch):
    await seed_words_and_phrases(db_session)
    word_id = (await client.get("/api/words?q=дерево")).json()[0]["id"]

    async def fake_fetch(word):
        return {"title": word, "sections": []}

    monkeypatch.setattr(
        "app.api.routes.words.fetch_wiktionary_entry",
        fake_fetch,
    )
    res = await client.post(f"/api/words/{word_id}/refresh-grammar")
    assert res.status_code == 200
    assert res.json()["id"] == word_id

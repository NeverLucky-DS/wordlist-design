"""Contract tests for pipeline Mistral prompt templates (structure must stay stable)."""

from __future__ import annotations

import json
from unittest.mock import patch

from app.pipeline import enrichment, extraction, supplement, topics_catalog
from app.services import mistral_analyzer as essay_ma


def test_extraction_prompt_requires_words_and_redemittel_json():
    prompt = extraction._EXTRACTION_PROMPT.format(topic="Klimawandel", text="Artikeltext")
    assert "WÖRTER" in prompt
    assert "REDEMITTEL" in prompt
    assert '"words"' in prompt
    assert '"redemittel"' in prompt
    assert "einleitung | argument | gegenargument | beispiel | schluss" in prompt
    assert "Klimawandel" in prompt
    assert "pos:" in prompt


def test_enrichment_batch_prompt_requires_lexicon_fields():
    prompt = enrichment._BATCH_PROMPT.format(count=2, words_block="- Wort A\n- Wort B")
    assert '"words"' in prompt
    for field in ("article", "pos", "level", "ru", "rektion", "declension", "examples_generated"):
        assert f'"{field}"' in prompt
    assert "PFLICHTREGELN" in prompt
    assert "Noun|Verb|Adjective|Other" in prompt or "Noun" in prompt


def test_supplement_words_prompt_excludes_existing():
    prompt = supplement._GEN_WORDS_PROMPT.format(
        topic="Migration",
        n=10,
        focus="Fokus Verben",
        exclude="Zuwanderung, Integration",
    )
    assert "Migration" in prompt
    assert "Zuwanderung" in prompt
    assert '"words"' in prompt
    assert "Grundformen" in prompt


def test_supplement_redemittel_prompt_covers_all_essay_parts():
    prompt = supplement._GEN_REDEMITTEL_PROMPT.format(
        topic="Energie",
        n_einleitung=2,
        n_argument=2,
        n_gegenargument=1,
        n_beispiel=1,
        n_schluss=2,
        exclude="bereits da",
    )
    for part in supplement.ESSAY_PARTS:
        assert part in prompt
    assert '"redemittel"' in prompt
    assert "translation_ru" in prompt


def test_topics_catalog_prompt_returns_json_list():
    prompt = topics_catalog._GEN_TOPICS_PROMPT.format(n=5, exclude="klimawandel, energie")
    assert '"topics"' in prompt or "JSON" in prompt
    assert "klimawandel" in prompt


def test_essay_part_prompt_json_shape_documented():
    """The part prompt must keep documenting the error object fields the frontend expects."""
    prompt = essay_ma._build_part_prompt(
        part_key="argument1",
        part_label="Argument Eins",
        text="Beispieltext.",
        essay_type="argumentativ",
        level="C1",
        previous_points=[],
    )
    required_tokens = [
        "grammar|style|weak|vocabulary",
        "critical|medium|suggestion",
        "what_wrong_ru",
        "why_bad_ru",
        "how_to_fix_ru",
        "b1_variant_de",
        "b2_variant_de",
        "study_phrases_de",
    ]
    for token in required_tokens:
        assert token in prompt, f"missing {token}"


def test_mistral_http_always_requests_json_object():
    from app.pipeline import mistral_http

    captured = {}

    class FakeResp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": json.dumps({"ok": True})}}]}

    def fake_post(url, headers, json, timeout):
        captured["payload"] = json
        return FakeResp()

    with patch.object(mistral_http._requests, "post", fake_post):
        mistral_http._cooldown_until = 0.0
        mistral_http.post_mistral_json([{"role": "user", "content": "hi"}], "key", "model")

    assert captured["payload"]["response_format"] == {"type": "json_object"}


def test_round_focus_rotates():
    assert supplement.round_focus(0) == ""
    assert "VERBEN" in supplement.round_focus(1)
    assert "ADJEKTIVE" in supplement.round_focus(2)
    assert supplement.round_focus(99) == ""

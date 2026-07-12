"""Live integration tests against the Mistral API.

These tests call the real API and validate that responses match the JSON
contracts our prompts and parsers expect. They require MISTRAL_API_KEY
(in backend/.env or the environment) and will fail — not skip — if it is missing.

Unit tests elsewhere mock Mistral; this module is the contract check against production.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.mistral_live


def _load_mistral_credentials() -> tuple[str, str]:
    from dotenv import dotenv_values

    vals = dotenv_values(BACKEND_ROOT / ".env") if (BACKEND_ROOT / ".env").exists() else {}
    key = (vals.get("MISTRAL_API_KEY") or os.environ.get("MISTRAL_API_KEY") or "").strip()
    model = (
        vals.get("MISTRAL_MODEL")
        or os.environ.get("MISTRAL_MODEL")
        or "mistral-large-latest"
    ).strip()
    if not key:
        pytest.fail(
            "Live Mistral tests require MISTRAL_API_KEY in backend/.env or the environment."
        )
    return key, model


@pytest.fixture(scope="module", autouse=True)
def mistral_credentials():
    """Restore real API credentials for this module (conftest clears them for unit tests)."""
    key, model = _load_mistral_credentials()
    os.environ["MISTRAL_API_KEY"] = key
    os.environ["MISTRAL_MODEL"] = model

    from app.config import settings

    settings.mistral_api_key = key
    settings.mistral_model = model
    yield key, model


def _assert_part_response(data: dict) -> None:
    assert isinstance(data, dict)
    score = data.get("part_score")
    assert isinstance(score, (int, float)), "part_score must be numeric"
    assert 0 <= int(score) <= 100
    assert isinstance(data.get("part_feedback_ru"), str)
    assert data["part_feedback_ru"].strip()
    errors = data.get("errors")
    assert isinstance(errors, list)
    for err in errors:
        assert isinstance(err, dict)
        assert isinstance(err.get("excerpt"), str)
        assert err["type"] in {"grammar", "style", "weak", "vocabulary", "good", "strength", ""} or isinstance(
            err.get("type"), str
        )
        assert err.get("severity") in {"critical", "medium", "suggestion", ""} or isinstance(
            err.get("severity"), str
        )


def _assert_final_summary(data: dict) -> None:
    for field in (
        "structure_feedback_ru",
        "topic_feedback_ru",
        "overall_comment_ru",
    ):
        assert isinstance(data.get(field), str), f"missing or invalid {field}"
        assert data[field].strip()
    assert isinstance(data.get("strengths_ru"), list)
    assert isinstance(data.get("next_steps_ru"), list)


def test_post_mistral_json_minimal_contract(mistral_credentials):
    from app.pipeline.mistral_http import post_mistral_json

    key, model = mistral_credentials
    out = post_mistral_json(
        [
            {
                "role": "user",
                "content": 'Return JSON: {"status": "ok", "n": 1}',
            }
        ],
        key,
        model,
        temperature=0.0,
        delays=[10, 20],
    )
    assert isinstance(out, dict)
    assert out.get("status") == "ok"


def test_essay_part_prompt_live(mistral_credentials):
    from app.services.mistral_analyzer import PART_LABELS, _build_part_prompt, _call_mistral

    part_text = (
        "Ich bin der Meinung, dass Technologie unser Leben verbessert, "
        "weil sie uns viel Zeit spart."
    )
    prompt = _build_part_prompt(
        part_key="einleitung",
        part_label=PART_LABELS["einleitung"],
        text=part_text,
        essay_type="argumentativ",
        level="B1",
        previous_points=[],
    )
    parsed = _call_mistral(prompt, label="einleitung_live")
    _assert_part_response(parsed)


def test_essay_final_summary_live(mistral_credentials):
    from app.services.mistral_analyzer import _build_final_prompt, _call_mistral

    blocks = {
        "einleitung": "Technologie ist wichtig.",
        "argument1": "Sie spart Zeit.",
        "argument2": "",
        "schluss": "Balance ist nötig.",
    }
    part_reports = [
        {
            "part": "einleitung",
            "label": "Einleitung",
            "score": 72,
            "feedback_ru": "ok",
            "errors_count": 1,
            "is_empty": False,
        }
    ]
    prompt = _build_final_prompt(
        essay_type="argumentativ",
        level="B1",
        blocks=blocks,
        part_reports=part_reports,
    )
    parsed = _call_mistral(prompt, label="final_summary_live")
    _assert_final_summary(parsed)


async def test_iter_analyze_single_part_live(mistral_credentials):
    from app.services.mistral_analyzer import iter_analyze_events

    text = "Einleitung:\nTechnologie hilft uns im Alltag sehr.\n\nSchluss:\n"
    events = []
    async for event in iter_analyze_events(
        text=text,
        essay_type="argumentativ",
        level="B1",
        only_part="einleitung",
    ):
        events.append(event)

    assert any(e["type"] == "part_start" for e in events)
    assert any(e["type"] == "part_done" for e in events)
    done = next(e for e in events if e["type"] == "done")
    assert done["grade"] in {"A", "B", "C", "D"}
    assert isinstance(done["overall_score"], int)
    assert done.get("final_summary") is None
    assert not any(w.get("code") == "ai_not_configured" for w in done.get("warnings", []))


def test_extraction_prompt_live(mistral_credentials):
    from app.pipeline.extraction import _mistral_extract_sync

    key, model = mistral_credentials
    article = (
        "Der Klimawandel ist eine der größten Herausforderungen unserer Zeit. "
        "Wissenschaftler warnen, dass die globalen Temperaturen steigen und "
        "Extremwetterereignisse häufiger werden. Deshalb müssen wir den Ausstoß "
        "von Treibhausgasen reduzieren und erneuerbare Energien ausbauen. "
        "Politik und Wirtschaft sind gefordert, nachhaltige Lösungen zu finden."
    )
    words, phrases = _mistral_extract_sync(
        article, "Klimawandel", "http://test.local/article", key, model
    )
    assert len(words) >= 3, "expected at least a few B2-C1 words from the article"
    assert all(w.word.strip() for w in words)
    # Redemittel are optional but usually returned
    if phrases:
        assert phrases[0].text_de.strip()


def test_enrichment_batch_live(mistral_credentials):
    from app.pipeline.enrichment import _mistral_batch_sync

    key, model = mistral_credentials
    words_block = (
        "Wort: Klimawandel\n"
        "pos: Noun\n"
        "article: der\n"
        "examples_needed: 1\n"
        "Rohdaten: (keine)\n"
    )
    parsed = _mistral_batch_sync(words_block, count=1, mistral_api_key=key, mistral_model=model)
    items = parsed.get("words")
    assert isinstance(items, list) and len(items) >= 1
    item = items[0]
    assert item.get("word")
    assert item.get("ru", "").strip()
    assert item.get("pos") in {"Noun", "Verb", "Adjective", "Other"}


async def test_supplement_generate_words_live(mistral_credentials):
    import asyncio

    from app.pipeline.supplement import generate_words

    key, model = mistral_credentials
    sem = asyncio.Semaphore(1)
    words, errors = await generate_words(
        "Energiewende",
        n=3,
        exclude=["Solarstrom"],
        mistral_api_key=key,
        mistral_model=model,
        mistral_semaphore=sem,
    )
    assert not errors
    assert len(words) >= 1
    assert all(w.word.strip() for w in words)

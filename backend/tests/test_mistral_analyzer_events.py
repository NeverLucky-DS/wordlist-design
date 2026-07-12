"""Async tests for iter_analyze_events — Mistral flow, fallback, partial analysis."""

from __future__ import annotations

import pytest

from app.config import settings
from app.services import mistral_analyzer as ma


SAMPLE_ESSAY = (
    "Einleitung:\nTechnologie ist wichtig.\n\n"
    "Argument Eins:\nSie spart Zeit.\n\n"
    "Argument Zwei:\nSie schafft auch Risiken.\n\n"
    "Schluss:\nWir brauchen Balance."
)


async def _collect_events(**kwargs):
    events = []
    async for event in ma.iter_analyze_events(**kwargs):
        events.append(event)
    return events


def _part_response(score: int = 80, errors: list | None = None) -> dict:
    return {
        "part_score": score,
        "part_feedback_ru": "Комментарий к части.",
        "errors": errors or [],
    }


def _final_response() -> dict:
    return {
        "structure_feedback_ru": "Структура ok",
        "topic_feedback_ru": "Тема ok",
        "strengths_ru": ["Сильная сторона"],
        "next_steps_ru": ["Шаг 1"],
        "overall_comment_ru": "Итог",
    }


async def test_fallback_when_no_api_key(monkeypatch):
    monkeypatch.setattr(settings, "mistral_api_key", "")
    events = await _collect_events(
        text=SAMPLE_ESSAY, essay_type="argumentativ", level="B1"
    )
    assert len(events) == 1
    done = events[-1]
    assert done["type"] == "done"
    assert done["grade"] in {"A", "B", "C", "D"}
    assert any(w["code"] == "ai_not_configured" for w in done.get("warnings", []))


async def test_only_part_skips_final_summary(monkeypatch):
    monkeypatch.setattr(settings, "mistral_api_key", "")

    events = await _collect_events(
        text=SAMPLE_ESSAY,
        essay_type="argumentativ",
        level="B1",
        only_part="einleitung",
    )
    done = events[-1]
    assert done["type"] == "done"
    assert done.get("final_summary") is None
    assert all(e.get("part") == "einleitung" for e in done.get("errors", []))


async def test_full_flow_with_mocked_mistral(monkeypatch):
    monkeypatch.setattr(settings, "mistral_api_key", "test-key")
    calls: list[str] = []

    def fake_call(prompt: str, *, label: str) -> dict:
        calls.append(label)
        if label == "final_summary":
            return _final_response()
        return _part_response(85)

    monkeypatch.setattr(ma, "_call_mistral", fake_call)

    events = await _collect_events(
        text=SAMPLE_ESSAY, essay_type="argumentativ", level="B2"
    )

    types = [e["type"] for e in events]
    assert types.count("part_start") == 4
    assert types.count("part_done") == 4
    assert types[-1] == "done"
    assert set(calls) == {
        "einleitung",
        "argument1",
        "argument2",
        "schluss",
        "final_summary",
    }
    done = events[-1]
    assert done["overall_score"] >= 0
    assert done["final_summary"]["structure_feedback_ru"] == "Структура ok"


async def test_empty_part_skips_mistral_call(monkeypatch):
    monkeypatch.setattr(settings, "mistral_api_key", "test-key")
    calls: list[str] = []

    def fake_call(prompt: str, *, label: str) -> dict:
        calls.append(label)
        return _final_response() if label == "final_summary" else _part_response(70)

    monkeypatch.setattr(ma, "_call_mistral", fake_call)

    text = "Einleitung:\nNur Intro.\n\nSchluss:\n"
    events = await _collect_events(text=text, essay_type="argumentativ", level="B1")

    done = events[-1]
    assert done["type"] == "done"
    # argument1/argument2 empty → no mistral for them
    assert "argument1" not in calls
    assert "argument2" not in calls
    empty_reports = [r for r in done["part_reports"] if r.get("is_empty")]
    assert len(empty_reports) >= 2


async def test_part_failure_adds_warning_and_continues(monkeypatch):
    monkeypatch.setattr(settings, "mistral_api_key", "test-key")

    def fake_call(prompt: str, *, label: str) -> dict:
        if label == "argument1":
            raise RuntimeError("Mistral down")
        if label == "final_summary":
            return _final_response()
        return _part_response(75)

    monkeypatch.setattr(ma, "_call_mistral", fake_call)

    events = await _collect_events(
        text=SAMPLE_ESSAY, essay_type="argumentativ", level="B1"
    )
    done = events[-1]
    assert done["type"] == "done"
    assert any(w.get("code") == "part_failed" for w in done.get("warnings", []))
    arg1 = next(r for r in done["part_reports"] if r["part"] == "argument1")
    assert arg1["errors_count"] == 0


async def test_analyze_essay_wrapper_returns_dict(monkeypatch):
    monkeypatch.setattr(settings, "mistral_api_key", "")

    result = await ma.analyze_essay(
        text=SAMPLE_ESSAY, essay_type="argumentativ", level="B1"
    )
    assert "overall_score" in result
    assert "errors" in result
    assert "part_reports" in result


async def test_invalid_only_part_treated_as_full(monkeypatch):
    monkeypatch.setattr(settings, "mistral_api_key", "")

    events = await _collect_events(
        text=SAMPLE_ESSAY,
        essay_type="argumentativ",
        level="B1",
        only_part="invalid_part",
    )
    done = events[-1]
    # Falls back to full analysis (4 parts in reports)
    assert len(done["part_reports"]) == 4


async def test_stream_events_include_progress_fields(monkeypatch):
    monkeypatch.setattr(settings, "mistral_api_key", "test-key")
    monkeypatch.setattr(ma, "_call_mistral", lambda *a, **k: _part_response(88))

    events = await _collect_events(
        text="Einleitung:\nKurz.",
        essay_type="argumentativ",
        level="B1",
        only_part="einleitung",
    )
    part_done = next(e for e in events if e["type"] == "part_done")
    assert "all_errors" in part_done
    assert "part_reports" in part_done
    assert part_done["part"] == "einleitung"

"""Unit tests for essay Mistral analyzer — parsing, grading, error normalization."""

from __future__ import annotations

import pytest

from app.services import mistral_analyzer as ma


SAMPLE_ESSAY = (
    "Einleitung:\nTechnologie ist wichtig.\n\n"
    "Argument Eins:\nSie spart Zeit.\n\n"
    "Argument Zwei:\nSie schafft auch Risiken.\n\n"
    "Schluss:\nWir brauchen Balance."
)


class TestExtractParts:
    def test_splits_standard_four_part_essay(self):
        parts = ma._extract_parts(SAMPLE_ESSAY)
        assert parts["einleitung"] == "Technologie ist wichtig."
        assert parts["argument1"] == "Sie spart Zeit."
        assert parts["argument2"] == "Sie schafft auch Risiken."
        assert parts["schluss"] == "Wir brauchen Balance."

    def test_unmarked_text_goes_to_einleitung(self):
        parts = ma._extract_parts("Freier Text ohne Marker.")
        assert parts["einleitung"] == "Freier Text ohne Marker."
        assert parts["argument1"] == ""

    def test_empty_string_yields_empty_parts(self):
        parts = ma._extract_parts("")
        assert all(parts[k] == "" for k in ma.PART_ORDER)

    def test_partial_essay_only_filled_sections(self):
        text = "Einleitung:\nHallo.\n\nSchluss:\nTschüss."
        parts = ma._extract_parts(text)
        assert parts["einleitung"] == "Hallo."
        assert parts["argument1"] == ""
        assert parts["schluss"] == "Tschüss."


class TestPartPromptTemplate:
    def test_part_prompt_contains_required_contract(self):
        prompt = ma._build_part_prompt(
            part_key="einleitung",
            part_label="Einleitung",
            text="Technologie ist wichtig.",
            essay_type="argumentativ",
            level="B1",
            previous_points=["Уже было замечание"],
        )
        assert "Einleitung" in prompt
        assert "argumentativ" in prompt
        assert "B1" in prompt
        assert "part_score(0..100)" in prompt
        assert "errors[]" in prompt
        assert "annotation_kind" in prompt
        assert "excerpt" in prompt
        assert "correction" in prompt
        assert "corrected_sentence_de" in prompt
        assert "study_phrases_de" in prompt
        assert "Уже было замечание" in prompt
        assert "Technologie ist wichtig." in prompt

    def test_final_prompt_contains_structure_fields(self):
        parts = ma._extract_parts(SAMPLE_ESSAY)
        reports = [{"part": "einleitung", "score": 70, "feedback_ru": "ok", "errors_count": 0}]
        prompt = ma._build_final_prompt(
            essay_type="argumentativ",
            level="B2",
            blocks=parts,
            part_reports=reports,
        )
        assert "structure_feedback_ru" in prompt
        assert "topic_feedback_ru" in prompt
        assert "strengths_ru" in prompt
        assert "next_steps_ru" in prompt
        assert "overall_comment_ru" in prompt
        assert "argumentativ" in prompt


class TestErrorNormalization:
    def test_normalize_finds_excerpt_by_substring(self):
        text = "Technologie ist wichtig für uns."
        errors = [
            {
                "start": 99,
                "end": 100,
                "excerpt": "Technologie",
                "type": "grammar",
                "severity": "critical",
                "correction": "Die Technologie",
            }
        ]
        out = ma._normalize_error_ranges(errors, text, "einleitung")
        assert len(out) == 1
        assert out[0]["start"] == 0
        assert out[0]["end"] == len("Technologie")
        assert out[0]["part"] == "einleitung"

    def test_dedupe_same_excerpt_in_one_part(self):
        err = {
            "excerpt": "Technologie",
            "start": 0,
            "end": 11,
            "what_wrong_ru": "same",
            "type": "style",
            "severity": "suggestion",
        }
        assert len(ma._dedupe_errors_part([err, err.copy()])) == 1

    def test_remove_overlapping_keeps_shorter_critical(self):
        errors = [
            {"start": 0, "end": 20, "severity": "critical", "excerpt": "long fragment here"},
            {"start": 0, "end": 5, "severity": "critical", "excerpt": "long"},
        ]
        kept = ma._remove_overlapping_errors(errors)
        assert len(kept) == 1
        assert kept[0]["end"] - kept[0]["start"] <= 5

    def test_unactionable_hard_error_dropped_when_correction_equals_excerpt(self):
        err = {
            "annotation_kind": "critical",
            "type": "grammar",
            "severity": "critical",
            "excerpt": "ist wichtig",
            "correction": "ist wichtig",
        }
        assert ma._is_unactionable_hard_error(err) is True

    def test_good_fragment_not_unactionable(self):
        err = {
            "annotation_kind": "good_fragment",
            "excerpt": "gut",
            "correction": "gut",
        }
        assert ma._is_unactionable_hard_error(err) is False

    def test_cap_soft_errors_for_b1(self):
        soft = [
            {
                "start": i,
                "end": i + 1,
                "annotation_kind": "suggestion",
                "excerpt": f"x{i}",
                "type": "style",
                "severity": "suggestion",
            }
            for i in range(5)
        ]
        hard = [
            {
                "start": 100,
                "end": 101,
                "annotation_kind": "critical",
                "excerpt": "y",
                "type": "grammar",
                "severity": "critical",
            }
        ]
        capped = ma._cap_soft_errors(hard + soft, "B1", max_soft=2)
        assert len(capped) == 3  # 1 hard + 2 soft
        kinds = {e["annotation_kind"] for e in capped}
        assert kinds == {"critical", "suggestion"}
        assert sum(1 for e in capped if e["annotation_kind"] == "suggestion") == 2

    def test_b2_does_not_cap_soft_errors(self):
        soft = [
            {
                "start": i,
                "end": i + 1,
                "annotation_kind": "suggestion",
                "excerpt": f"x{i}",
            }
            for i in range(5)
        ]
        assert len(ma._cap_soft_errors(soft, "B2")) == 5


class TestAnnotationKindInference:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ({"annotation_kind": "good_fragment"}, "good_fragment"),
            ({"severity": "suggestion"}, "suggestion"),
            ({"type": "grammar", "severity": "critical"}, "critical"),
            ({"type": "vocabulary", "b2_variant_de": "präziser"}, "b2_potential"),
            ({"type": "style"}, "style"),
        ],
    )
    def test_infer_kind(self, raw, expected):
        assert ma._infer_annotation_kind(raw) == expected


class TestGrading:
    @pytest.mark.parametrize(
        ("scores", "expected_grade"),
        [
            ([90, 88], "A"),
            ([75, 72], "B"),
            ([60, 58], "C"),
            ([40, 45], "D"),
        ],
    )
    def test_grade_from_scores(self, scores, expected_grade):
        score, grade = ma._grade_from_scores(scores)
        assert grade == expected_grade
        assert 0 <= score <= 100

    def test_critical_errors_reduce_overall_score(self):
        scores = [80, 80]
        errors = [
            {"annotation_kind": "critical", "severity": "critical"},
            {"annotation_kind": "critical", "severity": "critical"},
        ]
        base, _ = ma._grade_from_scores(scores)
        penalized, grade = ma._grade_from_scores_and_errors(scores, errors)
        assert penalized < base
        assert grade in {"A", "B", "C", "D"}


class TestFallbackAnalysis:
    def test_fallback_has_four_part_reports(self):
        parts = ma._extract_parts(SAMPLE_ESSAY)
        result = ma._fallback_analysis(parts)
        assert result["grade"] in {"A", "B", "C", "D"}
        assert 0 <= result["overall_score"] <= 100
        assert len(result["part_reports"]) == 4
        assert result["final_summary"] is not None
        assert result["model"]

    def test_empty_part_gets_zero_score(self):
        fb = ma._fallback_part_analysis("schluss", "")
        assert fb["part_score"] == 0
        assert fb["errors"] == []

    def test_nonempty_part_gets_suggestion_error(self):
        fb = ma._fallback_part_analysis(
            "einleitung",
            "Dies ist ein langer Einleitungssatz mit genug Inhalt für Feedback.",
        )
        assert fb["part_score"] >= 55
        assert len(fb["errors"]) >= 1
        assert fb["errors"][0]["annotation_kind"] == "suggestion"


class TestCallMistralContract:
    def test_call_mistral_uses_shared_helper(self, monkeypatch):
        captured: dict = {}

        def fake_post(messages, api_key, model, **kwargs):
            captured["messages"] = messages
            captured["model"] = model
            captured["temperature"] = kwargs.get("temperature")
            return {"part_score": 77, "part_feedback_ru": "ok", "errors": []}

        monkeypatch.setattr(ma, "post_mistral_json", fake_post)
        result = ma._call_mistral("Test prompt", label="einleitung")
        assert result["part_score"] == 77
        assert captured["messages"][0]["content"] == "Return only valid JSON. No markdown."
        assert captured["messages"][1]["content"] == "Test prompt"
        assert captured["temperature"] == 0.2

"""Unit tests for pipeline word normalisation (lemma + article cleanup)."""

from __future__ import annotations

import pytest

from app.pipeline.normalize import _HAS_SIMPLEMMA, clean_word, dedupe_candidates, normalize_candidate
from app.pipeline.types import WordCandidate


def test_clean_word_strips_brackets_and_hints():
    assert clean_word("die Emission(en)") == "die Emission"
    assert clean_word("das Szenario (denkbare ~ )") == "das Szenario"
    assert clean_word("der Abstand [als Phrase]") == "der Abstand"
    assert clean_word("hinweisen *auf etw.") == "hinweisen"


def test_normalize_candidate_extracts_article_and_lemma():
    c = WordCandidate(word="die Anpassung (an + Akk.)", pos="Noun")
    out = normalize_candidate(c)
    assert out is not None
    assert out.word == "Anpassung"
    assert out.article == "die"


def test_normalize_candidate_keeps_collocations():
    c = WordCandidate(word="fossile Energieträger", pos="Noun", article="Die")
    out = normalize_candidate(c)
    assert out is not None
    assert out.word == "fossile Energieträger"
    assert out.article == "die"


def test_normalize_candidate_rejects_garbage():
    assert normalize_candidate(WordCandidate(word="ab")) is None
    assert normalize_candidate(WordCandidate(word="CO2-Wert 42%")) is None
    assert normalize_candidate(WordCandidate(word="")) is None


@pytest.mark.skipif(not _HAS_SIMPLEMMA, reason="simplemma not installed")
def test_normalize_candidate_lemmatizes_inflected_forms():
    out = normalize_candidate(WordCandidate(word="Emissionen", pos="Noun", article="die"))
    assert out is not None
    assert out.word == "Emission"

    out = normalize_candidate(WordCandidate(word="nachhaltigen", pos="Adjective"))
    assert out is not None
    assert out.word == "nachhaltig"


def test_dedupe_candidates_merges_examples_and_article():
    a = WordCandidate(word="Klimawandel", article=None, examples=["Satz 1."])
    b = WordCandidate(word="klimawandel", article="der", examples=["Satz 2."])
    merged = dedupe_candidates([a, b])
    assert len(merged) == 1
    assert merged[0].article == "der"
    assert merged[0].examples == ["Satz 1.", "Satz 2."]

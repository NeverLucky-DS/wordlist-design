from __future__ import annotations


def _pick_pos(pos: str | None) -> str:
    value = (pos or "").lower()
    if "verb" in value:
        return "verb"
    if "noun" in value or "substantiv" in value:
        return "noun"
    if "adjective" in value:
        return "adjective"
    if "adverb" in value:
        return "adverb"
    return "unknown"


def normalize_wiktionary_entry(raw: dict | None, *, word: str) -> dict:
    if not raw:
        return {"status": "not_found", "word": word}

    title = raw.get("title") or word
    lang = raw.get("lang") or "de"
    pos = _pick_pos(raw.get("pos"))

    forms = raw.get("forms")
    if not isinstance(forms, list):
        forms = []

    metadata = raw.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    grammar_data = {
        "status": "ok",
        "word": title,
        "lang": lang,
        "type": pos,
        "article": raw.get("article"),
        "plural": raw.get("plural"),
        "governing_case": raw.get("governing_case"),
        "preposition": raw.get("preposition"),
        "example_governing": raw.get("example_governing"),
        "forms": forms,
        "source_url": raw.get("source_url"),
        "metadata": metadata,
    }

    has_core = any(
        grammar_data.get(key)
        for key in ("article", "plural", "governing_case", "preposition", "forms")
    )
    if not has_core:
        grammar_data["status"] = "partial"
    return grammar_data

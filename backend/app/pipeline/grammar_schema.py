from __future__ import annotations

"""Canonical grammar_data schema — validation & normalisation.

One source of truth for the shape the frontend reads (js/app.js `_mapApiWord`).
Used on every write so malformed LLM output (mixed DE/EN keys, capitalised
adjective keys, per-person objects where a string is expected) can never reach
the DB, and to deterministically normalise legacy v1–v3 rows.

Canonical `grammar_data`:
    {
      "definition": "<German one-sentence Bedeutung>"  (optional),
      "rektion":    "auf + Akk." | "",
      "ready_phrase": "..." | "",
      "ipa":        "[…]" | "",
      "declension": { ... per POS ... }
    }

declension per POS:
    noun: {Nominativ:{singular,plural}, Genitiv:{…}, Dativ:{…}, Akkusativ:{…}}
    verb: {"Präsens":{ich,du,"er/sie/es",wir,ihr,"sie/Sie"}, "Präteritum":str,
           "Partizip II":str, "hilfsverb":"haben"|"sein"}
    adj:  {"positiv":str, "komparativ":str, "superlativ":str}
"""

from typing import Any

_CASES = ("Nominativ", "Genitiv", "Dativ", "Akkusativ")
_PERSONS = ("ich", "du", "er/sie/es", "wir", "ihr", "sie/Sie")

# tolerated aliases → canonical key (lets us absorb older/LLM variants)
_PRESENT_ALIASES = {"präsens": "Präsens", "praesens": "Präsens", "present": "Präsens"}
_PRAET_ALIASES = {"präteritum": "Präteritum", "prateritum": "Präteritum",
                  "simple_past": "Präteritum", "preterite": "Präteritum", "imperfekt": "Präteritum"}
_PART_ALIASES = {"partizip ii": "Partizip II", "partizip2": "Partizip II",
                 "partizipii": "Partizip II", "perfect": "Partizip II", "partizip_ii": "Partizip II"}
_AUX_ALIASES = {"hilfsverb": "hilfsverb", "auxiliary": "hilfsverb", "aux": "hilfsverb"}
_PERSON_ALIASES = {
    "ich": "ich", "du": "du",
    "er": "er/sie/es", "er/sie/es": "er/sie/es", "er, sie, es": "er/sie/es",
    "wir": "wir", "ihr": "ihr",
    "sie": "sie/Sie", "sie/sie": "sie/Sie", "sie/Sie": "sie/Sie",
}


def _s(v: Any) -> str:
    """Coerce a value to a clean display string (objects → first person form)."""
    if isinstance(v, dict):
        for k in ("er/sie/es", "ich"):
            if v.get(k):
                return str(v[k]).strip()
        for val in v.values():
            if val:
                return str(val).strip()
        return ""
    return str(v or "").strip()


def _norm_present(raw: Any) -> dict:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in raw.items():
        person = _PERSON_ALIASES.get(str(k).strip().lower())
        if person and str(v).strip():
            out[person] = str(v).strip()
    return {p: out[p] for p in _PERSONS if p in out}


def normalize_declension(pos: str, raw: Any) -> dict:
    """Return a declension dict in canonical shape for *pos* (best effort)."""
    if not isinstance(raw, dict):
        return {}
    lower = {str(k).strip().lower(): (k, v) for k, v in raw.items()}

    if pos == "noun":
        out: dict = {}
        # canonical full-case shape already?
        for case in _CASES:
            cell = raw.get(case)
            if isinstance(cell, dict) and (cell.get("singular") or cell.get("plural")):
                out[case] = {"singular": _s(cell.get("singular")) or "—",
                             "plural": _s(cell.get("plural")) or "—"}
        if out:
            return out
        # legacy compact {Genus, Plural, "Genitiv Singular"} → keep what we have
        compact: dict = {}
        plural = _s(raw.get("Plural") or raw.get("plural"))
        gen = _s(raw.get("Genitiv Singular") or raw.get("genitiv_singular"))
        if plural:
            compact["Plural"] = plural
        if gen:
            compact["Genitiv Singular"] = gen
        return compact

    if pos == "verb":
        out = {}
        present = None
        for k, (orig, v) in lower.items():
            if k in _PRESENT_ALIASES:
                present = _norm_present(v)
                break
        if present:
            out["Präsens"] = present
        for k, (orig, v) in lower.items():
            if k in _PRAET_ALIASES and _s(v):
                out["Präteritum"] = _s(v)
            elif k in _PART_ALIASES and _s(v):
                out["Partizip II"] = _s(v)
            elif k in _AUX_ALIASES and _s(v):
                aux = _s(v).split(",")[0].strip().lower()
                out["hilfsverb"] = "sein" if aux == "sein" else "haben"
        return out

    if pos == "adjective":
        out = {}
        pos_v = _s(raw.get("positiv") or raw.get("Positiv"))
        komp = _s(raw.get("komparativ") or raw.get("Komparativ"))
        sup = _s(raw.get("superlativ") or raw.get("Superlativ"))
        if pos_v:
            out["positiv"] = pos_v
        if komp and komp != "—":
            out["komparativ"] = komp
        if sup and sup != "—":
            out["superlativ"] = sup if sup.startswith("am ") else f"am {sup}"
        return out

    return {}


def merge_declension(wiktionary: dict, llm: dict, pos: str) -> dict:
    """Prefer authoritative Wiktionary forms; fill gaps from the (normalised) LLM.

    For verbs this matters most: Wiktionary gives ich/du/er + Präteritum +
    Partizip II + Hilfsverb authoritatively; the LLM supplies wir/ihr/sie.
    """
    wikt = normalize_declension(pos, wiktionary or {})
    extra = normalize_declension(pos, llm or {})
    if not wikt:
        return extra
    if not extra:
        return wikt

    if pos == "verb":
        merged = dict(wikt)
        # merge present persons: Wiktionary wins per-person, LLM fills the rest
        present = dict(extra.get("Präsens") or {})
        present.update(wikt.get("Präsens") or {})
        if present:
            merged["Präsens"] = {p: present[p] for p in _PERSONS if p in present}
        for key in ("Präteritum", "Partizip II", "hilfsverb"):
            if not merged.get(key) and extra.get(key):
                merged[key] = extra[key]
        return merged

    # nouns / adjectives: Wiktionary is authoritative and complete — use it as-is
    # (merge is only reached when `wikt` is non-empty), so no legacy keys leak in.
    return wikt


def normalize_grammar_data(pos: str, data: Any) -> dict:
    """Full grammar_data normaliser used on write."""
    src = data if isinstance(data, dict) else {}
    out: dict = {
        "definition": _s(src.get("definition")),
        "rektion": _s(src.get("rektion")),
        "ready_phrase": _s(src.get("ready_phrase")),
        "ipa": _s(src.get("ipa")),
        "declension": normalize_declension(pos, src.get("declension")),
    }
    return out

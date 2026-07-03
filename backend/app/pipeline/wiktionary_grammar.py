from __future__ import annotations

"""Deterministic grammar extraction from de.wiktionary.org overview templates.

The German Wiktionary stores complete paradigm tables in three "Übersicht"
templates, plus IPA in {{Lautschrift}}. Parsing them directly is accurate and
free — far better than asking an LLM to reproduce declension tables (which is
where the v3 pipeline produced mixed DE/EN keys and empty tables).

What this module is authoritative for:
- Nouns      → full declension (4 cases × Sg/Pl) + Genus → article
- Adjectives → Positiv / Komparativ / Superlativ
- Verbs      → Hilfsverb, Partizip II, Präteritum, Präsens (ich/du/er) — the
               forms the overview template actually carries. The remaining
               present persons (wir/ihr/sie) are left to the LLM + verification,
               because deriving them is unreliable for strong verbs.
- IPA        → first {{Lautschrift}}

Output `declension` dicts use exactly the keys the frontend reads
(js/app.js `_mapApiWord`):
  noun: {Nominativ:{singular,plural}, Genitiv:{...}, Dativ:{...}, Akkusativ:{...}}
  verb: {"Präsens":{...}, "Präteritum": str, "Partizip II": str, "hilfsverb": str}
  adj:  {positiv, komparativ, superlativ}
"""

import re
from dataclasses import dataclass, field

_TEMPLATE_NAMES = {
    "noun": "Deutsch Substantiv Übersicht",
    "verb": "Deutsch Verb Übersicht",
    "adjective": "Deutsch Adjektiv Übersicht",
}

_GENUS_TO_ARTICLE = {"m": "der", "f": "die", "n": "das"}
_CASES = ("Nominativ", "Genitiv", "Dativ", "Akkusativ")


@dataclass
class WiktGrammar:
    pos: str | None = None              # noun | verb | adjective | None
    article: str | None = None          # der | die | das | None
    declension: dict = field(default_factory=dict)
    ipa: str = ""

    def is_empty(self) -> bool:
        return not self.declension and not self.article and not self.ipa


# ---------------------------------------------------------------------------
# Template extraction
# ---------------------------------------------------------------------------

def _find_template(wikitext: str, name: str) -> str | None:
    """Return the body (between the outermost braces) of {{name ...}} or None."""
    start = wikitext.find("{{" + name)
    if start == -1:
        return None
    i = start + 2
    depth = 1
    while i < len(wikitext) and depth:
        if wikitext.startswith("{{", i):
            depth += 1
            i += 2
        elif wikitext.startswith("}}", i):
            depth -= 1
            i += 2
        else:
            i += 1
    return wikitext[start:i]


def _parse_params(template: str) -> dict[str, str]:
    """Split a template body into {param: value}, ignoring nested templates/links."""
    # Drop the leading "{{Name" and trailing "}}"
    inner = template
    inner = re.sub(r"^\{\{[^|]*", "", inner.strip())
    inner = inner.rstrip("}").strip()

    # Split on top-level pipes only (not inside [[..]] or {{..}})
    parts: list[str] = []
    buf = ""
    depth_brace = depth_brack = 0
    for ch in inner:
        if ch == "{":
            depth_brace += 1
        elif ch == "}":
            depth_brace = max(0, depth_brace - 1)
        elif ch == "[":
            depth_brack += 1
        elif ch == "]":
            depth_brack = max(0, depth_brack - 1)
        if ch == "|" and depth_brace == 0 and depth_brack == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf)

    params: dict[str, str] = {}
    for p in parts:
        if "=" not in p:
            continue
        key, _, val = p.partition("=")
        key = key.strip()
        val = _clean_value(val)
        if key and val:
            params[key] = val
    return params


def _clean_value(val: str) -> str:
    val = val.strip()
    val = re.sub(r"<!--.*?-->", "", val, flags=re.DOTALL)
    val = re.sub(r"<ref.*?</ref>", "", val, flags=re.DOTALL)
    val = re.sub(r"<ref[^>]*/>", "", val)
    # [[link|text]] → text ; [[link]] → link
    val = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]", r"\1", val)
    val = val.replace("'''", "").replace("''", "")
    return val.strip().strip("|").strip()


# ---------------------------------------------------------------------------
# IPA
# ---------------------------------------------------------------------------

def _extract_ipa(wikitext: str) -> str:
    m = re.search(r"\{\{Lautschrift\|([^}|]+)\}\}", wikitext)
    if not m:
        return ""
    ipa = m.group(1).strip()
    return f"[{ipa}]" if ipa else ""


# ---------------------------------------------------------------------------
# Per-POS builders
# ---------------------------------------------------------------------------

def _build_noun(p: dict[str, str]) -> tuple[str | None, dict]:
    article = _GENUS_TO_ARTICLE.get(p.get("Genus", "").strip().lower()[:1])
    decl: dict = {}
    for case in _CASES:
        sg = p.get(f"{case} Singular", "").strip()
        pl = p.get(f"{case} Plural", "").strip()
        if sg or pl:
            decl[case] = {"singular": sg or "—", "plural": pl or "—"}
    return article, decl


def _build_verb(p: dict[str, str]) -> dict:
    er = p.get("Präsens_er, sie, es") or p.get("Präsens_er") or ""
    praesens = {}
    for label, key in (("ich", "Präsens_ich"), ("du", "Präsens_du"), ("er/sie/es", None)):
        if key:
            v = p.get(key, "").strip()
        else:
            v = er.strip()
        if v:
            praesens[label] = v
    decl: dict = {}
    if praesens:
        decl["Präsens"] = praesens
    if p.get("Präteritum_ich"):
        decl["Präteritum"] = p["Präteritum_ich"].strip()
    if p.get("Partizip II"):
        decl["Partizip II"] = p["Partizip II"].strip()
    if p.get("Hilfsverb"):
        decl["hilfsverb"] = p["Hilfsverb"].strip().split(",")[0].strip()
    return decl


def _build_adjective(p: dict[str, str]) -> dict:
    pos = p.get("Positiv", "").strip()
    komp = p.get("Komparativ", "").strip()
    sup = p.get("Superlativ", "").strip()
    decl: dict = {}
    if pos:
        decl["positiv"] = pos
    if komp and komp != "—":
        decl["komparativ"] = komp
    if sup and sup != "—":
        # Wiktionary stores the bare superlative ("nachhaltigsten"); display as "am …"
        decl["superlativ"] = sup if sup.startswith("am ") else f"am {sup}"
    return decl


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_grammar(wikitext: str) -> WiktGrammar:
    """Parse a German Wiktionary page's wikitext into structured grammar.

    Detects POS from whichever Übersicht template is present.
    """
    out = WiktGrammar(ipa=_extract_ipa(wikitext))
    if not wikitext:
        return out

    for pos, name in _TEMPLATE_NAMES.items():
        tmpl = _find_template(wikitext, name)
        if not tmpl:
            continue
        params = _parse_params(tmpl)
        out.pos = pos
        if pos == "noun":
            out.article, out.declension = _build_noun(params)
        elif pos == "verb":
            out.declension = _build_verb(params)
        elif pos == "adjective":
            out.declension = _build_adjective(params)
        break

    return out

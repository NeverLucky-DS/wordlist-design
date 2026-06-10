from __future__ import annotations

"""Per-word verification pass.

After a word is assembled (Wiktionary grammar + LLM content), a second LLM call
checks each entry for correctness and completeness and returns, per word:
  - ok:     all required fields correct & complete
  - issues: short human-readable problems
  - fix:    only the fields that must be corrected (ru/definition/rektion/article)

The caller applies `fix`, then writes the word if it is `ok` (or fixable);
otherwise it goes to word_failures with the issues, so nothing wrong/empty
silently lands in the DB.
"""

from .mistral_http import post_mistral_json

_VERIFY_PROMPT = """Du bist ein strenger Korrektor für ein DaF-Wörterbuch (B2–C1).
Prüfe {count} Einträge auf KORREKTHEIT und VOLLSTÄNDIGKEIT.

Pro Eintrag prüfen:
- Artikel (der/die/das) für Nomen korrekt?
- Russische Übersetzung "ru" korrekt und nicht leer?
- Deutsche Definition korrekt, ein Satz, kein Zirkelschluss?
- Rektion korrekt (oder zu Recht leer)?
- Enthält JEDES Beispiel das Stichwort (auch flektiert) und ist es korrektes Deutsch?
  Stimmen die russischen Übersetzungen der Beispiele?

Gib AUSSCHLIESSLICH ein JSON-Objekt zurück (kein Markdown):
{{"words": [
  {{"word": "<exakt das Eingabewort>",
    "ok": true,
    "issues": [],
    "fix": {{}}
  }}
]}}
- "ok": false, wenn etwas falsch oder ein Pflichtfeld (ru, definition) leer ist.
- "fix": NUR zu korrigierende Felder aus {{ru, definition, rektion, article}}. Sonst {{}}.
- Erfinde nichts. Bei Unsicherheit ok=false mit kurzer "issues"-Beschreibung.

Einträge:
{words_block}
"""


def _decl_summary(pos: str, decl: dict) -> str:
    if not isinstance(decl, dict) or not decl:
        return "(keine)"
    if pos == "verb":
        pres = decl.get("Präsens") or {}
        return (f"Hilfsverb={decl.get('hilfsverb','?')}, "
                f"er-Form={pres.get('er/sie/es','?')}, "
                f"Prät={decl.get('Präteritum','?')}, PartII={decl.get('Partizip II','?')}")
    if pos == "adjective":
        return f"{decl.get('positiv','?')} / {decl.get('komparativ','?')} / {decl.get('superlativ','?')}"
    nom = decl.get("Nominativ") or {}
    return f"Nom Sg/Pl = {nom.get('singular','?')} / {nom.get('plural','?')}"


def _build_block(entries: list[dict]) -> str:
    blocks = []
    for i, e in enumerate(entries, 1):
        ex_lines = "\n".join(
            f"    • {x.get('text_de','')}  →  {x.get('text_ru','—')}"
            for x in (e.get("examples") or [])[:3]
        ) or "    (keine)"
        blocks.append(
            f"--- Wort {i}: {e['word']}\n"
            f"  Wortart: {e.get('pos','?')} | Artikel: {e.get('article') or '-'}\n"
            f"  ru: {e.get('ru','')}\n"
            f"  Definition: {e.get('definition','')}\n"
            f"  Rektion: {e.get('rektion') or '-'}\n"
            f"  Grammatik: {_decl_summary(e.get('pos',''), e.get('declension') or {})}\n"
            f"  Beispiele:\n{ex_lines}"
        )
    return "\n\n".join(blocks)


def verify_words(entries: list[dict], api_key: str, model: str) -> dict[str, dict]:
    """Return {word_lower: {ok: bool, issues: list, fix: dict}}."""
    if not entries:
        return {}
    prompt = _VERIFY_PROMPT.format(count=len(entries), words_block=_build_block(entries))
    parsed = post_mistral_json(
        [
            {"role": "system", "content": "Return only a valid JSON object. No markdown, no prose."},
            {"role": "user", "content": prompt},
        ],
        api_key, model, temperature=0.0, timeout=180, delays=[5, 15, 30],
    )
    items = parsed.get("words")
    if not isinstance(items, list):
        items = next((v for v in parsed.values() if isinstance(v, list)), [])

    out: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict) or not item.get("word"):
            continue
        fix = item.get("fix") if isinstance(item.get("fix"), dict) else {}
        clean_fix = {k: str(v).strip() for k, v in fix.items()
                     if k in ("ru", "definition", "rektion", "article") and str(v).strip()}
        out[str(item["word"]).strip().lower()] = {
            "ok": bool(item.get("ok", False)),
            "issues": [str(x) for x in (item.get("issues") or [])][:5],
            "fix": clean_fix,
        }
    return out

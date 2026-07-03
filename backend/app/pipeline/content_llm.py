from __future__ import annotations

"""LLM content generation — everything that is NOT grammar.

Grammar (declension/conjugation/Steigerung/IPA/article) comes deterministically
from Wiktionary (see wiktionary_grammar.py). The LLM is only asked for what it is
actually good at and what dictionaries don't give in clean form:

  - ru:          Russian translation (2–5 words)
  - definition:  one-sentence German Bedeutung (B2-level, plain)
  - rektion:     governed preposition + case, e.g. "auf + Akk." (or "")
  - ready_phrase: a short collocation showing usage (or "")
  - examples:    up to 3 B2–C1 sentences (headword in **bold**) WITH a Russian
                 translation each; article-supplied examples are reused & translated.

Batched (N words per call) to stay under the free Mistral rate limit.
"""

from .mistral_http import post_mistral_json

_CONTENT_PROMPT = """Du bist ein zweisprachiges (Deutsch–Russisch) Lexikon-Redaktionssystem für DaF (B2–C1).
Unten stehen {count} deutsche Wörter mit Wörterbuch-Hinweisen. Bearbeite ALLE.

Gib AUSSCHLIESSLICH ein JSON-Objekt zurück (kein Markdown):
{{"words": [
  {{
    "word": "<exakt das Eingabewort>",
    "ru": "точный перевод на русский (2-5 слов)",
    "definition": "Kurze deutsche Definition in EINEM Satz (B2, ohne das Wort selbst zu wiederholen).",
    "rektion": "Rektion wie 'auf + Akk.' / 'an + Dat.' — nur wenn das Wort eine Präposition regiert, sonst \\"\\"",
    "ready_phrase": "kurze typische Kollokation mit dem Wort, oder \\"\\"",
    "examples": [
      {{"de": "Beispiel mit **Wort** fett markiert.", "ru": "русский перевод этого предложения."}}
    ]
  }}
]}}

REGELN:
- "ru" und "definition" sind PFLICHT und dürfen nicht leer sein.
- "examples": GENAU 3 Stück. Übernimm zuerst die vorhandenen Quell-Beispiele (übersetze sie ins Russische),
  ergänze dann auf 3 mit neuen B2–C1-Sätzen zum Thema. Das Stichwort IMMER als **Wort** markieren.
- Jedes Beispiel MUSS eine russische Übersetzung "ru" haben.
- Erfinde keine Rektion/Kollokation, wenn es keine gibt — dann "".

Eingabewörter:
{words_block}
"""


def _build_block(words: list[dict]) -> str:
    """words: [{word, pos, article, definitions, examples}] → prompt block."""
    blocks = []
    for i, w in enumerate(words, 1):
        defs = (w.get("definitions") or "").strip()
        ex = w.get("examples") or []
        ex_lines = "\n".join(f"    • {e}" for e in ex[:3]) or "    (keine)"
        blocks.append(
            f"--- Wort {i}: {w['word']}\n"
            f"  Wortart: {w.get('pos','?')} | Artikel: {w.get('article') or '-'}\n"
            f"  Wörterbuch-Bedeutungen: {defs[:500] or '(keine)'}\n"
            f"  Quell-Beispiele (übernehmen + übersetzen):\n{ex_lines}"
        )
    return "\n\n".join(blocks)


def generate_content(
    words: list[dict],
    api_key: str,
    model: str,
) -> dict[str, dict]:
    """Return {word_lower: content_dict}. Raises on hard LLM failure."""
    if not words:
        return {}
    prompt = _CONTENT_PROMPT.format(count=len(words), words_block=_build_block(words))
    parsed = post_mistral_json(
        [
            {"role": "system", "content": "Return only a valid JSON object. No markdown, no prose."},
            {"role": "user", "content": prompt},
        ],
        api_key, model, temperature=0.2, timeout=180, delays=[5, 15, 30],
    )
    items = parsed.get("words")
    if not isinstance(items, list):
        items = next((v for v in parsed.values() if isinstance(v, list)), [])

    out: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict) or not item.get("word"):
            continue
        examples = []
        for e in item.get("examples", []) or []:
            if isinstance(e, dict) and e.get("de"):
                examples.append({"text_de": str(e["de"]).strip(),
                                 "text_ru": str(e.get("ru", "")).strip(),
                                 "is_ai": True})
            elif isinstance(e, str) and e.strip():
                examples.append({"text_de": e.strip(), "text_ru": "", "is_ai": True})
        out[str(item["word"]).strip().lower()] = {
            "ru": str(item.get("ru", "")).strip(),
            "definition": str(item.get("definition", "")).strip(),
            "rektion": str(item.get("rektion", "")).strip(),
            "ready_phrase": str(item.get("ready_phrase", "")).replace("**", "").strip(),
            "examples": examples[:3],
        }
    return out

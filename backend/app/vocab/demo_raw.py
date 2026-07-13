"""Transparency demo: show the RAW per-word data collected from the dictionaries
*before* anything is sent to Mistral.

For each sample lemma we stream the chosen DSL sources, collect the matching
card from each, and print:
  1) the raw DSL body per dictionary (markup-stripped for readability)
  2) the merged "pre-LLM payload" — exactly what stage [3] would hand to the LLM

Run:  python3 -m backend.app.vocab.demo_raw  [word ...]
      DICT_ROOT=/path/to/dictionaries python3 backend/app/vocab/demo_raw.py Haus gehen
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# allow running as a plain script (no package install)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # backend/ on path

from app.vocab import dsl
from app.vocab.sources import DSL_SOURCES, Source

SAMPLE = ["Haus", "gehen", "wichtig", "Umwelt", "Entwicklung", "ander"]


def build_payload(word: str, hits: dict[str, tuple[Source, dsl.RawEntry]]) -> dict:
    """Merge per-dictionary parses into the pre-LLM aggregate for one lemma."""
    translations: list[str] = []
    forms: list[str] = []
    pos: list[str] = []
    article = None
    examples: list[str] = []
    synonyms_de: list[str] = []
    collocations: list[str] = []

    for key, (src, entry) in hits.items():
        p = dsl.parse_entry(entry)
        if src.role == "general":
            article = article or p.article
            for f in p.forms:
                if f not in forms:
                    forms.append(f)
            for x in p.pos:
                if x not in pos:
                    pos.append(x)
            for t in p.translations:
                if t not in translations:
                    translations.append(t)
            for e in p.examples:
                if e not in examples:
                    examples.append(e)
        elif src.role == "synonyms":
            synonyms_de += [dsl.strip_markup(l).lstrip("•* ")
                            for l in entry.body_lines if "•" in l]
        elif src.role == "collocations":
            collocations += [dsl.strip_markup(l) for l in entry.body_lines]

    return {
        "word": word,
        "article": article,
        "pos": pos,
        "forms": forms,
        "translations_ru": translations[:12],
        "examples_from_dict": examples[:8],
        "synonyms_de": synonyms_de[:12],
        "collocations": collocations[:8],
        "sources_hit": sorted(hits.keys()),
    }


def main(words: list[str]) -> None:
    targets = set(words)
    # per source: stream once, collect all sample hits
    per_word: dict[str, dict[str, tuple[Source, dsl.RawEntry]]] = {w: {} for w in words}
    for src in DSL_SOURCES:
        if not src.path.exists():
            print(f"!! missing: {src.key} -> {src.path}", file=sys.stderr)
            continue
        found = dsl.collect(src.path, targets)
        for hw, entry in found.items():
            per_word[hw][src.key] = (src, entry)

    for w in words:
        hits = per_word[w]
        print("=" * 78)
        print(f"WORD: {w}   (found in: {', '.join(sorted(hits)) or 'NONE'})")
        print("=" * 78)
        for key, (src, entry) in hits.items():
            print(f"\n--- [{key}] ({src.role}) raw card, markup-stripped ---")
            for line in entry.body_lines[:6]:
                print("   ", dsl.strip_markup(line)[:200])
        print("\n>>> MERGED pre-LLM payload:")
        print(json.dumps(build_payload(w, hits), ensure_ascii=False, indent=2))
        print()


if __name__ == "__main__":
    main(sys.argv[1:] or SAMPLE)

"""Registry of the dictionaries we actually ingest.

Chosen set (per design decision): general De-Ru + enrichment (synonyms,
collocations, idioms). EXCLUDED: Landeskunde (Германия/Австрия), slang,
technical (aviation/nuclear/plastics/...).

`format` drives which reader is used. DSL sources are handled by `dsl.py`
(dependency-free). `stardict`/`mdx` are wired later via pyglossary.

Dictionaries live in the main working tree (untracked, ~391 MB); the pipeline
worktree references them by absolute path via DICT_ROOT.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DICT_ROOT = Path(
    os.environ.get("DICT_ROOT", "/Users/shallbe/Desktop/Код/Wordlist design/dictionaries")
)


@dataclass(frozen=True)
class Source:
    key: str
    role: str          # "general" | "synonyms" | "collocations" | "idioms"
    fmt: str           # "dsl" | "stardict" | "mdx"
    rel: str           # path relative to DICT_ROOT
    coverage: bool = False   # True = may create new lemmas; False = enrich only
    contents_lang: str = "ru"   # ru = De-Ru gloss; de = De-De (Duden synonyms)

    @property
    def path(self) -> Path:
        return DICT_ROOT / self.rel


SOURCES: list[Source] = [
    # --- coverage: lemma-keyed general De-Ru (translation + grammar backbone) ---
    Source("universal", "general", "dsl", "UniversalDeRu/UniversalDeRu.dsl.dz", coverage=True),
    Source("langenscheidt", "general", "dsl",
           "De-Ru-Langenscheidts_Grosswoerterbuch/De-Ru-Langenscheidts_Grosswoerterbuch.dsl.dz",
           coverage=True),
    Source("lein", "general", "dsl", "deu-rus_Lein_and_1_1/deu-rus_Lein_and_1_1.dsl", coverage=True),
    Source("allgemein", "general", "dsl",
           "Общелексический немецко-русский словарь/deu-rus_Allgemeinwoerterbuch_as_1_0.dsl",
           coverage=True),
    # --- enrichment only (does NOT define coverage) ---
    # Advanced is form-rich (179k lemmas + 408k inflected forms): great for extra
    # translations + a form->lemma map, but must not mint inflected-form "lemmas".
    Source("advanced", "general", "stardict",
           "Advanced German Russian/Advanced German Russian.ifo"),
    Source("duden_syn", "synonyms", "dsl",
           "DUDEN_Synonymwörterbuch_2020_(Deu-Deu)/Duden-Synonim 2020.dsl", contents_lang="de"),
    Source("collocations", "collocations", "dsl",
           "deu-rus_Woerterbindungen_Adjektiven_Partizipien_as_1_1/"
           "deu-rus_Woerterbindungen_Adjektiven_Partizipien_as_1_1.dsl"),
    Source("idioms", "idioms", "mdx",
           "Idioms (De-Ru) (MDX)/De-Ru_Idioms_Lingvo_x3.mdx"),
]

DSL_SOURCES = [s for s in SOURCES if s.fmt == "dsl"]

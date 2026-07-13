"""Unified reader over all source formats.

Yields (lemma_key, contribution) pairs for a Source, where `contribution` is a
partial record fragment. DSL is handled by the dependency-free `dsl` module;
StarDict/MDX go through pyglossary (HTML glosses are stripped here).

Roles:
  general      -> translations, examples, article, forms, pos   (defines coverage)
  synonyms     -> synonyms (de)          (Duden, keyed by lemma)
  collocations -> collocations           (keyed by the head noun of the phrase)
  idioms       -> idioms                 (MDX, keyed by lemma keyword)
"""
from __future__ import annotations

import html
import re
from typing import Iterator

from app.vocab import dsl
from app.vocab.sources import Source

# NOTE: do not touch logging.getLogger("pyglossary") before pyglossary is
# imported — pyglossary installs a custom Logger subclass (with .isDebug) at
# import time, and pre-creating the named logger poisons it with a plain one.

_HTML_TAG = re.compile(r"<[^>]+>")
_WORD = re.compile(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß\-]+")


def strip_html(s: str) -> str:
    s = s.replace("●", "\n").replace("◆", " ").replace("&emsp;", " ")
    s = _HTML_TAG.sub(" ", s)
    s = html.unescape(s)
    return re.sub(r"[ \t]+", " ", s)


def _senses(defi: str) -> tuple[list[str], list[str]]:
    trans, examples = [], []
    for line in strip_html(defi).split("\n"):
        line = line.strip(" ;")
        if not line or len(line) < 2:
            continue
        # a line carrying a German→Russian dash is an example, else a gloss
        if "—" in line or " - " in line:
            examples.append(line[:200])
        else:
            trans.append(line[:200])
    return trans[:15], examples[:10]


def _last_token(phrase: str) -> str | None:
    toks = _WORD.findall(phrase)
    return toks[-1] if toks else None


def iter_source(source: Source) -> Iterator[tuple[str, dict]]:
    if not source.path.exists():
        return
    if source.fmt == "dsl":
        yield from _iter_dsl(source)
    else:
        yield from _iter_pyglossary(source)


def _iter_dsl(source: Source) -> Iterator[tuple[str, dict]]:
    for entry in dsl.iter_entries(source.path):
        head = entry.headwords[0]
        if source.role == "general":
            p = dsl.parse_entry(entry)
            yield head, {
                "translations": p.translations[:15],
                "examples": p.examples[:10],
                "article": p.article,
                "forms": p.forms,
                "pos": p.pos,
            }
        elif source.role == "synonyms":
            syn = [dsl.strip_markup(l).lstrip("•* ")
                   for l in entry.body_lines if "•" in l]
            if syn:
                yield head, {"synonyms": syn[:15]}
        elif source.role == "collocations":
            key = _last_token(head)
            if key:
                meaning = " ".join(dsl.strip_markup(l) for l in entry.body_lines)
                yield key, {"collocations": [f"{head} — {meaning}"[:200]]}


def _iter_pyglossary(source: Source) -> Iterator[tuple[str, dict]]:
    import logging
    from pyglossary import Glossary
    Glossary.init()
    logging.getLogger("pyglossary").setLevel(logging.ERROR)
    glos = Glossary()
    # StarDict streams fine in direct mode; MDX must be read non-direct
    glos.read(str(source.path), direct=(source.fmt == "stardict"))
    for e in glos:
        words = e.l_word if isinstance(e.l_word, (list, tuple)) else [e.s_word]
        if source.role == "general":
            trans, ex = _senses(e.defi)
            if trans or ex:
                for w in words:
                    yield w, {"translations": trans, "examples": ex}
        elif source.role == "idioms":
            ids = re.findall(r"bword://([^\"]+)", e.defi)
            if not ids:
                flat = strip_html(e.defi).strip()
                ids = [flat[:150]] if flat else []
            if ids:
                for w in words:
                    yield w, {"idioms": ids[:12]}

"""Dependency-free ABBYY Lingvo DSL reader.

Handles UTF-16LE / UTF-8-BOM encodings and dictzip (`.dsl.dz`, gzip-compatible)
compression. Yields raw entries and offers a light structured extraction so we
can inspect exactly what the deterministic parse pulls from each dictionary
*before* anything is sent to an LLM.

This is stage [1]+[2] of the vocab pipeline for DSL sources only. StarDict/MDX
sources (Advanced German Russian, Idioms) are added later via pyglossary.
"""
from __future__ import annotations

import gzip
import io
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


# --- low-level: open a .dsl / .dsl.dz as decoded text lines ------------------

def _read_bytes(path: Path) -> bytes:
    if path.suffix == ".dz":
        with gzip.open(path, "rb") as fh:
            return fh.read()
    return path.read_bytes()


def _decode(raw: bytes) -> str:
    if raw[:2] == b"\xff\xfe":
        return raw.decode("utf-16-le")
    if raw[:2] == b"\xfe\xff":
        return raw.decode("utf-16-be")
    if raw[:3] == b"\xef\xbb\xbf":
        return raw[3:].decode("utf-8")
    # ABBYY DSL default is UTF-16LE
    try:
        return raw.decode("utf-16-le")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace")


def read_lines(path: Path) -> list[str]:
    text = _decode(_read_bytes(path))
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


# --- entry iteration ---------------------------------------------------------

@dataclass
class RawEntry:
    headwords: list[str]      # one card can head several spellings
    body_lines: list[str]     # raw DSL markup, tab-indent already stripped

    @property
    def body(self) -> str:
        return "\n".join(self.body_lines)


def iter_entries(path: Path) -> Iterator[RawEntry]:
    """Yield (headwords, body) cards. Header lines (`#...`) and blanks skipped."""
    heads: list[str] = []
    body: list[str] = []
    for line in read_lines(path):
        if not line:
            continue
        if line.startswith("#"):
            continue
        if line[0] in (" ", "\t"):
            body.append(line.lstrip("\t "))
        else:
            # a new headword line: flush the previous card if it had a body
            if heads and body:
                yield RawEntry(heads, body)
                heads, body = [], []
            heads.append(line.strip())
    if heads and body:
        yield RawEntry(heads, body)


def collect(path: Path, targets: set[str]) -> dict[str, RawEntry]:
    """Stream `path`, keep only cards whose headword is in `targets`."""
    found: dict[str, RawEntry] = {}
    for entry in iter_entries(path):
        for hw in entry.headwords:
            if hw in targets and hw not in found:
                found[hw] = entry
    return found


# --- markup handling ---------------------------------------------------------

_TAG = re.compile(r"\[/?[^\]]*\]")


def strip_markup(s: str) -> str:
    s = _TAG.sub("", s)
    s = s.replace("\\[", "[").replace("\\]", "]").replace("\\\\", "\\")
    s = s.replace("<<", "").replace(">>", "")
    return re.sub(r"[ \t]+", " ", s).strip()


# --- light structured extraction (naive, pre-LLM) ----------------------------

_GENDER = {"m": "der", "f": "die", "n": "das"}
_POS_HINTS = ["vt", "vi", "vr", "adv", "adj", "prp", "prä", "konj", "pron", "num", "part"]


@dataclass
class Parsed:
    headword: str
    article: str | None = None          # der/die/das
    pos: list[str] = field(default_factory=list)
    forms: list[str] = field(default_factory=list)   # genitive/plural hints like "-es,-¨er"
    translations: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)  # idioms / phrase lines (• or [m3])


_GRAM_ONLY = re.compile(r"^[nmf]\b[\s\-]|^-[a-zäöüß]*\s*,")   # "n -es, Häuser", "-s, -"
_FORMS = re.compile(r"\b[mfn]\b\s*(-[^\s;,]+(?:\s*,\s*[^\s;.]+)?)")


def _is_noise(clean: str) -> bool:
    return clean.endswith(".wav") or bool(_GRAM_ONLY.match(clean))


def parse_entry(entry: RawEntry) -> Parsed:
    """Naive, pre-LLM extraction. Gender/POS/forms are read only from the main
    definition lines (not example sub-lines) to avoid false positives."""
    p = Parsed(headword=entry.headwords[0])
    for raw in entry.body_lines:
        clean = strip_markup(raw)
        if not clean:
            continue
        is_example = "•" in raw or "[m2]" in raw or "[m3]" in raw
        if is_example:
            p.examples.append(clean.lstrip("•* "))
            continue
        # --- main line: mine grammar here, never from examples ---
        gram = re.search(r"\b([mfn])\b", clean)
        if gram and p.article is None:
            p.article = _GENDER.get(gram.group(1))
            fm = _FORMS.search(clean)
            if fm and fm.group(1).strip(" ,") not in p.forms:
                p.forms.append(fm.group(1).strip(" ,"))
        for hint in _POS_HINTS:
            if re.search(rf"\b{hint}\b", clean) and hint not in p.pos:
                p.pos.append(hint)
        if not _is_noise(clean):
            p.translations.append(clean)
    return p

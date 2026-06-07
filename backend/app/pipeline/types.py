from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class SourceItem:
    url: str
    title: str
    source_type: str = "article"  # essay | article | academic


@dataclass
class WordCandidate:
    word: str
    pos: str = "Other"
    article: str | None = None
    examples: list[str] = field(default_factory=list)
    source_url: str = ""


@dataclass
class EnrichedWord:
    de: str
    article: str | None
    pos: str
    level: str | None
    ru: str
    rektion: str
    ready_phrase: str
    declension: dict
    examples_generated: list[str]


@dataclass
class PipelineError:
    stage: Literal["fetch", "extract", "wiktionary", "mistral", "db"]
    item: str
    error: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "item": self.item,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }

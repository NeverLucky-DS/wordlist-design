from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class EssayCreate(BaseModel):
    title: str = ""
    text: str = ""
    essay_type: str = "argumentativ"
    topic: str = ""
    level: str = "B1"


class EssayUpdate(BaseModel):
    title: str | None = None
    text: str | None = None
    essay_type: str | None = None
    topic: str | None = None
    level: str | None = None


class EssayOut(BaseModel):
    id: int
    title: str
    text: str
    essay_type: str
    topic: str
    level: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EssayListItemOut(BaseModel):
    id: int
    title: str
    text: str
    essay_type: str
    topic: str
    level: str
    created_at: datetime
    updated_at: datetime
    grade: str | None = None
    overall_score: int | None = None
    last_analyzed_at: datetime | None = None


class EssayAnalysisErrorOut(BaseModel):
    part: str = ""
    excerpt: str = ""
    start: int
    end: int
    type: str
    severity: str
    annotation_kind: str = ""
    explanation_ru: str
    correction: str
    rule: str
    what_wrong_ru: str = ""
    why_bad_ru: str = ""
    how_to_fix_ru: str = ""
    b1_variant_de: str = ""
    b2_variant_de: str = ""
    b1_explain_ru: str = ""
    b2_explain_ru: str = ""
    study_phrases_de: list[str] = Field(default_factory=list)


class EssayPartReportOut(BaseModel):
    part: str
    label: str
    score: int
    feedback_ru: str
    errors_count: int
    is_empty: bool = False


class EssayFinalSummaryOut(BaseModel):
    structure_feedback_ru: str
    topic_feedback_ru: str
    strengths_ru: list[str] = Field(default_factory=list)
    next_steps_ru: list[str] = Field(default_factory=list)
    overall_comment_ru: str = ""


class EssayAnalysisOut(BaseModel):
    essay_id: int
    overall_score: int
    grade: str
    errors: list[EssayAnalysisErrorOut]
    part_reports: list[EssayPartReportOut] = Field(default_factory=list)
    final_summary: EssayFinalSummaryOut | None = None
    model: str


class EssayAnalysisRecordOut(EssayAnalysisOut):
    created_at: datetime | None = None
    text_snapshot: str = ""
    is_stale: bool = False


class WordOut(BaseModel):
    id: int
    german: str
    article: str | None
    word_type: str
    translation_ru: str
    level: str
    grammar_data: dict | None
    examples: list
    source: str
    topics: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class PhraseOut(BaseModel):
    id: int
    text_de: str
    translation_ru: str
    essay_part: str
    topic: str | None = None
    level: str
    known: bool = False


class TopicSummaryOut(BaseModel):
    slug: str
    title_de: str
    title_ru: str = ""
    level_default: str = "B1"


class TopicOut(BaseModel):
    slug: str
    title_de: str
    title_ru: str = ""
    level_default: str = "B1"
    essay_type_hints: list[str] = Field(default_factory=list)
    notes_ru: str = ""
    word_count: int = 0
    level_counts: dict[str, int] = Field(default_factory=dict)
    phrase_count: int = 0


class PhraseKnownUpdate(BaseModel):
    known: bool


class TrainingQueueItemOut(BaseModel):
    word_id: int
    german: str
    article: str | None
    translation_ru: str
    level: str
    score: int


class TrainingResultIn(BaseModel):
    word_id: int
    user_answer: str
    response_ms: int = 5000


class TrainingResultOut(BaseModel):
    word_id: int
    expected: str
    is_correct: bool
    new_score: int
    delta: int


class ScoreTrendPointOut(BaseModel):
    essay_id: int
    title: str
    score: int
    grade: str
    analyzed_at: datetime


class RecentEssayOut(BaseModel):
    id: int
    title: str
    grade: str | None = None
    overall_score: int | None = None
    updated_at: datetime


class DashboardOut(BaseModel):
    streak_current: int
    streak_last_date: date | None = None
    words_learned: int
    last_grade: str | None = None
    last_score: int | None = None
    last_essay_title: str | None = None
    last_analyzed_at: datetime | None = None
    score_trend: list[ScoreTrendPointOut] = Field(default_factory=list)
    recent_essays: list[RecentEssayOut] = Field(default_factory=list)

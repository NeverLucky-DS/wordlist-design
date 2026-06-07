from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Essay(Base):
    __tablename__ = "essays"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    text: Mapped[str] = mapped_column(Text, default="")
    essay_type: Mapped[str] = mapped_column(String(64), default="argumentativ")
    topic: Mapped[str] = mapped_column(String(128), default="")
    level: Mapped[str] = mapped_column(String(8), default="B1")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    analyses: Mapped[list["EssayAnalysis"]] = relationship(back_populates="essay")


class EssayAnalysis(Base):
    __tablename__ = "essay_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    essay_id: Mapped[int] = mapped_column(ForeignKey("essays.id", ondelete="CASCADE"))
    errors_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade: Mapped[str | None] = mapped_column(String(4), nullable=True)
    text_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    part_reports_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    final_summary_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    essay: Mapped["Essay"] = relationship(back_populates="analyses")


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True)
    german: Mapped[str] = mapped_column(String(255))
    article: Mapped[str | None] = mapped_column(String(16), nullable=True)
    word_type: Mapped[str] = mapped_column(String(32))
    translation_ru: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(8), default="B1")
    grammar_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    examples: Mapped[list] = mapped_column(JSONB, default=list)
    source: Mapped[str] = mapped_column(String(128), default="seed_csv")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    topics: Mapped[list["WordTopic"]] = relationship(back_populates="word")


class WordTopic(Base):
    __tablename__ = "word_topics"
    __table_args__ = (UniqueConstraint("word_id", "topic", name="uq_word_topic"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"))
    topic: Mapped[str] = mapped_column(String(64))

    word: Mapped["Word"] = relationship(back_populates="topics")


class UserWordProgress(Base):
    __tablename__ = "user_word_progress"
    __table_args__ = (UniqueConstraint("user_id", "word_id", name="uq_user_word"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"))
    score: Mapped[int] = mapped_column(Integer, default=0)
    last_seen: Mapped[datetime | None] = mapped_column(nullable=True)
    times_correct: Mapped[int] = mapped_column(Integer, default=0)
    times_wrong: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Phrase(Base):
    __tablename__ = "phrases"

    id: Mapped[int] = mapped_column(primary_key=True)
    text_de: Mapped[str] = mapped_column(Text)
    translation_ru: Mapped[str] = mapped_column(Text, default="")
    essay_part: Mapped[str] = mapped_column(String(64), default="")
    topic: Mapped[str | None] = mapped_column(String(64), nullable=True)
    level: Mapped[str] = mapped_column(String(8), default="B1")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class UserPhraseKnown(Base):
    __tablename__ = "user_phrase_known"
    __table_args__ = (UniqueConstraint("user_id", "phrase_id", name="uq_user_phrase"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1)
    phrase_id: Mapped[int] = mapped_column(ForeignKey("phrases.id", ondelete="CASCADE"))
    known: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class UserStats(Base):
    __tablename__ = "user_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, default=1)
    streak_current: Mapped[int] = mapped_column(Integer, default=0)
    streak_last_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_words_learned: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

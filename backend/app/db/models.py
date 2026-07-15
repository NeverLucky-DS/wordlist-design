from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    # Per-user Mistral API key, encrypted at rest (Fernet). NULL = not attached.
    # Used by the server-side vocab enrichment worker; never returned to clients.
    mistral_key_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    sessions: Mapped[list["AuthSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    essays: Mapped[list["Essay"]] = relationship(
        back_populates="user", passive_deletes=True
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="sessions")


class GuestSession(Base):
    __tablename__ = "guest_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    essays: Mapped[list["Essay"]] = relationship(
        back_populates="guest_session", passive_deletes=True
    )


class Essay(Base):
    __tablename__ = "essays"
    __table_args__ = (
        CheckConstraint(
            "(user_id IS NOT NULL AND guest_session_id IS NULL) OR "
            "(user_id IS NULL AND guest_session_id IS NOT NULL)",
            name="ck_essay_exactly_one_owner",
        ),
        Index("ix_essays_user_updated", "user_id", "updated_at"),
        Index("ix_essays_guest_updated", "guest_session_id", "updated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    guest_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), default="")
    text: Mapped[str] = mapped_column(Text, default="")
    content_json: Mapped[dict] = mapped_column(JSON_TYPE, default=dict)
    essay_type: Mapped[str] = mapped_column(String(64), default="argumentativ")
    topic: Mapped[str] = mapped_column(String(128), default="")
    level: Mapped[str] = mapped_column(String(8), default="B1")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[Optional["User"]] = relationship(back_populates="essays")
    guest_session: Mapped[Optional["GuestSession"]] = relationship(
        back_populates="essays"
    )
    versions: Mapped[list["EssayVersion"]] = relationship(
        back_populates="essay", cascade="all, delete-orphan"
    )
    analyses: Mapped[list["EssayAnalysis"]] = relationship(
        back_populates="essay", cascade="all, delete-orphan"
    )


class EssayVersion(Base):
    __tablename__ = "essay_versions"
    __table_args__ = (Index("ix_essay_versions_essay_created", "essay_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    essay_id: Mapped[int] = mapped_column(ForeignKey("essays.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), default="")
    text: Mapped[str] = mapped_column(Text, default="")
    content_json: Mapped[dict] = mapped_column(JSON_TYPE, default=dict)
    reason: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    essay: Mapped["Essay"] = relationship(back_populates="versions")
    analyses: Mapped[list["EssayAnalysis"]] = relationship(back_populates="version")


class EssayAnalysis(Base):
    __tablename__ = "essay_analyses"
    __table_args__ = (
        Index("ix_essay_analyses_essay_created", "essay_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    essay_id: Mapped[int] = mapped_column(ForeignKey("essays.id", ondelete="CASCADE"))
    version_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("essay_versions.id", ondelete="CASCADE"), nullable=True
    )
    scope: Mapped[str] = mapped_column(String(16), default="full")
    part: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    progress_step: Mapped[str] = mapped_column(String(32), default="queued")
    cancellation_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    errors_json: Mapped[dict] = mapped_column(JSON_TYPE, default=dict)
    warnings_json: Mapped[list] = mapped_column(JSON_TYPE, default=list)
    overall_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    text_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    part_reports_json: Mapped[dict] = mapped_column(JSON_TYPE, default=dict)
    final_summary_json: Mapped[dict] = mapped_column(JSON_TYPE, default=dict)
    model: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    schema_version: Mapped[int] = mapped_column(Integer, default=1)
    prompt_version: Mapped[str] = mapped_column(String(32), default="2026-07-13")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    essay: Mapped["Essay"] = relationship(back_populates="analyses")
    version: Mapped[Optional["EssayVersion"]] = relationship(back_populates="analyses")


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True)
    german: Mapped[str] = mapped_column(String(255))
    article: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    word_type: Mapped[str] = mapped_column(String(32))
    translation_ru: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(8), default="B1")
    grammar_data: Mapped[Optional[dict]] = mapped_column(JSON_TYPE, nullable=True)
    examples: Mapped[list] = mapped_column(JSON_TYPE, default=list)
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
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"))
    score: Mapped[int] = mapped_column(Integer, default=0)
    last_seen: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    times_correct: Mapped[int] = mapped_column(Integer, default=0)
    times_wrong: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Phrase(Base):
    __tablename__ = "phrases"

    id: Mapped[int] = mapped_column(primary_key=True)
    text_de: Mapped[str] = mapped_column(Text)
    translation_ru: Mapped[str] = mapped_column(Text, default="")
    essay_part: Mapped[str] = mapped_column(String(64), default="")
    topic: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    level: Mapped[str] = mapped_column(String(8), default="B1")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class UserPhraseKnown(Base):
    __tablename__ = "user_phrase_known"
    __table_args__ = (UniqueConstraint("user_id", "phrase_id", name="uq_user_phrase"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    phrase_id: Mapped[int] = mapped_column(ForeignKey("phrases.id", ondelete="CASCADE"))
    known: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class UserStats(Base):
    __tablename__ = "user_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    streak_current: Mapped[int] = mapped_column(Integer, default=0)
    streak_last_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    total_words_learned: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


# ── Wörterbuch: dictionary mirror + personal word list ───────────────────────
# The enrichment worker owns `enrichment.db` (SQLite) and keeps writing to it.
# These tables are a read-optimized replica in Postgres, so that fuzzy search
# (pg_trgm) and the per-user word list live in ONE database and can be joined.
# `app.vocab.mirror` syncs them incrementally; nothing here writes back.


class VocabCard(Base):
    __tablename__ = "vocab_cards"
    __table_args__ = (Index("ix_vocab_cards_band", "band"),)

    lemma: Mapped[str] = mapped_column(String(128), primary_key=True)
    # Two search keys, both case-folded: `lemma_norm` substitutes umlauts the
    # correct way (grün→gruen), `lemma_ascii` flattens them (grün→grun). People
    # type both on an umlaut-less keyboard and neither form finds the other, so
    # search scores against whichever matches better. GIN trigram indexes are
    # added on both by the migration (they cannot live in the model: SQLite,
    # which the test suite builds with create_all, has no GIN).
    lemma_norm: Mapped[str] = mapped_column(String(160))
    lemma_ascii: Mapped[str] = mapped_column(String(160))
    level: Mapped[str] = mapped_column(String(16), default="unlisted")
    # Display band, clamped to the B1–C1 brush set (see LEVEL_BAND).
    band: Mapped[str] = mapped_column(String(4), default="C1")
    topic: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    pos: Mapped[str] = mapped_column(String(16), default="other")
    article: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    ru: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[str] = mapped_column(String(8), default="high")
    register: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    data: Mapped[dict] = mapped_column(JSON_TYPE, default=dict)
    # `cards.created_at` from SQLite — the incremental sync watermark.
    source_created_at: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    synced_at: Mapped[datetime] = mapped_column(server_default=func.now())

    translations: Mapped[list["VocabCardTranslation"]] = relationship(
        back_populates="card", cascade="all, delete-orphan", passive_deletes=True
    )


class VocabCardTranslation(Base):
    """One row per Russian meaning (`ru_all`), so RU→DE search can be indexed.

    Kept separate instead of a joined string: trigram similarity against one
    long concatenation scores badly, against a single meaning it scores well.
    """

    __tablename__ = "vocab_card_translations"
    __table_args__ = (
        UniqueConstraint("lemma", "idx", name="uq_vocab_card_translation"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    lemma: Mapped[str] = mapped_column(
        ForeignKey("vocab_cards.lemma", ondelete="CASCADE"), index=True
    )
    idx: Mapped[int] = mapped_column(Integer, default=0)  # 0 = primary meaning
    ru: Mapped[str] = mapped_column(String(255))
    ru_norm: Mapped[str] = mapped_column(String(255))  # GIN trigram index in migration

    card: Mapped["VocabCard"] = relationship(back_populates="translations")


class UserWordList(Base):
    """A word the user put on their learning list.

    Keyed by `lemma` as plain text on purpose — no FK to `vocab_cards`:
      • the enrichment prompt already separates homographs by case
        (Morgen/morgen, Essen/essen), so a lemma is unambiguous on its own;
      • the future browser extension adds words straight off arbitrary pages,
        which may not be in our dictionary (yet).
    The snapshot columns let the list render in one query without touching
    `vocab_cards`; they are refreshed on add and may lag a re-enrichment.
    """

    __tablename__ = "user_word_list"
    __table_args__ = (
        UniqueConstraint("user_id", "lemma", name="uq_user_word_list"),
        Index("ix_user_word_list_user_added", "user_id", "added_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    lemma: Mapped[str] = mapped_column(String(128))
    ru: Mapped[str] = mapped_column(Text, default="")
    level: Mapped[str] = mapped_column(String(16), default="unlisted")
    band: Mapped[str] = mapped_column(String(4), default="C1")
    pos: Mapped[str] = mapped_column(String(16), default="other")
    article: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    topic: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="learning")
    added_at: Mapped[datetime] = mapped_column(server_default=func.now())

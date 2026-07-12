"""accounts, essay versions, and background analysis runs

Revision ID: a91c2e4d7b30
Revises: 678b5be647b5
Create Date: 2026-07-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a91c2e4d7b30"
down_revision: Union[str, Sequence[str], None] = "678b5be647b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "guest_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_guest_sessions_token_hash", "guest_sessions", ["token_hash"], unique=True)

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_auth_sessions_token_hash", "auth_sessions", ["token_hash"], unique=True)

    # Existing rows are prototype data owned by the old implicit user 1.
    op.execute("DELETE FROM essay_analyses")
    op.execute("DELETE FROM essays")
    op.execute("DELETE FROM user_word_progress")
    op.execute("DELETE FROM user_phrase_known")
    op.execute("DELETE FROM user_stats")

    op.add_column("essays", sa.Column("user_id", sa.Integer(), nullable=True))
    op.add_column("essays", sa.Column("guest_session_id", sa.Integer(), nullable=True))
    op.add_column(
        "essays",
        sa.Column(
            "content_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.create_foreign_key("fk_essays_user", "essays", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key(
        "fk_essays_guest",
        "essays",
        "guest_sessions",
        ["guest_session_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "ck_essay_exactly_one_owner",
        "essays",
        "(user_id IS NOT NULL AND guest_session_id IS NULL) OR "
        "(user_id IS NULL AND guest_session_id IS NOT NULL)",
    )
    op.create_index("ix_essays_user_updated", "essays", ["user_id", "updated_at"])
    op.create_index("ix_essays_guest_updated", "essays", ["guest_session_id", "updated_at"])

    op.create_table(
        "essay_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("essay_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("content_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reason", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["essay_id"], ["essays.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_essay_versions_essay_created",
        "essay_versions",
        ["essay_id", "created_at"],
    )

    op.add_column("essay_analyses", sa.Column("version_id", sa.Integer(), nullable=True))
    op.add_column("essay_analyses", sa.Column("scope", sa.String(length=16), server_default="full", nullable=False))
    op.add_column("essay_analyses", sa.Column("part", sa.String(length=32), nullable=True))
    op.add_column("essay_analyses", sa.Column("status", sa.String(length=32), server_default="queued", nullable=False))
    op.add_column("essay_analyses", sa.Column("progress_step", sa.String(length=32), server_default="queued", nullable=False))
    op.add_column("essay_analyses", sa.Column("cancellation_requested", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column(
        "essay_analyses",
        sa.Column(
            "warnings_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column("essay_analyses", sa.Column("schema_version", sa.Integer(), server_default="1", nullable=False))
    op.add_column("essay_analyses", sa.Column("prompt_version", sa.String(length=32), server_default="2026-07-13", nullable=False))
    op.add_column("essay_analyses", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("essay_analyses", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.add_column("essay_analyses", sa.Column("finished_at", sa.DateTime(), nullable=True))
    op.create_foreign_key(
        "fk_essay_analyses_version",
        "essay_analyses",
        "essay_versions",
        ["version_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_essay_analyses_essay_created",
        "essay_analyses",
        ["essay_id", "created_at"],
    )

    op.create_foreign_key(
        "fk_user_word_progress_user",
        "user_word_progress",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_user_phrase_known_user",
        "user_phrase_known",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_user_stats_user",
        "user_stats",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_user_stats_user", "user_stats", type_="foreignkey")
    op.drop_constraint("fk_user_phrase_known_user", "user_phrase_known", type_="foreignkey")
    op.drop_constraint("fk_user_word_progress_user", "user_word_progress", type_="foreignkey")
    op.drop_index("ix_essay_analyses_essay_created", table_name="essay_analyses")
    op.drop_constraint("fk_essay_analyses_version", "essay_analyses", type_="foreignkey")
    for column in (
        "finished_at",
        "started_at",
        "error_message",
        "prompt_version",
        "schema_version",
        "warnings_json",
        "cancellation_requested",
        "progress_step",
        "status",
        "part",
        "scope",
        "version_id",
    ):
        op.drop_column("essay_analyses", column)
    op.drop_index("ix_essay_versions_essay_created", table_name="essay_versions")
    op.drop_table("essay_versions")
    op.drop_index("ix_essays_guest_updated", table_name="essays")
    op.drop_index("ix_essays_user_updated", table_name="essays")
    op.drop_constraint("ck_essay_exactly_one_owner", "essays", type_="check")
    op.drop_constraint("fk_essays_guest", "essays", type_="foreignkey")
    op.drop_constraint("fk_essays_user", "essays", type_="foreignkey")
    op.drop_column("essays", "content_json")
    op.drop_column("essays", "guest_session_id")
    op.drop_column("essays", "user_id")
    op.drop_index("ix_auth_sessions_token_hash", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_index("ix_guest_sessions_token_hash", table_name="guest_sessions")
    op.drop_table("guest_sessions")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

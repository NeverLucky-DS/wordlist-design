"""drop legacy topic enrichment pipeline tables

Revision ID: b3f8c1d2e4a5
Revises: a91c2e4d7b30
Create Date: 2026-07-13
"""

from typing import Sequence, Union

from alembic import op

revision: str = "b3f8c1d2e4a5"
down_revision: Union[str, Sequence[str], None] = "a91c2e4d7b30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("word_failures")
    op.drop_table("topic_queue")
    op.drop_table("pipeline_runs")


def downgrade() -> None:
    import sqlalchemy as sa
    from sqlalchemy.dialects import postgresql

    json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")

    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("words_added", sa.Integer(), nullable=False),
        sa.Column("words_linked", sa.Integer(), nullable=False),
        sa.Column("phrases_added", sa.Integer(), nullable=False),
        sa.Column("target_words", sa.Integer(), nullable=False),
        sa.Column("errors_json", json_type, nullable=False),
        sa.Column("started_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "word_failures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("word", sa.String(length=255), nullable=False),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("pos", sa.String(length=32), nullable=False),
        sa.Column("article", sa.String(length=16), nullable=True),
        sa.Column("examples", json_type, nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("error", sa.Text(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("word", "topic", name="uq_failure_word_topic"),
    )
    op.create_table(
        "topic_queue",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("target_words", sa.Integer(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_run_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("topic", name="uq_topic_queue_topic"),
    )

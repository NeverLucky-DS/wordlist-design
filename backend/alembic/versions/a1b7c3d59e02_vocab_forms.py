"""vocab_forms — inflected form -> headword index

Closes the hole measured on 2026-07-26: `ist` (zipf 7.08) answered `Ist-Wert`,
`mich` answered `Michelin-Männchen`, `bin` answered `Bingo`, `gibt` answered
nothing. Those forms have no card by design, so search had nothing exact to
match and pg_trgm filled the silence.

The table is derived — `mirror.rebuild_forms()` regenerates it from
`vocab_cards.morphology` and the closed-class tables in `vocab/inflect.py`, so
downgrade loses nothing that a rebuild cannot restore.

Revision ID: a1b7c3d59e02
Revises: f2a80d6c9e13
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b7c3d59e02"
down_revision: Union[str, Sequence[str], None] = "f2a80d6c9e13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vocab_forms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("form", sa.String(length=128), nullable=False),
        sa.Column("form_norm", sa.String(length=160), nullable=False),
        sa.Column("base_lemma", sa.String(length=128), nullable=False),
        sa.Column("cell_de", sa.String(length=96), nullable=False, server_default=""),
        sa.Column("cell_ru", sa.String(length=96), nullable=False, server_default=""),
        sa.Column("ru", sa.Text(), nullable=False, server_default=""),
        sa.Column("pos", sa.String(length=16), nullable=False, server_default="other"),
        sa.Column("source", sa.String(length=16), nullable=False,
                  server_default="paradigm"),
        sa.ForeignKeyConstraint(["base_lemma"], ["vocab_cards.lemma"],
                                ondelete="CASCADE"),
        sa.UniqueConstraint("form", "base_lemma", name="uq_vocab_form"),
    )
    # Lookup is always an equality on the folded form — a plain btree, not the
    # GIN trigram index the lemma columns carry. Fuzziness is the fallback this
    # table exists to pre-empt, so it must not be fuzzy itself.
    op.create_index("ix_vocab_forms_norm", "vocab_forms", ["form_norm"])


def downgrade() -> None:
    op.drop_index("ix_vocab_forms_norm", table_name="vocab_forms")
    op.drop_table("vocab_forms")

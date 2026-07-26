"""vocab_cards.level_est — our estimated CEFR level

`goethe.py` answers `unlisted` for 88 067 of 92 090 cards, because Goethe
publishes A1–B1 only and no official B2/C1 list exists. This column carries an
estimate for that tail, measured against 420 held-out cards that do carry a
published level: 38 % exact, 91 % within one step, 91 % on the "core vocabulary
or beyond" boundary (see vocab/levels.py for the full figures and what they
license).

Stored apart from `level` rather than filling it in, because the two are
different kinds of claim and the UI has to be able to dress them differently.
`band` — the brush key — is deliberately NOT recomputed from it.

Revision ID: b8e2f47a1c93
Revises: a1b7c3d59e02
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "b8e2f47a1c93"
down_revision: Union[str, Sequence[str], None] = "a1b7c3d59e02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("vocab_cards", sa.Column("level_est", sa.String(length=4),
                                           nullable=True))


def downgrade() -> None:
    op.drop_column("vocab_cards", "level_est")

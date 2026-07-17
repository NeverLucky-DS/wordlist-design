"""add encrypted per-user Mistral key column

Revision ID: c5a71e9f2d84
Revises: b3f8c1d2e4a5
Create Date: 2026-07-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c5a71e9f2d84"
down_revision: Union[str, Sequence[str], None] = "b3f8c1d2e4a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("mistral_key_enc", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "mistral_key_enc")

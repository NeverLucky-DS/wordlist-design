"""woerterbuch mirror and word list

Revision ID: 88b9d9797836
Revises: c5a71e9f2d84
Create Date: 2026-07-15 02:41:58.752451

Strictly additive: new tables, the pg_trgm extension and its indexes. Autogenerate
additionally proposed dropping the unique constraints on `users.email`,
`auth_sessions.token_hash` and `guest_sessions.token_hash` — that is pre-existing
drift (the models declare `unique=True, index=True`, which renders as a unique
index, while the live database carries an equivalent unique *constraint* created
by an old `create_all`). Both enforce the same thing, so the drift is harmless;
dropping them would silently remove uniqueness from logins and session tokens.
Deliberately left out — that decision belongs in its own migration, not here.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '88b9d9797836'
down_revision: Union[str, Sequence[str], None] = 'c5a71e9f2d84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Fuzzy search lives or dies by this: trigram similarity is what lets
    # "зависимости" find "зависимость" and "fortschrit" find "Fortschritt".
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        'vocab_cards',
        sa.Column('lemma', sa.String(length=128), nullable=False),
        sa.Column('lemma_norm', sa.String(length=160), nullable=False),
        sa.Column('lemma_ascii', sa.String(length=160), nullable=False),
        sa.Column('level', sa.String(length=16), nullable=False),
        sa.Column('band', sa.String(length=4), nullable=False),
        sa.Column('topic', sa.String(length=64), nullable=True),
        sa.Column('pos', sa.String(length=16), nullable=False),
        sa.Column('article', sa.String(length=8), nullable=True),
        sa.Column('ru', sa.Text(), nullable=False),
        sa.Column('confidence', sa.String(length=8), nullable=False),
        sa.Column('register', sa.String(length=32), nullable=True),
        sa.Column('data', sa.JSON().with_variant(
            postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
        sa.Column('source_created_at', sa.Float(), nullable=False),
        sa.Column('synced_at', sa.DateTime(), server_default=sa.text('now()'),
                  nullable=False),
        sa.PrimaryKeyConstraint('lemma'),
    )
    op.create_index('ix_vocab_cards_band', 'vocab_cards', ['band'], unique=False)
    op.create_index(op.f('ix_vocab_cards_source_created_at'), 'vocab_cards',
                    ['source_created_at'], unique=False)
    op.create_index(
        'ix_vocab_cards_lemma_trgm', 'vocab_cards', ['lemma_norm'],
        postgresql_using='gin', postgresql_ops={'lemma_norm': 'gin_trgm_ops'},
    )
    op.create_index(
        'ix_vocab_cards_lemma_ascii_trgm', 'vocab_cards', ['lemma_ascii'],
        postgresql_using='gin', postgresql_ops={'lemma_ascii': 'gin_trgm_ops'},
    )

    op.create_table(
        'vocab_card_translations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lemma', sa.String(length=128), nullable=False),
        sa.Column('idx', sa.Integer(), nullable=False),
        sa.Column('ru', sa.String(length=255), nullable=False),
        sa.Column('ru_norm', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['lemma'], ['vocab_cards.lemma'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lemma', 'idx', name='uq_vocab_card_translation'),
    )
    op.create_index(op.f('ix_vocab_card_translations_lemma'),
                    'vocab_card_translations', ['lemma'], unique=False)
    op.create_index(
        'ix_vocab_card_translations_ru_trgm', 'vocab_card_translations', ['ru_norm'],
        postgresql_using='gin', postgresql_ops={'ru_norm': 'gin_trgm_ops'},
    )

    op.create_table(
        'user_word_list',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lemma', sa.String(length=128), nullable=False),
        sa.Column('ru', sa.Text(), nullable=False),
        sa.Column('level', sa.String(length=16), nullable=False),
        sa.Column('band', sa.String(length=4), nullable=False),
        sa.Column('pos', sa.String(length=16), nullable=False),
        sa.Column('article', sa.String(length=8), nullable=True),
        sa.Column('topic', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('added_at', sa.DateTime(), server_default=sa.text('now()'),
                  nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'lemma', name='uq_user_word_list'),
    )
    op.create_index('ix_user_word_list_user_added', 'user_word_list',
                    ['user_id', 'added_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_user_word_list_user_added', table_name='user_word_list')
    op.drop_table('user_word_list')
    op.drop_index('ix_vocab_card_translations_ru_trgm',
                  table_name='vocab_card_translations')
    op.drop_index(op.f('ix_vocab_card_translations_lemma'),
                  table_name='vocab_card_translations')
    op.drop_table('vocab_card_translations')
    op.drop_index('ix_vocab_cards_lemma_ascii_trgm', table_name='vocab_cards')
    op.drop_index('ix_vocab_cards_lemma_trgm', table_name='vocab_cards')
    op.drop_index(op.f('ix_vocab_cards_source_created_at'), table_name='vocab_cards')
    op.drop_index('ix_vocab_cards_band', table_name='vocab_cards')
    op.drop_table('vocab_cards')
    # pg_trgm is left installed: other work may rely on it, and dropping an
    # extension is not this migration's business to undo.

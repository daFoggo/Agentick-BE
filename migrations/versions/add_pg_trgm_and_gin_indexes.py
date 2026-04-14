"""Add pg_trgm extension and GIN indexes for user search

Revision ID: 4a8f3c2d1e09
Revises: 2906579696ec
Create Date: 2026-04-14 01:58:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '4a8f3c2d1e09'
down_revision: Union[str, None] = '0d2c8c754bc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm extension for trigram-based fuzzy search
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm;')

    # Create GIN indexes using trigram ops for fast ILIKE / similarity queries
    op.execute(
        'CREATE INDEX idx_user_email_trgm ON "user" USING gin (email gin_trgm_ops);'
    )
    op.execute(
        'CREATE INDEX idx_user_name_trgm ON "user" USING gin (name gin_trgm_ops);'
    )


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS idx_user_name_trgm;')
    op.execute('DROP INDEX IF EXISTS idx_user_email_trgm;')
    op.execute('DROP EXTENSION IF EXISTS pg_trgm;')

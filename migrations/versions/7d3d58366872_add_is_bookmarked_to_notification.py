"""add is_bookmarked to notification

Revision ID: 7d3d58366872
Revises: 79adb4a15d9e
Create Date: 2026-05-01 15:25:02.672959

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d3d58366872'
down_revision: Union[str, None] = '79adb4a15d9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add column as nullable first
    op.add_column('notification', sa.Column('is_bookmarked', sa.Boolean(), nullable=True))
    # 2. Set default value for existing rows
    op.execute("UPDATE notification SET is_bookmarked = FALSE")
    # 3. Alter column to be NOT NULL
    op.alter_column('notification', 'is_bookmarked', nullable=False)


def downgrade() -> None:
    op.drop_column('notification', 'is_bookmarked')

"""add BOOKMARKED to notificationstatus enum

Revision ID: a1b2c3d4e5f6
Revises: 00c96898d1d0
Create Date: 2026-05-02 15:43:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '00c96898d1d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use op.execute to add the value to the enum type
    # Postgres doesn't allow ALTER TYPE ... ADD VALUE inside a transaction block
    op.execute("COMMIT") 
    op.execute("ALTER TYPE notificationstatus ADD VALUE 'BOOKMARKED'")
    op.execute("BEGIN")


def downgrade() -> None:
    pass

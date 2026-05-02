"""merge heads

Revision ID: f1e2d3c4b5a6
Revises: a1b2c3d4e5f6, c3d4e5f6a1b2
Create Date: 2026-05-02 17:05:00.000000

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f1e2d3c4b5a6'
down_revision: Union[str, Sequence[str], None] = ('a1b2c3d4e5f6', 'c3d4e5f6a1b2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

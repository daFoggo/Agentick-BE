"""drop calendar_id from event

Revision ID: e7f9b8c2d1a0
Revises: 3b1347bebfb7
Create Date: 2026-04-30 22:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7f9b8c2d1a0'
down_revision: Union[str, None] = '3b1347bebfb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update legacy event types
    op.execute("UPDATE event SET type = 'task' WHERE type = 'task_block'")

    # Drop foreign key constraint first
    op.drop_constraint('event_calendar_id_fkey', 'event', type_='foreignkey')
    # Drop the column
    op.drop_column('event', 'calendar_id')


def downgrade() -> None:
    # Add column back
    op.add_column('event', sa.Column('calendar_id', sa.String(length=36), nullable=True))
    # Add foreign key back
    op.create_foreign_key('event_calendar_id_fkey', 'event', 'calendar', ['calendar_id'], ['id'])

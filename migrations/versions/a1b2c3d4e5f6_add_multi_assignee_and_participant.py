"""add multi assignee and participant

Revision ID: a1b2c3d4e5f6
Revises: e7f9b8c2d1a0
Create Date: 2026-05-01 16:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "e7f9b8c2d1a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create task_assignee table
    op.create_table(
        "task_assignee",
        sa.Column("task_id", sa.String(length=36), sa.ForeignKey("task.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("project_member_id", sa.String(length=36), sa.ForeignKey("project_member.id", ondelete="CASCADE"), primary_key=True)
    )
    # Create event_participant table
    op.create_table(
        "event_participant",
        sa.Column("event_id", sa.String(length=36), sa.ForeignKey("event.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("team_member_id", sa.String(length=36), sa.ForeignKey("team_member.id", ondelete="CASCADE"), primary_key=True)
    )

def downgrade() -> None:
    op.drop_table("event_participant")
    op.drop_table("task_assignee")

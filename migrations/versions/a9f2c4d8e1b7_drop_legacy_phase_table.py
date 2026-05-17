"""drop legacy phase table

Revision ID: a9f2c4d8e1b7
Revises: 56631e2717e5
Create Date: 2026-05-16 21:37:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a9f2c4d8e1b7"
down_revision: Union[str, None] = "56631e2717e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("task_phase_id_fkey", "task", type_="foreignkey")
    op.drop_column("task", "phase_id")
    op.drop_table("phase")


def downgrade() -> None:
    op.create_table(
        "phase",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order", sa.Float(), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("task", sa.Column("phase_id", sa.String(length=36), nullable=True))
    op.create_foreign_key("task_phase_id_fkey", "task", "phase", ["phase_id"], ["id"])

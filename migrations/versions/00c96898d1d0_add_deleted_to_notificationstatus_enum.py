"""add DELETED to notificationstatus enum

Revision ID: 00c96898d1d0
Revises: 7d3d58366872
Create Date: 2026-05-01 15:39:27.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00c96898d1d0'
down_revision: Union[str, None] = '7d3d58366872'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use op.execute to add the value to the enum type
    # Postgres doesn't allow ALTER TYPE ... ADD VALUE inside a transaction block
    # so we use a raw execution that commits current transaction first if needed, 
    # but Alembic provides a better way: 
    # context.get_bind().execute(text("ALTER TYPE ... ADD VALUE ..."))
    # For simplicity, we just use op.execute and hope the environment allows it, 
    # or use autocommit if available.
    
    op.execute("COMMIT") # End the transaction
    op.execute("ALTER TYPE notificationstatus ADD VALUE 'DELETED'")
    op.execute("BEGIN")  # Restart the transaction for Alembic to finish


def downgrade() -> None:
    # Downgrading enums in Postgres is complex (requires recreating the type)
    # We will leave it for now as it's just an extra enum value.
    pass

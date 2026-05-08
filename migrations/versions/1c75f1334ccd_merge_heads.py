"""merge heads

Revision ID: 1c75f1334ccd
Revises: ('1299fba30b45', 'adbae1aba004', 'f3daa6c53a6c')
Create Date: 2026-05-08 07:13:02.215108

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "1c75f1334ccd"
down_revision: Union[str, None] = ("1299fba30b45", "adbae1aba004", "f3daa6c53a6c")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

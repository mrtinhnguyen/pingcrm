"""add location to contacts

Revision ID: a3b4c5d6e7f9
Revises: f2a3b4c5d6e8
Create Date: 2026-03-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a3b4c5d6e7f9"
down_revision: Union[str, None] = "f2a3b4c5d6e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("contacts", sa.Column("location", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("contacts", "location")

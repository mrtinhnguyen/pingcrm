"""add sync_2nd_tier to users

Revision ID: a1b2c4d5e6f7
Revises: dc46fcbffa66
Create Date: 2026-03-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c4d5e6f7'
down_revision: Union[str, None] = 'dc46fcbffa66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('sync_2nd_tier', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    op.drop_column('users', 'sync_2nd_tier')

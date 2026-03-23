"""add read receipt columns

Revision ID: c7d8e9f0a1b2
Revises: a1b2c4d5e6f7
Create Date: 2026-03-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, None] = 'a1b2c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('interactions', sa.Column('is_read_by_recipient', sa.Boolean(), nullable=True))
    op.add_column('contacts', sa.Column('telegram_read_outbox_max_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('contacts', 'telegram_read_outbox_max_id')
    op.drop_column('interactions', 'is_read_by_recipient')

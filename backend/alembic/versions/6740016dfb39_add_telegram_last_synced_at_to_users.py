"""add_telegram_last_synced_at_to_users

Revision ID: 6740016dfb39
Revises: f3a4b5c6d7e8
Create Date: 2026-03-13 10:15:19.221013

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6740016dfb39'
down_revision: Union[str, None] = 'f3a4b5c6d7e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('telegram_last_synced_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'telegram_last_synced_at')

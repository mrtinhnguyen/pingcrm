"""add priority_settings to users

Revision ID: c5d6e7f8a1b2
Revises: b4c5d6e7f8a0
Create Date: 2026-03-08 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "c5d6e7f8a1b2"
down_revision = "b4c5d6e7f8a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("priority_settings", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("users", "priority_settings")

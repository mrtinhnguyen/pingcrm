"""add birthday to contacts

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-03-08
"""
from alembic import op
import sqlalchemy as sa

revision = "e2f3a4b5c6d7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name='contacts' AND column_name='birthday'"
    ))
    if result.fetchone() is None:
        op.add_column("contacts", sa.Column("birthday", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("contacts", "birthday")

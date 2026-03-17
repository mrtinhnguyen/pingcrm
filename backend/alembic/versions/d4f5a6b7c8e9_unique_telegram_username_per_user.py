"""unique telegram_username per user

Revision ID: d4f5a6b7c8e9
Revises: c3191053d3a5
Create Date: 2026-03-17
"""
from typing import Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = 'd4f5a6b7c8e9'
down_revision: Union[str, None] = 'c3191053d3a5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Normalize existing telegram_username values: strip, lowercase, remove leading @
    conn.execute(text("""
        UPDATE contacts
        SET telegram_username = lower(trim(leading '@' from trim(telegram_username)))
        WHERE telegram_username IS NOT NULL
    """))

    # Resolve duplicates: keep the one with telegram_user_id set, or most recently updated
    conn.execute(text("""
        UPDATE contacts
        SET telegram_username = NULL
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                    ROW_NUMBER() OVER (
                        PARTITION BY user_id, lower(telegram_username)
                        ORDER BY
                            (telegram_user_id IS NOT NULL) DESC,
                            updated_at DESC NULLS LAST,
                            created_at DESC
                    ) AS rn
                FROM contacts
                WHERE telegram_username IS NOT NULL
            ) ranked
            WHERE rn > 1
        )
    """))

    op.create_index(
        'uq_contacts_telegram_username_per_user',
        'contacts',
        ['user_id', sa.text('lower(telegram_username)')],
        unique=True,
        postgresql_where=text("telegram_username IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index('uq_contacts_telegram_username_per_user', table_name='contacts')

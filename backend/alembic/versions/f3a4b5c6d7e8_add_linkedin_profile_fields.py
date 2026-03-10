"""add linkedin profile fields to contacts

Revision ID: f3a4b5c6d7e8
Revises: 97d166ac9db2
Create Date: 2026-03-10
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = 'f3a4b5c6d7e8'
down_revision: Union[str, None] = '97d166ac9db2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('contacts', sa.Column('linkedin_profile_id', sa.String(), nullable=True))
    op.add_column('contacts', sa.Column('linkedin_headline', sa.String(), nullable=True))
    op.add_column('contacts', sa.Column('linkedin_bio', sa.Text(), nullable=True))
    op.create_index('ix_contacts_linkedin_profile_id', 'contacts', ['linkedin_profile_id'])


def downgrade() -> None:
    op.drop_index('ix_contacts_linkedin_profile_id', table_name='contacts')
    op.drop_column('contacts', 'linkedin_bio')
    op.drop_column('contacts', 'linkedin_headline')
    op.drop_column('contacts', 'linkedin_profile_id')

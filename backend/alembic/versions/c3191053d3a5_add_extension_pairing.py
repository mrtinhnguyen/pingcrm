"""add_extension_pairing

Revision ID: c3191053d3a5
Revises: 5aba078a5f9e
Create Date: 2026-03-16 15:58:21.229376

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3191053d3a5'
down_revision: Union[str, None] = '5aba078a5f9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'extension_pairings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=12), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('claimed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_extension_pairings_code'), 'extension_pairings', ['code'], unique=True)
    op.add_column('users', sa.Column('linkedin_extension_paired_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'linkedin_extension_paired_at')
    op.drop_index(op.f('ix_extension_pairings_code'), table_name='extension_pairings')
    op.drop_table('extension_pairings')

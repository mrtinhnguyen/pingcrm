"""add google_resource_name to contacts

Revision ID: d6e7f8a1b2c3
Revises: c5d6e7f8a1b2
Create Date: 2026-03-08 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d6e7f8a1b2c3"
down_revision = "c5d6e7f8a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("contacts", sa.Column("google_resource_name", sa.String(), nullable=True))
    op.create_index("ix_contacts_google_resource_name", "contacts", ["google_resource_name"])


def downgrade() -> None:
    op.drop_index("ix_contacts_google_resource_name", table_name="contacts")
    op.drop_column("contacts", "google_resource_name")

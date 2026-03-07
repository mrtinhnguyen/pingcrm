"""Encrypt existing plaintext token columns in-place.

Revision ID: d1e2f3a4b5c6
Revises: b7fee2bffb64
Create Date: 2026-03-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, None] = "b7fee2bffb64"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Token columns to encrypt: (table, column)
_TOKEN_COLUMNS = [
    ("users", "google_refresh_token"),
    ("users", "twitter_access_token"),
    ("users", "twitter_refresh_token"),
    ("users", "telegram_session"),
    ("google_accounts", "refresh_token"),
]


def _get_fernet():
    """Build Fernet instance from ENCRYPTION_KEY env var."""
    import os
    from cryptography.fernet import Fernet

    key = os.environ.get("ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError(
            "ENCRYPTION_KEY must be set to run this migration. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode())


def _is_encrypted(value: str) -> bool:
    """Heuristic: Fernet tokens are base64 and start with 'gAAAAA'."""
    return value.startswith("gAAAAA")


def upgrade() -> None:
    f = _get_fernet()
    conn = op.get_bind()

    for table, column in _TOKEN_COLUMNS:
        rows = conn.execute(
            sa.text(f"SELECT id, {column} FROM {table} WHERE {column} IS NOT NULL")
        ).fetchall()
        for row in rows:
            val = row[1]
            if _is_encrypted(val):
                continue  # already encrypted
            encrypted = f.encrypt(val.encode()).decode()
            conn.execute(
                sa.text(f"UPDATE {table} SET {column} = :enc WHERE id = :id"),
                {"enc": encrypted, "id": row[0]},
            )


def downgrade() -> None:
    f = _get_fernet()
    conn = op.get_bind()

    for table, column in _TOKEN_COLUMNS:
        rows = conn.execute(
            sa.text(f"SELECT id, {column} FROM {table} WHERE {column} IS NOT NULL")
        ).fetchall()
        for row in rows:
            val = row[1]
            if not _is_encrypted(val):
                continue  # already plaintext
            decrypted = f.decrypt(val.encode()).decode()
            conn.execute(
                sa.text(f"UPDATE {table} SET {column} = :dec WHERE id = :id"),
                {"dec": decrypted, "id": row[0]},
            )

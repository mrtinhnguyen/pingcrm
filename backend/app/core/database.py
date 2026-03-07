from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# ---------------------------------------------------------------------------
# TRANSACTION POLICY (Phase 5.2)
# ---------------------------------------------------------------------------
# API route handlers MUST use flush() only — never call commit() directly.
#   - flush() sends SQL to the DB within the current transaction without
#     finalising it, allowing subsequent operations to see the changes.
#   - commit() is the exclusive responsibility of get_db() (see below).
#
# get_db() dependency owns the transaction lifecycle:
#   - On successful handler return  → session.commit()
#   - On any exception              → session.rollback()
#   This keeps transaction boundaries at the HTTP request level.
#
# Celery tasks manage their own sessions independently (AsyncSessionLocal()
# context manager) and are responsible for their own commit/rollback.
#
# Reference: Phase 5.2 in Plans-archive.md
# ---------------------------------------------------------------------------

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a database session for a single request.

    Transaction behaviour (auto-commit on success):
        - Yields the session to the route handler.
        - Calls commit() when the handler returns without raising.
        - Calls rollback() if any exception propagates out of the handler.
        - Always closes the session in the finally block.

    Route handlers MUST use flush() instead of commit() so that this
    dependency retains exclusive ownership of the transaction boundary.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

"""
Database connection and session management.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Determine if using SQLite
def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")

# Async engine for FastAPI
async_engine_kwargs = {
    "echo": settings.debug,
    "future": True,
}
if not _is_sqlite(settings.database_url):
    async_engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    })

async_engine = create_async_engine(
    settings.database_url,
    **async_engine_kwargs,
)

# Sync engine for Alembic migrations
sync_engine_kwargs = {
    "echo": settings.debug,
    "future": True,
}
if not _is_sqlite(settings.database_url_sync):
    sync_engine_kwargs["pool_pre_ping"] = True

sync_engine = create_engine(
    settings.database_url_sync,
    **sync_engine_kwargs,
)

# Session factories
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db():
    """Get synchronous database session (for migrations/CLI)."""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

"""
Database configuration and session management.

This module handles SQLAlchemy engine creation and session management.
"""

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import declarative_base

from clever.config import settings

# SQLAlchemy base class for declarative models
Base = declarative_base()

# Async database engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.is_development,  # Log SQL queries in development
    pool_size=10,
    max_overflow=20,
    connect_args={"statement_cache_size": 0},  # Required for Supabase PgBouncer
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize database connection and create tables if they don't exist."""
    # Import models to register them with Base.metadata
    from clever import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Dependency to get async database session."""
    async with AsyncSessionLocal() as session:
        yield session

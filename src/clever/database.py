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
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize database connection and run any startup tasks."""
    # In a real app, this might include running migrations, creating tables, etc.
    # For this assessment, we'll keep it simple
    pass


async def get_db() -> AsyncSession:
    """Dependency to get async database session."""
    async with AsyncSessionLocal() as session:
        yield session

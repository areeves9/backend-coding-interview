"""
Test fixtures and configuration.

This module provides pytest fixtures for testing the API.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.pool import StaticPool

from clever.auth.deps import get_current_user
from clever.database import Base, get_db
from clever.models import Photo, User

# Test database URL - in-memory SQLite for speed
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(test_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id="test-user-123",
        email="test@example.com",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def other_user(test_session: AsyncSession) -> User:
    """Create another test user for ownership tests."""
    user = User(
        id="other-user-456",
        email="other@example.com",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_photo(test_session: AsyncSession, test_user: User) -> Photo:
    """Create a sample photo owned by test_user."""
    photo = Photo(
        pexels_id=12345,
        width=1920,
        height=1080,
        url="https://www.pexels.com/photo/12345",
        photographer="John Doe",
        photographer_url="https://www.pexels.com/@johndoe",
        photographer_id=100,
        avg_color="#AABBCC",
        src_original="https://images.pexels.com/photos/12345/original.jpg",
        src_large2x="https://images.pexels.com/photos/12345/large2x.jpg",
        src_large="https://images.pexels.com/photos/12345/large.jpg",
        src_medium="https://images.pexels.com/photos/12345/medium.jpg",
        src_small="https://images.pexels.com/photos/12345/small.jpg",
        src_portrait="https://images.pexels.com/photos/12345/portrait.jpg",
        src_landscape="https://images.pexels.com/photos/12345/landscape.jpg",
        src_tiny="https://images.pexels.com/photos/12345/tiny.jpg",
        alt="A beautiful landscape",
        user_id=test_user.id,
    )
    test_session.add(photo)
    await test_session.commit()
    await test_session.refresh(photo)
    return photo


@pytest_asyncio.fixture
async def other_user_photo(test_session: AsyncSession, other_user: User) -> Photo:
    """Create a photo owned by other_user for ownership tests."""
    photo = Photo(
        pexels_id=99999,
        width=800,
        height=600,
        url="https://www.pexels.com/photo/99999",
        photographer="Jane Smith",
        photographer_url="https://www.pexels.com/@janesmith",
        photographer_id=200,
        avg_color="#112233",
        src_original="https://images.pexels.com/photos/99999/original.jpg",
        src_large2x="https://images.pexels.com/photos/99999/large2x.jpg",
        src_large="https://images.pexels.com/photos/99999/large.jpg",
        src_medium="https://images.pexels.com/photos/99999/medium.jpg",
        src_small="https://images.pexels.com/photos/99999/small.jpg",
        src_portrait="https://images.pexels.com/photos/99999/portrait.jpg",
        src_landscape="https://images.pexels.com/photos/99999/landscape.jpg",
        src_tiny="https://images.pexels.com/photos/99999/tiny.jpg",
        alt="Another photo",
        user_id=other_user.id,
    )
    test_session.add(photo)
    await test_session.commit()
    await test_session.refresh(photo)
    return photo


@pytest_asyncio.fixture
async def client(
    test_engine,
    test_session: AsyncSession,
    test_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with mocked dependencies."""
    from clever.main import create_app

    app = create_app()

    # Override database dependency
    async def override_get_db():
        yield test_session

    # Override auth dependency to return test user
    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def client_as_other_user(
    test_engine,
    test_session: AsyncSession,
    other_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client authenticated as other_user."""
    from clever.main import create_app

    app = create_app()

    async def override_get_db():
        yield test_session

    async def override_get_current_user():
        return other_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


# Sample photo data for creating new photos
SAMPLE_PHOTO_DATA = {
    "pexels_id": 67890,
    "width": 1280,
    "height": 720,
    "url": "https://www.pexels.com/photo/67890",
    "photographer": "Test Photographer",
    "photographer_url": "https://www.pexels.com/@testphotographer",
    "photographer_id": 300,
    "avg_color": "#DDEEFF",
    "src_original": "https://images.pexels.com/photos/67890/original.jpg",
    "src_large2x": "https://images.pexels.com/photos/67890/large2x.jpg",
    "src_large": "https://images.pexels.com/photos/67890/large.jpg",
    "src_medium": "https://images.pexels.com/photos/67890/medium.jpg",
    "src_small": "https://images.pexels.com/photos/67890/small.jpg",
    "src_portrait": "https://images.pexels.com/photos/67890/portrait.jpg",
    "src_landscape": "https://images.pexels.com/photos/67890/landscape.jpg",
    "src_tiny": "https://images.pexels.com/photos/67890/tiny.jpg",
    "alt": "Test photo description",
}

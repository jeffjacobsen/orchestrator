"""
Pytest configuration and shared fixtures for backend tests.
"""

import os
import sys
import asyncio
from typing import AsyncGenerator, Generator
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, get_db
from app.core.config import settings


# Configure async event loop for pytest-asyncio
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Database fixtures
@pytest.fixture(scope="function")
async def test_db_engine():
    """Create a test database engine using SQLite in-memory."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
def override_get_db(test_db_session):
    """Override the get_db dependency to use test database."""
    async def _override_get_db():
        yield test_db_session

    from app.main import app
    app.dependency_overrides[get_db] = _override_get_db

    yield

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def api_key():
    """Return test API key."""
    return os.getenv("TEST_API_KEY", "test-api-key-12345")


@pytest.fixture(scope="function")
def api_key_headers(api_key):
    """Return headers with API key for authenticated requests."""
    return {
        "X-API-Key": api_key
    }


# Mock settings for testing
@pytest.fixture(scope="function")
def mock_settings():
    """Override settings for testing."""
    original_settings = {}

    # Save original settings
    for key in dir(settings):
        if not key.startswith("_"):
            original_settings[key] = getattr(settings, key)

    # Override for tests
    settings.orchestrator_working_directory = "/tmp/test_orchestrator"
    settings.api_key = "test-api-key-12345"

    yield settings

    # Restore original settings
    for key, value in original_settings.items():
        setattr(settings, key, value)

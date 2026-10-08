"""Pytest fixtures for integration tests.

Tests run against a dedicated PostgreSQL database (``POSTGRES_TEST_DB``)
that must be created and migrated beforehand — see README. Each test
runs inside a transaction that is rolled back at the end, so tests are
fully isolated from each other.
"""

import asyncio
from collections.abc import AsyncIterator
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from tg_order_bot.config import get_settings
from tg_order_bot.database.models.catalog import Category, Product
from tg_order_bot.database.models.user import User


@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped event loop for pytest-asyncio."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    """Session-scoped async engine bound to the test database.

    Uses ``NullPool`` to avoid stale connections between tests — each
    connect() opens a fresh connection, which is required on Windows
    with the ProactorEventLoop.
    """
    settings = get_settings()
    url = (
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_test_db}"
    )
    engine = create_async_engine(
        url,
        echo=False,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Per-test session wrapped in a transaction that is rolled back.

    Uses the SQLAlchemy "nested transaction" trick so that code under
    test can call ``session.commit()`` freely without affecting other
    tests.
    """
    connection = await engine.connect()
    transaction = await connection.begin()

    factory = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )

    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()
            if transaction.is_active:
                await transaction.rollback()
            await connection.close()


@pytest_asyncio.fixture
async def user(session: AsyncSession) -> User:
    """A test user persisted in the database."""
    user = User(
        telegram_id=111_222_333,
        username="testuser",
        full_name="Test User",
    )
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def category(session: AsyncSession) -> Category:
    """A test category."""
    category = Category(name="Test Category", sort_order=0, is_active=True)
    session.add(category)
    await session.flush()
    return category


@pytest_asyncio.fixture
async def product(session: AsyncSession, category: Category) -> Product:
    """A test product in the test category."""
    product = Product(
        category_id=category.id,
        name="Test Product",
        price=Decimal("100.00"),
        sort_order=0,
        is_active=True,
    )
    session.add(product)
    await session.flush()
    return product

"""Async database engine and session factory.

The engine is created once at module import (fail-fast on invalid DSN).
Sessions are produced by ``async_session_factory`` and should be closed
after use — typically via the ``get_session`` dependency.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from tg_order_bot.config import get_settings

settings = get_settings()

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield an async database session, closing it afterwards.

    Intended for use as a FastAPI-style dependency or aiogram middleware.
    The session is automatically closed even if an exception occurs.
    """
    async with async_session_factory() as session:
        yield session

"""Tests for the database engine and session configuration."""

from sqlalchemy.ext.asyncio import AsyncEngine

from tg_order_bot.database.session import async_session_factory, engine


def test_engine_is_async() -> None:
    """Ensure the engine is an AsyncEngine instance."""
    assert isinstance(engine, AsyncEngine)


def test_engine_uses_asyncpg_driver() -> None:
    """Ensure the DSN uses the asyncpg driver."""
    assert engine.url.drivername == "postgresql+asyncpg"


def test_session_factory_is_configured() -> None:
    """Ensure the session factory is bound to the engine."""
    assert async_session_factory.kw["bind"] is engine

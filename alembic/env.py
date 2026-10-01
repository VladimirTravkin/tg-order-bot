"""Alembic environment configuration.

Configures Alembic to run migrations against the async SQLAlchemy engine
using the database URL from application settings (``.env``) instead of
``alembic.ini``. All ORM models are imported so that ``Base.metadata``
contains the full schema for autogeneration.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from tg_order_bot.config import get_settings

# Import all models so that Base.metadata is fully populated.
from tg_order_bot.database import models  # noqa: F401
from tg_order_bot.database.base import Base

# Alembic Config object, provides access to values in alembic.ini.
config = context.config

# Configure Python logging from alembic.ini's [loggers] section.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject the database URL from application settings.
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

# Metadata for 'autogenerate' support.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL without connecting to the database. Useful for
    reviewing migrations or applying them via external tooling.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations using an existing connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for 'online' mode (the default)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

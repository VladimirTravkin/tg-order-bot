"""Tests for ``common.services.users``."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tg_order_bot.common.services import get_or_create_user
from tg_order_bot.database.models.user import User


@pytest.mark.asyncio
async def test_get_or_create_user_creates_new(session: AsyncSession) -> None:
    """First call creates a new User row."""
    user = await get_or_create_user(
        session=session,
        telegram_id=555_000_111,
        username="newuser",
        full_name="New User",
    )

    assert user.id is not None
    assert user.telegram_id == 555_000_111
    assert user.username == "newuser"
    assert user.full_name == "New User"


@pytest.mark.asyncio
async def test_get_or_create_user_returns_existing(session: AsyncSession) -> None:
    """Second call returns the same User row instead of creating a new one."""
    first = await get_or_create_user(
        session=session,
        telegram_id=555_000_222,
        username="sameuser",
        full_name="Same User",
    )
    second = await get_or_create_user(
        session=session,
        telegram_id=555_000_222,
        username="sameuser",
        full_name="Same User",
    )

    assert first.id == second.id

    stmt = select(User).where(User.telegram_id == 555_000_222)
    users = (await session.execute(stmt)).scalars().all()
    assert len(users) == 1


@pytest.mark.asyncio
async def test_get_or_create_user_updates_fields(session: AsyncSession) -> None:
    """Username and full_name are refreshed on each call."""
    user = await get_or_create_user(
        session=session,
        telegram_id=555_000_333,
        username="old_username",
        full_name="Old Name",
    )
    assert user.username == "old_username"
    assert user.full_name == "Old Name"

    user = await get_or_create_user(
        session=session,
        telegram_id=555_000_333,
        username="new_username",
        full_name="New Name",
    )
    assert user.username == "new_username"
    assert user.full_name == "New Name"

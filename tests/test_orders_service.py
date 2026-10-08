"""Tests for ``orders.service``."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tg_order_bot.cart.service import add_to_cart, get_cart_items
from tg_order_bot.database.models.catalog import Product
from tg_order_bot.database.models.enums import OrderStatus
from tg_order_bot.database.models.order import OrderItem
from tg_order_bot.database.models.user import User
from tg_order_bot.orders.service import (
    create_order,
    format_order_for_admin,
    format_order_for_user,
    notify_admins,
)


@pytest.mark.asyncio
async def test_create_order_returns_none_on_empty_cart(session: AsyncSession, user: User) -> None:
    """create_order returns None if the cart is empty."""
    order = await create_order(
        session=session,
        user=user,
        customer_name="Test",
        customer_phone="+70000000000",
        comment=None,
    )
    assert order is None


@pytest.mark.asyncio
async def test_create_order_with_items(session: AsyncSession, user: User, product: Product) -> None:
    """create_order persists Order + OrderItem, snapshots product data."""
    await add_to_cart(session, user, product.id)
    await add_to_cart(session, user, product.id)  # quantity=2

    order = await create_order(
        session=session,
        user=user,
        customer_name="Иван",
        customer_phone="+79991234567",
        comment="Позвонить вечером",
    )

    assert order is not None
    assert order.id is not None
    assert order.user_id == user.id
    assert order.status == OrderStatus.NEW
    assert order.total == Decimal("200.00")  # 100.00 × 2
    assert order.customer_name == "Иван"
    assert order.customer_phone == "+79991234567"
    assert order.comment == "Позвонить вечером"

    # OrderItem created with snapshot
    stmt = select(OrderItem).where(OrderItem.order_id == order.id)
    items = (await session.execute(stmt)).scalars().all()
    assert len(items) == 1
    assert items[0].product_id == product.id
    assert items[0].product_name == product.name
    assert items[0].product_price == product.price
    assert items[0].quantity == 2


@pytest.mark.asyncio
async def test_create_order_clears_cart(
    session: AsyncSession, user: User, product: Product
) -> None:
    """After create_order the cart is empty."""
    await add_to_cart(session, user, product.id)

    await create_order(
        session=session,
        user=user,
        customer_name="Test",
        customer_phone="+70000000000",
        comment=None,
    )

    cart = await get_cart_items(session, user)
    assert cart == []


@pytest.mark.asyncio
async def test_format_order_for_user_contains_essentials(
    session: AsyncSession, user: User, product: Product
) -> None:
    """format_order_for_user includes name, phone, items, total."""
    await add_to_cart(session, user, product.id)
    order = await create_order(
        session=session,
        user=user,
        customer_name="Иван",
        customer_phone="+79991234567",
        comment=None,
    )
    assert order is not None

    text = format_order_for_user(order)
    assert f"#{order.id}" in text
    assert "Иван" in text
    assert "+79991234567" in text
    assert product.name in text
    assert str(order.total) in text


@pytest.mark.asyncio
async def test_format_order_for_admin_contains_telegram_id(
    session: AsyncSession, user: User, product: Product
) -> None:
    """Admin format includes telegram_id and username."""
    await add_to_cart(session, user, product.id)
    order = await create_order(
        session=session,
        user=user,
        customer_name="Иван",
        customer_phone="+79991234567",
        comment=None,
    )
    assert order is not None

    text = format_order_for_admin(order, user)
    assert str(user.telegram_id) in text
    assert f"@{user.username}" in text
    assert product.name in text


@pytest.mark.asyncio
async def test_notify_admins_sends_to_each(
    session: AsyncSession, user: User, product: Product
) -> None:
    """notify_admins sends to every admin from settings."""
    await add_to_cart(session, user, product.id)
    order = await create_order(
        session=session,
        user=user,
        customer_name="Иван",
        customer_phone="+79991234567",
        comment=None,
    )
    assert order is not None

    bot = MagicMock()
    bot.send_message = AsyncMock()

    await notify_admins(bot, order, user)

    # admin_ids from .env — at least one
    assert bot.send_message.await_count >= 1

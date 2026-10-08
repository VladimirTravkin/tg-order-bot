"""Tests for ``admin.service``."""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tg_order_bot.admin.service import (
    get_order_with_details,
    get_orders_page,
    status_filter_label,
    update_order_status,
)
from tg_order_bot.cart.service import add_to_cart
from tg_order_bot.database.models.catalog import Product
from tg_order_bot.database.models.enums import OrderStatus
from tg_order_bot.database.models.user import User
from tg_order_bot.orders.service import create_order


async def _make_order(session: AsyncSession, user: User, product: Product) -> int:
    """Helper: add a product and create an order, return its id."""
    await add_to_cart(session, user, product.id)
    order = await create_order(
        session=session,
        user=user,
        customer_name="Тест",
        customer_phone="+70000000000",
        comment=None,
    )
    assert order is not None
    return order.id


@pytest.mark.asyncio
async def test_get_orders_page_returns_all(
    session: AsyncSession, user: User, product: Product
) -> None:
    """Without filter returns all orders."""
    await _make_order(session, user, product)
    await _make_order(session, user, product)

    orders, total = await get_orders_page(session, page=0, status_filter="all")
    assert total == 2
    assert len(orders) == 2


@pytest.mark.asyncio
async def test_get_orders_page_filters_by_status(
    session: AsyncSession, user: User, product: Product
) -> None:
    """Filter 'new' returns only NEW orders."""
    order_id = await _make_order(session, user, product)
    await update_order_status(session, order_id, OrderStatus.CONFIRMED)
    await _make_order(session, user, product)  # still NEW

    new_orders, new_total = await get_orders_page(
        session, status_filter="new"
    )
    assert new_total == 1
    assert new_orders[0].status == OrderStatus.NEW


@pytest.mark.asyncio
async def test_get_order_with_details_eager_loads(
    session: AsyncSession, user: User, product: Product
) -> None:
    """Items and user are loaded (no N+1)."""
    order_id = await _make_order(session, user, product)

    order = await get_order_with_details(session, order_id)
    assert order is not None
    assert len(order.items) == 1
    assert order.user is not None
    assert order.user.id == user.id


@pytest.mark.asyncio
async def test_update_order_status_changes_status(
    session: AsyncSession, user: User, product: Product
) -> None:
    """update_order_status persists the new status."""
    order_id = await _make_order(session, user, product)

    updated = await update_order_status(session, order_id, OrderStatus.SHIPPED)
    assert updated is not None
    assert updated.status == OrderStatus.SHIPPED


@pytest.mark.asyncio
async def test_update_order_status_returns_none_if_missing(
    session: AsyncSession,
) -> None:
    """update_order_status returns None for unknown id."""
    result = await update_order_status(session, 999_999, OrderStatus.DONE)
    assert result is None


def test_status_filter_label_covers_all_keys() -> None:
    """All known filter keys map to non-default labels."""
    for key in ("all", "new", "in_progress", "done", "cancelled"):
        label = status_filter_label(key)
        assert label != key  # not the default fallback


def test_status_filter_label_default_fallback() -> None:
    """Unknown key is returned unchanged."""
    assert status_filter_label("unknown") == "unknown"

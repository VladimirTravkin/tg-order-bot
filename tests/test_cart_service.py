"""Tests for ``cart.service``."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tg_order_bot.cart.service import (
    add_to_cart,
    clear_cart,
    get_cart_items,
    remove_from_cart,
)
from tg_order_bot.database.models.cart import CartItem
from tg_order_bot.database.models.catalog import Product
from tg_order_bot.database.models.user import User


@pytest.mark.asyncio
async def test_add_to_cart_creates_new_item(
    session: AsyncSession, user: User, product: Product
) -> None:
    """Adding a product creates a single CartItem with quantity=1."""
    item = await add_to_cart(session, user, product.id)

    assert item.id is not None
    assert item.user_id == user.id
    assert item.product_id == product.id
    assert item.quantity == 1


@pytest.mark.asyncio
async def test_add_to_cart_increments_quantity(
    session: AsyncSession, user: User, product: Product
) -> None:
    """Adding the same product twice increments quantity."""
    await add_to_cart(session, user, product.id)
    item = await add_to_cart(session, user, product.id)

    assert item.quantity == 2

    stmt = select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product.id)
    items = (await session.execute(stmt)).scalars().all()
    assert len(items) == 1


@pytest.mark.asyncio
async def test_get_cart_items_returns_user_items(
    session: AsyncSession,
    user: User,
    product: Product,
    category,
) -> None:
    """get_cart_items returns only the user's items with product loaded."""
    other_product = Product(
        category_id=category.id,
        name="Other Product",
        price=50,
        sort_order=1,
        is_active=True,
    )
    session.add(other_product)
    await session.flush()

    await add_to_cart(session, user, product.id)
    await add_to_cart(session, user, other_product.id)

    items = await get_cart_items(session, user)
    assert len(items) == 2
    # Product loaded via selectinload
    assert all(item.product is not None for item in items)


@pytest.mark.asyncio
async def test_remove_from_cart_removes_item(
    session: AsyncSession, user: User, product: Product
) -> None:
    """remove_from_cart returns True and deletes the row."""
    await add_to_cart(session, user, product.id)

    removed = await remove_from_cart(session, user, product.id)
    assert removed is True

    items = await get_cart_items(session, user)
    assert items == []


@pytest.mark.asyncio
async def test_remove_from_cart_returns_false_if_missing(
    session: AsyncSession, user: User, product: Product
) -> None:
    """remove_from_cart returns False when the product isn't in the cart."""
    removed = await remove_from_cart(session, user, product.id)
    assert removed is False


@pytest.mark.asyncio
async def test_clear_cart_empties_all_items(
    session: AsyncSession, user: User, product: Product, category
) -> None:
    """clear_cart removes every item for the user."""
    other = Product(
        category_id=category.id,
        name="Other",
        price=10,
        sort_order=1,
        is_active=True,
    )
    session.add(other)
    await session.flush()

    await add_to_cart(session, user, product.id)
    await add_to_cart(session, user, other.id)

    await clear_cart(session, user)

    items = await get_cart_items(session, user)
    assert items == []

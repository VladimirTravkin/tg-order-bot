"""Cart service — add, view, remove, and clear cart items.

All functions accept an AsyncSession and a User instance. They return
CartItem rows for the view; other operations return None.
"""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tg_order_bot.database.models.cart import CartItem
from tg_order_bot.database.models.user import User


async def add_to_cart(
    session: AsyncSession,
    user: User,
    product_id: int,
) -> CartItem:
    """Add a product to the user's cart, or increment quantity.

    If the product is already in the cart, ``quantity`` is incremented
    by 1. The UniqueConstraint on (user_id, product_id) guarantees
    there is only one row per product.
    """
    stmt = (
        select(CartItem)
        .where(CartItem.user_id == user.id)
        .where(CartItem.product_id == product_id)
    )
    item = (await session.execute(stmt)).scalar_one_or_none()

    if item is None:
        item = CartItem(
            user_id=user.id,
            product_id=product_id,
            quantity=1,
        )
        session.add(item)
    else:
        item.quantity += 1

    await session.flush()
    return item


async def get_cart_items(
    session: AsyncSession,
    user: User,
) -> list[CartItem]:
    """Return all cart items for the user, with products eagerly loaded.

    ``selectinload`` ensures the ``product`` relationship is fetched in
    a single additional query (no N+1).
    """
    stmt = (
        select(CartItem)
        .where(CartItem.user_id == user.id)
        .options(selectinload(CartItem.product))
        .order_by(CartItem.created_at)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def remove_from_cart(
    session: AsyncSession,
    user: User,
    product_id: int,
) -> bool:
    """Remove a product from the user's cart.

    Returns True if a row was deleted, False if the product was not in
    the cart.
    """
    stmt = (
        delete(CartItem)
        .where(CartItem.user_id == user.id)
        .where(CartItem.product_id == product_id)
    )
    result = await session.execute(stmt)
    return getattr(result, "rowcount", 0) > 0


async def clear_cart(
    session: AsyncSession,
    user: User,
) -> None:
    """Remove all items from the user's cart."""
    stmt = delete(CartItem).where(CartItem.user_id == user.id)
    await session.execute(stmt)


__all__ = [
    "add_to_cart",
    "clear_cart",
    "get_cart_items",
    "remove_from_cart",
]

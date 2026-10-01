"""Data-access functions for the catalog.

All functions are async and accept an AsyncSession as the first argument.
They return ORM instances; serialization to Telegram messages happens in
handlers.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tg_order_bot.database.models.catalog import Category, Product


async def get_active_categories(session: AsyncSession) -> list[Category]:
    """Return active categories ordered by ``sort_order`` then ``id``.

    Only ``is_active=True`` rows are returned. The secondary sort by
    ``id`` keeps ordering stable when ``sort_order`` is equal.
    """
    stmt = (
        select(Category)
        .where(Category.is_active.is_(True))
        .order_by(Category.sort_order, Category.id)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_category(session: AsyncSession, category_id: int) -> Category | None:
    """Return a category by id, or ``None`` if not found."""
    return await session.get(Category, category_id)


async def get_products_by_category(
    session: AsyncSession, category_id: int
) -> list[Product]:
    """Return active products in the given category.

    Products are ordered by ``sort_order`` then ``id`` for stable output.
    """
    stmt = (
        select(Product)
        .where(Product.category_id == category_id)
        .where(Product.is_active.is_(True))
        .order_by(Product.sort_order, Product.id)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_product(session: AsyncSession, product_id: int) -> Product | None:
    """Return a product by id, or ``None`` if not found."""
    return await session.get(Product, product_id)

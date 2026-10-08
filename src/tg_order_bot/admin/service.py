"""Admin service — query and manage orders.

All functions accept an AsyncSession. Pagination is done via LIMIT+OFFSET
with a fixed page size.
"""

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tg_order_bot.common.labels import status_label
from tg_order_bot.common.services import get_all_users
from tg_order_bot.database.models.enums import OrderStatus
from tg_order_bot.database.models.order import Order
from tg_order_bot.database.session import async_session_factory

logger = logging.getLogger(__name__)

# Number of orders shown per page in the admin panel.
ORDERS_PER_PAGE = 10

# Maps filter keys (from callback data) to sets of order statuses.
STATUS_FILTERS: dict[str, set[OrderStatus]] = {
    "all": set(OrderStatus),
    "new": {OrderStatus.NEW},
    "in_progress": {OrderStatus.CONFIRMED, OrderStatus.PAID, OrderStatus.SHIPPED},
    "done": {OrderStatus.DONE},
    "cancelled": {OrderStatus.CANCELLED},
}


def status_filter_label(key: str) -> str:
    """Human-readable label for a filter key."""
    return {
        "all": "Все",
        "new": "🆕 Новые",
        "in_progress": "⏳ В работе",
        "done": "✔️ Завершённые",
        "cancelled": "❌ Отменённые",
    }.get(key, key)


async def get_orders_page(
    session: AsyncSession,
    page: int = 0,
    status_filter: str = "all",
) -> tuple[list[Order], int]:
    """Return a page of orders plus total count for the given filter.

    Orders are sorted by creation time descending (newest first).
    """
    statuses = STATUS_FILTERS.get(status_filter, set(OrderStatus))

    base = select(Order).where(Order.status.in_(statuses))

    total = (
        await session.execute(
            select(func.count()).select_from(base.subquery())
        )
    ).scalar_one()

    stmt = (
        base.order_by(Order.created_at.desc())
        .offset(page * ORDERS_PER_PAGE)
        .limit(ORDERS_PER_PAGE)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all()), total


async def get_order_with_details(
    session: AsyncSession, order_id: int
) -> Order | None:
    """Return an order with items and user eagerly loaded."""
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.items),
            selectinload(Order.user),
        )
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def update_order_status(
    session: AsyncSession,
    order_id: int,
    new_status: OrderStatus,
) -> Order | None:
    """Update an order's status. Returns the order or None if not found."""
    order = await get_order_with_details(session, order_id)
    if order is None:
        return None

    order.status = new_status
    await session.commit()
    await session.refresh(order, attribute_names=["items", "user"])

    logger.info("Order #%d status -> %s", order.id, new_status.value)
    return order


async def broadcast_message(bot: Bot, text: str) -> tuple[int, int]:
    """Send ``text`` to every user. Returns (sent, failed) counts.

    Errors per user are logged and skipped so one failure doesn't stop
    the whole broadcast.
    """
    async with async_session_factory() as session:
        users = await get_all_users(session)

    sent = 0
    failed = 0
    for user in users:
        try:
            await bot.send_message(user.telegram_id, text)
            sent += 1
        except TelegramAPIError:
            failed += 1
            logger.warning(
                "Broadcast failed for user_id=%d (telegram_id=%d)",
                user.id,
                user.telegram_id,
            )

    logger.info("Broadcast finished: sent=%d, failed=%d", sent, failed)
    return sent, failed


__all__ = [
    "ORDERS_PER_PAGE",
    "STATUS_FILTERS",
    "broadcast_message",
    "get_order_with_details",
    "get_orders_page",
    "status_filter_label",
    "status_label",
    "update_order_status",
]

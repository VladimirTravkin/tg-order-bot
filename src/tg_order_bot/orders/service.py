"""Order service — create orders and notify admins.

``create_order`` takes a snapshot of the current cart: it copies product
name and price into OrderItem so historical orders stay accurate even
if the catalog changes later. The cart is emptied in the same
transaction.
"""

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from tg_order_bot.cart.service import clear_cart, get_cart_items
from tg_order_bot.common.labels import status_label
from tg_order_bot.config import get_settings
from tg_order_bot.database.models.enums import OrderStatus
from tg_order_bot.database.models.order import Order, OrderItem
from tg_order_bot.database.models.user import User

logger = logging.getLogger(__name__)


async def create_order(
    session: AsyncSession,
    user: User,
    customer_name: str,
    customer_phone: str,
    comment: str | None,
) -> Order | None:
    """Create an order from the user's current cart.

    Returns the created Order on success, or None if the cart is empty
    (nothing to order). The cart is cleared as part of the same
    transaction.

    Product name and price are snapshotted into OrderItem; the FK to
    products is nullable so historical orders survive product deletion.
    """
    items = await get_cart_items(session, user)
    if not items:
        return None

    total = sum((item.product.price * item.quantity) for item in items if item.product)

    order = Order(
        user_id=user.id,
        status=OrderStatus.NEW,
        total=total,
        customer_name=customer_name,
        customer_phone=customer_phone,
        comment=comment,
    )
    session.add(order)
    await session.flush()  # get order.id

    for item in items:
        if item.product is None:
            continue
        session.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                product_name=item.product.name,
                product_price=item.product.price,
                quantity=item.quantity,
            )
        )

    await clear_cart(session, user)
    await session.commit()
    await session.refresh(order)

    logger.info(
        "Order #%d created by user_id=%d, total=%s",
        order.id,
        user.id,
        order.total,
    )
    return order


def format_order_for_user(order: Order) -> str:
    """Human-readable summary of the order for the customer."""
    lines = [
        f"✅ <b>Заказ #{order.id} принят!</b>\n",
        f"👤 {order.customer_name}",
        f"📞 {order.customer_phone}",
    ]
    if order.comment:
        lines.append(f"💬 {order.comment}")

    lines.append("\n<b>Состав заказа:</b>")
    for idx, item in enumerate(order.items, start=1):
        subtotal = item.product_price * item.quantity
        lines.append(
            f"{idx}. {item.product_name} — {item.product_price} ₽ × {item.quantity} = {subtotal} ₽"
        )

    lines.append(f"\n<b>Итого: {order.total} ₽</b>")
    lines.append("\nМы свяжемся с вами для подтверждения.")
    return "\n".join(lines)


def format_order_for_admin(order: Order, user: User) -> str:
    """Summary of the order for admins (includes contact info)."""
    username = f"@{user.username}" if user.username else "без username"
    lines = [
        f"🆕 <b>Новый заказ #{order.id}</b>\n",
        f"👤 <b>Клиент:</b> {order.customer_name} ({username})",
        f"🆔 <b>Telegram ID:</b> <code>{user.telegram_id}</code>",
        f"📞 <b>Телефон:</b> {order.customer_phone}",
    ]
    if order.comment:
        lines.append(f"💬 <b>Комментарий:</b> {order.comment}")

    lines.append("\n<b>Состав:</b>")
    for idx, item in enumerate(order.items, start=1):
        subtotal = item.product_price * item.quantity
        lines.append(
            f"{idx}. {item.product_name} — {item.product_price} ₽ × {item.quantity} = {subtotal} ₽"
        )

    lines.append(f"\n💰 <b>Итого: {order.total} ₽</b>")
    lines.append(f"📊 <b>Статус:</b> {status_label(order.status)}")
    return "\n".join(lines)


async def notify_admins(bot: Bot, order: Order, user: User) -> None:
    """Send an order notification to every admin from settings.

    Errors per admin are logged and ignored so that one unreachable
    admin doesn't prevent the others from receiving the notification.
    """
    settings = get_settings()
    if not settings.admin_ids:
        logger.warning("No admins configured — skipping order notification")
        return

    text = format_order_for_admin(order, user)
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, text)
            logger.info("Order #%d notification sent to admin %d", order.id, admin_id)
        except TelegramAPIError:
            logger.exception("Failed to notify admin %d about order #%d", admin_id, order.id)


__all__ = [
    "create_order",
    "format_order_for_admin",
    "format_order_for_user",
    "notify_admins",
]

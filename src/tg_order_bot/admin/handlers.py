"""Handlers for the admin panel.

Access control is enforced by ``AdminFilterMiddleware`` attached to
this router in ``bot.py``. Handlers themselves don't check admin IDs.
"""

import logging
from typing import TypeGuard

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InaccessibleMessage, Message
from sqlalchemy.ext.asyncio import AsyncSession

from tg_order_bot.admin.callbacks import AdminCallback
from tg_order_bot.admin.keyboards import (
    get_admin_menu_keyboard,
    get_broadcast_confirm_keyboard,
    get_order_card_keyboard,
    get_orders_list_keyboard,
)
from tg_order_bot.admin.service import (
    broadcast_message,
    get_order_with_details,
    get_orders_page,
    status_filter_label,
    status_label,
    update_order_status,
)
from tg_order_bot.common.keyboards import BTN_ADMIN
from tg_order_bot.common.services import count_users
from tg_order_bot.database.models.enums import OrderStatus
from tg_order_bot.database.models.order import Order
from tg_order_bot.infrastructure.google_sheets import (
    GoogleSheetsError,
    export_orders,
)

logger = logging.getLogger(__name__)

router = Router(name="admin")


class BroadcastForm(StatesGroup):
    """FSM for the broadcast flow."""

    text = State()
    confirm = State()


def _is_editable(
    message: Message | InaccessibleMessage | None,
) -> TypeGuard[Message]:
    """Return True if the message can be edited by the bot."""
    return message is not None and not isinstance(message, InaccessibleMessage)


def _format_order_card(order: Order) -> str:
    """Format an order as HTML for the admin panel."""
    user = order.user
    username = f"@{user.username}" if user and user.username else "—"
    telegram_id = user.telegram_id if user else "—"

    lines = [
        f"📋 <b>Заказ #{order.id}</b>\n",
        f"👤 <b>Клиент:</b> {order.customer_name} ({username})",
        f"🆔 <b>Telegram ID:</b> <code>{telegram_id}</code>",
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
    lines.append(f"🕐 <b>Создан:</b> {order.created_at:%Y-%m-%d %H:%M}")
    return "\n".join(lines)


# === Entry points ===


@router.message(Command("admin"))
@router.message(F.text == BTN_ADMIN)
async def on_admin_button(message: Message) -> None:
    """Open the admin panel from the reply keyboard button or command."""
    await message.answer(
        "🔧 <b>Админ-панель</b>\n\nВыберите действие:",
        reply_markup=get_admin_menu_keyboard(),
    )


@router.callback_query(AdminCallback.filter(F.action == "menu"))
async def on_admin_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Return to the admin menu."""
    if not _is_editable(callback.message):
        await callback.answer()
        return

    await state.clear()
    await callback.message.edit_text(
        "🔧 <b>Админ-панель</b>\n\nВыберите действие:",
        reply_markup=get_admin_menu_keyboard(),
    )
    await callback.answer()


# === Orders list ===


@router.callback_query(AdminCallback.filter(F.action == "orders_list"))
async def on_orders_list(
    callback: CallbackQuery,
    callback_data: AdminCallback,
    session: AsyncSession,
) -> None:
    """Show the orders list with the selected filter and first page."""
    if not _is_editable(callback.message):
        await callback.answer()
        return

    status_filter = callback_data.status_filter or "all"
    orders, total = await get_orders_page(session, page=0, status_filter=status_filter)

    await _render_orders_list(callback, orders, page=0, total=total, status_filter=status_filter)


@router.callback_query(AdminCallback.filter(F.action == "orders_page"))
async def on_orders_page(
    callback: CallbackQuery,
    callback_data: AdminCallback,
    session: AsyncSession,
) -> None:
    """Paginate the orders list."""
    if not _is_editable(callback.message):
        await callback.answer()
        return

    status_filter = callback_data.status_filter or "all"
    orders, total = await get_orders_page(
        session, page=callback_data.page, status_filter=status_filter
    )

    await _render_orders_list(
        callback,
        orders,
        page=callback_data.page,
        total=total,
        status_filter=status_filter,
    )


async def _render_orders_list(
    callback: CallbackQuery,
    orders: list[Order],
    page: int,
    total: int,
    status_filter: str,
) -> None:
    """Common rendering for the orders list + filters.

    Wraps edit_text in try/except so that re-opening the same filter
    (e.g. tapping the active filter twice) does not crash the bot with
    "message is not modified".
    """
    if not _is_editable(callback.message):
        await callback.answer()
        return

    label = status_filter_label(status_filter)

    if total == 0:
        text = f"📋 <b>Заказы — {label}</b>\n\nПока нет заказов в этой категории."
        markup = get_orders_list_keyboard(orders, page, total, status_filter)
    else:
        text = (
            f"📋 <b>Заказы — {label}</b>\n"
            f"Всего: {total}\n\n"
            "Нажмите на заказ, чтобы открыть карточку."
        )
        markup = get_orders_list_keyboard(orders, page, total, status_filter)

    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            # Same content — silently ignore, just acknowledge the callback.
            pass
        else:
            raise

    await callback.answer()


# === Order card ===


@router.callback_query(AdminCallback.filter(F.action == "order_view"))
async def on_order_view(
    callback: CallbackQuery,
    callback_data: AdminCallback,
    session: AsyncSession,
) -> None:
    """Show the order card."""
    if not _is_editable(callback.message) or callback_data.order_id is None:
        await callback.answer()
        return

    order = await get_order_with_details(session, callback_data.order_id)
    if order is None:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    await callback.message.edit_text(
        _format_order_card(order),
        reply_markup=get_order_card_keyboard(order),
    )
    await callback.answer()


# === Change status ===


@router.callback_query(AdminCallback.filter(F.action == "order_status"))
async def on_order_status(
    callback: CallbackQuery,
    callback_data: AdminCallback,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """Change an order status and notify the customer."""
    if (
        not _is_editable(callback.message)
        or callback_data.order_id is None
        or callback_data.status is None
    ):
        await callback.answer()
        return

    try:
        new_status = OrderStatus(callback_data.status)
    except ValueError:
        await callback.answer("Неизвестный статус", show_alert=True)
        return

    order = await update_order_status(session, callback_data.order_id, new_status)
    if order is None:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    # Notify customer (best-effort).
    if order.user is not None:
        await _notify_customer(bot, order)

    await callback.message.edit_text(
        _format_order_card(order),
        reply_markup=get_order_card_keyboard(order),
    )
    await callback.answer(f"Статус: {status_label(new_status)}")


async def _notify_customer(bot: Bot, order: Order) -> None:
    """Send a status update to the customer (best-effort)."""
    messages = {
        OrderStatus.CONFIRMED: "✅ Ваш заказ #%d подтверждён!",
        OrderStatus.PAID: "💰 Оплата по заказу #%d получена.",
        OrderStatus.SHIPPED: "📦 Заказ #%d отправлен!",
        OrderStatus.DONE: "✔️ Заказ #%d выполнен. Спасибо!",
        OrderStatus.CANCELLED: "❌ Заказ #%d отменён.",
    }
    template = messages.get(order.status)
    if template is None or order.user is None:
        return

    try:
        await bot.send_message(order.user.telegram_id, template % order.id)
    except Exception:
        logger.exception("Failed to notify customer about order #%d status change", order.id)


# === Export to Google Sheets ===


@router.callback_query(AdminCallback.filter(F.action == "export_sheets"))
async def on_export_sheets(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Export all orders to the configured Google Sheet."""
    if not _is_editable(callback.message):
        await callback.answer()
        return

    await callback.answer("⏳ Выгружаю в Google Sheets...")

    try:
        written, timestamp = await export_orders(session)
    except GoogleSheetsError as exc:
        logger.exception("Google Sheets export failed")
        await callback.message.edit_text(
            f"❌ <b>Ошибка выгрузки</b>\n\n<code>{exc}</code>",
            reply_markup=get_admin_menu_keyboard(),
        )
        return

    await callback.message.edit_text(
        f"✅ <b>Выгружено в Google Sheets</b>\n\nЗаказов: <b>{written}</b>\nВремя: {timestamp}",
        reply_markup=get_admin_menu_keyboard(),
    )


# === Broadcast ===


# === Broadcast ===


@router.callback_query(AdminCallback.filter(F.action == "broadcast"))
async def on_broadcast_start(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Start broadcast: ask for the message text."""
    if not _is_editable(callback.message):
        await callback.answer()
        return

    total_users = await count_users(session)
    await state.set_state(BroadcastForm.text)

    await callback.message.edit_text(
        f"📢 <b>Рассылка</b>\n\n"
        f"Всего получателей: <b>{total_users}</b>\n\n"
        f"Отправьте текст сообщения (HTML поддерживается).\n"
        f"Отмена: /cancel",
    )
    await callback.answer()


@router.message(BroadcastForm.text, Command("cancel"))
async def on_broadcast_cancel_command(message: Message, state: FSMContext) -> None:
    """Cancel broadcast via /cancel."""
    await state.clear()
    await message.answer(
        "❌ Рассылка отменена.",
        reply_markup=get_admin_menu_keyboard(),
    )


@router.message(BroadcastForm.text)
async def on_broadcast_text(message: Message, state: FSMContext) -> None:
    """Store the broadcast text and ask for confirmation."""
    if message.text is None:
        return

    await state.update_data(text=message.text)
    await state.set_state(BroadcastForm.confirm)

    preview = message.text
    if len(preview) > 500:
        preview = preview[:500] + "..."

    await message.answer(
        f"📢 <b>Предпросмотр:</b>\n\n{preview}\n\nОтправить всем пользователям?",
        reply_markup=get_broadcast_confirm_keyboard(),
    )


@router.callback_query(BroadcastForm.confirm, AdminCallback.filter(F.action == "broadcast_confirm"))
async def on_broadcast_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Send the broadcast to all users."""
    if not _is_editable(callback.message):
        await callback.answer()
        return

    data = await state.get_data()
    text = data.get("text")
    await state.clear()

    if not text:
        await callback.answer("Текст не найден", show_alert=True)
        return

    await callback.message.edit_text("📢 Отправка... Это может занять время.")
    sent, failed = await broadcast_message(bot, text)

    await callback.message.edit_text(
        f"✅ <b>Рассылка завершена</b>\n\nДоставлено: {sent}\nОшибок: {failed}",
        reply_markup=get_admin_menu_keyboard(),
    )
    await callback.answer()


__all__ = ["router"]

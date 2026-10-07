"""Inline keyboards for the admin panel."""

from math import ceil

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tg_order_bot.admin.callbacks import AdminCallback
from tg_order_bot.admin.service import (
    ORDERS_PER_PAGE,
    status_filter_label,
    status_label,
)
from tg_order_bot.database.models.enums import OrderStatus
from tg_order_bot.database.models.order import Order

# Available filter keys for the orders list (must match STATUS_FILTERS).
FILTER_KEYS = ("all", "new", "in_progress", "done", "cancelled")


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu of the admin panel."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📋 Заказы",
            callback_data=AdminCallback(action="orders_list", status_filter="all").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📢 Рассылка",
            callback_data=AdminCallback(action="broadcast").pack(),
        )
    )
    return builder.as_markup()


def get_orders_filter_keyboard(active_filter: str = "all") -> InlineKeyboardMarkup:
    """Filter row for the orders list.

    The active filter is marked with a bullet (•) so the admin sees
    which one is currently applied.
    """
    builder = InlineKeyboardBuilder()
    for key in FILTER_KEYS:
        label = status_filter_label(key)
        text = f"• {label}" if key == active_filter else label
        builder.button(
            text=text,
            callback_data=AdminCallback(action="orders_list", status_filter=key).pack(),
        )
    builder.adjust(2)
    return builder.as_markup()


def get_orders_list_keyboard(
    orders: list[Order],
    page: int,
    total: int,
    status_filter: str,
) -> InlineKeyboardMarkup:
    """List of orders with pagination controls.

    Each order is a button; the last two rows hold navigation.
    """
    builder = InlineKeyboardBuilder()

    for order in orders:
        builder.row(
            InlineKeyboardButton(
                text=f"#{order.id} — {order.total} ₽ ({status_label(order.status)})",
                callback_data=AdminCallback(
                    action="order_view", order_id=order.id
                ).pack(),
            )
        )

    # Pagination
    total_pages = max(1, ceil(total / ORDERS_PER_PAGE))
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=AdminCallback(
                    action="orders_page",
                    status_filter=status_filter,
                    page=page - 1,
                ).pack(),
            )
        )
    nav_buttons.append(
        InlineKeyboardButton(
            text=f"Стр. {page + 1}/{total_pages}",
            callback_data=AdminCallback(
                action="orders_list", status_filter=status_filter
            ).pack(),
        )
    )
    if page + 1 < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперёд ▶️",
                callback_data=AdminCallback(
                    action="orders_page",
                    status_filter=status_filter,
                    page=page + 1,
                ).pack(),
            )
        )
    builder.row(*nav_buttons)

    # Back to filters
    builder.row(
        InlineKeyboardButton(
            text="◀️ К фильтрам",
            callback_data=AdminCallback(
                action="orders_list", status_filter="all"
            ).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🏠 Меню админа",
            callback_data=AdminCallback(action="menu").pack(),
        )
    )
    return builder.as_markup()


def get_order_card_keyboard(order: Order) -> InlineKeyboardMarkup:
    """Keyboard for an order card: change-status buttons + back."""
    builder = InlineKeyboardBuilder()

    # One row per status (skip current status)
        # One row per status (skip current status)
    for status in OrderStatus:
        if status == order.status:
            continue
        builder.row(
            InlineKeyboardButton(
                text=f"→ {status_label(status)}",
                callback_data=AdminCallback(
                    action="order_status",
                    order_id=order.id,
                    status=status.value,
                ).pack(),
            )
        )

    # Back to list (all filter)
    builder.row(
        InlineKeyboardButton(
            text="◀️ К списку",
            callback_data=AdminCallback(
                action="orders_list", status_filter="all"
            ).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🏠 Меню админа",
            callback_data=AdminCallback(action="menu").pack(),
        )
    )
    return builder.as_markup()


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirmation keyboard for broadcast."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Отправить",
            callback_data=AdminCallback(action="broadcast").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=AdminCallback(action="menu").pack(),
        )
    )
    return builder.as_markup()

__all__ = [
    "FILTER_KEYS",
    "get_admin_menu_keyboard",
    "get_broadcast_confirm_keyboard",
    "get_order_card_keyboard",
    "get_orders_filter_keyboard",
    "get_orders_list_keyboard",
]

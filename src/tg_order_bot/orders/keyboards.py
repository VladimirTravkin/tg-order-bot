"""Inline keyboards for the checkout flow.

Three keyboards cover all FSM steps:

- :func:`get_cancel_keyboard` — used on the name and phone steps
- :func:`get_skip_or_cancel_keyboard` — used on the comment step
- :func:`get_confirm_keyboard` — used on the confirmation step
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tg_order_bot.orders.callbacks import OrderCallback


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Single "cancel" button — for name and phone steps."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Отменить",
        callback_data=OrderCallback(action="cancel"),
    )
    return builder.as_markup()


def get_skip_or_cancel_keyboard() -> InlineKeyboardMarkup:
    """Two buttons: skip comment, or cancel the checkout."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⏭ Пропустить",
            callback_data=OrderCallback(action="skip").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data=OrderCallback(action="cancel").pack(),
        )
    )
    return builder.as_markup()


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Two buttons: confirm the order, or cancel."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data=OrderCallback(action="confirm").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data=OrderCallback(action="cancel").pack(),
        )
    )
    return builder.as_markup()


__all__ = [
    "get_cancel_keyboard",
    "get_confirm_keyboard",
    "get_skip_or_cancel_keyboard",
]

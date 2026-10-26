"""Persistent reply keyboard shown at the bottom of the chat.

Buttons mirror the main sections of the bot: catalog, cart, help,
plus an "Admin" button shown only to admins.
"""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Text labels used both in buttons and in handlers' filters.
BTN_CATALOG = "🛍 Каталог"
BTN_CART = "🛒 Корзина"
BTN_HELP = "💬 Помощь"
BTN_ADMIN = "🔧 Админ"
BTN_START = "🚀 Запустить бота"


def get_main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Build the main menu reply keyboard.

    ``is_admin`` controls whether the "🔧 Админ" button is included.
    ``resize_keyboard=True`` shrinks buttons to fit the screen.
    """
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=BTN_CATALOG),
        KeyboardButton(text=BTN_CART),
    )
    if is_admin:
        builder.row(KeyboardButton(text=BTN_ADMIN))
    builder.row(KeyboardButton(text=BTN_HELP))
    builder.row(KeyboardButton(text=BTN_START))
    return builder.as_markup(resize_keyboard=True)


__all__ = [
    "BTN_ADMIN",
    "BTN_CART",
    "BTN_CATALOG",
    "BTN_HELP",
    "BTN_START",
    "get_main_menu_keyboard",
]

"""Persistent reply keyboard shown at the bottom of the chat.

Buttons mirror the main sections of the bot: catalog, cart, help.
"""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Text labels used both in buttons and in handlers' filters.
BTN_CATALOG = "📦 Каталог"
BTN_CART = "🛒 Корзина"
BTN_HELP = "❓ Помощь"


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Build the main menu reply keyboard.

    Two rows: first has catalog and cart, second has a single help
    button. ``resize_keyboard=True`` shrinks buttons to fit the screen.
    """
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=BTN_CATALOG),
        KeyboardButton(text=BTN_CART),
    )
    builder.row(KeyboardButton(text=BTN_HELP))
    return builder.as_markup(resize_keyboard=True)


__all__ = ["BTN_CART", "BTN_CATALOG", "BTN_HELP", "get_main_menu_keyboard"]

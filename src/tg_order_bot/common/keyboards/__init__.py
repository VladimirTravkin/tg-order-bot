"""Reusable keyboards for the bot.

Reply keyboards are attached to messages and replace the device's
native keyboard. Inline keyboards are attached to messages and appear
directly under them.
"""

from tg_order_bot.common.keyboards.main_menu import (
    BTN_CART,
    BTN_CATALOG,
    BTN_HELP,
    get_main_menu_keyboard,
)

__all__ = ["BTN_CART", "BTN_CATALOG", "BTN_HELP", "get_main_menu_keyboard"]

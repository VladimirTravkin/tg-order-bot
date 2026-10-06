"""Callback data schemas for the order flow."""

from typing import Literal

from aiogram.filters.callback_data import CallbackData


class OrderCallback(CallbackData, prefix="order"):
    """Callback for checkout actions.

    ``action`` distinguishes what the user pressed:

    - ``start``   — begin checkout (from cart)
    - ``cancel``  — cancel checkout at any step
    - ``skip``    — skip the optional comment step
    - ``confirm`` — confirm and create the order
    - ``use_default_name`` — accept the Telegram name as-is
    """

    action: Literal["start", "cancel", "skip", "confirm", "use_default_name"]


__all__ = ["OrderCallback"]

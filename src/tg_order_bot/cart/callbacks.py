"""Callback data schemas for the cart.

All cart actions share a single factory with a prefix of ``cart``.
The ``product_id`` field is only used by ``add`` and ``remove``.
"""

from typing import Literal

from aiogram.filters.callback_data import CallbackData


class CartCallback(CallbackData, prefix="cart"):
    """Callback for cart operations.

    ``action`` distinguishes what the user pressed:

    - ``add``    — add product (``product_id``) to the cart
    - ``view``   — show the cart
    - ``remove`` — remove product (``product_id``) from the cart
    - ``clear``  — empty the entire cart
    """

    action: Literal["add", "view", "remove", "clear"]
    product_id: int | None = None


__all__ = ["CartCallback"]

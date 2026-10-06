"""Callback data schemas for the admin panel.

A single factory covers all admin actions. Most fields are optional
and only used by the relevant action:

- ``menu``         — show the admin main menu
- ``orders_list``  — show a list of orders (uses ``status_filter``)
- ``orders_page``  — paginate the list (uses ``status_filter`` and ``page``)
- ``order_view``   — open a single order card (uses ``order_id``)
- ``order_status`` — change an order's status (uses ``order_id`` and ``status``)
- ``broadcast``    — start a broadcast (no extra fields)
"""

from typing import Literal

from aiogram.filters.callback_data import CallbackData


class AdminCallback(CallbackData, prefix="admin"):
    """Callback for admin panel actions."""

    action: Literal[
        "menu",
        "orders_list",
        "orders_page",
        "order_view",
        "order_status",
        "broadcast",
    ]
    status_filter: str | None = None
    page: int = 0
    order_id: int | None = None
    status: str | None = None


__all__ = ["AdminCallback"]

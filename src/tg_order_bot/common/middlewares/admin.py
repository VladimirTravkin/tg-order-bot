"""Middleware that restricts access to handlers by admin ID.

Applied to the admin router in ``bot.py``. Non-admins are silently
ignored: no response, no error, no hint that the bot has admin
functionality.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from tg_order_bot.config import get_settings


class AdminFilterMiddleware(BaseMiddleware):
    """Pass updates only from Telegram IDs listed in ``ADMIN_IDS``.

    Uses ``data["event_from_user"]`` (populated by aiogram) to check
    the sender. If the sender is missing or not an admin, the update
    is dropped without invoking the handler.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        settings = get_settings()
        user = data.get("event_from_user")

        if user is None or user.id not in settings.admin_ids:
            return None

        return await handler(event, data)


__all__ = ["AdminFilterMiddleware"]

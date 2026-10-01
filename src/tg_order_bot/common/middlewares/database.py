"""Middleware that provides a database session to handlers.

Each incoming update gets its own ``AsyncSession``, which is opened
before the handler runs and closed automatically afterwards. Handlers
receive the session via the ``session`` key in the data dict.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from tg_order_bot.database.session import async_session_factory


class DbSessionMiddleware(BaseMiddleware):
    """Inject an AsyncSession into handler data.

    The session is scoped to a single update — it is created just
    before the handler chain runs and closed in a ``finally`` block
    regardless of whether the handler raised.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with async_session_factory() as session:
            data["session"] = session
            return await handler(event, data)


__all__ = ["DbSessionMiddleware"]

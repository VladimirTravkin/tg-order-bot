"""Aiogram middlewares for the application.

Middlewares intercept updates before they reach handlers, allowing
cross-cutting concerns such as database sessions, rate limiting,
and admin access to be handled in one place.
"""

from tg_order_bot.common.middlewares.admin import AdminFilterMiddleware
from tg_order_bot.common.middlewares.database import DbSessionMiddleware
from tg_order_bot.common.middlewares.throttling import ThrottlingMiddleware

__all__ = [
    "AdminFilterMiddleware",
    "DbSessionMiddleware",
    "ThrottlingMiddleware",
]

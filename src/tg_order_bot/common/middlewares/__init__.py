"""Aiogram middlewares for the application.

Middlewares intercept updates before they reach handlers, allowing
cross-cutting concerns such as database sessions and rate limiting
to be handled in one place.
"""

from tg_order_bot.common.middlewares.database import DbSessionMiddleware

__all__ = ["DbSessionMiddleware"]

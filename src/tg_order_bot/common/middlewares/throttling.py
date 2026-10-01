"""Middleware that limits how often a single user can trigger handlers.

Uses Redis ``SET key value NX PX <ttl>`` as an atomic "acquire or skip"
operation. If the key already exists, the update is silently dropped.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

import redis.asyncio as aioredis
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from tg_order_bot.config import get_settings

logger = logging.getLogger(__name__)

# Rate limit: one update per user per this many milliseconds.
THROTTLE_TTL_MS = 600

# Redis key prefix — keeps throttle keys namespaced.
KEY_PREFIX = "throttle:"


class ThrottlingMiddleware(BaseMiddleware):
    """Rate-limit updates from the same Telegram user.

    Uses an atomic Redis SET NX PX operation so that concurrent updates
    from the same user cannot both acquire the slot.

    The Redis client is created lazily on first update to avoid opening
    a connection during module import (important for tests).
    """

    def __init__(self) -> None:
        """Create the middleware; the Redis client is created lazily."""
        self._redis: aioredis.Redis | None = None

    def _get_redis(self) -> aioredis.Redis:
        """Return the Redis client, creating it on first call."""
        if self._redis is None:
            settings = get_settings()
            self._redis = aioredis.Redis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
        return self._redis

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        if user is None:
            # Can't throttle without a user — let the update through.
            return await handler(event, data)

        redis = self._get_redis()
        key = f"{KEY_PREFIX}{user.id}"

        # Atomic: set only if not exists, with TTL. Returns None if key
        # already existed → the update is too soon.
        acquired = await redis.set(key, "1", px=THROTTLE_TTL_MS, nx=True)
        if acquired is None:
            logger.debug("Throttled update from user_id=%d", user.id)
            return None

        return await handler(event, data)


__all__ = ["ThrottlingMiddleware"]

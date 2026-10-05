"""Bot and dispatcher factory.

Provides functions to construct the aiogram ``Bot`` and ``Dispatcher``
instances, and to register all routers. Kept separate from the entry
point so that tests and tooling can create a bot without starting it.
"""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from tg_order_bot.catalog.handlers import router as catalog_router
from tg_order_bot.common.handlers import router as common_router
from tg_order_bot.common.middlewares import DbSessionMiddleware, ThrottlingMiddleware
from tg_order_bot.config import get_settings
from tg_order_bot.database.session import engine

settings = get_settings()


def create_bot() -> Bot:
    """Create and return a Bot instance.

    Uses HTML as the default parse mode for outgoing messages.
    """
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    """Create and return a Dispatcher with Redis-backed FSM storage.

    Registers middlewares and includes all routers. The order of
    routers matters: more specific ones should come first.
    """
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)

    # Middlewares: DB session for every update.
    dp.update.outer_middleware(DbSessionMiddleware())

    # Throttling: only for messages (spam protection).
    dp.message.middleware(ThrottlingMiddleware())

    # Routers
    dp.include_router(common_router)
    dp.include_router(catalog_router)

    return dp


async def shutdown(bot: Bot, dp: Dispatcher) -> None:
    """Release resources held by the bot and dispatcher.

    Closes the Telegram HTTP session, the FSM storage connection, and
    disposes the database engine.
    """
    await bot.session.close()
    await dp.storage.close()
    await engine.dispose()

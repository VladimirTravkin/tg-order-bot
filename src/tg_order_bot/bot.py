"""Bot and dispatcher factory.

Provides functions to construct the aiogram ``Bot`` and ``Dispatcher``
instances, and to register all handlers. Kept separate from the entry
point so that tests and tooling can create a bot without starting it.
"""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message

from tg_order_bot.common.middlewares import DbSessionMiddleware
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

    Handlers are registered by calling :func:`register_handlers`.
    Middlewares are registered here as well — they apply to all
    incoming updates.
    """
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)

    # Middlewares: DB session for every update.
    dp.update.outer_middleware(DbSessionMiddleware())

    register_handlers(dp)
    return dp


def register_handlers(dp: Dispatcher) -> None:
    """Register all handlers on the given dispatcher.

    Currently only a placeholder ``/start`` handler is registered.
    Real handlers will be added in subsequent steps.
    """

    @dp.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        """Handle the /start command with a welcome message."""
        if message.from_user is None:
            return
        await message.answer(
            f"Привет, {message.from_user.full_name}!\n\n"
            "Я бот для приёма заказов. Скоро здесь появятся каталог, "
            "корзина и оформление заказа. Stay tuned!"
        )


async def shutdown(bot: Bot, dp: Dispatcher) -> None:
    """Release resources held by the bot and dispatcher.

    Closes the Telegram HTTP session, the FSM storage connection, and
    disposes the database engine.
    """
    await bot.session.close()
    await dp.storage.close()
    await engine.dispose()

"""Application entry point.

Run with::

    python -m tg_order_bot

or via the Makefile::

    make run
"""

import asyncio
import logging
from contextlib import suppress

from tg_order_bot.bot import create_bot, create_dispatcher, shutdown
from tg_order_bot.common.logging import setup_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    """Start the bot and run polling until interrupted."""
    setup_logging()
    logger.info("Starting bot...")

    bot = create_bot()
    dp = create_dispatcher()

    try:
        me = await bot.get_me()
        logger.info("Bot started as @%s (id=%d)", me.username, me.id)

        await dp.start_polling(bot)

    except asyncio.CancelledError:
        logger.info("Bot stopped by cancellation")
        raise
    finally:
        logger.info("Shutting down...")
        await shutdown(bot, dp)
        logger.info("Goodbye")


def run() -> None:
    """Synchronous wrapper for ``main`` — used by ``python -m``."""
    # Ctrl+C is a normal way to stop the bot in development.
    with suppress(KeyboardInterrupt):
        asyncio.run(main())


if __name__ == "__main__":
    run()

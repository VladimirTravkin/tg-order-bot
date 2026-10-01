"""Logging configuration for the application.

Provides a single ``setup_logging`` entry point that configures the root
logger with a human-readable format. Called once at application startup.
"""

import logging
import sys

from tg_order_bot.config import get_settings

# Format: "2026-09-30 14:30:00 | INFO     | tg_order_bot.bot | Bot started"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Third-party loggers that are too noisy at INFO level.
NOISY_LOGGERS = (
    "aiogram",
    "aiogram.event",
    "aiogram.dispatcher",
    "asyncio",
    "sqlalchemy.engine",
    "httpx",
    "httpcore",
    "redis",
    "redis.asyncio",
)


def setup_logging() -> None:
    """Configure the root logger for the application.

    Reads the log level from application settings, sets up a single
    StreamHandler writing to stdout, and silences noisy third-party
    loggers by raising their level to WARNING.

    This function should be called once at application startup, before
    any other modules emit log records.
    """
    settings = get_settings()

    logging.basicConfig(
        level=settings.log_level.upper(),
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        stream=sys.stdout,
        force=True,
    )

    for logger_name in NOISY_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

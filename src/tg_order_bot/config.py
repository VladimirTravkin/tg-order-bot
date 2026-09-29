"""Application settings loaded from environment variables.

Settings are validated at startup via pydantic-settings. Missing or malformed
values cause the application to fail fast with a clear error message.
"""

import re
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration.

    Values are read from environment variables or a local ``.env`` file.
    See ``.env.example`` for the full list of supported variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === Telegram ===
    bot_token: str = Field(
        ...,
        description="Telegram bot token issued by @BotFather",
    )
    admin_ids: Annotated[list[int], NoDecode] = Field(
        default_factory=list,
        description="Telegram user IDs with admin access (comma-separated)",
    )

    # === Database ===
    database_url: str = Field(
        ...,
        description="PostgreSQL DSN, e.g. postgresql+asyncpg://user:pass@host:5432/db",
    )

    # === Redis ===
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis DSN used for FSM state storage",
    )

    # === Application ===
    environment: str = Field(
        default="dev",
        description="Runtime environment: 'dev' or 'prod'",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR",
    )

    @field_validator("bot_token")
    @classmethod
    def _validate_bot_token(cls, value: str) -> str:
        """Ensure the bot token looks like a real Telegram token."""
        pattern = r"^\d+:[A-Za-z0-9_-]+$"
        if not re.match(pattern, value):
            raise ValueError(
                "BOT_TOKEN has invalid format. Expected '123456789:ABCdef...'"
            )
        return value

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value: object) -> object:
        """Parse comma-separated string of admin IDs into a list of ints."""
        if isinstance(value, str):
            if not value.strip():
                return []
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance.

    The cache ensures the .env file is parsed only once per process.
    """
    return Settings()  # type: ignore[call-arg]

"""Reusable service functions shared across domains."""

from tg_order_bot.common.services.users import (
    count_users,
    get_all_users,
    get_or_create_user,
)

__all__ = ["count_users", "get_all_users", "get_or_create_user"]

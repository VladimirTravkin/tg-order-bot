"""Reusable service functions shared across domains.

Services encapsulate data-access logic that is not tied to a single
bot domain (e.g. cart, orders, admin). They accept an ``AsyncSession``
as the first argument and return ORM instances.
"""

from tg_order_bot.common.services.users import get_or_create_user

__all__ = ["get_or_create_user"]

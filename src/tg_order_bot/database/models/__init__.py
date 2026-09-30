"""ORM models for the application.

All model classes must be imported here so that Alembic can discover
them via ``Base.metadata`` for autogeneration of migrations.
"""

from tg_order_bot.database.models.cart import CartItem
from tg_order_bot.database.models.catalog import Category, Product
from tg_order_bot.database.models.enums import OrderStatus
from tg_order_bot.database.models.mixins import TimestampMixin
from tg_order_bot.database.models.order import Order, OrderItem
from tg_order_bot.database.models.user import User

__all__ = [
    "CartItem",
    "Category",
    "Order",
    "OrderItem",
    "OrderStatus",
    "Product",
    "TimestampMixin",
    "User",
]

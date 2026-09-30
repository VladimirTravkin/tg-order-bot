"""Enumerations used across ORM models."""

from enum import StrEnum


class OrderStatus(StrEnum):
    """Lifecycle states of an order.

    Inherits from ``str`` so values can be serialized to JSON and stored
    as plain strings in the database (``native_enum=False``).
    """

    NEW = "new"
    CONFIRMED = "confirmed"
    PAID = "paid"
    SHIPPED = "shipped"
    DONE = "done"
    CANCELLED = "cancelled"

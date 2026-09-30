"""Tests for ORM model metadata and structure.

These tests do not connect to a database — they verify the declarative
metadata that SQLAlchemy builds from the model definitions.
"""

import pytest
from sqlalchemy import inspect

from tg_order_bot.database.base import Base
from tg_order_bot.database.models import (
    CartItem,
    Category,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    User,
)


def test_all_tables_registered() -> None:
    """Ensure every expected table is present in Base.metadata."""
    expected = {
        "cart_items",
        "categories",
        "order_items",
        "orders",
        "products",
        "users",
    }
    assert set(Base.metadata.tables.keys()) == expected


def test_user_telegram_id_is_unique() -> None:
    """Ensure users.telegram_id is unique and indexed."""
    columns = inspect(User).columns
    assert columns["telegram_id"].unique is True
    assert columns["telegram_id"].index is True


def test_product_price_uses_numeric() -> None:
    """Ensure product price uses NUMERIC(10, 2), not FLOAT."""
    col_type = inspect(Product).columns["price"].type
    assert getattr(col_type, "precision", None) == 10
    assert getattr(col_type, "scale", None) == 2


def test_order_status_default_is_new() -> None:
    """Ensure a new order defaults to OrderStatus.NEW."""
    column = inspect(Order).columns["status"]
    assert column.default is not None
    assert getattr(column.default, "arg", None) == OrderStatus.NEW


def test_order_item_product_id_is_nullable() -> None:
    """Ensure order_items.product_id is nullable (SET NULL on delete)."""
    column = inspect(OrderItem).columns["product_id"]
    assert column.nullable is True


def test_cart_item_has_unique_constraint() -> None:
    """Ensure cart_items has a unique (user_id, product_id) constraint."""
    mapper = inspect(CartItem)
    table = getattr(mapper, "local_table", None)
    assert table is not None
    unique_names = {
        c.name for c in table.constraints if c.__class__.__name__ == "UniqueConstraint"
    }
    assert "uq_cart_user_product" in unique_names


@pytest.mark.parametrize(
    "status",
    ["new", "confirmed", "paid", "shipped", "done", "cancelled"],
)
def test_order_status_values(status: str) -> None:
    """Ensure every expected OrderStatus value is defined."""
    assert status in {s.value for s in OrderStatus}


def test_category_is_active_default_true() -> None:
    """Ensure categories default to active."""
    column = inspect(Category).columns["is_active"]
    assert column.default is not None
    assert getattr(column.default, "arg", None) is True

"""Tests for ``infrastructure.google_sheets``.

Only the pure-python helpers are exercised here. Real API calls
require Google credentials and are covered by manual smoke tests.
"""

from datetime import datetime
from decimal import Decimal

from tg_order_bot.database.models.enums import OrderStatus
from tg_order_bot.database.models.order import Order, OrderItem
from tg_order_bot.infrastructure.google_sheets import (
    HEADERS,
    _format_products,
    _order_to_row,
)


def _make_order() -> Order:
    """In-memory Order with two items (no DB)."""
    order = Order(
        id=42,
        status=OrderStatus.SHIPPED,
        total=Decimal("1280.00"),
        customer_name="Иван Иванов",
        customer_phone="+79991234567",
        comment=None,
        created_at=datetime(2026, 10, 8, 12, 30),
    )
    order.items = [
        OrderItem(
            id=1,
            order_id=42,
            product_id=1,
            product_name="Маргарита",
            product_price=Decimal("590.00"),
            quantity=1,
        ),
        OrderItem(
            id=2,
            order_id=42,
            product_id=2,
            product_name="Пепперони",
            product_price=Decimal("690.00"),
            quantity=1,
        ),
    ]
    return order


def test_headers_are_stable() -> None:
    """HEADERS is the contract between exporter and spreadsheet."""
    assert HEADERS == [
        "#",
        "Дата",
        "Клиент",
        "Телефон",
        "Статус",
        "Товары",
        "Итого, ₽",
    ]


def test_format_products_snapshot() -> None:
    """_format_products joins items as 'Name×Qty, ...'."""
    order = _make_order()
    assert _format_products(order) == "Маргарита×1, Пепперони×1"


def test_order_to_row_uses_russian_status() -> None:
    """_order_to_row uses status_label (Russian), not raw enum value."""
    order = _make_order()
    row = _order_to_row(order)

    assert row[0] == "42"
    assert row[1].startswith("2026-10-08")
    assert row[2] == "Иван Иванов"
    assert row[3] == "+79991234567"
    assert "Отправлен" in row[4]  # Russian label, not "shipped"
    assert row[5] == "Маргарита×1, Пепперони×1"
    assert row[6] == "1280.00"

"""Tests for ``common.labels``."""

from tg_order_bot.common.labels import STATUS_LABELS, status_label
from tg_order_bot.database.models.enums import OrderStatus


def test_status_label_covers_every_status() -> None:
    """Every OrderStatus has a label."""
    for status in OrderStatus:
        assert status in STATUS_LABELS


def test_status_label_returns_russian_text() -> None:
    """Labels are not the raw values (Russian text expected)."""
    for status in OrderStatus:
        label = status_label(status)
        assert label != status.value
        # Cyrillic letters present
        assert any("\u0400" <= ch <= "\u04FF" for ch in label)


def test_status_label_specific_values() -> None:
    """Sanity-check a few known values."""
    assert "Новый" in status_label(OrderStatus.NEW)
    assert "Отправлен" in status_label(OrderStatus.SHIPPED)
    assert "Отменён" in status_label(OrderStatus.CANCELLED)

"""Human-readable labels for enums used across the UI.

Kept in ``common`` so any layer (admin, orders, google_sheets) can
reuse them without depending on each other.
"""

from tg_order_bot.database.models.enums import OrderStatus

# Human-readable labels for order statuses.
STATUS_LABELS: dict[OrderStatus, str] = {
    OrderStatus.NEW: "🆕 Новый",
    OrderStatus.CONFIRMED: "✅ Подтверждён",
    OrderStatus.PAID: "💰 Оплачен",
    OrderStatus.SHIPPED: "📦 Отправлен",
    OrderStatus.DONE: "✔️ Завершён",
    OrderStatus.CANCELLED: "❌ Отменён",
}


def status_label(status: OrderStatus) -> str:
    """Return a human-readable label for an order status."""
    return STATUS_LABELS.get(status, status.value)


__all__ = ["STATUS_LABELS", "status_label"]

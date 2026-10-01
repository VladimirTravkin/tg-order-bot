"""Order models — placed orders and their line items."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tg_order_bot.database.base import Base
from tg_order_bot.database.models.enums import OrderStatus
from tg_order_bot.database.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from tg_order_bot.database.models.catalog import Product
    from tg_order_bot.database.models.user import User


class Order(Base, TimestampMixin):
    """A customer order.

    Stores a snapshot of the customer's contact details at checkout time
    (``customer_name``, ``customer_phone``) so that later profile changes
    do not affect historical orders. ``total`` is also a snapshot.
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(
            OrderStatus,
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
    ),
    default=OrderStatus.NEW,
    index=True,
    nullable=False,
)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="orders", lazy="raise")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class OrderItem(Base):
    """A single line in an order.

    Stores snapshots of ``product_name`` and ``product_price`` so that
    historical orders remain accurate even if the product is renamed,
    repriced, or removed from the catalog.
    """

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    product_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items", lazy="raise")
    product: Mapped["Product | None"] = relationship(lazy="raise")

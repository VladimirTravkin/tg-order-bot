"""Cart model — items a user intends to order."""

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tg_order_bot.database.base import Base
from tg_order_bot.database.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from tg_order_bot.database.models.catalog import Product
    from tg_order_bot.database.models.user import User


class CartItem(Base, TimestampMixin):
    """A product in the user's cart.

    The pair ``(user_id, product_id)`` is unique — adding the same product
    twice increments ``quantity`` instead of creating a new row.
    """

    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),
        CheckConstraint("quantity > 0", name="ck_cart_quantity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    user: Mapped["User"] = relationship(back_populates="cart_items", lazy="selectin")
    product: Mapped["Product"] = relationship(
        back_populates="cart_items", lazy="selectin"
    )

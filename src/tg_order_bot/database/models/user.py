"""User model — Telegram users interacting with the bot."""

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tg_order_bot.database.base import Base
from tg_order_bot.database.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from tg_order_bot.database.models.cart import CartItem
    from tg_order_bot.database.models.order import Order


class User(Base, TimestampMixin):
    """A Telegram user known to the bot.

    ``telegram_id`` is the numeric ID from Telegram (may exceed 32-bit
    int range, hence ``BigInteger``). ``phone`` is filled in during the
    first checkout and reused for subsequent orders.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False,
    )
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    cart_items: Mapped[list["CartItem"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="raise",
    )
    orders: Mapped[list["Order"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="raise",
    )

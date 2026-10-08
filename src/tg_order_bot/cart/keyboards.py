"""Inline keyboards for the cart flow."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tg_order_bot.cart.callbacks import CartCallback
from tg_order_bot.database.models.cart import CartItem
from tg_order_bot.orders.callbacks import OrderCallback


def get_add_to_cart_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Keyboard shown on the product card — "add to cart" button."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🛒 В корзину",
        callback_data=CartCallback(action="add", product_id=product_id),
    )
    return builder.as_markup()


def get_cart_keyboard(items: list[CartItem]) -> InlineKeyboardMarkup:
    """Keyboard shown in the cart view.

    Each item gets its own "remove" button in a separate row. The last
    row has "clear cart" and "checkout" buttons. ``checkout`` is a
    placeholder until step 11.
    """
    builder = InlineKeyboardBuilder()

    for item in items:
        product_name = item.product.name if item.product else "товар"
        builder.row(
            InlineKeyboardButton(
                text=f"🗑 Убрать «{product_name}»",
                callback_data=CartCallback(action="remove", product_id=item.product_id).pack(),
            )
        )

    if items:
        builder.row(
            InlineKeyboardButton(
                text="🗑 Очистить корзину",
                callback_data=CartCallback(action="clear").pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📝 Оформить заказ",
                callback_data=OrderCallback(action="start").pack(),
            )
        )

    return builder.as_markup()


def get_empty_cart_keyboard() -> InlineKeyboardMarkup:
    """Keyboard shown when the cart is empty — link back to the catalog."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🛍 Перейти в каталог",
        callback_data="catalog:open:",
    )
    return builder.as_markup()


__all__ = [
    "get_add_to_cart_keyboard",
    "get_cart_keyboard",
    "get_empty_cart_keyboard",
]

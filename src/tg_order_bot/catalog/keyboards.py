"""Inline keyboards for the catalog flow.

Every button carries a ``CatalogCallback`` or ``CartCallback`` so the
handler can dispatch on ``action`` and ``id`` without parsing strings.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tg_order_bot.cart.callbacks import CartCallback
from tg_order_bot.catalog.callbacks import CatalogCallback
from tg_order_bot.database.models.catalog import Category, Product

# Prefixes for category and product buttons keep labels short and readable.
CATEGORY_ICON = "📂"
PRODUCT_ICON = "🔹"


def get_categories_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    """Build an inline keyboard listing all active categories.

    One button per row; long names are truncated to 60 characters.
    """
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=f"{CATEGORY_ICON} {category.name}",
            callback_data=CatalogCallback(action="category", id=category.id),
        )
    builder.adjust(1)
    return builder.as_markup()


def get_products_keyboard(
    category_id: int, products: list[Product]
) -> InlineKeyboardMarkup:
    """Build an inline keyboard listing products in a category.

    Each row: one product button. The last row has a "back to
    categories" button.
    """
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=f"{PRODUCT_ICON} {product.name} — {product.price} ₽",
            callback_data=CatalogCallback(action="product", id=product.id),
        )
    builder.button(
        text="◀️ К категориям",
        callback_data=CatalogCallback(action="open"),
    )
    builder.adjust(1)
    return builder.as_markup()


def get_product_keyboard(product: Product) -> InlineKeyboardMarkup:
    """Build an inline keyboard for a product card.

    Buttons: add to cart, back to category.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🛒 В корзину",
            callback_data=CartCallback(action="add", product_id=product.id).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="◀️ К товарам категории",
            callback_data=CatalogCallback(
                action="category", id=product.category_id
            ).pack(),
        )
    )
    return builder.as_markup()


def get_empty_category_keyboard() -> InlineKeyboardMarkup:
    """Build a keyboard for an empty category — only a back button."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="◀️ К категориям",
        callback_data=CatalogCallback(action="open"),
    )
    return builder.as_markup()


__all__ = [
    "get_categories_keyboard",
    "get_empty_category_keyboard",
    "get_product_keyboard",
    "get_products_keyboard",
]

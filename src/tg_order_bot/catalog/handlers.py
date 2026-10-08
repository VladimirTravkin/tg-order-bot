"""Handlers for the catalog flow.

Covers three user actions:

- pressing the "Catalog" reply button (or sending ``/catalog``)
- picking a category (shows its products)
- picking a product (shows its card)

All handlers are registered on ``router``, which is included by the
dispatcher in ``bot.py``.
"""

import logging
from typing import TypeGuard

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InaccessibleMessage,
    InputMediaPhoto,
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession

from tg_order_bot.catalog.callbacks import CatalogCallback
from tg_order_bot.catalog.keyboards import (
    get_categories_keyboard,
    get_empty_category_keyboard,
    get_product_keyboard,
    get_products_keyboard,
)
from tg_order_bot.catalog.service import (
    get_active_categories,
    get_category,
    get_product,
    get_products_by_category,
)

logger = logging.getLogger(__name__)

router = Router(name="catalog")


def _is_editable(
    message: Message | InaccessibleMessage | None,
) -> TypeGuard[Message]:
    """Return True if the message can be edited by the bot.

    Telegram only allows editing messages sent less than 48 hours ago
    and messages the bot has access to. Older or restricted messages
    arrive as ``InaccessibleMessage``.
    """
    return message is not None and not isinstance(message, InaccessibleMessage)


@router.message(Command("catalog"))
@router.message(F.text.lower().in_({"каталог", "🛍 каталог"}))
async def cmd_catalog(message: Message, session: AsyncSession) -> None:
    """Show the list of active categories.

    Triggered by the ``/catalog`` command or the "📦 Каталог" reply
    button. If there are no categories, replies with a notice.
    """
    categories = await get_active_categories(session)
    if not categories:
        await message.answer("Пока нет ни одной категории. Заходите позже!")
        return

    await message.answer(
        "<b>Каталог</b>\n\nВыберите категорию:",
        reply_markup=get_categories_keyboard(categories),
    )


@router.callback_query(CatalogCallback.filter(F.action == "open"))
async def on_open_catalog(callback: CallbackQuery, session: AsyncSession) -> None:
    """Re-open the category list from a callback (e.g. "back" button)."""
    if not _is_editable(callback.message):
        await callback.answer()
        return

    categories = await get_active_categories(session)
    if not categories:
        await callback.answer("Каталог пуст", show_alert=True)
        return

    await callback.message.edit_text(
        "<b>Каталог</b>\n\nВыберите категорию:",
        reply_markup=get_categories_keyboard(categories),
    )
    await callback.answer()


@router.callback_query(CatalogCallback.filter(F.action == "category"))
async def on_category_selected(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    session: AsyncSession,
) -> None:
    """Show products of the selected category."""
    if not _is_editable(callback.message) or callback_data.id is None:
        await callback.answer()
        return

    category = await get_category(session, callback_data.id)
    if category is None or not category.is_active:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    products = await get_products_by_category(session, category.id)
    if not products:
        await callback.message.edit_text(
            f"<b>{category.name}</b>\n\nВ этой категории пока нет товаров.",
            reply_markup=get_empty_category_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"<b>{category.name}</b>\n\nВыберите товар:",
        reply_markup=get_products_keyboard(category.id, products),
    )
    await callback.answer()


@router.callback_query(CatalogCallback.filter(F.action == "product"))
async def on_product_selected(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    session: AsyncSession,
) -> None:
    """Show a product card with description, price and action buttons."""
    if not _is_editable(callback.message) or callback_data.id is None:
        await callback.answer()
        return

    product = await get_product(session, callback_data.id)
    if product is None or not product.is_active:
        await callback.answer("Товар не найден", show_alert=True)
        return

    text = f"<b>{product.name}</b>\n\n"
    if product.description:
        text += f"{product.description}\n\n"
    text += f"<b>Цена:</b> {product.price} ₽"

    # If the product has a photo, edit the message caption instead of
    # the text. Otherwise, just edit the text.
    if product.photo_url:
        try:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=product.photo_url, caption=text),
                reply_markup=get_product_keyboard(product),
            )
        except Exception:
            logger.exception("Failed to edit media for product %d", product.id)
            await callback.message.edit_text(text, reply_markup=get_product_keyboard(product))
    else:
        await callback.message.edit_text(text, reply_markup=get_product_keyboard(product))

    await callback.answer()


__all__ = ["router"]

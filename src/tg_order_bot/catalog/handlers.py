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


async def _replace_with_text(
    callback: CallbackQuery,
    text: str,
    reply_markup=None,
) -> None:
    """Delete the current message and send a new text one.

    Used because the previous message may be a photo (no text to edit),
    so ``edit_text`` would fail with "there is no text in the message".
    """
    if not _is_editable(callback.message):
        return
    try:
        await callback.message.delete()
    except Exception:
        # Message might be too old or already deleted — ignore.
        logger.debug("Could not delete message", exc_info=True)
    await callback.message.answer(text, reply_markup=reply_markup)


async def _replace_with_product_card(
    callback: CallbackQuery,
    text: str,
    photo_url: str | None,
    reply_markup=None,
) -> None:
    """Delete the current message and send a product card.

    Sends a photo card if ``photo_url`` is set, otherwise a text card.
    """
    if not _is_editable(callback.message):
        return
    try:
        await callback.message.delete()
    except Exception:
        logger.debug("Could not delete message", exc_info=True)

    if photo_url:
        await callback.message.answer_photo(
            photo=photo_url,
            caption=text,
            reply_markup=reply_markup,
        )
    else:
        await callback.message.answer(text, reply_markup=reply_markup)


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
    categories = await get_active_categories(session)
    if not categories:
        await callback.answer("Каталог пуст", show_alert=True)
        return

    await _replace_with_text(
        callback,
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
    if callback_data.id is None:
        await callback.answer()
        return

    category = await get_category(session, callback_data.id)
    if category is None or not category.is_active:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    products = await get_products_by_category(session, category.id)
    if not products:
        await _replace_with_text(
            callback,
            f"<b>{category.name}</b>\n\nВ этой категории пока нет товаров.",
            reply_markup=get_empty_category_keyboard(),
        )
        await callback.answer()
        return

    await _replace_with_text(
        callback,
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
    if callback_data.id is None:
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

    await _replace_with_product_card(
        callback,
        text,
        photo_url=product.photo_url,
        reply_markup=get_product_keyboard(product),
    )
    await callback.answer()


__all__ = ["router"]

"""Handlers for the cart flow.

Covers three user actions:

- adding a product from the product card (inline button)
- viewing the cart (reply button or inline button)
- removing a single item or clearing the entire cart

All handlers rely on the ``DbSessionMiddleware`` to inject an
``AsyncSession`` and on ``get_or_create_user`` to resolve the user.
"""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, InaccessibleMessage, Message
from sqlalchemy.ext.asyncio import AsyncSession

from tg_order_bot.cart.callbacks import CartCallback
from tg_order_bot.cart.keyboards import (
    get_cart_keyboard,
    get_empty_cart_keyboard,
)
from tg_order_bot.cart.service import (
    add_to_cart,
    clear_cart,
    get_cart_items,
    remove_from_cart,
)
from tg_order_bot.common.keyboards import BTN_CART
from tg_order_bot.common.services import get_or_create_user
from tg_order_bot.database.models.cart import CartItem
from tg_order_bot.database.models.user import User

logger = logging.getLogger(__name__)

router = Router(name="cart")


def _format_cart(items: list[CartItem]) -> str:
    """Format cart items as an HTML message body with total."""
    if not items:
        return (
            "🛒 <b>Корзина пуста</b>\n\n"
            "Добавьте товары из каталога, чтобы оформить заказ."
        )

    lines = ["🛒 <b>Корзина</b>\n"]
    total = 0
    for idx, item in enumerate(items, start=1):
        product = item.product
        name = product.name if product else "товар"
        price = product.price if product else 0
        subtotal = price * item.quantity
        total += subtotal
        lines.append(
            f"{idx}. <b>{name}</b>\n"
            f"   {price} ₽ × {item.quantity} = {subtotal} ₽"
        )

    lines.append(f"\n<b>Итого:</b> {total} ₽")
    return "\n".join(lines)


async def _resolve_user(session: AsyncSession, telegram_user) -> User:
    """Ensure the Telegram user exists in the database."""
    return await get_or_create_user(
        session=session,
        telegram_id=telegram_user.id,
        username=telegram_user.username,
        full_name=telegram_user.full_name,
    )


# === View cart (reply button + command) ===


@router.message(F.text == BTN_CART)
async def on_cart_button(message: Message, session: AsyncSession) -> None:
    """Show the cart when the reply keyboard button is pressed."""
    if message.from_user is None:
        return

    user = await _resolve_user(session, message.from_user)
    items = await get_cart_items(session, user)

    if not items:
        await message.answer(
            _format_cart(items),
            reply_markup=get_empty_cart_keyboard(),
        )
        return

    await message.answer(
        _format_cart(items),
        reply_markup=get_cart_keyboard(items),
    )


# === Add to cart (inline button on product card) ===


@router.callback_query(CartCallback.filter(F.action == "add"))
async def on_add_to_cart(
    callback: CallbackQuery,
    callback_data: CartCallback,
    session: AsyncSession,
) -> None:
    """Add a product to the cart, or increment its quantity."""
    if callback_data.product_id is None:
        await callback.answer("Товар не найден", show_alert=True)
        return
    if callback.from_user is None:
        await callback.answer()
        return

    user = await _resolve_user(session, callback.from_user)
    await add_to_cart(session, user, callback_data.product_id)
    await session.commit()

    await callback.answer("Товар добавлен в корзину ✅", show_alert=False)


# === Remove single item ===


@router.callback_query(CartCallback.filter(F.action == "remove"))
async def on_remove_from_cart(
    callback: CallbackQuery,
    callback_data: CartCallback,
    session: AsyncSession,
) -> None:
    """Remove a single product from the cart and refresh the view."""
    if callback_data.product_id is None:
        await callback.answer()
        return
    if not _is_editable(callback.message):
        await callback.answer()
        return
    if callback.from_user is None:
        await callback.answer()
        return

    user = await _resolve_user(session, callback.from_user)
    removed = await remove_from_cart(session, user, callback_data.product_id)
    await session.commit()

    items = await get_cart_items(session, user)

    if not items:
        await callback.message.edit_text(
            _format_cart(items),
            reply_markup=get_empty_cart_keyboard(),
        )
    else:
        await callback.message.edit_text(
            _format_cart(items),
            reply_markup=get_cart_keyboard(items),
        )

    if removed:
        await callback.answer("Товар убран из корзины")
    else:
        await callback.answer("Товар не найден", show_alert=True)


# === Clear cart ===


@router.callback_query(CartCallback.filter(F.action == "clear"))
async def on_clear_cart(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Empty the entire cart and show the empty state."""
    if not _is_editable(callback.message):
        await callback.answer()
        return
    if callback.from_user is None:
        await callback.answer()
        return

    user = await _resolve_user(session, callback.from_user)
    removed = await clear_cart(session, user)
    await session.commit()

    await callback.message.edit_text(
        _format_cart([]),
        reply_markup=get_empty_cart_keyboard(),
    )
    await callback.answer(f"Удалено позиций: {removed}")


# === Helpers ===


def _is_editable(message: Message | InaccessibleMessage | None) -> bool:
    """Return True if the message can be edited by the bot.

    Same guard used in the catalog handlers: Telegram forbids editing
    messages older than 48 hours, and those arrive as
    ``InaccessibleMessage``.
    """
    return message is not None and not isinstance(message, InaccessibleMessage)


__all__ = ["router"]

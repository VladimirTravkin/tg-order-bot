"""Handlers for the checkout flow.

The flow is a 4-step FSM:

1. ``name``    — user enters name (default from Telegram)
2. ``phone``   — user enters phone
3. ``comment`` — user enters comment or skips
4. ``confirm`` — user reviews and confirms

Any step can be cancelled via the "❌ Отменить" button or the
``/cancel`` command.
"""

import logging
from typing import TypeGuard

from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InaccessibleMessage, Message
from sqlalchemy.ext.asyncio import AsyncSession

from tg_order_bot.cart.service import get_cart_items
from tg_order_bot.common.services import get_or_create_user
from tg_order_bot.database.models.user import User
from tg_order_bot.orders.callbacks import OrderCallback
from tg_order_bot.orders.keyboards import (
    get_cancel_keyboard,
    get_confirm_keyboard,
    get_name_keyboard,
    get_skip_or_cancel_keyboard,
)
from tg_order_bot.orders.service import (
    create_order,
    format_order_for_user,
    notify_admins,
)
from tg_order_bot.orders.states import OrderForm

logger = logging.getLogger(__name__)

router = Router(name="orders")


def _is_editable(
    message: Message | InaccessibleMessage | None,
) -> TypeGuard[Message]:
    """Return True if the message can be edited by the bot."""
    return message is not None and not isinstance(message, InaccessibleMessage)


async def _resolve_user(session: AsyncSession, telegram_user) -> User:
    """Ensure the Telegram user exists in the database."""
    return await get_or_create_user(
        session=session,
        telegram_id=telegram_user.id,
        username=telegram_user.username,
        full_name=telegram_user.full_name,
    )


# === Step 0: start checkout (from cart button) ===


@router.callback_query(OrderCallback.filter(F.action == "start"))
async def on_start_checkout(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Enter the FSM at the name step."""
    if not _is_editable(callback.message) or callback.from_user is None:
        await callback.answer()
        return

    # Check the cart is not empty.
    user = await _resolve_user(session, callback.from_user)
    items = await get_cart_items(session, user)
    if not items:
        await callback.answer("Корзина пуста", show_alert=True)
        return

    await state.set_state(OrderForm.name)

    # Offer the Telegram name as a one-tap default.
    default_name = callback.from_user.full_name or "—"
    await callback.message.edit_text(
        "📝 <b>Оформление заказа</b>\n\n"
        "<b>Шаг 1/3.</b> Введите ваше имя — "
        "или нажмите «Оставить как есть».",
        reply_markup=get_name_keyboard(default_name),
    )
    await callback.answer()


@router.callback_query(
    OrderForm.name,
    OrderCallback.filter(F.action == "use_default_name"),
)
async def on_use_default_name(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Use the Telegram name as-is and move to the phone step."""
    if not _is_editable(callback.message) or callback.from_user is None:
        await callback.answer()
        return

    user = await _resolve_user(session, callback.from_user)
    name = user.full_name or "—"

    await state.update_data(customer_name=name)
    await state.set_state(OrderForm.phone)

    await callback.message.edit_text(
        "Шаг 2/3. Введите ваш телефон для связи:",
        reply_markup=get_cancel_keyboard(),
    )
    await callback.answer(f"Имя: {name}")


# === Step 1: name ===


@router.message(OrderForm.name)
async def on_name_input(message: Message, state: FSMContext) -> None:
    """Store the name and move to the phone step."""
    if message.from_user is None or message.text is None:
        return

    name = message.text.strip()
    if not name:
        await message.answer("Пожалуйста, введите имя.")
        return

    await state.update_data(customer_name=name)
    await state.set_state(OrderForm.phone)

    await message.answer(
        "Шаг 2/3. Введите ваш телефон для связи:",
        reply_markup=get_cancel_keyboard(),
    )


# === Step 2: phone ===


@router.message(OrderForm.phone)
async def on_phone_input(message: Message, state: FSMContext) -> None:
    """Store the phone and move to the comment step."""
    if message.text is None:
        return

    phone = message.text.strip()
    if not phone:
        await message.answer("Пожалуйста, введите телефон.")
        return

    await state.update_data(customer_phone=phone)
    await state.set_state(OrderForm.comment)

    await message.answer(
        "Шаг 3/3. Добавьте комментарий к заказу (необязательно).",
        reply_markup=get_skip_or_cancel_keyboard(),
    )


# === Step 3: comment (or skip) ===


@router.message(OrderForm.comment)
async def on_comment_input(message: Message, state: FSMContext) -> None:
    """Store the comment and move to confirmation."""
    if message.text is None:
        return

    comment = message.text.strip() or None
    await state.update_data(comment=comment)
    await _show_confirmation(message, state)


@router.callback_query(
    OrderForm.comment, OrderCallback.filter(F.action == "skip")
)
async def on_skip_comment(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Skip comment step and move to confirmation."""
    if not _is_editable(callback.message):
        await callback.answer()
        return

    await state.update_data(comment=None)
    await _show_confirmation(callback.message, state)
    await callback.answer()


async def _show_confirmation(
    message: Message, state: FSMContext
) -> None:
    """Build and show the confirmation message."""
    data = await state.get_data()
    name = data.get("customer_name", "—")
    phone = data.get("customer_phone", "—")
    comment = data.get("comment") or "(нет)"

    await state.set_state(OrderForm.confirm)

    text = (
        f"📝 <b>Проверьте заказ:</b>\n\n"
        f"👤 {name}\n"
        f"📞 {phone}\n"
        f"💬 {comment}\n\n"
        f"Нажмите «✅ Подтвердить», чтобы отправить заказ."
    )
    await message.answer(text, reply_markup=get_confirm_keyboard())


# === Step 4: confirm ===


@router.callback_query(
    OrderForm.confirm, OrderCallback.filter(F.action == "confirm")
)
async def on_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
) -> None:
    """Create the order and notify admins."""
    if not _is_editable(callback.message) or callback.from_user is None:
        await callback.answer()
        return

    data = await state.get_data()
    user = await _resolve_user(session, callback.from_user)

    order = await create_order(
        session=session,
        user=user,
        customer_name=data.get("customer_name", "—"),
        customer_phone=data.get("customer_phone", "—"),
        comment=data.get("comment"),
    )

    await state.clear()

    if order is None:
        await callback.message.edit_text(
            "❌ Не удалось создать заказ — корзина пуста."
        )
        await callback.answer()
        return

    await notify_admins(bot, order, user)

    await callback.message.edit_text(
        format_order_for_user(order),
    )
    await callback.answer("Заказ отправлен ✅")


# === Cancel (button and command) ===


@router.callback_query(OrderCallback.filter(F.action == "cancel"))
async def on_cancel(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Cancel the checkout on any step."""
    if not _is_editable(callback.message):
        await callback.answer()
        return

    await state.clear()
    await callback.message.edit_text(
        "❌ Оформление заказа отменено.\n\n"
        "Ваша корзина сохранена — вы можете оформить заказ позже."
    )
    await callback.answer("Отменено")


@router.message(Command("cancel"), StateFilter("*"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Cancel checkout via /cancel command (works in any state)."""
    current_state = await state.get_state()
    if current_state is None:
        return  # Not in FSM — ignore

    await state.clear()
    await message.answer(
        "❌ Оформление заказа отменено.\n\n"
        "Ваша корзина сохранена."
    )


__all__ = ["router"]

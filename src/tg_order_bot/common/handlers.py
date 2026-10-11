"""Common handlers: /start, /help.

These are the entry points users interact with first. The /start
handler also shows the persistent reply keyboard.
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from tg_order_bot.common.keyboards import BTN_HELP, get_main_menu_keyboard
from tg_order_bot.config import get_settings

router = Router(name="common")


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Greet the user and show the main menu keyboard.

    Admins get an extra "🔧 Админ" button on the reply keyboard.
    """
    if message.from_user is None:
        return

    settings = get_settings()
    is_admin = message.from_user.id in settings.admin_ids

    await message.answer(
        f"👋 Привет, <b>{message.from_user.full_name}</b>!\n\n"
        "Я бот для приёма заказов. Через меня вы можете:\n"
        "🛍 Посмотреть каталог товаров\n"
        "🛒 Собрать корзину\n"
        "📝 Оформить заказ\n\n"
        "Выберите действие на клавиатуре ниже:",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin),
    )


@router.message(Command("help"))
@router.message(F.text == BTN_HELP)
async def cmd_help(message: Message) -> None:
    """Show a short help message."""
    await message.answer(
        "<b>Помощь</b>\n\n"
        "🛍 <b>Каталог</b> — посмотреть товары по категориям\n"
        "🛒 <b>Корзина</b> — посмотреть выбранные товары\n\n"
        "Если что-то пошло не так — напишите /start, чтобы начать заново.",
    )


__all__ = ["router"]

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.handlers.start import get_user_language
from src.keyboards import get_language_keyboard
from src.locales import locale

router = Router()


@router.message(Command("language"))
async def cmd_language(message: Message) -> None:
    """Handle /language command - show language selection."""
    if message.from_user is None:
        return

    lang = await get_user_language(message.from_user.id)
    await message.answer(
        locale.get(lang, "language.choose"),
        reply_markup=get_language_keyboard(),
    )

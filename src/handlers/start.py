from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from src.database import async_session
from src.keyboards import get_language_keyboard, get_main_menu
from src.locales import locale
from src.models import User

router = Router()


async def get_user(telegram_id: int) -> User | None:
    """Get user by Telegram ID."""
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def get_user_language(telegram_id: int) -> str:
    """Get user's language preference."""
    user = await get_user(telegram_id)
    return user.language if user else "en"


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command - register user or show welcome."""
    if message.from_user is None:
        return

    user = await get_user(message.from_user.id)

    if user is None:
        # New user - ask for language
        await message.answer(
            "Please choose your language:\nПожалуйста, выберите язык:",
            reply_markup=get_language_keyboard(),
        )
    else:
        # Existing user - show welcome
        lang = user.language
        await message.answer(
            locale.get(lang, "welcome"),
            reply_markup=get_main_menu(lang),
        )


@router.callback_query(F.data.startswith("lang:"))
async def process_language_selection(callback: CallbackQuery) -> None:
    """Handle language selection from inline keyboard."""
    if callback.message is None or callback.from_user is None:
        return

    lang = callback.data.split(":")[1]

    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == callback.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            # Create new user with selected language
            user = User(telegram_id=callback.from_user.id, language=lang)
            session.add(user)
            await session.commit()
        else:
            # Update existing user's language
            user.language = lang
            await session.commit()

    # Remove inline keyboard and show welcome
    await callback.message.edit_text(locale.get(lang, "language.changed"))
    await callback.message.answer(
        locale.get(lang, "welcome"),
        reply_markup=get_main_menu(lang),
    )
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command - show available commands."""
    if message.from_user is None:
        return

    lang = await get_user_language(message.from_user.id)
    await message.answer(
        locale.get(lang, "help"),
        reply_markup=get_main_menu(lang),
    )


@router.message(F.text.in_([
    locale.get("en", "buttons.help"),
    locale.get("ru", "buttons.help"),
]))
async def btn_help(message: Message) -> None:
    """Handle Help button press."""
    if message.from_user is None:
        return

    lang = await get_user_language(message.from_user.id)
    await message.answer(
        locale.get(lang, "help"),
        reply_markup=get_main_menu(lang),
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Handle /cancel command - cancel current FSM operation."""
    if message.from_user is None:
        return

    lang = await get_user_language(message.from_user.id)
    current_state = await state.get_state()

    if current_state is None:
        await message.answer(
            locale.get(lang, "cancel.nothing"),
            reply_markup=get_main_menu(lang),
        )
        return

    await state.clear()
    await message.answer(
        locale.get(lang, "cancel.cancelled"),
        reply_markup=get_main_menu(lang),
    )


@router.message(F.text.in_([
    locale.get("en", "buttons.cancel"),
    locale.get("ru", "buttons.cancel"),
]))
async def btn_cancel(message: Message, state: FSMContext) -> None:
    """Handle Cancel button press - same as /cancel command."""
    if message.from_user is None:
        return

    lang = await get_user_language(message.from_user.id)
    current_state = await state.get_state()

    if current_state is None:
        await message.answer(
            locale.get(lang, "cancel.nothing"),
            reply_markup=get_main_menu(lang),
        )
        return

    await state.clear()
    await message.answer(
        locale.get(lang, "cancel.cancelled"),
        reply_markup=get_main_menu(lang),
    )

from html import escape

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy import or_, select

from src.database import async_session
from src.handlers.dreams import get_user_id_and_lang
from src.keyboards import get_cancel_keyboard, get_main_menu
from src.locales import locale
from src.models import Dream

router = Router()


class SearchStates(StatesGroup):
    """States for search."""

    waiting_for_query = State()


@router.message(F.text.in_([
    locale.get("en", "buttons.search"),
    locale.get("ru", "buttons.search"),
]))
async def btn_search(message: Message, state: FSMContext) -> None:
    """Handle Search button - ask for search query."""
    if message.from_user is None:
        return

    user_id, lang = await get_user_id_and_lang(message.from_user.id)
    if user_id is None:
        await message.answer(locale.get(lang, "not_registered"))
        return

    await state.update_data(user_id=user_id, lang=lang)
    await state.set_state(SearchStates.waiting_for_query)
    await message.answer(
        locale.get(lang, "search.prompt"),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(SearchStates.waiting_for_query)
async def process_search_query(message: Message, state: FSMContext) -> None:
    """Process search query from button flow."""
    data = await state.get_data()
    lang = data.get("lang", "en")

    if not message.text:
        await message.answer(locale.get(lang, "search.prompt"))
        return

    user_id = data["user_id"]
    query = message.text.strip().lower()

    await state.clear()
    await perform_search(message, user_id, query, lang)


@router.message(Command("search"))
async def cmd_search(message: Message, command: CommandObject) -> None:
    """Search dreams by keywords in title, description, and tags."""
    if message.from_user is None:
        return

    user_id, lang = await get_user_id_and_lang(message.from_user.id)
    if user_id is None:
        await message.answer(locale.get(lang, "not_registered"))
        return

    if not command.args:
        await message.answer(
            locale.get(lang, "search.usage"),
            reply_markup=get_main_menu(lang),
        )
        return

    query = command.args.strip().lower()
    await perform_search(message, user_id, query, lang)


async def perform_search(message: Message, user_id: int, query: str, lang: str) -> None:
    """Perform the actual search and display results."""
    async with async_session() as session:
        # Search in title, description, tags, and notes (case-insensitive)
        search_pattern = f"%{query}%"
        stmt = (
            select(Dream)
            .where(
                Dream.user_id == user_id,
                or_(
                    Dream.title.ilike(search_pattern),
                    Dream.description.ilike(search_pattern),
                    Dream.tags.ilike(search_pattern),
                    Dream.notes.ilike(search_pattern),
                ),
            )
            .order_by(Dream.dream_date.desc(), Dream.id.desc())
            .limit(20)
        )
        result = await session.execute(stmt)
        dreams = result.scalars().all()

        if not dreams:
            await message.answer(
                locale.get(lang, "search.no_results", query=escape(query)),
                reply_markup=get_main_menu(lang),
            )
            return

        lines = [locale.get(lang, "search.header", query=escape(query))]
        for dream in dreams:
            lines.append(f"<b>#{dream.id}</b> {dream.format_short()}")

        lines.append(f"\n{locale.get(lang, 'search.found', count=len(dreams))}")
        lines.append(f"\n{locale.get(lang, 'list.view_hint')}")

        await message.answer("\n".join(lines), reply_markup=get_main_menu(lang))

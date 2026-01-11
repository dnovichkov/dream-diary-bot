from datetime import date
from html import escape
from io import BytesIO

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import func, select

from src.config import settings
from src.database import async_session
from src.handlers.start import get_user_language
from src.keyboards import (
    get_cancel_keyboard,
    get_main_menu,
    get_skip_cancel_keyboard,
    get_today_cancel_keyboard,
)
from src.locales import locale
from src.models import Dream, User

router = Router()


class NewDreamStates(StatesGroup):
    """States for creating a new dream."""

    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_tags = State()
    waiting_for_notes = State()
    waiting_for_date = State()


class EditDreamStates(StatesGroup):
    """States for editing a dream."""

    waiting_for_field = State()
    waiting_for_value = State()


async def get_user_id_and_lang(telegram_id: int) -> tuple[int | None, str]:
    """Get internal user ID and language by Telegram ID."""
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            return user.id, user.language
        return None, "en"


async def get_dream_by_id(dream_id: int, user_id: int) -> Dream | None:
    """Get dream by ID if it belongs to the user."""
    async with async_session() as session:
        stmt = select(Dream).where(Dream.id == dream_id, Dream.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


# --- NEW DREAM ---


@router.message(Command("new"))
@router.message(F.text.in_([
    locale.get("en", "buttons.new_dream"),
    locale.get("ru", "buttons.new_dream"),
]))
async def cmd_new(message: Message, state: FSMContext) -> None:
    """Start creating a new dream entry."""
    if message.from_user is None:
        return

    user_id, lang = await get_user_id_and_lang(message.from_user.id)
    if user_id is None:
        await message.answer(locale.get(lang, "not_registered"))
        return

    await state.update_data(user_id=user_id, lang=lang)
    await state.set_state(NewDreamStates.waiting_for_title)
    await message.answer(
        locale.get(lang, "new_dream.creating"),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(NewDreamStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext) -> None:
    """Process dream title."""
    data = await state.get_data()
    lang = data.get("lang", "en")

    if not message.text:
        await message.answer(locale.get(lang, "new_dream.enter_title"))
        return

    title = message.text.strip()
    if len(title) > 255:
        await message.answer(locale.get(lang, "new_dream.title_too_long"))
        return

    await state.update_data(title=title)
    await state.set_state(NewDreamStates.waiting_for_description)
    await message.answer(
        locale.get(lang, "new_dream.step_2"),
        reply_markup=get_skip_cancel_keyboard(lang),
    )


@router.message(NewDreamStates.waiting_for_description, Command("skip"))
@router.message(NewDreamStates.waiting_for_description, F.text.in_([
    locale.get("en", "buttons.skip"),
    locale.get("ru", "buttons.skip"),
]))
async def skip_description(message: Message, state: FSMContext) -> None:
    """Skip description."""
    data = await state.get_data()
    lang = data.get("lang", "en")

    await state.update_data(description="")
    await state.set_state(NewDreamStates.waiting_for_tags)
    await message.answer(
        locale.get(lang, "new_dream.step_3"),
        reply_markup=get_skip_cancel_keyboard(lang),
    )


@router.message(NewDreamStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext) -> None:
    """Process dream description."""
    data = await state.get_data()
    lang = data.get("lang", "en")

    if not message.text:
        await message.answer(locale.get(lang, "new_dream.enter_description"))
        return

    await state.update_data(description=message.text.strip())
    await state.set_state(NewDreamStates.waiting_for_tags)
    await message.answer(
        locale.get(lang, "new_dream.step_3"),
        reply_markup=get_skip_cancel_keyboard(lang),
    )


@router.message(NewDreamStates.waiting_for_tags, Command("skip"))
@router.message(NewDreamStates.waiting_for_tags, F.text.in_([
    locale.get("en", "buttons.skip"),
    locale.get("ru", "buttons.skip"),
]))
async def skip_tags(message: Message, state: FSMContext) -> None:
    """Skip tags."""
    data = await state.get_data()
    lang = data.get("lang", "en")

    await state.update_data(tags="")
    await state.set_state(NewDreamStates.waiting_for_notes)
    await message.answer(
        locale.get(lang, "new_dream.step_4"),
        reply_markup=get_skip_cancel_keyboard(lang),
    )


@router.message(NewDreamStates.waiting_for_tags)
async def process_tags(message: Message, state: FSMContext) -> None:
    """Process dream tags."""
    data = await state.get_data()
    lang = data.get("lang", "en")

    if not message.text:
        await message.answer(locale.get(lang, "new_dream.enter_tags"))
        return

    tags = message.text.strip()
    if len(tags) > 500:
        await message.answer(locale.get(lang, "new_dream.tags_too_long"))
        return

    await state.update_data(tags=tags)
    await state.set_state(NewDreamStates.waiting_for_notes)
    await message.answer(
        locale.get(lang, "new_dream.step_4"),
        reply_markup=get_skip_cancel_keyboard(lang),
    )


@router.message(NewDreamStates.waiting_for_notes, Command("skip"))
@router.message(NewDreamStates.waiting_for_notes, F.text.in_([
    locale.get("en", "buttons.skip"),
    locale.get("ru", "buttons.skip"),
]))
async def skip_notes(message: Message, state: FSMContext) -> None:
    """Skip notes."""
    data = await state.get_data()
    lang = data.get("lang", "en")

    await state.update_data(notes="")
    await state.set_state(NewDreamStates.waiting_for_date)
    await message.answer(
        locale.get(lang, "new_dream.step_5", today=date.today()),
        reply_markup=get_today_cancel_keyboard(lang),
    )


@router.message(NewDreamStates.waiting_for_notes)
async def process_notes(message: Message, state: FSMContext) -> None:
    """Process dream notes."""
    data = await state.get_data()
    lang = data.get("lang", "en")

    if not message.text:
        await message.answer(locale.get(lang, "new_dream.enter_notes"))
        return

    await state.update_data(notes=message.text.strip())
    await state.set_state(NewDreamStates.waiting_for_date)
    await message.answer(
        locale.get(lang, "new_dream.step_5", today=date.today()),
        reply_markup=get_today_cancel_keyboard(lang),
    )


@router.message(NewDreamStates.waiting_for_date, Command("today"))
@router.message(NewDreamStates.waiting_for_date, F.text.in_([
    locale.get("en", "buttons.today"),
    locale.get("ru", "buttons.today"),
]))
async def use_today_date(message: Message, state: FSMContext) -> None:
    """Use today's date."""
    await state.update_data(dream_date=date.today())
    await save_new_dream(message, state)


@router.message(NewDreamStates.waiting_for_date)
async def process_date(message: Message, state: FSMContext) -> None:
    """Process dream date."""
    data = await state.get_data()
    lang = data.get("lang", "en")

    if not message.text:
        await message.answer(locale.get(lang, "new_dream.enter_date"))
        return

    try:
        dream_date = date.fromisoformat(message.text.strip())
    except ValueError:
        await message.answer(locale.get(lang, "new_dream.invalid_date"))
        return

    await state.update_data(dream_date=dream_date)
    await save_new_dream(message, state)


async def save_new_dream(message: Message, state: FSMContext) -> None:
    """Save the new dream to database."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    await state.clear()

    async with async_session() as session:
        dream = Dream(
            user_id=data["user_id"],
            title=data["title"],
            description=data.get("description", ""),
            tags=data.get("tags", ""),
            notes=data.get("notes", ""),
            dream_date=data.get("dream_date", date.today()),
        )
        session.add(dream)
        await session.commit()
        await session.refresh(dream)

        await message.answer(
            locale.get(
                lang,
                "new_dream.saved",
                id=dream.id,
                title=escape(dream.title),
                date=dream.dream_date,
            ),
            reply_markup=get_main_menu(lang),
        )


# --- LIST DREAMS ---


def build_pagination_keyboard(page: int, total_pages: int, lang: str = "en") -> InlineKeyboardMarkup | None:
    """Build pagination keyboard."""
    if total_pages <= 1:
        return None

    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(
            text=locale.get(lang, "buttons.prev"),
            callback_data=f"page:{page - 1}",
        ))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(
            text=locale.get(lang, "buttons.next"),
            callback_data=f"page:{page + 1}",
        ))

    if not buttons:
        return None

    return InlineKeyboardMarkup(inline_keyboard=[buttons])


@router.message(Command("list"))
@router.message(F.text.in_([
    locale.get("en", "buttons.my_dreams"),
    locale.get("ru", "buttons.my_dreams"),
]))
async def cmd_list(message: Message) -> None:
    """List user's dreams with pagination."""
    if message.from_user is None:
        return

    user_id, lang = await get_user_id_and_lang(message.from_user.id)
    if user_id is None:
        await message.answer(locale.get(lang, "not_registered"))
        return

    await show_dreams_page(message, user_id, lang, page=0)


async def show_dreams_page(
    message: Message,
    user_id: int,
    lang: str,
    page: int,
    edit_message: bool = False,
) -> None:
    """Show a page of dreams."""
    per_page = settings.dreams_per_page
    offset = page * per_page

    async with async_session() as session:
        # Get total count
        count_stmt = select(func.count(Dream.id)).where(Dream.user_id == user_id)
        total = (await session.execute(count_stmt)).scalar() or 0

        if total == 0:
            text = locale.get(lang, "list.empty")
            if edit_message and hasattr(message, "edit_text"):
                await message.edit_text(text)
            else:
                await message.answer(text)
            return

        total_pages = (total + per_page - 1) // per_page

        # Get dreams for current page
        stmt = (
            select(Dream)
            .where(Dream.user_id == user_id)
            .order_by(Dream.dream_date.desc(), Dream.id.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await session.execute(stmt)
        dreams = result.scalars().all()

        # Format output
        lines = [locale.get(lang, "list.header", page=page + 1, total_pages=total_pages) + "\n"]
        for dream in dreams:
            lines.append(f"<b>#{dream.id}</b> {dream.format_short()}")

        lines.append(f"\n{locale.get(lang, 'list.total', count=total)}")
        lines.append(locale.get(lang, "list.view_hint"))

        text = "\n".join(lines)
        keyboard = build_pagination_keyboard(page, total_pages, lang)

        if edit_message and hasattr(message, "edit_text"):
            await message.edit_text(text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("page:"))
async def process_pagination(callback: CallbackQuery) -> None:
    """Handle pagination button press."""
    if callback.message is None or callback.from_user is None:
        return

    page = int(callback.data.split(":")[1])
    user_id, lang = await get_user_id_and_lang(callback.from_user.id)

    if user_id is None:
        await callback.answer(locale.get(lang, "not_registered"))
        return

    await show_dreams_page(callback.message, user_id, lang, page, edit_message=True)
    await callback.answer()


# --- VIEW DREAM ---


@router.message(Command("view"))
async def cmd_view(message: Message, command: CommandObject) -> None:
    """View a specific dream by ID."""
    if message.from_user is None:
        return

    user_id, lang = await get_user_id_and_lang(message.from_user.id)
    if user_id is None:
        await message.answer(locale.get(lang, "not_registered"))
        return

    if not command.args:
        await message.answer(locale.get(lang, "view.usage"))
        return

    try:
        dream_id = int(command.args.strip())
    except ValueError:
        await message.answer(locale.get(lang, "view.invalid_id"))
        return

    dream = await get_dream_by_id(dream_id, user_id)
    if dream is None:
        await message.answer(locale.get(lang, "view.not_found", id=dream_id))
        return

    await message.answer(f"<pre>{dream.format_full(lang)}</pre>")


# --- EDIT DREAM ---


@router.message(Command("edit"))
async def cmd_edit(message: Message, command: CommandObject, state: FSMContext) -> None:
    """Start editing a dream."""
    if message.from_user is None:
        return

    user_id, lang = await get_user_id_and_lang(message.from_user.id)
    if user_id is None:
        await message.answer(locale.get(lang, "not_registered"))
        return

    if not command.args:
        await message.answer(locale.get(lang, "edit.usage"))
        return

    try:
        dream_id = int(command.args.strip())
    except ValueError:
        await message.answer(locale.get(lang, "view.invalid_id"))
        return

    dream = await get_dream_by_id(dream_id, user_id)
    if dream is None:
        await message.answer(locale.get(lang, "view.not_found", id=dream_id))
        return

    await state.update_data(edit_dream_id=dream_id, user_id=user_id, lang=lang)
    await state.set_state(EditDreamStates.waiting_for_field)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=locale.get(lang, "edit.field_title"), callback_data="edit:title")],
            [InlineKeyboardButton(text=locale.get(lang, "edit.field_description"), callback_data="edit:description")],
            [InlineKeyboardButton(text=locale.get(lang, "edit.field_tags"), callback_data="edit:tags")],
            [InlineKeyboardButton(text=locale.get(lang, "edit.field_notes"), callback_data="edit:notes")],
            [InlineKeyboardButton(text=locale.get(lang, "edit.field_date"), callback_data="edit:dream_date")],
            [InlineKeyboardButton(text=locale.get(lang, "edit.field_cancel"), callback_data="edit:cancel")],
        ]
    )

    await message.answer(
        locale.get(lang, "edit.header", id=dream_id, title=escape(dream.title)),
        reply_markup=keyboard,
    )


@router.callback_query(EditDreamStates.waiting_for_field, F.data.startswith("edit:"))
async def process_edit_field_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle field selection for editing."""
    if callback.message is None:
        return

    data = await state.get_data()
    lang = data.get("lang", "en")
    field = callback.data.split(":")[1]

    if field == "cancel":
        await state.clear()
        await callback.message.edit_text(locale.get(lang, "edit.cancelled"))
        await callback.answer()
        return

    await state.update_data(edit_field=field)
    await state.set_state(EditDreamStates.waiting_for_value)

    field_prompts = {
        "title": "edit.enter_title",
        "description": "edit.enter_description",
        "tags": "edit.enter_tags",
        "notes": "edit.enter_notes",
        "dream_date": "edit.enter_date",
    }

    await callback.message.edit_text(locale.get(lang, field_prompts[field]))
    await callback.answer()


@router.message(EditDreamStates.waiting_for_value)
async def process_edit_value(message: Message, state: FSMContext) -> None:
    """Process the new value for the field."""
    data = await state.get_data()
    lang = data.get("lang", "en")

    if not message.text:
        await message.answer(locale.get(lang, "edit.enter_value"))
        return

    field = data["edit_field"]
    dream_id = data["edit_dream_id"]
    user_id = data["user_id"]

    value = message.text.strip()

    # Validate based on field
    if field == "title" and len(value) > 255:
        await message.answer(locale.get(lang, "new_dream.title_too_long"))
        return
    if field == "tags" and len(value) > 500:
        await message.answer(locale.get(lang, "new_dream.tags_too_long"))
        return
    if field == "dream_date":
        try:
            value = date.fromisoformat(value)
        except ValueError:
            await message.answer(locale.get(lang, "new_dream.invalid_date"))
            return

    async with async_session() as session:
        stmt = select(Dream).where(Dream.id == dream_id, Dream.user_id == user_id)
        result = await session.execute(stmt)
        dream = result.scalar_one_or_none()

        if dream is None:
            await message.answer(locale.get(lang, "edit.not_found"))
            await state.clear()
            return

        setattr(dream, field, value)
        await session.commit()

    await state.clear()
    await message.answer(locale.get(lang, "edit.updated", id=dream_id))


# --- DELETE DREAM ---


@router.message(Command("delete"))
async def cmd_delete(message: Message, command: CommandObject) -> None:
    """Delete a dream with confirmation."""
    if message.from_user is None:
        return

    user_id, lang = await get_user_id_and_lang(message.from_user.id)
    if user_id is None:
        await message.answer(locale.get(lang, "not_registered"))
        return

    if not command.args:
        await message.answer(locale.get(lang, "delete.usage"))
        return

    try:
        dream_id = int(command.args.strip())
    except ValueError:
        await message.answer(locale.get(lang, "view.invalid_id"))
        return

    dream = await get_dream_by_id(dream_id, user_id)
    if dream is None:
        await message.answer(locale.get(lang, "view.not_found", id=dream_id))
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=locale.get(lang, "buttons.yes_delete"),
                    callback_data=f"delete:confirm:{dream_id}",
                ),
                InlineKeyboardButton(
                    text=locale.get(lang, "buttons.no_cancel"),
                    callback_data="delete:cancel",
                ),
            ]
        ]
    )

    await message.answer(
        locale.get(
            lang,
            "delete.confirm",
            id=dream_id,
            title=escape(dream.title),
            date=dream.dream_date,
        ),
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("delete:"))
async def process_delete_confirmation(callback: CallbackQuery) -> None:
    """Handle delete confirmation."""
    if callback.message is None or callback.from_user is None:
        return

    _, lang = await get_user_id_and_lang(callback.from_user.id)
    parts = callback.data.split(":")
    action = parts[1]

    if action == "cancel":
        await callback.message.edit_text(locale.get(lang, "delete.cancelled"))
        await callback.answer()
        return

    if action == "confirm":
        dream_id = int(parts[2])
        user_id, lang = await get_user_id_and_lang(callback.from_user.id)

        if user_id is None:
            await callback.answer(locale.get(lang, "not_registered"))
            return

        async with async_session() as session:
            stmt = select(Dream).where(Dream.id == dream_id, Dream.user_id == user_id)
            result = await session.execute(stmt)
            dream = result.scalar_one_or_none()

            if dream is None:
                await callback.message.edit_text(locale.get(lang, "delete.not_found"))
                await callback.answer()
                return

            await session.delete(dream)
            await session.commit()

        await callback.message.edit_text(locale.get(lang, "delete.deleted", id=dream_id))
        await callback.answer()


# --- EXPORT DREAMS ---


def format_dream_for_export(dream: Dream, index: int, lang: str = "en") -> str:
    """Format a single dream for text export."""
    t = lambda key: locale.get(lang, f"export.{key}")

    lines = [
        "=" * 40,
        locale.get(lang, "export.dream_header", index=index, date=dream.dream_date),
        "-" * 40,
        f"{t('field_title')}: {dream.title}",
    ]

    if dream.description:
        lines.append(f"\n{t('field_description')}:\n{dream.description}")

    if dream.tags:
        lines.append(f"\n{t('field_tags')}: {dream.tags}")

    if dream.notes:
        lines.append(f"\n{t('field_notes')}:\n{dream.notes}")

    lines.append("")
    return "\n".join(lines)


@router.message(Command("export"))
@router.message(F.text.in_([
    locale.get("en", "buttons.export"),
    locale.get("ru", "buttons.export"),
]))
async def cmd_export(message: Message) -> None:
    """Export all user's dreams to a text file."""
    if message.from_user is None:
        return

    user_id, lang = await get_user_id_and_lang(message.from_user.id)
    if user_id is None:
        await message.answer(locale.get(lang, "not_registered"))
        return

    async with async_session() as session:
        stmt = (
            select(Dream)
            .where(Dream.user_id == user_id)
            .order_by(Dream.dream_date.desc(), Dream.id.desc())
        )
        result = await session.execute(stmt)
        dreams = result.scalars().all()

    if not dreams:
        await message.answer(
            locale.get(lang, "export.empty"),
            reply_markup=get_main_menu(lang),
        )
        return

    # Build text content
    header = locale.get(lang, "export.header", date=date.today(), count=len(dreams))
    lines = [header, ""]

    for i, dream in enumerate(dreams, start=1):
        lines.append(format_dream_for_export(dream, i, lang))

    content = "\n".join(lines)

    # Create file
    file_bytes = content.encode("utf-8")
    filename = f"dreams_export_{date.today()}.txt"
    input_file = BufferedInputFile(file_bytes, filename=filename)

    await message.answer_document(
        document=input_file,
        caption=locale.get(lang, "export.caption", count=len(dreams)),
        reply_markup=get_main_menu(lang),
    )

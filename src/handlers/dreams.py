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
from src.keyboards import (
    BTN_EXPORT,
    BTN_MY_DREAMS,
    BTN_NEW_DREAM,
    BTN_SKIP,
    BTN_TODAY,
    get_cancel_keyboard,
    get_main_menu,
    get_skip_cancel_keyboard,
    get_today_cancel_keyboard,
)
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


async def get_user_id(telegram_id: int) -> int | None:
    """Get internal user ID by Telegram ID."""
    async with async_session() as session:
        stmt = select(User.id).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def get_dream_by_id(dream_id: int, user_id: int) -> Dream | None:
    """Get dream by ID if it belongs to the user."""
    async with async_session() as session:
        stmt = select(Dream).where(Dream.id == dream_id, Dream.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


# --- NEW DREAM ---


@router.message(Command("new"))
@router.message(F.text == BTN_NEW_DREAM)
async def cmd_new(message: Message, state: FSMContext) -> None:
    """Start creating a new dream entry."""
    if message.from_user is None:
        return

    user_id = await get_user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Please use /start first to register.")
        return

    await state.update_data(user_id=user_id)
    await state.set_state(NewDreamStates.waiting_for_title)
    await message.answer(
        "<b>Creating a new dream entry</b>\n\n"
        "Step 1/5: Enter the <b>title</b> of your dream.",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(NewDreamStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext) -> None:
    """Process dream title."""
    if not message.text:
        await message.answer("Please enter a text title.")
        return

    title = message.text.strip()
    if len(title) > 255:
        await message.answer("Title is too long (max 255 characters). Please try again.")
        return

    await state.update_data(title=title)
    await state.set_state(NewDreamStates.waiting_for_description)
    await message.answer(
        "Step 2/5: Enter the <b>description</b> of your dream.",
        reply_markup=get_skip_cancel_keyboard(),
    )


@router.message(NewDreamStates.waiting_for_description, Command("skip"))
@router.message(NewDreamStates.waiting_for_description, F.text == BTN_SKIP)
async def skip_description(message: Message, state: FSMContext) -> None:
    """Skip description."""
    await state.update_data(description="")
    await state.set_state(NewDreamStates.waiting_for_tags)
    await message.answer(
        "Step 3/5: Enter <b>tags</b> (comma-separated keywords).\n"
        "Example: flying, lucid, nightmare",
        reply_markup=get_skip_cancel_keyboard(),
    )


@router.message(NewDreamStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext) -> None:
    """Process dream description."""
    if not message.text:
        await message.answer("Please enter a text description or tap Skip.")
        return

    await state.update_data(description=message.text.strip())
    await state.set_state(NewDreamStates.waiting_for_tags)
    await message.answer(
        "Step 3/5: Enter <b>tags</b> (comma-separated keywords).\n"
        "Example: flying, lucid, nightmare",
        reply_markup=get_skip_cancel_keyboard(),
    )


@router.message(NewDreamStates.waiting_for_tags, Command("skip"))
@router.message(NewDreamStates.waiting_for_tags, F.text == BTN_SKIP)
async def skip_tags(message: Message, state: FSMContext) -> None:
    """Skip tags."""
    await state.update_data(tags="")
    await state.set_state(NewDreamStates.waiting_for_notes)
    await message.answer(
        "Step 4/5: Enter any personal <b>notes</b> or comments.",
        reply_markup=get_skip_cancel_keyboard(),
    )


@router.message(NewDreamStates.waiting_for_tags)
async def process_tags(message: Message, state: FSMContext) -> None:
    """Process dream tags."""
    if not message.text:
        await message.answer("Please enter tags or tap Skip.")
        return

    tags = message.text.strip()
    if len(tags) > 500:
        await message.answer("Tags are too long (max 500 characters). Please try again.")
        return

    await state.update_data(tags=tags)
    await state.set_state(NewDreamStates.waiting_for_notes)
    await message.answer(
        "Step 4/5: Enter any personal <b>notes</b> or comments.",
        reply_markup=get_skip_cancel_keyboard(),
    )


@router.message(NewDreamStates.waiting_for_notes, Command("skip"))
@router.message(NewDreamStates.waiting_for_notes, F.text == BTN_SKIP)
async def skip_notes(message: Message, state: FSMContext) -> None:
    """Skip notes."""
    await state.update_data(notes="")
    await state.set_state(NewDreamStates.waiting_for_date)
    await message.answer(
        f"Step 5/5: Enter the <b>date</b> of the dream (YYYY-MM-DD).\n"
        f"Or tap Today to use: {date.today()}",
        reply_markup=get_today_cancel_keyboard(),
    )


@router.message(NewDreamStates.waiting_for_notes)
async def process_notes(message: Message, state: FSMContext) -> None:
    """Process dream notes."""
    if not message.text:
        await message.answer("Please enter notes or tap Skip.")
        return

    await state.update_data(notes=message.text.strip())
    await state.set_state(NewDreamStates.waiting_for_date)
    await message.answer(
        f"Step 5/5: Enter the <b>date</b> of the dream (YYYY-MM-DD).\n"
        f"Or tap Today to use: {date.today()}",
        reply_markup=get_today_cancel_keyboard(),
    )


@router.message(NewDreamStates.waiting_for_date, Command("today"))
@router.message(NewDreamStates.waiting_for_date, F.text == BTN_TODAY)
async def use_today_date(message: Message, state: FSMContext) -> None:
    """Use today's date."""
    await state.update_data(dream_date=date.today())
    await save_new_dream(message, state)


@router.message(NewDreamStates.waiting_for_date)
async def process_date(message: Message, state: FSMContext) -> None:
    """Process dream date."""
    if not message.text:
        await message.answer("Please enter a date or tap Today.")
        return

    try:
        dream_date = date.fromisoformat(message.text.strip())
    except ValueError:
        await message.answer(
            "Invalid date format. Please use YYYY-MM-DD (e.g., 2024-01-15) or tap Today."
        )
        return

    await state.update_data(dream_date=dream_date)
    await save_new_dream(message, state)


async def save_new_dream(message: Message, state: FSMContext) -> None:
    """Save the new dream to database."""
    data = await state.get_data()
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
            f"Dream saved successfully!\n\n"
            f"<b>ID:</b> {dream.id}\n"
            f"<b>Title:</b> {escape(dream.title)}\n"
            f"<b>Date:</b> {dream.dream_date}\n\n"
            f"Use /view {dream.id} to see the full entry.",
            reply_markup=get_main_menu(),
        )


# --- LIST DREAMS ---


def build_pagination_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup | None:
    """Build pagination keyboard."""
    if total_pages <= 1:
        return None

    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="<< Prev", callback_data=f"page:{page - 1}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="Next >>", callback_data=f"page:{page + 1}"))

    if not buttons:
        return None

    return InlineKeyboardMarkup(inline_keyboard=[buttons])


@router.message(Command("list"))
@router.message(F.text == BTN_MY_DREAMS)
async def cmd_list(message: Message) -> None:
    """List user's dreams with pagination."""
    if message.from_user is None:
        return

    user_id = await get_user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Please use /start first to register.")
        return

    await show_dreams_page(message, user_id, page=0)


async def show_dreams_page(
    message: Message,
    user_id: int,
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
            text = "You don't have any dream entries yet.\nUse /new to create one."
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
        lines = [f"<b>Your dreams</b> (page {page + 1}/{total_pages}):\n"]
        for dream in dreams:
            lines.append(f"<b>#{dream.id}</b> {dream.format_short()}")

        lines.append(f"\nTotal: {total} entries")
        lines.append("Use /view [id] to see details.")

        text = "\n".join(lines)
        keyboard = build_pagination_keyboard(page, total_pages)

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
    user_id = await get_user_id(callback.from_user.id)

    if user_id is None:
        await callback.answer("Please use /start first.")
        return

    await show_dreams_page(callback.message, user_id, page, edit_message=True)
    await callback.answer()


# --- VIEW DREAM ---


@router.message(Command("view"))
async def cmd_view(message: Message, command: CommandObject) -> None:
    """View a specific dream by ID."""
    if message.from_user is None:
        return

    user_id = await get_user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Please use /start first to register.")
        return

    if not command.args:
        await message.answer("Usage: /view [id]\nExample: /view 1")
        return

    try:
        dream_id = int(command.args.strip())
    except ValueError:
        await message.answer("Invalid ID. Please provide a number.")
        return

    dream = await get_dream_by_id(dream_id, user_id)
    if dream is None:
        await message.answer(f"Dream #{dream_id} not found.")
        return

    await message.answer(f"<pre>{dream.format_full()}</pre>")


# --- EDIT DREAM ---


@router.message(Command("edit"))
async def cmd_edit(message: Message, command: CommandObject, state: FSMContext) -> None:
    """Start editing a dream."""
    if message.from_user is None:
        return

    user_id = await get_user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Please use /start first to register.")
        return

    if not command.args:
        await message.answer("Usage: /edit [id]\nExample: /edit 1")
        return

    try:
        dream_id = int(command.args.strip())
    except ValueError:
        await message.answer("Invalid ID. Please provide a number.")
        return

    dream = await get_dream_by_id(dream_id, user_id)
    if dream is None:
        await message.answer(f"Dream #{dream_id} not found.")
        return

    await state.update_data(edit_dream_id=dream_id, user_id=user_id)
    await state.set_state(EditDreamStates.waiting_for_field)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Title", callback_data="edit:title")],
            [InlineKeyboardButton(text="Description", callback_data="edit:description")],
            [InlineKeyboardButton(text="Tags", callback_data="edit:tags")],
            [InlineKeyboardButton(text="Notes", callback_data="edit:notes")],
            [InlineKeyboardButton(text="Date", callback_data="edit:dream_date")],
            [InlineKeyboardButton(text="Cancel", callback_data="edit:cancel")],
        ]
    )

    await message.answer(
        f"Editing dream #{dream_id}: <b>{escape(dream.title)}</b>\n\n"
        "Select the field to edit:",
        reply_markup=keyboard,
    )


@router.callback_query(EditDreamStates.waiting_for_field, F.data.startswith("edit:"))
async def process_edit_field_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle field selection for editing."""
    if callback.message is None:
        return

    field = callback.data.split(":")[1]

    if field == "cancel":
        await state.clear()
        await callback.message.edit_text("Edit cancelled.")
        await callback.answer()
        return

    await state.update_data(edit_field=field)
    await state.set_state(EditDreamStates.waiting_for_value)

    field_names = {
        "title": "title",
        "description": "description",
        "tags": "tags",
        "notes": "notes",
        "dream_date": "date (YYYY-MM-DD)",
    }

    await callback.message.edit_text(
        f"Enter the new <b>{field_names[field]}</b>:\n"
        "(Use /cancel to abort)"
    )
    await callback.answer()


@router.message(EditDreamStates.waiting_for_value)
async def process_edit_value(message: Message, state: FSMContext) -> None:
    """Process the new value for the field."""
    if not message.text:
        await message.answer("Please enter a text value.")
        return

    data = await state.get_data()
    field = data["edit_field"]
    dream_id = data["edit_dream_id"]
    user_id = data["user_id"]

    value = message.text.strip()

    # Validate based on field
    if field == "title" and len(value) > 255:
        await message.answer("Title is too long (max 255 characters).")
        return
    if field == "tags" and len(value) > 500:
        await message.answer("Tags are too long (max 500 characters).")
        return
    if field == "dream_date":
        try:
            value = date.fromisoformat(value)
        except ValueError:
            await message.answer("Invalid date format. Use YYYY-MM-DD.")
            return

    async with async_session() as session:
        stmt = select(Dream).where(Dream.id == dream_id, Dream.user_id == user_id)
        result = await session.execute(stmt)
        dream = result.scalar_one_or_none()

        if dream is None:
            await message.answer("Dream not found.")
            await state.clear()
            return

        setattr(dream, field, value)
        await session.commit()

    await state.clear()
    await message.answer(
        f"Dream #{dream_id} updated successfully!\n"
        f"Use /view {dream_id} to see the changes."
    )


# --- DELETE DREAM ---


@router.message(Command("delete"))
async def cmd_delete(message: Message, command: CommandObject) -> None:
    """Delete a dream with confirmation."""
    if message.from_user is None:
        return

    user_id = await get_user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Please use /start first to register.")
        return

    if not command.args:
        await message.answer("Usage: /delete [id]\nExample: /delete 1")
        return

    try:
        dream_id = int(command.args.strip())
    except ValueError:
        await message.answer("Invalid ID. Please provide a number.")
        return

    dream = await get_dream_by_id(dream_id, user_id)
    if dream is None:
        await message.answer(f"Dream #{dream_id} not found.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Yes, delete",
                    callback_data=f"delete:confirm:{dream_id}",
                ),
                InlineKeyboardButton(
                    text="No, cancel",
                    callback_data="delete:cancel",
                ),
            ]
        ]
    )

    await message.answer(
        f"Are you sure you want to delete dream #{dream_id}?\n"
        f"<b>{escape(dream.title)}</b> ({dream.dream_date})\n\n"
        "This action cannot be undone.",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("delete:"))
async def process_delete_confirmation(callback: CallbackQuery) -> None:
    """Handle delete confirmation."""
    if callback.message is None or callback.from_user is None:
        return

    parts = callback.data.split(":")
    action = parts[1]

    if action == "cancel":
        await callback.message.edit_text("Deletion cancelled.")
        await callback.answer()
        return

    if action == "confirm":
        dream_id = int(parts[2])
        user_id = await get_user_id(callback.from_user.id)

        if user_id is None:
            await callback.answer("Please use /start first.")
            return

        async with async_session() as session:
            stmt = select(Dream).where(Dream.id == dream_id, Dream.user_id == user_id)
            result = await session.execute(stmt)
            dream = result.scalar_one_or_none()

            if dream is None:
                await callback.message.edit_text("Dream not found or already deleted.")
                await callback.answer()
                return

            await session.delete(dream)
            await session.commit()

        await callback.message.edit_text(f"Dream #{dream_id} has been deleted.")
        await callback.answer("Deleted")


# --- EXPORT DREAMS ---


def format_dream_for_export(dream: Dream, index: int) -> str:
    """Format a single dream for text export."""
    lines = [
        "=" * 40,
        f"Dream #{index} | {dream.dream_date}",
        "-" * 40,
        f"Title: {dream.title}",
    ]

    if dream.description:
        lines.append(f"\nDescription:\n{dream.description}")

    if dream.tags:
        lines.append(f"\nTags: {dream.tags}")

    if dream.notes:
        lines.append(f"\nNotes:\n{dream.notes}")

    lines.append("")
    return "\n".join(lines)


@router.message(Command("export"))
@router.message(F.text == BTN_EXPORT)
async def cmd_export(message: Message) -> None:
    """Export all user's dreams to a text file."""
    if message.from_user is None:
        return

    user_id = await get_user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Please use /start first to register.")
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
            "Your dream diary is empty.\nUse /new to create your first entry.",
            reply_markup=get_main_menu(),
        )
        return

    # Build text content
    lines = [
        "Dream Diary",
        f"Export date: {date.today()}",
        f"Total dreams: {len(dreams)}",
        "",
    ]

    for i, dream in enumerate(dreams, start=1):
        lines.append(format_dream_for_export(dream, i))

    content = "\n".join(lines)

    # Create file
    file_bytes = content.encode("utf-8")
    filename = f"dreams_export_{date.today()}.txt"
    input_file = BufferedInputFile(file_bytes, filename=filename)

    await message.answer_document(
        document=input_file,
        caption=f"Your dream diary export ({len(dreams)} dreams)",
        reply_markup=get_main_menu(),
    )

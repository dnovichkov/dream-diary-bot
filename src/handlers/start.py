from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select

from src.database import async_session
from src.models import User

router = Router()

HELP_TEXT = """
<b>Dream Diary Bot</b> - your personal dream journal.

<b>Available commands:</b>

/new - Create a new dream entry
/list - View your dreams (with pagination)
/search &lt;query&gt; - Search dreams by keywords
/view &lt;id&gt; - View a specific dream
/edit &lt;id&gt; - Edit a dream entry
/delete &lt;id&gt; - Delete a dream entry
/cancel - Cancel current operation
/help - Show this help message

<b>Dream entry structure:</b>
- Title (required)
- Description
- Tags (comma-separated keywords)
- Notes (personal comments)
- Date (defaults to today)
""".strip()


async def get_or_create_user(telegram_id: int) -> User:
    """Get existing user or create a new one."""
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            user = User(telegram_id=telegram_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command - register user and show welcome message."""
    if message.from_user is None:
        return

    await get_or_create_user(message.from_user.id)

    welcome_text = (
        f"Welcome to <b>Dream Diary Bot</b>!\n\n"
        f"This bot helps you keep a personal dream journal. "
        f"Record your dreams, add tags and notes, and search through them later.\n\n"
        f"Use /help to see available commands."
    )
    await message.answer(welcome_text)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command - show available commands."""
    await message.answer(HELP_TEXT)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Handle /cancel command - cancel current FSM operation."""
    current_state = await state.get_state()

    if current_state is None:
        await message.answer("Nothing to cancel.")
        return

    await state.clear()
    await message.answer("Operation cancelled.")

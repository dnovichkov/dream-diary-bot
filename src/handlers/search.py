from html import escape

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy import or_, select

from src.database import async_session
from src.handlers.dreams import get_user_id
from src.models import Dream

router = Router()


@router.message(Command("search"))
async def cmd_search(message: Message, command: CommandObject) -> None:
    """Search dreams by keywords in title, description, and tags."""
    if message.from_user is None:
        return

    user_id = await get_user_id(message.from_user.id)
    if user_id is None:
        await message.answer("Please use /start first to register.")
        return

    if not command.args:
        await message.answer(
            "Usage: /search [query]\n"
            "Example: /search flying\n\n"
            "Searches in title, description, and tags."
        )
        return

    query = command.args.strip().lower()

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
            await message.answer(f'No dreams found matching "{escape(query)}".')
            return

        lines = [f'<b>Search results for "{escape(query)}":</b>\n']
        for dream in dreams:
            lines.append(f"<b>#{dream.id}</b> {dream.format_short()}")

        lines.append(f"\nFound: {len(dreams)} entries")
        if len(dreams) == 20:
            lines.append("(Showing first 20 results)")
        lines.append("\nUse /view [id] to see details.")

        await message.answer("\n".join(lines))

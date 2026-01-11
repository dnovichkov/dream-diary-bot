import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from alembic import command
from alembic.config import Config

from src.config import settings
from src.database import init_db
from src.handlers import setup_routers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """Run Alembic migrations."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


async def main() -> None:
    """Initialize and start the bot."""
    logger.info("Starting Dream Diary Bot...")

    # Run database migrations
    logger.info("Running database migrations...")
    run_migrations()
    logger.info("Migrations completed")

    # Initialize database (creates tables if not exist)
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized")

    # Create bot instance
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Create dispatcher with FSM storage
    dp = Dispatcher(storage=MemoryStorage())

    # Setup routers
    router = setup_routers()
    dp.include_router(router)

    # Start polling
    logger.info("Bot is starting polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

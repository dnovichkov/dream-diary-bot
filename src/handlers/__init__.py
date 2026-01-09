from aiogram import Router

from . import start, dreams, search


def setup_routers() -> Router:
    """Create and configure the main router with all sub-routers."""
    router = Router()
    router.include_router(start.router)
    router.include_router(dreams.router)
    router.include_router(search.router)
    return router

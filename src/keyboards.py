"""Keyboard layouts for the bot."""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from src.locales import locale


def get_main_menu(lang: str = "en") -> ReplyKeyboardMarkup:
    """Get main menu keyboard."""
    t = lambda key: locale.get(lang, f"buttons.{key}")
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t("new_dream")),
                KeyboardButton(text=t("my_dreams")),
            ],
            [
                KeyboardButton(text=t("search")),
                KeyboardButton(text=t("export")),
            ],
            [
                KeyboardButton(text=t("help")),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder=locale.get(lang, "placeholders.main_menu"),
    )


def get_skip_cancel_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """Get keyboard with Skip and Cancel buttons for multi-step forms."""
    t = lambda key: locale.get(lang, f"buttons.{key}")
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t("skip")),
                KeyboardButton(text=t("cancel")),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder=locale.get(lang, "placeholders.skip_cancel"),
    )


def get_cancel_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """Get keyboard with only Cancel button (for required fields)."""
    t = lambda key: locale.get(lang, f"buttons.{key}")
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("cancel"))],
        ],
        resize_keyboard=True,
        input_field_placeholder=locale.get(lang, "placeholders.cancel"),
    )


def get_today_cancel_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """Get keyboard with Today and Cancel buttons for date input."""
    t = lambda key: locale.get(lang, f"buttons.{key}")
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t("today")),
                KeyboardButton(text=t("cancel")),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder=locale.get(lang, "placeholders.today_cancel"),
    )


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Get language selection keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="English", callback_data="lang:en"),
                InlineKeyboardButton(text="Русский", callback_data="lang:ru"),
            ]
        ]
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    """Remove reply keyboard."""
    return ReplyKeyboardRemove()

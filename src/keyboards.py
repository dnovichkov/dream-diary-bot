"""Keyboard layouts for the bot."""

from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

# Main menu buttons text
BTN_NEW_DREAM = "New dream"
BTN_MY_DREAMS = "My dreams"
BTN_SEARCH = "Search"
BTN_EXPORT = "Export"
BTN_HELP = "Help"
BTN_SKIP = "Skip"
BTN_TODAY = "Today"
BTN_CANCEL = "Cancel"


def get_main_menu() -> ReplyKeyboardMarkup:
    """Get main menu keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_NEW_DREAM),
                KeyboardButton(text=BTN_MY_DREAMS),
            ],
            [
                KeyboardButton(text=BTN_SEARCH),
                KeyboardButton(text=BTN_EXPORT),
            ],
            [
                KeyboardButton(text=BTN_HELP),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose an action or type a command...",
    )


def get_skip_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard with Skip and Cancel buttons for multi-step forms."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_SKIP),
                KeyboardButton(text=BTN_CANCEL),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Enter value, skip, or cancel...",
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard with only Cancel button (for required fields)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CANCEL)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Enter value or cancel...",
    )


def get_today_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard with Today and Cancel buttons for date input."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_TODAY),
                KeyboardButton(text=BTN_CANCEL),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Enter date or use today...",
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    """Remove reply keyboard."""
    return ReplyKeyboardRemove()

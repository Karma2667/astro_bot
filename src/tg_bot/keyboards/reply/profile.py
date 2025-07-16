from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton


async def get_location_reply() -> ReplyKeyboardMarkup:
    keyboard_buttons = [
        [KeyboardButton(text=_("share_location_btn"), request_location=True)],
        [KeyboardButton(text=_("decline_btn"))],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard_buttons, resize_keyboard=True, one_time_keyboard=True
    )

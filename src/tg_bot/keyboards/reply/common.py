from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton


async def get_menu_reply(locale: str = None) -> ReplyKeyboardMarkup:
    keyboard_buttons = [
        [
            KeyboardButton(text=_("horoscope_btn", locale=locale) if locale else _("horoscope_btn")),
            KeyboardButton(text=_("event_btn", locale=locale) if locale else _("event_btn")),
        ],
        [
            KeyboardButton(text=_("profile_btn", locale=locale) if locale else _("profile_btn")),
            KeyboardButton(text=_("taro_btn", locale=locale) if locale else _("taro_btn")),
        ],
        [
            KeyboardButton(text=_("help_btn", locale=locale) if locale else _("help_btn"))
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True)


async def get_decline_reply() -> ReplyKeyboardMarkup:
    keyboard_buttons = [[KeyboardButton(text=_("decline_btn"))]] 
    return ReplyKeyboardMarkup(
        keyboard=keyboard_buttons, resize_keyboard=True, one_time_keyboard=True
    )

from aiogram.utils.i18n import gettext as __ # type: ignore 
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton # type: ignore


async def get_menu_reply(locale: str = None) -> ReplyKeyboardMarkup:
    horoscope_text = __("horoscope_btn", locale=locale) if locale else __("horoscope_btn")
    event_text = __("event_btn", locale=locale) if locale else __("event_btn")
    profile_text = __("profile_btn", locale=locale) if locale else __("profile_btn")
    taro_text = __("taro_btn", locale=locale) if locale else __("taro_btn")
    angel_numbers_text = __("angel_numbers_btn", locale=locale) if locale else __("angel_numbers_btn")
    help_text = __("help_btn", locale=locale) if locale else __("help_btn")
    numerology_matrix_text = __("numerology_matrix_btn", locale=locale) if locale else __("numerology_matrix_btn")
    
    keyboard_buttons = [
        [
            KeyboardButton(text=horoscope_text),
            KeyboardButton(text=event_text),
        ],
        [
            KeyboardButton(text=profile_text),
            KeyboardButton(text=taro_text),
        ],
        [
            KeyboardButton(text=numerology_matrix_text), 
        ],
        [
            KeyboardButton(text=angel_numbers_text),
            KeyboardButton(text=help_text)
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True)


async def get_decline_reply() -> ReplyKeyboardMarkup:
    keyboard_buttons = [[KeyboardButton(text=__("decline_btn"))]] 
    return ReplyKeyboardMarkup(
        keyboard=keyboard_buttons, resize_keyboard=True, one_time_keyboard=True
    )

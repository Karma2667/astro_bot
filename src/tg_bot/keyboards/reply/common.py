# keyboards/reply/common.py
from aiogram.utils.i18n import gettext as __ # <-- Переименовали импорт
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton


async def get_menu_reply(locale: str = None) -> ReplyKeyboardMarkup:
    # Для кнопок меню используем контекстную локаль или переданную явно
    # Безопасно используем __ с проверкой
    horoscope_text = __("horoscope_btn", locale=locale) if locale else __("horoscope_btn")
    event_text = __("event_btn", locale=locale) if locale else __("event_btn")
    profile_text = __("profile_btn", locale=locale) if locale else __("profile_btn")
    taro_text = __("taro_btn", locale=locale) if locale else __("taro_btn")
    help_text = __("help_btn", locale=locale) if locale else __("help_btn")
    
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
            KeyboardButton(text=help_text)
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True)


async def get_decline_reply() -> ReplyKeyboardMarkup:
    # Для кнопки "Отмена" используем контекстную локаль
    keyboard_buttons = [[KeyboardButton(text=__("decline_btn"))]] # <-- Используем __
    return ReplyKeyboardMarkup(
        keyboard=keyboard_buttons, resize_keyboard=True, one_time_keyboard=True
    )

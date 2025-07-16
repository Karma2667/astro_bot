from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.inline.callback import BasicCallback


async def get_language_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("russian_btn"),
                    callback_data=BasicCallback.LANGUAGE + " " + "ru",
                ),
                InlineKeyboardButton(
                    text=_("english_btn"),
                    callback_data=BasicCallback.LANGUAGE + " " + "en",
                ),
            ],
        ]
    )

from aiogram.utils.i18n import gettext as _ # type: ignore
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton # type: ignore

from keyboards.inline.callback import HoroscopeCallback


async def get_horo_inline():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("today_btn"), callback_data=HoroscopeCallback.TODAY
                ),
                InlineKeyboardButton(
                    text=_("month_btn"), callback_data=HoroscopeCallback.MONTH
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_("date_btn"), callback_data=HoroscopeCallback.DATE
                ),
                InlineKeyboardButton(
                    text=_("zodiac_compatibility_btn"), callback_data=HoroscopeCallback.ZODIAC_COMPATIBILITY_START
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_("mail_btn"), callback_data=HoroscopeCallback.MAIL
                ),
            ],
        ]
    )


async def get_subscribe_inline():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("mail_subscribe_btn"),
                    callback_data=HoroscopeCallback.SUBSCRIBE,
                ),
            ],
        ]
    )


async def get_unsubscribe_inline():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("mail_unsubscribe_btn"),
                    callback_data=HoroscopeCallback.UNSUBSCRIBE,
                ),
            ],
        ]
    )

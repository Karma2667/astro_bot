from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.inline.callback import EventsCallback


async def get_events_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("event_study_btn"), callback_data=EventsCallback.STUDY
                ),
                InlineKeyboardButton(
                    text=_("event_mood_btn"), callback_data=EventsCallback.MOOD
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_("event_love_btn"), callback_data=EventsCallback.LOVE
                ),
                InlineKeyboardButton(
                    text=_("event_income_btn"), callback_data=EventsCallback.INCOME
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_("event_success_btn"), callback_data=EventsCallback.SUCCESS
                ),
            ],
        ]
    )


async def get_duration_freely_inline(theme: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("event_duration_45_btn"),
                    callback_data=EventsCallback.DURATION_45 + " " + theme,
                ),
                InlineKeyboardButton(
                    text=_("event_duration_90_btn"),
                    callback_data=EventsCallback.DURATION_90 + " " + theme,
                ),
            ],
        ]
    )


async def get_duration_paid_inline(theme: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("event_duration_45_btn"),
                    callback_data=EventsCallback.DURATION_45 + " " + theme,
                ),
                InlineKeyboardButton(
                    text=_("event_duration_90_btn"),
                    callback_data=EventsCallback.DURATION_90 + " " + theme,
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_("event_duration_180_btn"),
                    callback_data=EventsCallback.DURATION_180 + " " + theme,
                ),
                InlineKeyboardButton(
                    text=_("event_duration_365_btn"),
                    callback_data=EventsCallback.DURATION_365 + " " + theme,
                ),
            ],
        ]
    )

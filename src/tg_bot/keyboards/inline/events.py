from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from logger import bot_logger
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
                 InlineKeyboardButton(
                    text=_("event_compatibility_btn"), callback_data=EventsCallback.COMPATIBILITY
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

async def get_date_selection_inline(theme: str) -> InlineKeyboardMarkup:
    bot_logger.info(f"get_date_selection_inline: Creating keyboard for theme '{theme}'") 
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("today_btn"), # "📅 Сегодня"
                    callback_data=f"{EventsCallback.DURATION_TODAY} {theme}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_("tomorrow_btn"), # "📆 Завтра"
                    callback_data=f"{EventsCallback.DURATION_TOMORROW} {theme}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_("pick_date_btn"), # "🗓️ Выбрать дату"
                    callback_data=f"{EventsCallback.DURATION_PICK_DATE} {theme}"
                ),
            ],
        ]
    )
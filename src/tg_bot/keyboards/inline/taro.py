from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from logger import bot_logger
from keyboards.inline.callback import TaroCallback


async def get_taro_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("taro_study_btn"), callback_data=TaroCallback.STUDY
                ),
                InlineKeyboardButton(
                    text=_("taro_mood_btn"), callback_data=TaroCallback.MOOD
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_("taro_love_btn"), callback_data=TaroCallback.LOVE
                ),
                InlineKeyboardButton(
                    text=_("taro_income_btn"), callback_data=TaroCallback.INCOME
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_("taro_success_btn"), callback_data=TaroCallback.SUCCESS
                ),
                 InlineKeyboardButton(
                    text=_("taro_compatibility_btn"), callback_data=TaroCallback.COMPATIBILITY
                ),
            ],
        ]
    )


async def get_taro_date_selection_inline(theme: str) -> InlineKeyboardMarkup:
    bot_logger.info(f"get_date_selection_inline: Creating keyboard for theme '{theme}'") # Добавь это в клавиатуру, если есть bot_logger
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("today_btn"), # "📅 Сегодня"
                    callback_data=f"{TaroCallback.DURATION_TODAY.value} {theme}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_("tomorrow_btn"), # "📆 Завтра"
                    callback_data=f"{TaroCallback.DURATION_TOMORROW.value} {theme}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_("pick_date_btn"), # "🗓️ Выбрать дату"
                    callback_data=f"{TaroCallback.DURATION_PICK_DATE.value} {theme}"
                ),
            ],
        ]
    )
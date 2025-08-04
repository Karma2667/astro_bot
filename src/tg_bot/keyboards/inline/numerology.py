from aiogram.utils.i18n import gettext as _ # type: ignore
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton # type: ignore
from keyboards.inline.callback import NumerologyCallback

async def get_angel_numbers_start_inline():
    """Клавиатура начала толкования Ангельских чисел."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("angel_numbers_btn"), # "Ангельские числа"
                    callback_data=NumerologyCallback.START_ANGEL
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("angel_numbers_from_birthdate_btn"), # "Рассчитать из даты рождения"
                    callback_data=NumerologyCallback.START_BIRTHDATE_ANGEL
                )
            ],
        ]
    )
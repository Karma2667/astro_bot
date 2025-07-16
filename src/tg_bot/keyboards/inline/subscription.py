from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.inline.callback import SubscriptionCallback


async def get_subscription_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("sub_month_btn"), callback_data=SubscriptionCallback.MONTHLY
                ),
                InlineKeyboardButton(
                    text=_("sub_forever_btn"),
                    callback_data=SubscriptionCallback.FOREVER,
                ),
            ]
        ]
    )

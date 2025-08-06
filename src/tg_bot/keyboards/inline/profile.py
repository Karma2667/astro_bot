from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.inline.callback import ProfileCallback
from database.profile.models import Profile


async def get_profile_inline() -> InlineKeyboardButton:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("change_profile_btn"),
                    callback_data=ProfileCallback.CHANGE_PROFILE,
                ),
                InlineKeyboardButton(
                    text=_("change_data_btn"), callback_data=ProfileCallback.CHANGE_DATA
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_("delete_profile_btn"),
                    callback_data=ProfileCallback.DELETE_PROFILE,
                ),
                InlineKeyboardButton(
                    text=_("change_subscription_btn"),
                    callback_data=ProfileCallback.CHANGE_STATUS,
                ),
            ],
        ]
    )


async def get_profile_list_inline(profiles: list[Profile]) -> InlineKeyboardMarkup:
    buttons = []
    for profile in profiles:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=profile.title,
                    callback_data=ProfileCallback.PROFILE_OPTION
                    + " "
                    + str(profile.id),
                )
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                text=_("add_profile_btn"), callback_data=ProfileCallback.ADD_PROFILE
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_change_profile_data_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("profile_change_title_btn"),
                    callback_data=ProfileCallback.CHANGE_TITLE,
                ),
                InlineKeyboardButton(
                    text=_("profile_change_birth_date_btn"),
                    callback_data=ProfileCallback.CHANGE_BIRTH_DATE,
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_("profile_change_birth_time_btn"),
                    callback_data=ProfileCallback.CHANGE_BIRTH_TIME,
                ),
                InlineKeyboardButton(
                    text=_("profile_change_birth_location_btn"),
                    callback_data=ProfileCallback.CHANGE_BIRTH_LOCATION,
                ),
            ],
        ]
    )

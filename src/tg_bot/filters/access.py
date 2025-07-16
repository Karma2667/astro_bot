from aiogram.types import Message
from aiogram.filters import BaseFilter
from aiogram.utils.i18n import gettext as _
from aiogram.fsm.context import FSMContext

from database.profile.service import find_profiles_by_user_id
from keyboards.reply.common import get_menu_reply


class ProfileRegistered(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        user_id = message.from_user.id
        profiles = await find_profiles_by_user_id(user_id)
        if profiles and len(profiles) > 0:
            return True
        await message.answer(text=_('not_registered'), reply_markup=await get_menu_reply())
        return False
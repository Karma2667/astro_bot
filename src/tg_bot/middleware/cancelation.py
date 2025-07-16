from aiogram.types import Message
from aiogram.utils.i18n import gettext as _
from aiogram.dispatcher.middlewares.base import BaseMiddleware

from keyboards.reply.common import get_menu_reply

class DeclineMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()

    async def __call__(self, handler, event, data):
        if isinstance(event, Message) and event.text == _('decline_btn'):
            state = data.get('state')
            await state.clear()
            await event.answer(text=_('declined_msg'), reply_markup=await get_menu_reply())
            return
        else:
            return await handler(event, data)
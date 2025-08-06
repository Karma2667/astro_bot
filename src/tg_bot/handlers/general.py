from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import StateFilter 
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from logger import bot_logger

from handlers.basic import handle_help_cmd, handle_menu_cmd
from handlers.profile import handle_profile_cmd
from handlers.horoscope import handle_horoscope_cmd
from handlers.events import handle_event_cmd
from filters.access import ProfileRegistered


general_router = Router(name="general")

@general_router.message(StateFilter(None)) 
async def handle_any_msg(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} sending message: {message.text}")

    
    text = message.text
    if text:
        if text == _("horoscope_btn") and await ProfileRegistered()(
            message=message, state=state
        ):
            await handle_horoscope_cmd(message=message, state=state)
            return
        elif text == _("event_btn") and await ProfileRegistered()(
            message=message, state=state
        ):
            await handle_event_cmd(message=message, state=state)
            return
        elif text == _("profile_btn") and await ProfileRegistered()(
            message=message, state=state
        ):
            await handle_profile_cmd(message=message, state=state)
            return
        elif text == _("help_btn"):
            await handle_help_cmd(message=message, state=state)
            return

    await handle_menu_cmd(message=message, state=state)
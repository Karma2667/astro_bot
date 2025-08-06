from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
import re
from datetime import datetime, time, date

from logger import bot_logger
from keyboards.reply.common import get_menu_reply, get_decline_reply
from states.register import RegistrationStates
from database.profile.models import Profile
from database.user.models import User
from database.profile.service import create_profile, find_profiles_by_user_id
from database.user.service import find_user_by_id, set_current_profile
from typing import Optional


register_router = Router(name="register")


def get_zodiac_sign(birth_date: date) -> str:
    day = birth_date.day
    month = birth_date.month
    if (month == 3 and day >= 21) or (month == 4 and day <= 19): return "aries"
    if (month == 4 and day >= 20) or (month == 5 and day <= 20): return "taurus"
    if (month == 5 and day >= 21) or (month == 6 and day <= 20): return "gemini"
    if (month == 6 and day >= 21) or (month == 7 and day <= 22): return "cancer"
    if (month == 7 and day >= 23) or (month == 8 and day <= 22): return "leo"
    if (month == 8 and day >= 23) or (month == 9 and day <= 22): return "virgo"
    if (month == 9 and day >= 23) or (month == 10 and day <= 22): return "libra"
    if (month == 10 and day >= 23) or (month == 11 and day <= 21): return "scorpio"
    if (month == 11 and day >= 22) or (month == 12 and day <= 21): return "sagittarius"
    if (month == 12 and day >= 22) or (month == 1 and day <= 19): return "capricorn"
    if (month == 1 and day >= 20) or (month == 2 and day <= 18): return "aquarius"
    if (month == 2 and day >= 19) or (month == 3 and day <= 20): return "pisces"
    return "unknown"


@register_router.message(Command("register"))
async def handle_register_cmd(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} is registering")
    user_id = message.from_user.id
    user_profiles = await find_profiles_by_user_id(user_id=user_id)
    if user_profiles and len(user_profiles) >= 3:
        await message.answer(text=_("max_profiles_msg"), reply_markup=await get_menu_reply())
    else:
        await message.answer(text=_("send_prof_name_msg"), reply_markup=await get_decline_reply())
        await state.set_state(RegistrationStates.title.state)

@register_router.message(RegistrationStates.title)
async def handle_title_state(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} sending title: {message.text}")
    if message.text:
        await state.update_data(title=message.text)
        await message.answer(text=_("send_birth_date_msg"))
        await state.set_state(RegistrationStates.birth_date.state)
    else:
        await message.answer(text=_("prof_name_err_msg"))

@register_router.message(RegistrationStates.birth_date)
async def handle_birth_date_state(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} sending birth date: {message.text}")
    date_pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    if message.text and re.match(date_pattern, message.text):
        try:
            birth_date = datetime.strptime(message.text, "%d.%m.%Y").date()
            current_date = datetime.now().date()
            if birth_date.year >= 1900 and birth_date < current_date:
                await state.update_data(birth_date=message.text)
                await message.answer(text=_("send_birth_time_msg"))
                await state.set_state(RegistrationStates.birth_time.state)
            else:
                await message.answer(text=_("birth_date_err_msg"))
        except ValueError:
            await message.answer(text=_("birth_date_err_msg"))
    else:
        await message.answer(text=_("birth_date_err_msg"))

@register_router.message(RegistrationStates.birth_time)
async def handle_birth_time_state(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} sending birth time: {message.text}")
    time_pattern = r"^\d{2}:\d{2}$"
    if message.text and re.match(time_pattern, message.text):
        try:
            birth_time = datetime.strptime(message.text, "%H:%M").time()
            if birth_time.hour < 24 and birth_time.minute < 60:
                await state.update_data(birth_time=message.text)
                await message.answer(text=_("send_birth_location_msg"))
                await state.set_state(RegistrationStates.birth_location.state)
            else:
                await message.answer(text=_("birth_time_err_msg"))
        except ValueError:
            await message.answer(text=_("birth_time_err_msg"))
    else:
        await message.answer(text=_("birth_time_err_msg"))

@register_router.message(RegistrationStates.birth_location)
async def handle_birth_location_state(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} sending birth location: {message.text}")
    if message.text:
        await state.update_data(birth_location=message.text)
        await register(message=message, state=state)
    else:
        await message.answer(text=_("birth_location_err_msg"))

async def process_data(fsm_data: dict, user: User) -> Optional[Profile]:
    try:
        birth_date = datetime.strptime(fsm_data.get("birth_date"), "%d.%m.%Y").date()
        zodiac_sign = get_zodiac_sign(birth_date)
        
        profile = Profile(
            user_id=user.user_id,
            title=fsm_data.get("title"),
            birth_date=birth_date,
            birth_time=datetime.strptime(fsm_data.get("birth_time"), "%H:%M").time(),
            birth_location_name=fsm_data.get("birth_location"),
            zodiac_sign=zodiac_sign, # Знак зодиака добавляется здесь
        )
        
        created_profile = await create_profile(profile=profile)
        return created_profile
    except Exception as e:
        bot_logger.error(f"Exception in process_data: {e}", exc_info=True)
        return None

async def register(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        user = await find_user_by_id(user_id=user_id)
        if not user:
            await message.answer(text=_("user_not_found_msg"))
            return

        fsm_data = await state.get_data()
        new_profile = await process_data(fsm_data=fsm_data, user=user)

        if new_profile is None:
            await message.answer(text=_("error_msg"))
            await state.clear()
            return

        if not user.current_profile_id:
            await set_current_profile(user_id=user_id, profile_id=new_profile.id)
            await message.answer(text=_("new_profile_msg"), reply_markup=await get_menu_reply())
        else:
            await message.answer(text=_("add_profile_msg"), reply_markup=await get_menu_reply())

        await state.clear()
    except Exception as e:
        bot_logger.error(f"Exception in register function: {e}", exc_info=True)
        await message.answer(text=_("error_msg"))
        await state.clear()

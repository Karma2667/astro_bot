from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from timezonefinder import TimezoneFinder

import re
import pytz
from datetime import datetime, time

from logger import bot_logger
from keyboards.reply.common import get_menu_reply, get_decline_reply
from keyboards.reply.register import get_location_reply
from states.register import RegistrationStates
from database.profile.models import Profile
from database.user.models import User
from database.profile.service import create_profile, find_profiles_by_user_id
from database.user.service import find_user_by_id, set_current_profile


register_router = Router(name="register")


@register_router.message(Command("register"))
async def handle_register_cmd(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} is registering")
    user_id = message.from_user.id
    user_profiles = await find_profiles_by_user_id(user_id=user_id)
    if user_profiles and len(user_profiles) >= 3:
        await message.answer(
            text=_("max_profiles_msg"), reply_markup=await get_menu_reply()
        )
    else:
        await message.answer(
            text=_("send_prof_name_msg"), reply_markup=await get_decline_reply()
        )
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
    bot_logger.info(
        f"User {message.from_user.id} sending birth location: {message.text}"
    )
    if message.text:
        await state.update_data(birth_location=message.text)
        # await message.answer(
        #     text=_("send_current_location_msg"), reply_markup=await get_location_reply()
        # )
        await register(message=message, state=state)
    else:
        await message.answer(text=_("birth_location_err_msg"))


# @register_router.message(RegistrationStates.current_location)
# async def handle_current_location_state(message: Message, state: FSMContext):
#     bot_logger.info(
#         f"User {message.from_user.id} sending current location: {message.text}"
#     )
#     if message.location:
#         longitude, latitude = (
#             str(message.location.longitude),
#             str(message.location.latitude),
#         )
#         await state.update_data(location_longitude=longitude)
#         await state.update_data(location_latitude=latitude)
#         await register(message=message, state=state)
#     else:
#         await message.answer(text=_("current_location_err_msg"))


async def process_data(fsm_data: dict, user: User) -> Profile:
    user_id = user.user_id
    user = await find_user_by_id(user_id=user_id)
    title = fsm_data.get("title")

    try:
        birth_date = datetime.strptime(fsm_data.get("birth_date"), "%d.%m.%Y").date()
    except (ValueError, TypeError):
        raise ValueError("Invalid birth_date format. Expected DD.MM.YYYY")

    try:
        birth_time_obj = datetime.strptime(fsm_data.get("birth_time"), "%H:%M").time()
    except (ValueError, TypeError):
        birth_time_obj = time(0, 0)

    birth_location_name = fsm_data.get("birth_location")

    # location_latitude = float(fsm_data.get("location_latitude"))
    # location_longitude = float(fsm_data.get("location_longitude"))

    # tf = TimezoneFinder()
    # location_timezone_str = (
    #     tf.timezone_at(lat=location_latitude, lng=location_longitude) or "UTC"
    # )
    # location_timezone = pytz.timezone(location_timezone_str)

    # Get the UTC offset
    # location_offset = (
    #     location_timezone.utcoffset(datetime.now()).total_seconds() // 3600
    # )
    # location_timezone_offset = (
    #     f"{'+' if location_offset >= 0 else '-'}{abs(int(location_offset))}"
    # )

    profile = Profile(
        user_id=user_id,
        title=title,
        birth_date=birth_date,
        birth_time=birth_time_obj,
        birth_location_name=birth_location_name
        # location_latitude=location_latitude,
        # location_longitude=location_longitude,
        # location_timezone=location_timezone_offset,
    )

    return await create_profile(profile=profile)


async def register(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await find_user_by_id(user_id=user_id)

    if not user:
        await message.answer(
            text=_("user_not_found_msg"), reply_markup=await get_decline_reply()
        )
        await state.clear()
        return

    new_profile = await process_data(fsm_data=await state.get_data(), user=user)

    if not user.current_profile_id:
        updated_user = await set_current_profile(
            user_id=user_id, profile_id=new_profile.id
        )
        if updated_user:
            await message.answer(
                text=_("new_profile_msg"), reply_markup=await get_menu_reply()
            )
        else:
            await message.answer(
                text=_("error_setting_current_profile_msg"),
                reply_markup=await get_decline_reply(),
            )
    else:
        await message.answer(
            text=_("add_profile_msg"), reply_markup=await get_menu_reply()
        )

    await state.clear()

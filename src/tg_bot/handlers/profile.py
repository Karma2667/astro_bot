from aiogram import Router, F # type: ignore
from aiogram.filters import Command # type: ignore
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton # type: ignore
from aiogram.fsm.context import FSMContext # type: ignore
from aiogram.utils.i18n import gettext as _ # type: ignore
import re
from datetime import datetime, date


from logger import bot_logger
from handlers.register import handle_register_cmd
from handlers.subscription import handle_subscription_cmd
from filters.access import ProfileRegistered
from states.profile import ChangeDataStates
from keyboards.reply.common import get_menu_reply, get_decline_reply
from keyboards.inline.callback import ProfileCallback
from keyboards.inline.profile import (
    get_profile_inline,
    get_profile_list_inline,
    get_change_profile_data_inline,
)
from database.user.service import find_user_by_id, update_user
from database.profile.models import Profile
from database.profile.service import (
    find_current_profile_by_user_id,
    find_profiles_by_user_id,
    find_profile_by_id,
    delete_profile,
    update_profile,
    create_profile,
)
from datetime import datetime # Для форматирования даты
from database.user.models import Subscription # Для проверки типа подписки
from database.user.service import find_user_by_id # Для получения объекта User


profile_router = Router(name="profile")

# === ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ОПРЕДЕЛЕНИЯ ЗНАКА ЗОДИАКА ===
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


async def format_profile(user: "User", profile: Profile) -> str:
    if profile is None:
        return _("no_profile_msg")
    
    if profile.zodiac_sign:
        zodiac_key = f"profile_zodiac_{profile.zodiac_sign.lower()}"
        zodiac_info = _(zodiac_key)
        if zodiac_info == zodiac_key: 
             bot_logger.warning(f"Translation for zodiac sign '{zodiac_key}' not found.")
             zodiac_info = profile.zodiac_sign.capitalize()
    else:
        zodiac_info = _("no_zodiac_msg")
    
    profile_lines = [
        f'<b>{_("profile_title_msg")}</b>', # "Профиль"
        f'{_("profile_name_msg")} {profile.title}', # Используем profile.title
        f'{_("profile_birth_msg")} {profile.birth_date.strftime("%d.%m.%Y")} {profile.birth_time.strftime("%H:%M")}',
        f'{_("profile_birth_location_msg")} {profile.birth_location_name or _("unknown_location")}',
        f'{_("profile_zodiac_msg")} {zodiac_info}',
        "", # Пустая строка как разделитель
    ]
    profile_info_text = "\n".join(profile_lines)
    subscription_lines = [f'<b>{_("subscription_info_title")}</b>'] # "Информация о подписке"
    
    subscription_type_key = f"subscription_type_{user.subscription.value}"
    subscription_type_text = _(subscription_type_key)
    subscription_lines.append(f"{_('subscription_type_label')}: {subscription_type_text}") # "Тип подписки: ..."

    if user.subscription not in [Subscription.FOREVER, Subscription.FREELY]:
        if user.subscription_expiration_date:
            expiration_text = user.subscription_expiration_date.strftime("%d.%m.%Y")
            subscription_lines.append(f"{_('subscription_expires_label')}: {expiration_text}") # "Действует до: ..."
        else:
            subscription_lines.append(f"{_('subscription_expires_label')}: {('subscription_unknown_expiration_text')}") # Нужно добавить перевод
    elif user.subscription == Subscription.FOREVER:
         subscription_lines.append(f"{_('subscription_expires_label')}: {('subscription_never_expires_text')}") # "Бессрочная"    # Для Subscription.FREELY дата истечения не показывается.
    
    subscription_info_text = "\n".join(subscription_lines)
    # Объединяем обе части
    final_text = f"{profile_info_text}\n{subscription_info_text}"
    return final_text


@profile_router.message(Command("profile"), ProfileRegistered())
async def handle_profile_cmd(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} using command /profile")
    user_id = message.from_user.id
    
    user = await find_user_by_id(user_id=user_id)
    if not user:
        await message.answer(_("error_msg")) # Или более специфичное сообщение об ошибке
        return
    
    profile = await find_current_profile_by_user_id(user_id=user_id)
    if profile is None:
        await message.answer(_("no_active_profile_msg"))
        await handle_register_cmd(message, state)
        return
    
    profile_text = await format_profile(user=user, profile=profile)
    
    await message.answer(text=profile_text, reply_markup=await get_profile_inline())
    
async def get_zodiac_inline():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    signs = ["aries", "taurus", "gemini", "cancer", "leo", "virgo",
             "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    buttons = [InlineKeyboardButton(text=sign.capitalize(), callback_data=f"zodiac_{sign}") for sign in signs]
    keyboard.inline_keyboard = [[button] for button in buttons] # Каждая кнопка на новой строке
    return keyboard

@profile_router.callback_query(F.data.startswith("zodiac_"))
async def process_zodiac_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} using callback {callback.data}")
    sign = callback.data.split("_")[1]
    user_id = callback.message.chat.id
    profile = await find_current_profile_by_user_id(user_id=user_id)
    if profile:
        await update_profile(profile_id=profile.id, update_data={"zodiac_sign": sign})
        await callback.message.answer(
            text=_("zodiac_set_msg").format(sign=sign.capitalize()),
            reply_markup=await get_menu_reply()
        )
    else:
        await callback.message.answer(text=_("user_not_found_msg"))
    await callback.answer()
    

@profile_router.callback_query(F.data.startswith(ProfileCallback.CHANGE_PROFILE))
async def handle_change_profile_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} using callback {callback.data}")
    user_id = callback.message.chat.id
    user_profiles = await find_profiles_by_user_id(user_id=user_id)
    await callback.message.answer(
        text=_("choose_profile_msg"),
        reply_markup=await get_profile_list_inline(profiles=user_profiles),
    )
    await callback.answer()

@profile_router.callback_query(F.data.startswith(ProfileCallback.CHANGE_DATA))
async def handle_change_data_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} using callback {callback.data}")
    await callback.message.answer(
        text=_("prefer_to_change_msg"),
        reply_markup=await get_change_profile_data_inline(),
    )
    await callback.answer()

@profile_router.callback_query(F.data.startswith(ProfileCallback.DELETE_PROFILE))
async def handle_delete_profile_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} using callback {callback.data}")
    user_id = callback.message.chat.id
    user = await find_user_by_id(user_id=user_id)
    profile = await find_profile_by_id(profile_id=user.current_profile_id)
    await delete_profile(profile_id=profile.id)
    user_profiles = await find_profiles_by_user_id(user_id=user_id)
    if user_profiles and len(user_profiles) > 0:
        new_current_profile = user_profiles[0]
        await update_user(user_id=user_id, update_data={"current_profile_id": new_current_profile.id})
        await callback.message.answer(text=_("profile_deleted_changed_msg"))
    else:
        await callback.message.answer(text=_("profile_deleted_new_msg"))
    await callback.answer()

@profile_router.callback_query(F.data.startswith(ProfileCallback.CHANGE_STATUS))
async def handle_change_status_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} using callback {callback.data}")
    await handle_subscription_cmd(message=callback.message, state=state)
    await callback.answer()

@profile_router.callback_query(F.data.startswith(ProfileCallback.PROFILE_OPTION))
async def handle_profile_option_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} using callback {callback.data}")
    profile_id = int(callback.data.split()[1])
    user_id = callback.message.chat.id
    await update_user(user_id=user_id, update_data={"current_profile_id": profile_id})
    await callback.message.answer(text=_("profile_changed_msg"))
    await callback.answer()

@profile_router.callback_query(F.data.startswith(ProfileCallback.ADD_PROFILE))
async def handle_add_profile_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} using callback {callback.data}")
    await handle_register_cmd(message=callback.message, state=state)
    await callback.answer()

@profile_router.callback_query(F.data.startswith(ProfileCallback.CHANGE_TITLE))
async def handle_change_title_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChangeDataStates.title.state)
    await callback.message.answer(text=_("send_prof_name_msg"), reply_markup=await get_decline_reply())
    await callback.answer()

@profile_router.callback_query(F.data.startswith(ProfileCallback.CHANGE_BIRTH_DATE))
async def handle_change_birth_date_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChangeDataStates.birth_date.state)
    await callback.message.answer(text=_("send_birth_date_msg"), reply_markup=await get_decline_reply())
    await callback.answer()

@profile_router.callback_query(F.data.startswith(ProfileCallback.CHANGE_BIRTH_TIME))
async def handle_change_birth_time_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChangeDataStates.birth_time.state)
    await callback.message.answer(text=_("send_birth_time_msg"), reply_markup=await get_decline_reply())
    await callback.answer()

@profile_router.callback_query(F.data.startswith(ProfileCallback.CHANGE_BIRTH_LOCATION))
async def handle_change_birth_location_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChangeDataStates.birth_location.state)
    await callback.message.answer(text=_("send_birth_location_msg"), reply_markup=await get_decline_reply())
    await callback.answer()

@profile_router.message(ChangeDataStates.title)
async def handle_profile_change_title(message: Message, state: FSMContext):
    if message.text and len(message.text) <= 100:
        user_id = message.from_user.id
        current_profile = await find_current_profile_by_user_id(user_id=user_id)
        await update_profile(profile_id=current_profile.id, update_data={"title": message.text})
        await message.answer(text=_("title_changed_msg"), reply_markup=await get_menu_reply())
        await state.clear()
    else:
        await message.answer(text=_("prof_name_err_msg"), reply_markup=await get_decline_reply())

@profile_router.message(ChangeDataStates.birth_date)
async def handle_profile_change_birth_date(message: Message, state: FSMContext):
    date_pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    if message.text and re.match(date_pattern, message.text):
        user_id = message.from_user.id
        current_profile = await find_current_profile_by_user_id(user_id=user_id)
        try:
            birth_date = datetime.strptime(message.text, "%d.%m.%Y").date()
            if 1900 <= birth_date.year < datetime.now().year:
                update_data = {
                    "birth_date": birth_date,
                    "zodiac_sign": get_zodiac_sign(birth_date)
                }
                await update_profile(profile_id=current_profile.id, update_data=update_data)
                
                await message.answer(
                    text=_("birth_date_changed_and_zodiac_msg").format(zodiac=update_data["zodiac_sign"].capitalize()),
                    reply_markup=await get_menu_reply()
                )
                await state.clear()
            else:
                await message.answer(text=_("birth_date_err_msg"), reply_markup=await get_decline_reply())
        except ValueError:
            await message.answer(text=_("birth_date_err_msg"), reply_markup=await get_decline_reply())
    else:
        await message.answer(text=_("birth_date_err_msg"), reply_markup=await get_decline_reply())

@profile_router.message(ChangeDataStates.birth_time)
async def handle_profile_change_birth_time(message: Message, state: FSMContext):
    time_pattern = r"^\d{2}:\d{2}$"
    if message.text and re.match(time_pattern, message.text):
        user_id = message.from_user.id
        current_profile = await find_current_profile_by_user_id(user_id=user_id)
        try:
            birth_time = datetime.strptime(message.text, "%H:%M").time()
            await update_profile(profile_id=current_profile.id, update_data={"birth_time": birth_time})
            await message.answer(text=_("birth_time_changed_msg"), reply_markup=await get_menu_reply())
            await state.clear()
        except ValueError:
            await message.answer(text=_("birth_time_err_msg"), reply_markup=await get_decline_reply())
    else:
        await message.answer(text=_("birth_time_err_msg"), reply_markup=await get_decline_reply())
        
@profile_router.message(ChangeDataStates.birth_location)
async def handle_profile_change_birth_location(message: Message, state: FSMContext):
    if message.text and len(message.text) <= 200:
        user_id = message.from_user.id
        current_profile = await find_current_profile_by_user_id(user_id=user_id)
        await update_profile(profile_id=current_profile.id, update_data={"birth_location_name": message.text})
        await message.answer(text=_("birth_location_changed_msg"), reply_markup=await get_menu_reply())
        await state.clear()
    else:
        await message.answer(text=_("birth_location_err_msg"), reply_markup=await get_decline_reply())
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

import re
from datetime import datetime

from logger import bot_logger
from states.horoscope import DateState
from filters.access import ProfileRegistered
from keyboards.reply.common import get_decline_reply
from keyboards.inline.callback import HoroscopeCallback
from keyboards.reply.common import get_menu_reply
from keyboards.inline.horoscope import (
    get_horo_inline,
    get_subscribe_inline,
    get_unsubscribe_inline,
)
from gpt.template import load_template, inject_profile_into_template, TemplateType
from gpt.gpt import send_gpt_request
from database.user.models import Subscription
from database.user.service import find_user_by_id, update_user
from database.profile.models import Profile
from database.profile.service import find_current_profile_by_user_id
from database.predictions.models import Prediction, PredictionType
from database.predictions.service import (
    create_prediction,
    find_prediction_by_recognition_and_type,
)

horoscope_router = Router(name="horoscope")

async def shorten_horoscope(sub: Subscription, horoscope: str) -> str:
    if sub is Subscription.FREELY:
        crop_idx = len(horoscope) // 3
        return horoscope[:crop_idx] + "..."
    return horoscope

async def format_horoscope(sub: Subscription, horoscope: str) -> str:
    extra = ""
    if sub is Subscription.FREELY:
        extra = f'\n\n{_("freely_unavailable_msg")}'
    return await shorten_horoscope(sub=sub, horoscope=horoscope) + extra

async def make_horoscope(user_id: int, date: str) -> str:
    user = await find_user_by_id(user_id=user_id)
    user_profile = await find_current_profile_by_user_id(user_id=user_id)
    
    if not user_profile.zodiac_sign:
        return _("no_zodiac_msg")

    # --- Логика определения recognition_str остается без изменений ---
    match date:
        case "today":
            recognition_str = datetime.today().strftime("%d.%m.%Y")
        case "month":
            recognition_str = datetime.today().strftime("%m.%Y")
        case _:
            recognition_str = date
    recognition_str = f'{recognition_str} {user.locale} {user_profile.id}'
    
    db_horoscope = await find_prediction_by_recognition_and_type(
        recognition_str=recognition_str, prediction_type=PredictionType.HOROSCOPE
    )

    if db_horoscope:
        return await format_horoscope(
            sub=user.subscription, horoscope=db_horoscope.prediction
        )
    
    template = await load_template(
        locale=user.locale, template_type=TemplateType.HOROSCOPE
    )

    # 1. Получаем системное имя знака из БД (например, "Aries")
    zodiac_sign_key = user_profile.zodiac_sign.lower() # .lower() для надежности
    
    # 2. Переводим его, используя контекст i18n. 
    #    Функция _() сама поймет, что у user.locale = 'ru' и возьмет нужный перевод.
    translated_zodiac_sign = _(zodiac_sign_key)

    # 3. Используем уже переведенное значение в промпте
    prompt = await inject_profile_into_template(
        extra=f"зодиак {translated_zodiac_sign}, {date}", template=template, profile=user_profile
    )
    # ---------------------------

    response = await send_gpt_request(prompt=prompt)
    
    if not response:
        return _("error_msg")

    await create_prediction(
        Prediction(
            profile_id=user_profile.id,
            prediction=response,
            prediction_type=PredictionType.HOROSCOPE,
            recognition_str=recognition_str,
        )
    )

    return await format_horoscope(sub=user.subscription, horoscope=response)

@horoscope_router.message(Command("horoscope"), ProfileRegistered())
async def handle_horoscope_cmd(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} using command /horoscope")
    user_profile = await find_current_profile_by_user_id(user_id=message.from_user.id)
    if not user_profile.zodiac_sign:
        await message.answer(
            text=_("no_zodiac_msg"),
            reply_markup=await get_decline_reply()
        )
        return
    await message.answer(
        text=_("create_horoscope_option_msg"),
        reply_markup=await get_horo_inline()
    )

@horoscope_router.callback_query(F.data.startswith(HoroscopeCallback.TODAY))
async def handle_today_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} using callback {callback.data}")
    wait_msg = await callback.message.answer(text=_("wait_calc_msg"))
    horoscope = await make_horoscope(user_id=callback.message.chat.id, date="today")
    await wait_msg.delete()
    await callback.message.answer(text=horoscope, reply_markup=await get_menu_reply())
    await callback.answer()

@horoscope_router.callback_query(F.data.startswith(HoroscopeCallback.MONTH))
async def handle_month_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} using callback {callback.data}")
    wait_msg = await callback.message.answer(text=_("wait_calc_msg"))
    horoscope = await make_horoscope(user_id=callback.message.chat.id, date="month")
    await wait_msg.delete()
    await callback.message.answer(text=horoscope, reply_markup=await get_menu_reply())
    await callback.answer()

@horoscope_router.callback_query(F.data.startswith(HoroscopeCallback.DATE))
async def handle_date_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} using callback {callback.data}")
    await callback.message.answer(
        text=_("ask_date_msg"), reply_markup=await get_decline_reply()
    )
    await state.set_state(DateState.date.state)
    await callback.answer()

@horoscope_router.message(DateState.date)
async def handle_date(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} sending date: {message.text}")
    date_pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    if message.text and re.match(date_pattern, message.text):
        try:
            # Преобразование текста в дату остается для валидации
            datetime.strptime(message.text, "%d.%m.%Y").date() 
            
            # Убрана проверка на будущую дату
            wait_msg = await message.answer(text=_("wait_calc_msg"))
            horoscope = await make_horoscope(user_id=message.from_user.id, date=message.text)
            await wait_msg.delete()
            await message.answer(text=horoscope, reply_markup=await get_menu_reply())
            await state.clear()
            
        except ValueError:
            # Эта ошибка сработает, если дата некорректна, например, 32.12.2024
            await message.answer(text=_("date_error_msg"), reply_markup=await get_decline_reply())
    else:
        # Эта ошибка сработает, если формат не ДД.ММ.ГГГГ
        await message.answer(text=_("date_error_msg"), reply_markup=await get_decline_reply())

@horoscope_router.callback_query(F.data.startswith(HoroscopeCallback.MAIL))
async def handle_mail_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} using callback {callback.data}")
    user_id = callback.message.chat.id
    user = await find_user_by_id(user_id=user_id)
    if user.is_mail_subscribed:
        await callback.message.answer(
            text=_("mail_subscribed_msg").format(str(await callback.bot.get_my_name()).split("'")[1]),
            reply_markup=await get_unsubscribe_inline()
        )
    else:
        await callback.message.answer(
            text=_("mail_unsubscribe_msg"),
            reply_markup=await get_subscribe_inline()
        )
    await callback.answer()

@horoscope_router.callback_query(F.data.startswith(HoroscopeCallback.SUBSCRIBE))
async def handle_subscribe_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} using callback {callback.data}")
    user_id = callback.message.chat.id
    user = await find_user_by_id(user_id=user_id)
    user.is_mail_subscribed = True
    await update_user(user_id=user_id, updated_user=user)
    await callback.message.edit_text(
        text=_("mail_subscribed_msg").format(str(await callback.bot.get_my_name()).split("'")[1]),
        reply_markup=await get_unsubscribe_inline()
    )
    await callback.answer()

@horoscope_router.callback_query(F.data.startswith(HoroscopeCallback.UNSUBSCRIBE))
async def handle_unsubscribe_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} using callback {callback.data}")
    user_id = callback.message.chat.id
    user = await find_user_by_id(user_id=user_id)
    user.is_mail_subscribed = False
    await update_user(user_id=user_id, updated_user=user)
    await callback.message.edit_text(
        text=_("mail_unsubscribe_msg"),
        reply_markup=await get_subscribe_inline()
    )
    await callback.answer()

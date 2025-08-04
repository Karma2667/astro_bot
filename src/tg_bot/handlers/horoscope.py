from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

import re
from datetime import datetime

from logger import bot_logger
from states.horoscope import DateState, CompatibilitySignsState
from filters.access import ProfileRegistered
from keyboards.reply.common import get_decline_reply
from keyboards.inline.callback import HoroscopeCallback
from keyboards.reply.common import get_menu_reply
from keyboards.inline.horoscope import (
    get_horo_inline,
    get_subscribe_inline,
    get_unsubscribe_inline,
)
from data.zodiac_signs import VALID_ZODIAC_SIGNS_LOWER
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

# handlers/horoscope.py
# ... (существующий код) ...

# --- НОВАЯ ФУНКЦИЯ ---
async def make_zodiac_compatibility(sign1_key: str, sign2_key: str, locale: str) -> str:
    """
    Генерирует совместимость двух знаков Зодиака.
    sign1_key, sign2_key - нормализованные (нижний регистр, без пробелов) названия знаков
                          (ключи из VALID_ZODIAC_SIGNS_LOWER).
    locale - локаль пользователя (например, "ru").
    """
    bot_logger.info(f"[Zodiac Compatibility] make_zodiac_compatibility called: sign1='{sign1_key}', sign2='{sign2_key}', locale='{locale}'")

    # 1. Проверка валидности входных данных
    if sign1_key not in VALID_ZODIAC_SIGNS_LOWER or sign2_key not in VALID_ZODIAC_SIGNS_LOWER:
        bot_logger.error(f"[Zodiac Compatibility] Invalid sign keys provided: '{sign1_key}', '{sign2_key}'")
        return _("error_generating_prediction_msg")

    # 2. Получаем оригинальные (системные) названия знаков для формирования ключа кэша
    original_sign1 = VALID_ZODIAC_SIGNS_LOWER[sign1_key]
    original_sign2 = VALID_ZODIAC_SIGNS_LOWER[sign2_key]

    # 3. Формируем ключ для кэширования
    # Сортируем имена, чтобы порядок ввода не влиял на ключ (Овен+Лев = Лев+Овен)
    sorted_signs = sorted([original_sign1, original_sign2])
    cache_key = f"zcompat_{sorted_signs[0]}_{sorted_signs[1]}_{locale}"

    # 4. Проверяем кэш (предполагается, что PredictionType.ZODIAC_COMPATIBILITY определен)
    try:
        db_result = await find_prediction_by_recognition_and_type(
            recognition_str=cache_key, prediction_type=PredictionType.ZODIAC_COMPATIBILITY
        )
        if db_result:
            bot_logger.info(f"[Zodiac Compatibility] Found in DB for key: {cache_key}")
            return db_result.prediction
    except Exception as e:
        bot_logger.warning(f"[Zodiac Compatibility] Error checking cache for key {cache_key}: {e}", exc_info=True)

    bot_logger.info(f"[Zodiac Compatibility] Not in DB. Calling GPT for key: {cache_key}")

    try:
        # 5. Загружаем шаблон для совместимости
        # Убедитесь, что TemplateType.ZODIAC_COMPATIBILITY определен и шаблон существует
        template = await load_template(
            locale=locale,
            template_type=TemplateType.ZODIAC_COMPATIBILITY
        )
    except Exception as e:
        bot_logger.error(f"[Zodiac Compatibility] Error loading template: {e}", exc_info=True)
        return _("error_generating_prediction_msg")

    # 6. Переводим названия знаков для использования в промпте
    # Предполагается, что в .po файлах ключи перевода - это системные имена знаков в нижнем регистре и с подчеркиванием
    # Например, msgid "aries" -> msgstr "Овен"
    translated_sign1 = _(original_sign1.lower().replace(" ", "_"))
    translated_sign2 = _(original_sign2.lower().replace(" ", "_"))

    # 7. Подставляем знаки в шаблон
    prompt = template.format(sign1=translated_sign1, sign2=translated_sign2)
    bot_logger.debug(f"[Zodiac Compatibility] Prepared prompt (len={len(prompt)}). First 150 chars: '{prompt[:150]}...'")

    # 8. Вызываем GPT
    try:
        response = await send_gpt_request(prompt=prompt)
        bot_logger.info(f"[Zodiac Compatibility] GPT API call completed. Response is None/Empty: {not response or not response.strip()}")
    except Exception as e:
        bot_logger.error(f"[Zodiac Compatibility] Exception during GPT API call: {e}", exc_info=True)
        return _("error_generating_prediction_msg")

    if not response or not response.strip():
        bot_logger.error(f"[Zodiac Compatibility] Failed to get a valid response from GPT API.")
        return _("error_generating_prediction_msg")

    response_text = response.strip()

    # 9. Сохраняем результат в БД
    # Для этого типа предсказаний нужен profile_id.
    # Временное решение: не кэшируем или используем заглушку.
    # Идеальное решение: создать отдельную таблицу для кэширования таких "общих" предсказаний
    # или определить "системный" профиль.
    # Пока просто логируем, что не кэшируем.
    bot_logger.info(f"[Zodiac Compatibility] Generated text (not cached in DB due to missing profile_id logic): {response_text[:100]}...")

    return response_text
# --- НОВАЯ ФУНКЦИЯ ---

# ... (остальной код файла) ...

@horoscope_router.callback_query(F.data == HoroscopeCallback.ZODIAC_COMPATIBILITY_START)
async def handle_zodiac_compatibility_start_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Совместимость знаков' - начало ввода."""
    bot_logger.info(f"User {callback.from_user.id} started zodiac compatibility process.")
    await callback.message.answer(
        text=_("zodiac_compatibility_ask_first_sign_msg"), # "Введите первый знак Зодиака:"
        reply_markup=await get_decline_reply()
    )
    await state.set_state(CompatibilitySignsState.waiting_for_first_sign)
    await callback.answer()

@horoscope_router.message(CompatibilitySignsState.waiting_for_first_sign)
async def handle_first_zodiac_sign(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} entered first sign: {message.text}")
    
    raw_sign = message.text.strip().lower() if message.text else ""

    await state.update_data(first_sign_key=raw_sign) # Сохраняем системное имя
    await message.answer(
        text=_("zodiac_compatibility_ask_second_sign_msg"), # "Введите второй знак Зодиака:"
        reply_markup=await get_decline_reply()
    )
    await state.set_state(CompatibilitySignsState.waiting_for_second_sign)

@horoscope_router.message(CompatibilitySignsState.waiting_for_second_sign)
async def handle_second_zodiac_sign(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} entered second sign: {message.text}")
    
    user_data = await state.get_data()
    first_sign_key = user_data.get('first_sign_key')
    
    if not first_sign_key:
        bot_logger.error(f"User {message.from_user.id} entered second sign without first sign in state.")
        await message.answer(text=_("error_msg"), reply_markup=await get_menu_reply())
        await state.clear()
        return

    raw_sign2 = message.text.strip().lower() if message.text else ""
    
    second_sign_key = raw_sign2 # Сохраняем системное имя второго знака

    user = await find_user_by_id(user_id=message.from_user.id)
    user_locale = user.locale if user else "ru" # По умолчанию 'ru'

    wait_msg = await message.answer(text=_("wait_calc_msg"))
    try:
        compatibility_text = await make_zodiac_compatibility(
            sign1_key=first_sign_key, 
            sign2_key=second_sign_key, 
            locale=user_locale
        )
        
        await wait_msg.delete()
        await message.answer(text=compatibility_text, reply_markup=await get_menu_reply())
        
    except Exception as e:
        bot_logger.error(f"Error in handle_second_zodiac_sign (compatibility generation) for user {message.from_user.id}: {e}", exc_info=True)
        await wait_msg.delete()
        await message.answer(text=_("error_generating_prediction_msg"), reply_markup=await get_menu_reply())
    finally:
        await state.clear()
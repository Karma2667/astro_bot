import traceback
import re
from aiogram import Router, F # type: ignore
from aiogram.filters import Command # type: ignore
from aiogram.fsm.context import FSMContext # type: ignore
from aiogram.types import Message, CallbackQuery # type: ignore
from aiogram.utils.i18n import gettext as _ # type: ignore
from datetime import datetime

from logger import bot_logger
from states.numerology import AngelNumbersStates, NumerologyMatrixStates 
from keyboards.reply.common import get_decline_reply, get_menu_reply
from keyboards.inline.numerology import get_angel_numbers_start_inline 
from keyboards.inline.callback import NumerologyCallback
from gpt.template import load_template, TemplateType
from gpt.gpt import send_gpt_request
from database.user.models import Subscription
from database.user.service import find_user_by_id
from database.predictions.models import Prediction, PredictionType
from database.predictions.service import (
    create_prediction,
    find_prediction_by_recognition_and_type,
)
from datetime import date, datetime
from constants.features import FEATURE_ANGEL_NUMBERS, get_limit_for_feature, FEATURE_NUMEROLOGY_MATRIX
from database.usage.service import get_user_usage, increment_user_usage 
from database.user.service import find_user_by_id 

numerology_router = Router(name="numerology")

async def shorten_numerology(sub: Subscription, text: str) -> str:
    if sub is Subscription.FREELY:
        crop_idx = len(text) // 3
        return text[:crop_idx] + "..."
    return text

async def format_numerology_result(sub: Subscription, text: str) -> str:
    extra = ""
    if sub is Subscription.FREELY:
        extra = f'\n\n{_("freely_unavailable_msg")}'
    return await shorten_numerology(sub=sub, text=text) + extra

async def make_angel_numbers(user_id: int, numbers_str: str = None, birthdate_angel_number: str = None) -> str:
    bot_logger.info(f"[Angel Numbers] make_angel_numbers called: user_id={user_id}, numbers={numbers_str}, birthdate_num={birthdate_angel_number}")

    user = await find_user_by_id(user_id=user_id)
    if not user:
        bot_logger.error(f"[Angel Numbers] User with id {user_id} not found.")
        return _("user_not_found_msg")

    validated_numbers = []
    if numbers_str:
        number_list = numbers_str.strip().split()
        for num_str in number_list:
            if num_str.isdigit():
                validated_numbers.append(num_str)
            else:
                bot_logger.warning(f"[Angel Numbers] Invalid number part '{num_str}' in input '{numbers_str}' for user {user_id}.")

    if numbers_str and not validated_numbers:
         bot_logger.error(f"[Angel Numbers] No valid numbers found in input '{numbers_str}' for user {user_id}.")
         return _("invalid_numbers_msg")
         
    cache_parts = []
    if validated_numbers:
        cache_parts.append('_'.join(validated_numbers))
    if birthdate_angel_number:
        cache_parts.append(f"bd_{birthdate_angel_number}")
    
    if not cache_parts:
        bot_logger.error(f"[Angel Numbers] No numbers provided for user {user_id}.")
        return _("invalid_numbers_msg")
        
    cache_key = f"angel_nums_{'_'.join(cache_parts)}_{user.locale}"
    
    db_result = await find_prediction_by_recognition_and_type(
        recognition_str=cache_key, prediction_type=PredictionType.ANGEL_NUMBERS
    )
    
    if db_result and db_result.prediction:
        bot_logger.info(f"[Angel Numbers] Found in DB for key: {cache_key}")
        return await format_numerology_result(sub=user.subscription, text=db_result.prediction)
   
    bot_logger.info(f"[Angel Numbers] Not in DB. Calling GPT for key: {cache_key}")

    try:
        template = await load_template(
            locale=user.locale, template_type=TemplateType.ANGEL_NUMBERS
        )
    except Exception as e:
        bot_logger.error(f"[Angel Numbers] Error loading template: {e}", exc_info=True)
        return _("error_msg")

    descriptions = []
    if validated_numbers:
        descriptions.append(f"- Последовательность чисел, замеченная пользователем: {', '.join(validated_numbers)}")
    if birthdate_angel_number:
        descriptions.append(f"- Основное ангельское число (число судьбы) пользователя: {birthdate_angel_number}")

    data_description = "\n".join(descriptions) if descriptions else "Данные не предоставлены."

    prompt = template.format(data_description=data_description)
    bot_logger.debug(f"[Angel Numbers] Prepared prompt (len={len(prompt)}). First 150 chars: '{prompt[:150]}...'")
    
    try:
        response = await send_gpt_request(prompt=prompt)
        bot_logger.info(f"[Angel Numbers] GPT API call completed. Response is None/Empty: {not response or not response.strip()}")
    except Exception as e:
        bot_logger.error(f"[Angel Numbers] Exception during GPT API call for user {user_id}: {e}", exc_info=True)
        return _("error_msg")

    if not response or not response.strip():
        bot_logger.error(f"[Angel Numbers] Failed to get a valid response from GPT API for user {user_id}.")
        return _("error_msg")

    result_text = response.strip()
    
    try:
        from database.profile.service import find_current_profile_by_user_id
        user_profile = await find_current_profile_by_user_id(user_id=user_id)
        profile_id_to_use = user_profile.id if user_profile else None

        if profile_id_to_use:
            await create_prediction(
                Prediction(
                    profile_id=profile_id_to_use,
                    prediction=result_text,
                    prediction_type=PredictionType.ANGEL_NUMBERS.value,
                    recognition_str=cache_key,
                )
            )
            bot_logger.info(f"[Angel Numbers] Prediction saved to DB for key: {cache_key}")
        else:
             bot_logger.info(f"[Angel Numbers] No profile ID, result not saved to DB for key: {cache_key}")
    except Exception as e:
        bot_logger.error(f"[Angel Numbers] Error saving to DB for user {user_id}: {e}", exc_info=True)
   
    return await format_numerology_result(sub=user.subscription, text=result_text)

@numerology_router.message(Command("angel_numbers"))
async def handle_angel_numbers_cmd(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} using command /angel_numbers")
    await message.answer(
        text=_("choose_angel_numbers_type_msg"), # "Выберите способ получения ангельских чисел:"
        reply_markup=await get_angel_numbers_start_inline()
    )

@numerology_router.callback_query(F.data == NumerologyCallback.START_ANGEL)
async def handle_start_angel_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} started Angel Numbers process via callback.")
    await callback.message.answer(
        text=_("ask_angel_numbers_msg"),
        reply_markup=await get_decline_reply()
    )
    await state.set_state(AngelNumbersStates.waiting_for_numbers)
    await callback.answer()

async def _ask_for_angel_numbers(message: Message, state: FSMContext):
    await message.answer(
        text=_("ask_angel_numbers_msg"),
        reply_markup=await get_decline_reply()
    )
    await state.set_state(AngelNumbersStates.waiting_for_numbers)

@numerology_router.message(lambda msg: msg.text and msg.text == _("angel_numbers_btn"))
async def handle_angel_numbers_menu_button(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} pressed 'Angel Numbers' button from main menu")
    await _ask_for_angel_numbers(message, state)


def calculate_angel_number_from_date(birth_date_str: str) -> str:
    try:
        birth_date = datetime.strptime(birth_date_str, "%d.%m.%Y").date()
        
        day_str = str(birth_date.day)
        month_str = str(birth_date.month)
        year_str = str(birth_date.year)
        all_digits_str = day_str + month_str + year_str
        
        total = sum(int(digit) for digit in all_digits_str)
        
        while total > 9:
            if total in [11, 22, 33]:
                return str(total)
            total = sum(int(digit) for digit in str(total))
            
        return str(total)
    except ValueError:
        bot_logger.error(f"[Angel Numbers] Invalid date format for calculation: {birth_date_str}")
        return None # Или поднимать исключение
    
@numerology_router.callback_query(F.data == NumerologyCallback.START_ANGEL)
async def handle_start_angel_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} chose to input angel numbers manually.")
    await callback.message.answer(
        text=_("ask_angel_numbers_msg"),
        reply_markup=await get_decline_reply()
    )
    await state.set_state(AngelNumbersStates.waiting_for_numbers)
    await callback.answer()

@numerology_router.callback_query(F.data == NumerologyCallback.START_BIRTHDATE_ANGEL)
async def handle_start_birthdate_angel_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} chose to calculate angel numbers from birthdate.")
    await callback.message.answer(
        text=_("ask_birth_date_msg"), # "Введите вашу дату рождения (ДД.ММ.ГГГГ):"
        reply_markup=await get_decline_reply()
    )
    await state.set_state(AngelNumbersStates.waiting_for_birthdate)
    await callback.answer()

@numerology_router.message(AngelNumbersStates.waiting_for_numbers)
async def handle_angel_numbers_input(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} sending angel numbers: {message.text}")
    
    user_id = message.from_user.id # <-- Получаем user_id заранее
    user = await find_user_by_id(user_id=user_id)
    if not user:
        await message.answer(text=_("error_msg"), reply_markup=await get_menu_reply())
        await state.clear()
        return

    sub_name = user.subscription.value if hasattr(user.subscription, 'value') else (user.subscription.name.lower() if user.subscription else "freely")
    limit = get_limit_for_feature(sub_name, FEATURE_ANGEL_NUMBERS)

    if limit > 0:
        today = date.today()
        usage_record = await get_user_usage(user_id, FEATURE_ANGEL_NUMBERS, today)
        current_usage = usage_record.usage_count if usage_record else 0

        if current_usage >= limit:
            await message.answer(
                text=_("daily_limit_reached_msg"), # "Дневной лимит для этой функции исчерпан..."
                reply_markup=await get_menu_reply()
            )
            await state.clear()
            return # Останавливаем выполнение хендлера
    
    if message.text and re.match(r"^[\d\s]+$", message.text.strip()):
        wait_msg = await message.answer(text=_("wait_calc_msg"))
        try:
            result = await make_angel_numbers(user_id=user_id, numbers_str=message.text)
            await wait_msg.delete()
            await message.answer(text=result, reply_markup=await get_menu_reply())
            
            sub_name = user.subscription.value if hasattr(user.subscription, 'value') else (user.subscription.name.lower() if user.subscription else "freely")
            limit = get_limit_for_feature(sub_name, FEATURE_ANGEL_NUMBERS)

            if limit > 0: # Увеличиваем только если функция лимитирована
                today = date.today()
                await increment_user_usage(user_id, FEATURE_ANGEL_NUMBERS, today)
                bot_logger.info(f"Incremented usage count for user {user_id}, feature {FEATURE_ANGEL_NUMBERS}")
            
        except Exception as e:
            bot_logger.error(f"Error in handle_angel_numbers_input (generation) for user {user_id}: {e}", exc_info=True)
            await wait_msg.delete()
            await message.answer(text=_("error_msg"), reply_markup=await get_menu_reply())
        finally:
            await state.clear()
    else:
        await message.answer(text=_("invalid_numbers_msg"), reply_markup=await get_decline_reply())


@numerology_router.message(AngelNumbersStates.waiting_for_birthdate)
async def handle_birthdate_for_angel_numbers(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} sending birthdate for angel numbers: {message.text}")
    
    user_id = message.from_user.id # <-- Получаем user_id заранее
    
    user = await find_user_by_id(user_id=user_id)
    if not user:
        await message.answer(text=_("error_msg"), reply_markup=await get_menu_reply())
        await state.clear()
        return

    sub_name = user.subscription.value if hasattr(user.subscription, 'value') else (user.subscription.name.lower() if user.subscription else "freely")
    limit = get_limit_for_feature(sub_name, FEATURE_ANGEL_NUMBERS)

    if limit > 0:
        today = date.today()
        usage_record = await get_user_usage(user_id, FEATURE_ANGEL_NUMBERS, today)
        current_usage = usage_record.usage_count if usage_record else 0

        if current_usage >= limit:
            await message.answer(
                text=_("daily_limit_reached_msg"), # "Дневной лимит для этой функции исчерпан..."
                reply_markup=await get_menu_reply()
            )
            await state.clear()
            return # Останавливаем выполнение хендлера

    date_pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    if message.text and re.match(date_pattern, message.text):
        try:
            datetime.strptime(message.text, "%d.%m.%Y").date()
            
            birthdate_angel_number = calculate_angel_number_from_date(message.text)
            if not birthdate_angel_number:
                await message.answer(text=_("date_error_msg"), reply_markup=await get_decline_reply())
                return

            wait_msg = await message.answer(text=_("wait_calc_msg"))
            try:
                result = await make_angel_numbers(user_id=user_id, birthdate_angel_number=birthdate_angel_number)
                await wait_msg.delete()
                await message.answer(text=result, reply_markup=await get_menu_reply())
                
                sub_name = user.subscription.value if hasattr(user.subscription, 'value') else (user.subscription.name.lower() if user.subscription else "freely")
                limit = get_limit_for_feature(sub_name, FEATURE_ANGEL_NUMBERS)

                if limit > 0: # Увеличиваем только если функция лимитирована
                    today = date.today()
                    await increment_user_usage(user_id, FEATURE_ANGEL_NUMBERS, today)
                    bot_logger.info(f"Incremented usage count for user {user_id}, feature {FEATURE_ANGEL_NUMBERS}")
                
            except Exception as e:
                bot_logger.error(f"Error in handle_birthdate_for_angel_numbers (generation) for user {user_id}: {e}", exc_info=True)
                await wait_msg.delete()
                await message.answer(text=_("error_msg"), reply_markup=await get_menu_reply())
            finally:
                await state.clear() # Всегда очищаем состояние в конце

        except ValueError:
            await message.answer(text=_("date_error_msg"), reply_markup=await get_decline_reply())
    else:
        await message.answer(text=_("date_error_msg"), reply_markup=await get_decline_reply())

async def _ask_for_angel_numbers(message: Message, state: FSMContext):
    await message.answer(
        text=_("choose_angel_numbers_type_msg"), # "Выберите способ получения ангельских чисел:"
        reply_markup=await get_angel_numbers_start_inline() # <-- Ключевой момент
    )

def calculate_life_matrix(birth_date_str: str) -> dict:
    try:
        birth_date = datetime.strptime(birth_date_str, "%d.%m.%Y").date()
        day = birth_date.day
        month = birth_date.month
        year = birth_date.year

        life_path_number = (day + month + year) % 9 or 9 # Пример упрощенного расчета

        destiny_number = (day + month) % 9 or 9

        soul_number = month % 9 or 9

        conscious_number = day % 9 or 9

        birthday_number = day % 9 or 9

        first_trial = abs(day - month)
        maturity_number = (life_path_number + first_trial) % 9 or 9

        power_number = (day + month) % 9 or 9

        year_digits_sum = sum(int(digit) for digit in str(year))
        personality_number = year_digits_sum % 9 or 9

        return {
            "life_path": life_path_number,
            "destiny": destiny_number,
            "soul": soul_number,
            "conscious": conscious_number,
            "birthday": birthday_number,
            "maturity": maturity_number,
            "power": power_number,
            "personality": personality_number,
            "birth_date": birth_date_str
        }
    except ValueError as e:
        bot_logger.error(f"[Numerology Matrix] Invalid date format for calculation: {birth_date_str}. Error: {e}")
        return None

async def make_numerology_matrix(user_id: int, birth_date_str: str) -> str:
    bot_logger.info(f"[Numerology Matrix] make_numerology_matrix called: user_id={user_id}, birth_date={birth_date_str}")

    user = await find_user_by_id(user_id=user_id)
    if not user:
        bot_logger.error(f"[Numerology Matrix] User with id {user_id} not found.")
        return _("user_not_found_msg")

    calculated_numbers = calculate_life_matrix(birth_date_str)
    if not calculated_numbers:
        return _("date_error_msg") # Используем существующий перевод ошибки даты

    from database.profile.service import find_current_profile_by_user_id
    user_profile = await find_current_profile_by_user_id(user_id=user_id)
    profile_id_for_cache = user_profile.id if user_profile else "no_profile"
    cache_key = f"num_matrix_{birth_date_str}_{user.locale}_{profile_id_for_cache}"

    db_result = await find_prediction_by_recognition_and_type(
        recognition_str=cache_key, prediction_type=PredictionType.NUMEROLOGY_MATRIX
    )
    if db_result:
        bot_logger.info(f"[Numerology Matrix] Found in DB for key: {cache_key}")
        return await format_numerology_result(sub=user.subscription, text=db_result.prediction)

    bot_logger.info(f"[Numerology Matrix] Not in DB. Calling GPT for key: {cache_key}")

    try:
        template = await load_template(
            locale=user.locale, template_type=TemplateType.NUMEROLOGY_MATRIX
        )
    except Exception as e:
        bot_logger.error(f"[Numerology Matrix] Error loading template: {e}", exc_info=True)
        return _("error_msg")

    descriptions = []
    descriptions.append(f"- Число Жизни (Путь Жизни): {calculated_numbers['life_path']}")
    descriptions.append(f"- Число Судьбы (Выражение): {calculated_numbers['destiny']}")
    descriptions.append(f"- Число Души (Сердца): {calculated_numbers['soul']}")
    descriptions.append(f"- Число Сознания: {calculated_numbers['conscious']}")
    descriptions.append(f"- Число Дня рождения: {calculated_numbers['birthday']}")
    descriptions.append(f"- Число Зрелости: {calculated_numbers['maturity']}")
    descriptions.append(f"- Число Силы: {calculated_numbers['power']}")
    descriptions.append(f"- Число Личности: {calculated_numbers['personality']}")
    
    calculated_numbers_description = "\n".join(descriptions)

    prompt_data = {
        "birth_date": calculated_numbers["birth_date"],
        "calculated_numbers_description": calculated_numbers_description
    }
    try:
        prompt = template.format(**prompt_data)
    except KeyError as e:
        bot_logger.error(f"[Numerology Matrix] Missing key in template: {e}")
        return _("error_msg")
        
    bot_logger.debug(f"[Numerology Matrix] Prepared prompt (len={len(prompt)}). First 150 chars: '{prompt[:150]}...'")

    try:
        response = await send_gpt_request(prompt=prompt)
        bot_logger.info(f"[Numerology Matrix] GPT API call completed. Response is None/Empty: {not response or not response.strip()}")
    except Exception as e:
        bot_logger.error(f"[Numerology Matrix] Exception during GPT API call for user {user_id}: {e}", exc_info=True)
        return _("error_msg")

    if not response or not response.strip():
        bot_logger.error(f"[Numerology Matrix] Failed to get a valid response from GPT API for user {user_id}.")
        return _("error_msg")

    result_text = response.strip()

    try:
        profile_id_to_use = user_profile.id if user_profile else None
        if profile_id_to_use:
            prediction_to_save = Prediction(
                profile_id=profile_id_to_use,
                prediction=result_text,
                prediction_type=PredictionType.NUMEROLOGY_MATRIX, # <-- Используем .value
                recognition_str=cache_key,
            )
            await create_prediction(prediction_to_save)
            bot_logger.info(f"[Numerology Matrix] Prediction saved to DB for key: {cache_key}")
        else:
             bot_logger.info(f"[Numerology Matrix] No profile ID, result not saved to DB for key: {cache_key}")
    except Exception as e:
        bot_logger.error(f"[Numerology Matrix] Error saving to DB for user {user_id}: {e}", exc_info=True)

    return await format_numerology_result(sub=user.subscription, text=result_text)

@numerology_router.message(lambda msg: msg.text and msg.text == _("numerology_matrix_btn"))
async def handle_numerology_matrix_menu_button(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} pressed 'Numerology Matrix' button from main menu")
    
    user_id = message.from_user.id
    
    user = await find_user_by_id(user_id=user_id)
    if not user:
        await message.answer(text=_("error_msg"), reply_markup=await get_menu_reply())
        return

    sub_name = user.subscription.value if hasattr(user.subscription, 'value') else (user.subscription.name.lower() if user.subscription else "freely")
    limit = get_limit_for_feature(sub_name, FEATURE_NUMEROLOGY_MATRIX)

    if limit <= 0: # Для подписки freely limit будет 0
        await message.answer(
            text=_("feature_not_available_on_plan_msg"), # "Эта функция недоступна в вашем тарифе. Приобретите подписку для доступа."
            reply_markup=await get_menu_reply()
        )
        return # Останавливаем выполнение хендлера
    await message.answer(
        text=_("ask_birth_date_msg"), # "Введите вашу дату рождения (ДД.ММ.ГГГГ):"
        reply_markup=await get_decline_reply()
    )
    await state.set_state(NumerologyMatrixStates.waiting_for_birth_date)

@numerology_router.message(NumerologyMatrixStates.waiting_for_birth_date)
async def handle_matrix_birth_date(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} sending birth date for Matrix: {message.text}")
    date_pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    if message.text and re.match(date_pattern, message.text):
        try:
            datetime.strptime(message.text, "%d.%m.%Y").date()

            wait_msg = await message.answer(text=_("wait_calc_msg"))
            try:
                result = await make_numerology_matrix(user_id=message.from_user.id, birth_date_str=message.text)
                await wait_msg.delete()
                await message.answer(text=result, reply_markup=await get_menu_reply())
            except Exception as e:
                bot_logger.error(f"Error in handle_matrix_birth_date (generation) for user {message.from_user.id}: {e}", exc_info=True)
                await wait_msg.delete()
                await message.answer(text=_("error_msg"), reply_markup=await get_menu_reply())
            finally:
                await state.clear()

        except ValueError:
            await message.answer(text=_("date_error_msg"), reply_markup=await get_decline_reply())
    else:
        await message.answer(text=_("date_error_msg"), reply_markup=await get_decline_reply())

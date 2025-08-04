# handlers/numerology.py
import re
from aiogram import Router, F # type: ignore
from aiogram.filters import Command # type: ignore
from aiogram.fsm.context import FSMContext # type: ignore
from aiogram.types import Message, CallbackQuery # type: ignore
from aiogram.utils.i18n import gettext as _ # type: ignore

from logger import bot_logger
from states.numerology import AngelNumbersStates # Убедитесь, что импортируете обновленные состояния
from keyboards.reply.common import get_decline_reply, get_menu_reply
from keyboards.inline.numerology import get_angel_numbers_start_inline # Используем обновленную клавиатуру
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
    # --- ОБНОВЛЕНО ---
    # Обработка чисел, введенных пользователем
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
    # --- ОБНОВЛЕНО ---

    # --- ОБНОВЛЕНО ---
    # Формирование ключа для кэша теперь учитывает оба типа чисел
    cache_parts = []
    if validated_numbers:
        cache_parts.append('_'.join(validated_numbers))
    if birthdate_angel_number:
        cache_parts.append(f"bd_{birthdate_angel_number}")
    
    if not cache_parts:
        bot_logger.error(f"[Angel Numbers] No numbers provided for user {user_id}.")
        return _("invalid_numbers_msg") # Или другое сообщение об ошибке
        
    cache_key = f"angel_nums_{'_'.join(cache_parts)}_{user.locale}"
    # --- ОБНОВЛЕНО ---

    # --- ОБНОВЛЕНО ---
    # Проверка кэша
    db_result = await find_prediction_by_recognition_and_type(
        recognition_str=cache_key, prediction_type=PredictionType.ANGEL_NUMBERS
    )
    if db_result:
        bot_logger.info(f"[Angel Numbers] Found in DB for key: {cache_key}")
        return await format_numerology_result(sub=user.subscription, text=db_result.prediction)
    # --- ОБНОВЛЕНО ---

    bot_logger.info(f"[Angel Numbers] Not in DB. Calling GPT for key: {cache_key}")

    # --- ОБНОВЛЕНО ---
    # Загрузка шаблона
    try:
        template = await load_template(
            locale=user.locale, template_type=TemplateType.ANGEL_NUMBERS
        )
    except Exception as e:
        bot_logger.error(f"[Angel Numbers] Error loading template: {e}", exc_info=True)
        return _("error_msg")
    # --- ОБНОВЛЕНО ---

    # --- ОБНОВЛЕНО ---
    # Подстановка данных в шаблон
    # Теперь шаблон должен учитывать оба типа чисел
    descriptions = []
    if validated_numbers:
        descriptions.append(f"- Последовательность чисел, замеченная пользователем: {', '.join(validated_numbers)}")
    if birthdate_angel_number:
        descriptions.append(f"- Основное ангельское число (число судьбы) пользователя: {birthdate_angel_number}")

    data_description = "\n".join(descriptions) if descriptions else "Данные не предоставлены."

    # Передаем только data_description
    prompt = template.format(data_description=data_description)
    bot_logger.debug(f"[Angel Numbers] Prepared prompt (len={len(prompt)}). First 150 chars: '{prompt[:150]}...'")
    # --- ОБНОВЛЕНО ---

    # --- ОБНОВЛЕНО ---
    # Вызов GPT
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
    # --- ОБНОВЛЕНО ---

    # --- ОБНОВЛЕНО ---
    # Сохранение в БД
    try:
        from database.profile.service import find_current_profile_by_user_id
        user_profile = await find_current_profile_by_user_id(user_id=user_id)
        profile_id_to_use = user_profile.id if user_profile else None

        if profile_id_to_use:
            await create_prediction(
                Prediction(
                    profile_id=profile_id_to_use,
                    prediction=result_text,
                    prediction_type=PredictionType.ANGEL_NUMBERS,
                    recognition_str=cache_key,
                )
            )
            bot_logger.info(f"[Angel Numbers] Prediction saved to DB for key: {cache_key}")
        else:
             bot_logger.info(f"[Angel Numbers] No profile ID, result not saved to DB for key: {cache_key}")
    except Exception as e:
        bot_logger.error(f"[Angel Numbers] Error saving to DB for user {user_id}: {e}", exc_info=True)
    # --- ОБНОВЛЕНО ---

    return await format_numerology_result(sub=user.subscription, text=result_text)

@numerology_router.message(Command("angel_numbers"))
async def handle_angel_numbers_cmd(message: Message, state: FSMContext):
    """Обработчик команды /angel_numbers - показывает выбор типа."""
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

@numerology_router.message(AngelNumbersStates.waiting_for_numbers)
async def handle_angel_numbers_input(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} sending angel numbers: {message.text}")
    if message.text and re.match(r"^[\d\s]+$", message.text.strip()):
        wait_msg = await message.answer(text=_("wait_calc_msg"))
        try:
            result = await make_angel_numbers(user_id=message.from_user.id, numbers_str=message.text)
            await wait_msg.delete()
            await message.answer(text=result, reply_markup=await get_menu_reply())
        except Exception as e:
            bot_logger.error(f"Error in handle_angel_numbers (generation) for user {message.from_user.id}: {e}", exc_info=True)
            await wait_msg.delete()
            await message.answer(text=_("error_msg"), reply_markup=await get_menu_reply())
        finally:
            await state.clear()
    else:
        await message.answer(text=_("invalid_numbers_msg"), reply_markup=await get_decline_reply())

def calculate_angel_number_from_date(birth_date_str: str) -> str:
    """
    Рассчитывает основное ангельское число (число судьбы) из даты рождения.
    :param birth_date_str: Дата рождения в формате ДД.ММ.ГГГГ.
    :return: Строка с рассчитанным числом (например, "7", "11", "22").
    """
    try:
        # 1. Проверка и парсинг даты
        birth_date = datetime.strptime(birth_date_str, "%d.%m.%Y").date()
        
        # 2. Суммирование всех цифр
        day_str = str(birth_date.day)
        month_str = str(birth_date.month)
        year_str = str(birth_date.year)
        all_digits_str = day_str + month_str + year_str
        
        total = sum(int(digit) for digit in all_digits_str)
        
        # 3. Приведение к однозначному числу или мастер-числу
        while total > 9:
            # Проверка на мастер-числа 11, 22, 33
            if total in [11, 22, 33]:
                return str(total)
            # Если не мастер-число, суммируем цифры результата
            total = sum(int(digit) for digit in str(total))
            
        return str(total)
    except ValueError:
        # Неверный формат даты
        bot_logger.error(f"[Angel Numbers] Invalid date format for calculation: {birth_date_str}")
        return None # Или поднимать исключение
    
@numerology_router.callback_query(F.data == NumerologyCallback.START_ANGEL)
async def handle_start_angel_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик начала ввода чисел вручную."""
    bot_logger.info(f"User {callback.from_user.id} chose to input angel numbers manually.")
    await callback.message.answer(
        text=_("ask_angel_numbers_msg"),
        reply_markup=await get_decline_reply()
    )
    await state.set_state(AngelNumbersStates.waiting_for_numbers)
    await callback.answer()

@numerology_router.callback_query(F.data == NumerologyCallback.START_BIRTHDATE_ANGEL)
async def handle_start_birthdate_angel_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик начала расчета чисел из даты рождения."""
    bot_logger.info(f"User {callback.from_user.id} chose to calculate angel numbers from birthdate.")
    await callback.message.answer(
        text=_("ask_birth_date_msg"), # "Введите вашу дату рождения (ДД.ММ.ГГГГ):"
        reply_markup=await get_decline_reply()
    )
    await state.set_state(AngelNumbersStates.waiting_for_birthdate)
    await callback.answer()

@numerology_router.message(AngelNumbersStates.waiting_for_numbers)
async def handle_angel_numbers_input(message: Message, state: FSMContext):
    """Обработчик ввода ангельских чисел."""
    bot_logger.info(f"User {message.from_user.id} sending angel numbers: {message.text}")
    if message.text and re.match(r"^[\d\s]+$", message.text.strip()):
        # Вызываем функцию с введенными числами
        wait_msg = await message.answer(text=_("wait_calc_msg"))
        try:
            result = await make_angel_numbers(user_id=message.from_user.id, numbers_str=message.text)
            await wait_msg.delete()
            await message.answer(text=result, reply_markup=await get_menu_reply())
        except Exception as e:
            bot_logger.error(f"Error in handle_angel_numbers_input (generation) for user {message.from_user.id}: {e}", exc_info=True)
            await wait_msg.delete()
            await message.answer(text=_("error_msg"), reply_markup=await get_menu_reply())
        finally:
            await state.clear()
    else:
        await message.answer(text=_("invalid_numbers_msg"), reply_markup=await get_decline_reply())

@numerology_router.message(AngelNumbersStates.waiting_for_birthdate)
async def handle_birthdate_for_angel_numbers(message: Message, state: FSMContext):
    """Обработчик ввода даты рождения для расчета ангельских чисел."""
    bot_logger.info(f"User {message.from_user.id} sending birthdate for angel numbers: {message.text}")
    date_pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    if message.text and re.match(date_pattern, message.text):
        try:
            # Проверка валидности даты
            datetime.strptime(message.text, "%d.%m.%Y").date()
            
            # Рассчитываем число
            birthdate_angel_number = calculate_angel_number_from_date(message.text)
            if not birthdate_angel_number:
                await message.answer(text=_("date_error_msg"), reply_markup=await get_decline_reply())
                return

            # Вызываем функцию с рассчитанным числом
            wait_msg = await message.answer(text=_("wait_calc_msg"))
            try:
                result = await make_angel_numbers(user_id=message.from_user.id, birthdate_angel_number=birthdate_angel_number)
                await wait_msg.delete()
                await message.answer(text=result, reply_markup=await get_menu_reply())
            except Exception as e:
                bot_logger.error(f"Error in handle_birthdate_for_angel_numbers (generation) for user {message.from_user.id}: {e}", exc_info=True)
                await wait_msg.delete()
                await message.answer(text=_("error_msg"), reply_markup=await get_menu_reply())
            finally:
                await state.clear()

        except ValueError:
            await message.answer(text=_("date_error_msg"), reply_markup=await get_decline_reply())
    else:
        await message.answer(text=_("date_error_msg"), reply_markup=await get_decline_reply())
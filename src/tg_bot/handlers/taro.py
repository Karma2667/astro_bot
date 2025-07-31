
import asyncio
import logging
from aiogram import Router, F # type: ignore
from aiogram.filters import Command, StateFilter  # type: ignore
from aiogram.types import Message, CallbackQuery, FSInputFile # type: ignore
from aiogram.fsm.context import FSMContext # type: ignore
from aiogram.utils.i18n import gettext as __ # type: ignore
from gpt.template import load_template, TemplateType
from gpt.gpt import send_gpt_request
from database.user.service import find_user_by_id
from database.predictions.models import Prediction, PredictionType
from database.predictions.service import create_prediction, find_prediction_by_recognition_and_type
from database.user.service import find_user_by_id
from database.profile.service import find_current_profile_by_user_id 
from handlers.events import CompatibilityStates, make_compatibility
from logger import bot_logger
from keyboards.inline.taro import get_taro_inline, get_full_spread_button
from keyboards.inline.callback import TaroCallback
from keyboards.reply.common import get_menu_reply, get_decline_reply
from handlers.events import make_compatibility
from data.tarot_deck import draw_random_cards, get_card_image_path, get_card_info
from aiogram.types import BufferedInputFile # type: ignore # Для отправки байтов, если понадобится
import os # Для проверки существования файла

taro_router = Router(name="taro")

TELEGRAM_CAPTION_LIMIT = 1024

# --- ХЕНДЛЕРЫ КОМАНД И КНОПОК ---

@taro_router.message(lambda msg: msg.text and msg.text == __("taro_btn"))
async def handle_taro_menu_button(message: Message, state: FSMContext):
    """Обработчик нажатия кнопки 'Таро' в главном меню."""
    bot_logger.info(f"User {message.from_user.id} pressed 'Taro' button from main menu")
    await handle_taro_cmd(message, state)

@taro_router.message(Command("taro"))
async def handle_taro_cmd(message: Message, state: FSMContext):
    """Обработчик команды /taro."""
    bot_logger.info(f"User {message.from_user.id} using command /taro")
    await message.answer(
        text=__("choose_taro_theme_msg"),
        reply_markup=await get_taro_inline()
    )

async def handle_taro_theme_selection(callback: CallbackQuery, theme: str):
    """Вспомогательная функция для обработки выбора темы Таро."""
    bot_logger.info(f"[Taro] User {callback.from_user.id} selected theme: {theme}")
    user_id = callback.from_user.id
    wait_msg = None
    try:
        # Показываем сообщение ожидания
        wait_msg = await callback.message.answer(text=__("wait_calc_msg"))
        
        # === ГЕНЕРИРУЕМ ПРЕДСКАЗАНИЕ ДЛЯ ОДНОЙ КАРТЫ ===
        # ВАЖНО: теперь возвращается КОРТЕЖ (текст_предсказания, имя_карты)
        prediction_text, card_name = await make_taro_prediction(user_id=user_id, theme=theme)
        
        # Удаляем сообщение ожидания
        if wait_msg:
            await wait_msg.delete()
            wait_msg = None # Сбрасываем, чтобы знать, что сообщение удалено

        # === ОБРАБАТЫВАЕМ РЕЗУЛЬТАТ ===
        if not prediction_text or not card_name:
            # Ошибка уже залогирована в make_taro_prediction
            await callback.message.answer(text=__("error_generating_prediction_msg"), reply_markup=await get_menu_reply())
            await callback.answer()
            return

        # === ПОДГОТАВЛИВАЕМ КНОПКУ "Полный расклад" ===
        full_spread_keyboard = await get_full_spread_button(theme)

        # === ОТПРАВЛЯЕМ ИЗОБРАЖЕНИЕ И ТЕКСТ ===
        try:
            # Получаем путь к изображению карты
            image_path = get_card_image_path(card_name)
            
            # Проверяем, существует ли файл
            if not os.path.exists(image_path):
                 bot_logger.error(f"[Taro] Image file not found for card '{card_name}' at path: {image_path}")
                 # Отправляем только текст, если изображение не найдено
                 await callback.message.answer(
                     text=f"{prediction_text}\n\n(Изображение карты '{card_name}' не найдено)",
                     reply_markup=full_spread_keyboard
                 )
                 await callback.answer()
                 return

            input_file = FSInputFile(path=image_path)

            # Проверяем длину текста
            if len(prediction_text) <= TELEGRAM_CAPTION_LIMIT:
                # Если текст помещается в подпись, отправляем фото с подписью
                bot_logger.debug(f"[Taro] Sending image with caption for user {user_id}")
                await callback.message.answer_photo(
                    photo=input_file,
                    caption=prediction_text, # <-- Используем ТЕКСТ из кортежа
                    reply_markup=full_spread_keyboard
                )
            else:
                # Если текст слишком длинный, отправляем сначала фото без подписи, затем текст отдельно
                bot_logger.debug(f"[Taro] Caption too long ({len(prediction_text)} chars). Sending image and text separately for user {user_id}")
                # Отправляем фото без подписи
                await callback.message.answer_photo(
                    photo=input_file,
                    caption=f"Карта: {card_name}", # Минимальная подпись
                    reply_markup=None # Кнопку добавим к тексту
                )
                # Отправляем текст отдельным сообщением с кнопкой
                await callback.message.answer(
                    text=prediction_text,
                    reply_markup=full_spread_keyboard
                )

        except Exception as image_error:
            bot_logger.error(f"[Taro] Error sending image for card '{card_name}' to user {user_id}: {image_error}", exc_info=True)
            # Если ошибка с изображением, отправляем только текст с кнопкой
            await callback.message.answer(text=prediction_text, reply_markup=full_spread_keyboard)
            
    except Exception as e:
        bot_logger.error(f"[Taro] Error in handle_taro_theme_selection for user {user_id}: {e}", exc_info=True)
        # Удаляем wait_msg, если он еще существует
        if wait_msg:
            try:
                await wait_msg.delete()
            except Exception as delete_error:
                bot_logger.warning(f"[Taro] Could not delete wait_msg for user {user_id}: {delete_error}")
        # Отправляем сообщение об ошибке пользователю
        await callback.message.answer(text=__("error_generating_prediction_msg"), reply_markup=await get_menu_reply())
    finally:
        # ВСЕГДА отвечаем на callback, чтобы убрать "часики"
        await callback.answer()



@taro_router.callback_query(F.data == TaroCallback.STUDY.value)
async def handle_taro_study_callback(callback: CallbackQuery, state: FSMContext):
    await handle_taro_theme_selection(callback, "study")

@taro_router.callback_query(F.data == TaroCallback.MOOD.value)
async def handle_taro_mood_callback(callback: CallbackQuery, state: FSMContext):
    await handle_taro_theme_selection(callback, "mood")

@taro_router.callback_query(F.data == TaroCallback.LOVE.value)
async def handle_taro_love_callback(callback: CallbackQuery, state: FSMContext):
    await handle_taro_theme_selection(callback, "love")

@taro_router.callback_query(F.data == TaroCallback.INCOME.value)
async def handle_taro_income_callback(callback: CallbackQuery, state: FSMContext):
    await handle_taro_theme_selection(callback, "income")

@taro_router.callback_query(F.data == TaroCallback.SUCCESS.value)
async def handle_taro_success_callback(callback: CallbackQuery, state: FSMContext):
    await handle_taro_theme_selection(callback, "success")

@taro_router.callback_query(F.data == TaroCallback.COMPATIBILITY.value)
async def handle_taro_compatibility_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} selected 'Taro Compatibility'")
    await callback.message.answer(
        text=__("send_first_name_msg"),
        reply_markup=await get_decline_reply()
    )
    # Устанавливаем состояние FSM для обработки ввода имен в этом же роутере
    await state.set_state(CompatibilityStates.waiting_for_first_name)
    await callback.answer()

# --- ХЕНДЛЕРЫ ДЛЯ FSM СОВМЕСТИМОСТИ (работают внутри taro_router) ---

@taro_router.message(StateFilter(CompatibilityStates.waiting_for_first_name))
async def handle_taro_first_name_input(message: Message, state: FSMContext):
    """Обработчик ввода первого имени для Таро-совместимости."""
    bot_logger.info(f"[Taro] User {message.from_user.id} entered first name: {message.text}")

    if not message.text or len(message.text.strip()) < 2:
        await message.answer(text=__("invalid_name_msg"))
        return

    await state.update_data(first_name=message.text.strip())
    
    await message.answer(
        text=__("send_second_name_msg"),
        reply_markup=await get_decline_reply()
    )
    
    await state.set_state(CompatibilityStates.waiting_for_second_name)

@taro_router.message(StateFilter(CompatibilityStates.waiting_for_second_name))
async def handle_taro_second_name_input(message: Message, state: FSMContext):
    """Обработчик ввода второго имени для Таро-совместимости и запуск расчета."""
    bot_logger.info(f"[Taro] User {message.from_user.id} entered second name: {message.text}")
    
    if not message.text or len(message.text.strip()) < 2:
        await message.answer(text=__("invalid_name_msg"))
        return

    user_data = await state.get_data()
    first_name = user_data.get('first_name')
    second_name = message.text.strip()
    
    user_id = message.from_user.id
    
    wait_msg = await message.answer(text=__("wait_calc_msg"))
    
    try:
        # Вызываем функцию расчета совместимости из events.py
        compatibility_result = await make_compatibility(user_id=user_id, name1=first_name, name2=second_name)
        
        await wait_msg.delete()
        await message.answer(text=compatibility_result, reply_markup=await get_menu_reply())
    except Exception as e:
        bot_logger.error(f"[Taro] Error calculating compatibility for user {user_id}: {e}", exc_info=True)
        await wait_msg.delete()
        await message.answer(text=__("error_generating_prediction_msg"), reply_markup=await get_menu_reply())
        
    finally:
        await state.clear()


async def make_taro_prediction(user_id: int, theme: str) -> str:
    bot_logger.info(f"[Taro] make_taro_prediction called: user_id={user_id}, theme={theme}")
    
    user = await find_user_by_id(user_id=user_id)
    if not user:
        bot_logger.error(f"[Taro] User with id {user_id} not found.")
        return __("user_not_found_msg")

    user_profile = await find_current_profile_by_user_id(user_id=user_id)
    if not user_profile:
        bot_logger.error(f"[Taro] Profile not found for user_id {user_id}.")
        return __("error_profile_creation_msg") 
    
    drawn_cards = draw_random_cards(count=1)
    if not drawn_cards:
        bot_logger.error(f"[Taro Single] Failed to draw a card for user {user_id}.")
        return (__("error_generating_prediction_msg"), "")
    
    single_card_name = drawn_cards[0]
    bot_logger.info(f"[Taro Single] Drew card: '{single_card_name}'")

    cache_key = f"taro_single_{theme}_{single_card_name}_{user.locale}_{user_profile.id}"
    bot_logger.debug(f"[Taro Single] Generated cache key: {cache_key}")

    db_result = await find_prediction_by_recognition_and_type(
        recognition_str=cache_key, prediction_type=PredictionType.HOROSCOPE # Используем HOROSCOPE или создай отдельный тип TAROT_SINGLE
    )
    
    if db_result and db_result.prediction:
        bot_logger.info(f"[Taro Single] Found prediction in DB for key: {cache_key}")
        # Возвращаем текст из БД и имя карты
        return (db_result.prediction, single_card_name)
    else:
        if db_result:
            bot_logger.warning(f"[Taro Single] Found poisoned DB entry for key: {cache_key}. Will fetch a new one.")
            
        bot_logger.info(f"[Taro Single] No prediction in DB. Calling GPT API for key: {cache_key}")
        
        try:
            # Загружаем шаблон для одной карты, например, `gpt/templates/ru/taro/single_{theme}.txt`
            template = await load_template(
                locale=user.locale, template_type=TemplateType.TARO, taro_theme=f"{theme}"
            )
            # Подставляем имя карты в шаблон. Предполагаем, что в шаблоне есть переменная {card_name}
            prompt = template.format(card_name=single_card_name)
            bot_logger.debug(f"[Taro Single] Prompt prepared (len={len(prompt) if prompt else 0}). First 150 chars: '{prompt[:150] if prompt else 'None'}...'")
        except Exception as e:
            bot_logger.error(f"[Taro Single] Error preparing prompt for user {user_id}: {e}", exc_info=True)
            return (__("error_generating_prediction_msg"), single_card_name)
        
        try:
            response = await send_gpt_request(prompt=prompt)
            bot_logger.info(f"[Taro Single] GPT API call completed. Response is None: {response is None}")
        except Exception as e:
            bot_logger.error(f"[Taro Single] Exception during GPT API call for user {user_id}: {e}", exc_info=True)
            return (__("error_generating_prediction_msg"), single_card_name)

        if not response or not response.strip():
            bot_logger.error(f"[Taro Single] Failed to get a valid response from GPT API for user {user_id}.")
            return (__("error_generating_prediction_msg"), single_card_name)

        try:
            await create_prediction(
                Prediction(
                    profile_id=user_profile.id,
                    prediction=response.strip(),
                    prediction_type=PredictionType.HOROSCOPE, # Или TAROT_SINGLE
                    recognition_str=cache_key,
                )
            )
            bot_logger.info(f"[Taro Single] Prediction saved to DB for key: {cache_key}")
        except Exception as e:
            bot_logger.error(f"[Taro Single] Error saving prediction to DB for user {user_id}: {e}", exc_info=True)
            # Не возвращаем ошибку пользователю из-за ошибки БД

        return (response.strip(), single_card_name)
    
async def make_taro_full_prediction(user_id: int, theme: str) -> tuple[str, list[str]]:
    bot_logger.info(f"[Taro Full] make_taro_full_prediction called: user_id={user_id}, theme={theme}")
    
    user = await find_user_by_id(user_id=user_id)
    if not user:
        bot_logger.error(f"[Taro Full] User with id {user_id} not found.")
        return (__("user_not_found_msg"), [])

    user_profile = await find_current_profile_by_user_id(user_id=user_id)
    if not user_profile:
        bot_logger.error(f"[Taro Full] Profile not found for user_id {user_id}.")
        return (__("error_profile_creation_msg"), []) 

    # === ВЫБИРАЕМ ТРИ СЛУЧАЙНЫЕ КАРТЫ ===
    drawn_cards = draw_random_cards(count=3)
    if len(drawn_cards) != 3:
        bot_logger.error(f"[Taro Full] Failed to draw 3 cards for user {user_id}. Drew: {drawn_cards}")
        return (__("error_generating_prediction_msg"), [])
    
    card1_name, card2_name, card3_name = drawn_cards
    bot_logger.info(f"[Taro Full] Drew cards: '{card1_name}', '{card2_name}', '{card3_name}'")

    # === КЛЮЧ ДЛЯ КЭШИРОВАНИЯ ===
    sorted_cards = sorted(drawn_cards) # Сортируем для уникальности ключа
    cache_key = f"taro_full_{theme}_{'_'.join(sorted_cards)}_{user.locale}_{user_profile.id}"
    bot_logger.debug(f"[Taro Full] Generated cache key: {cache_key}")

    # Проверяем кэш
    db_result = await find_prediction_by_recognition_and_type(
        recognition_str=cache_key, prediction_type=PredictionType.HOROSCOPE # Или TAROT_FULL
    )
    
    if db_result and db_result.prediction:
        bot_logger.info(f"[Taro Full] Found prediction in DB for key: {cache_key}")
        # Возвращаем текст из БД и список карт
        return (db_result.prediction, drawn_cards)
    else:
        if db_result:
            bot_logger.warning(f"[Taro Full] Found poisoned DB entry for key: {cache_key}. Will fetch a new one.")
            
        bot_logger.info(f"[Taro Full] No prediction in DB. Calling GPT API for key: {cache_key}")
        
        # === ФОРМИРУЕМ PROMPT ===
        try:
            # Загружаем шаблон для трёх карт, например, `gpt/templates/ru/taro/full_{theme}.txt`
            template = await load_template(
                locale=user.locale, template_type=TemplateType.TARO, taro_theme=f"full_{theme}"
            )
            # Подставляем имена карт в шаблон.
            # Предполагаем, что в шаблоне есть переменные {card1_name}, {card2_name}, {card3_name}
            prompt = template.format(card1_name=card1_name, card2_name=card2_name, card3_name=card3_name)
            bot_logger.debug(f"[Taro Full] Prompt prepared (len={len(prompt) if prompt else 0}). First 150 chars: '{prompt[:150] if prompt else 'None'}...'")
        except Exception as e:
            bot_logger.error(f"[Taro Full] Error preparing prompt for user {user_id}: {e}", exc_info=True)
            return (__("error_generating_prediction_msg"), drawn_cards)

        # === ВЫЗЫВАЕМ GPT API ===
        try:
            response = await send_gpt_request(prompt=prompt)
            bot_logger.info(f"[Taro Full] GPT API call completed. Response is None: {response is None}")
        except Exception as e:
            bot_logger.error(f"[Taro Full] Exception during GPT API call for user {user_id}: {e}", exc_info=True)
            return (__("error_generating_prediction_msg"), drawn_cards)

        if not response or not response.strip():
            bot_logger.error(f"[Taro Full] Failed to get a valid response from GPT API for user {user_id}.")
            return (__("error_generating_prediction_msg"), drawn_cards)

        # === СОХРАНЯЕМ РЕЗУЛЬТАТ В БД ===
        try:
            await create_prediction(
                Prediction(
                    profile_id=user_profile.id,
                    prediction=response.strip(),
                    prediction_type=PredictionType.HOROSCOPE, # Или TAROT_FULL
                    recognition_str=cache_key,
                )
            )
            bot_logger.info(f"[Taro Full] Prediction saved to DB for key: {cache_key}")
        except Exception as e:
            bot_logger.error(f"[Taro Full] Error saving prediction to DB for user {user_id}: {e}", exc_info=True)
            # Не возвращаем ошибку пользователю из-за ошибки БД

        return (response.strip(), drawn_cards)



@taro_router.callback_query(F.data.startswith(TaroCallback.FULL_SPREAD.value))
async def handle_taro_full_spread_callback(callback: CallbackQuery, state: FSMContext):
    logger = logging.getLogger(__name__) # Или bot_logger
    logger.info(f"[Taro Full Handler] !!! STARTED !!! User {callback.from_user.id} with data '{callback.data}'")

    try:
        logger.info(f"[Taro Full Handler] User {callback.from_user.id} pressed 'Full Spread' button. Callback data: {callback.data}")
        try:
            _, theme = callback.data.split(":", 1)
            logger.info(f"[Taro Full Handler] Parsed theme: '{theme}'")
        except ValueError:
            logger.error(f"[Taro Full Handler] Invalid callback data format: {callback.data}")
            await callback.answer(text=__("invalid_callback_data_msg"), show_alert=True)
            return

        user_id = callback.from_user.id

        logger.info(f"[Taro Full Handler] Sending 'wait_calc_msg' to user {user_id}")
        wait_msg = await callback.message.answer(text=__("wait_calc_msg"))

        try:
            logger.info(f"[Taro Full Handler] Calling make_taro_full_prediction for user {user_id}, theme '{theme}'")
            full_prediction = await make_taro_full_prediction(user_id=user_id, theme=theme)
            logger.info(f"[Taro Full Handler] make_taro_full_prediction returned. Prediction length: {len(full_prediction) if full_prediction else 0}")

            logger.info(f"[Taro Full Handler] Deleting wait message for user {user_id}")
            await wait_msg.delete()

            logger.info(f"[Taro Full Handler] Sending full prediction to user {user_id}")
            menu_kb = await get_menu_reply()
            logger.debug(f"[Taro Full Handler] get_menu_reply returned keyboard object: {menu_kb is not None}")
            await callback.message.answer(text=full_prediction, reply_markup=menu_kb)
            logger.info(f"[Taro Full Handler] Full prediction sent to user {user_id}")

        except Exception as inner_e:
            logger.error(f"[Taro Full Handler] Error during prediction/messaging for user {user_id}: {inner_e}", exc_info=True)
            try:
                await wait_msg.delete()
            except Exception as del_e:
                logger.warning(f"[Taro Full Handler] Could not delete wait_msg for user {user_id}: {del_e}")
            error_msg = _("error_generating_prediction_msg")
            menu_kb = await get_menu_reply()
            await callback.message.answer(text=error_msg, reply_markup=menu_kb)

    except Exception as outer_e:
        logger.critical(f"[Taro Full Handler] UNHANDLED EXCEPTION for user {callback.from_user.id}: {outer_e}", exc_info=True)
        try:
            error_msg = _("error_generating_prediction_msg")
            menu_kb = await get_menu_reply()
            await callback.message.answer(text=error_msg, reply_markup=menu_kb)
        except:
            pass

    finally:
        logger.info(f"[Taro Full Handler] Answering callback for user {callback.from_user.id}")
        await callback.answer()
        logger.info(f"[Taro Full Handler] !!! FINISHED !!! for user {callback.from_user.id}")



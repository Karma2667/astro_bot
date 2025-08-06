
import asyncio
import logging
from aiogram import Router, F # type: ignore
from aiogram.filters import Command, StateFilter  # type: ignore
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto # type: ignore
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
from aiogram.types import BufferedInputFile # type: ignore 
import os

taro_router = Router(name="taro")

TELEGRAM_CAPTION_LIMIT = 1024



@taro_router.message(lambda msg: msg.text and msg.text == __("taro_btn"))
async def handle_taro_menu_button(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} pressed 'Taro' button from main menu")
    await handle_taro_cmd(message, state)

@taro_router.message(Command("taro"))
async def handle_taro_cmd(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} using command /taro")
    await message.answer(
        text=__("choose_taro_theme_msg"),
        reply_markup=await get_taro_inline()
    )

async def handle_taro_theme_selection(callback: CallbackQuery, theme: str):
    bot_logger.info(f"[Taro] User {callback.from_user.id} selected theme: {theme}")
    user_id = callback.from_user.id
    wait_msg = None
    try:
        wait_msg = await callback.message.answer(text=__("wait_calc_msg"))
        
        prediction_text, card_name = await make_taro_prediction(user_id=user_id, theme=theme)
        
        if wait_msg:
            await wait_msg.delete()
            wait_msg = None # Сбрасываем, чтобы знать, что сообщение удалено

        if not prediction_text or not card_name:
            await callback.message.answer(text=__("error_generating_prediction_msg"), reply_markup=await get_menu_reply())
            await callback.answer()
            return

        full_spread_keyboard = await get_full_spread_button(theme)

        try:
            image_path = get_card_image_path(card_name)
            
            if not os.path.exists(image_path):
                 bot_logger.error(f"[Taro] Image file not found for card '{card_name}' at path: {image_path}")
                 await callback.message.answer(
                     text=f"{prediction_text}\n\n(Изображение карты '{card_name}' не найдено)",
                     reply_markup=full_spread_keyboard
                 )
                 await callback.answer()
                 return

            input_file = FSInputFile(path=image_path)

            if len(prediction_text) <= TELEGRAM_CAPTION_LIMIT:
                bot_logger.debug(f"[Taro] Sending image with caption for user {user_id}")
                await callback.message.answer_photo(
                    photo=input_file,
                    caption=prediction_text, # <-- Используем ТЕКСТ из кортежа
                    reply_markup=full_spread_keyboard
                )
            else:
                bot_logger.debug(f"[Taro] Caption too long ({len(prediction_text)} chars). Sending image and text separately for user {user_id}")
                await callback.message.answer_photo(
                    photo=input_file,
                    caption=f"Карта: {card_name}", # Минимальная подпись
                    reply_markup=None # Кнопку добавим к тексту
                )
                await callback.message.answer(
                    text=prediction_text,
                    reply_markup=full_spread_keyboard
                )

        except Exception as image_error:
            bot_logger.error(f"[Taro] Error sending image for card '{card_name}' to user {user_id}: {image_error}", exc_info=True)
            await callback.message.answer(text=prediction_text, reply_markup=full_spread_keyboard)
            
    except Exception as e:
        bot_logger.error(f"[Taro] Error in handle_taro_theme_selection for user {user_id}: {e}", exc_info=True)
        if wait_msg:
            try:
                await wait_msg.delete()
            except Exception as delete_error:
                bot_logger.warning(f"[Taro] Could not delete wait_msg for user {user_id}: {delete_error}")
        await callback.message.answer(text=__("error_generating_prediction_msg"), reply_markup=await get_menu_reply())
    finally:
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
    await state.set_state(CompatibilityStates.waiting_for_first_name)
    await callback.answer()

@taro_router.message(StateFilter(CompatibilityStates.waiting_for_first_name))
async def handle_taro_first_name_input(message: Message, state: FSMContext):
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
            template = await load_template(
                locale=user.locale, template_type=TemplateType.TARO, taro_theme=f"{theme}"
            )
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
                    prediction_type=PredictionType.HOROSCOPE.value, # Или TAROT_SINGLE
                    recognition_str=cache_key,
                )
            )
            bot_logger.info(f"[Taro Single] Prediction saved to DB for key: {cache_key}")
        except Exception as e:
            bot_logger.error(f"[Taro Single] Error saving prediction to DB for user {user_id}: {e}", exc_info=True)
    
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

    drawn_cards = draw_random_cards(count=3)
    if len(drawn_cards) != 3:
        bot_logger.error(f"[Taro Full] Failed to draw 3 cards for user {user_id}. Drew: {drawn_cards}")
        return (__("error_generating_prediction_msg"), [])
    
    card1_name, card2_name, card3_name = drawn_cards
    bot_logger.info(f"[Taro Full] Drew cards: '{card1_name}', '{card2_name}', '{card3_name}'")

    sorted_cards = sorted(drawn_cards) # Сортируем для уникальности ключа
    cache_key = f"taro_full_{theme}_{'_'.join(sorted_cards)}_{user.locale}_{user_profile.id}"
    bot_logger.debug(f"[Taro Full] Generated cache key: {cache_key}")

    db_result = await find_prediction_by_recognition_and_type(
        recognition_str=cache_key, prediction_type=PredictionType.HOROSCOPE# Или TAROT_FULL
    )
    
    if db_result and db_result.prediction:
        bot_logger.info(f"[Taro Full] Found prediction in DB for key: {cache_key}")
        return (db_result.prediction, drawn_cards)
    else:
        if db_result:
            bot_logger.warning(f"[Taro Full] Found poisoned DB entry for key: {cache_key}. Will fetch a new one.")
            
        bot_logger.info(f"[Taro Full] No prediction in DB. Calling GPT API for key: {cache_key}")
        
        try:
            template = await load_template(
                locale=user.locale, template_type=TemplateType.TARO, taro_theme=f"full_{theme}"
            )
            prompt = template.format(card1_name=card1_name, card2_name=card2_name, card3_name=card3_name)
            bot_logger.debug(f"[Taro Full] Prompt prepared (len={len(prompt) if prompt else 0}). First 150 chars: '{prompt[:150] if prompt else 'None'}...'")
        except Exception as e:
            bot_logger.error(f"[Taro Full] Error preparing prompt for user {user_id}: {e}", exc_info=True)
            return (__("error_generating_prediction_msg"), drawn_cards)

        try:
            response = await send_gpt_request(prompt=prompt)
            bot_logger.info(f"[Taro Full] GPT API call completed. Response is None: {response is None}")
        except Exception as e:
            bot_logger.error(f"[Taro Full] Exception during GPT API call for user {user_id}: {e}", exc_info=True)
            return (__("error_generating_prediction_msg"), drawn_cards)

        if not response or not response.strip():
            bot_logger.error(f"[Taro Full] Failed to get a valid response from GPT API for user {user_id}.")
            return (__("error_generating_prediction_msg"), drawn_cards)

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

        return (response.strip(), drawn_cards)


@taro_router.callback_query(F.data.startswith(TaroCallback.FULL_SPREAD.value))
async def handle_taro_full_spread_callback(callback: CallbackQuery, state: FSMContext):
    logger = bot_logger 
    logger.info(f"[Taro Full Handler] !!! STARTED !!! User {callback.from_user.id} with data '{callback.data}'")
    
    wait_msg = None 
    
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
        
        logger.info(f"[Taro Full Handler] Calling make_taro_full_prediction for user {user_id}, theme '{theme}'")
        full_prediction_text, drawn_cards_list = await make_taro_full_prediction(user_id=user_id, theme=theme)

        logger.info(
            f"[Taro Full Handler] make_taro_full_prediction returned. "
            f"Prediction length: {len(full_prediction_text) if full_prediction_text else 0}, "
            f"Cards drawn: {drawn_cards_list}"
        )
        
        if wait_msg:
            logger.info(f"[Taro Full Handler] Deleting wait message for user {user_id}")
            await wait_msg.delete()
            wait_msg = None # Сбрасываем, чтобы знать, что сообщение удалено

        if drawn_cards_list and isinstance(drawn_cards_list, list) and len(drawn_cards_list) == 3:
            media_list = []
            successfully_added_media = 0 # Счетчик успешно добавленных фото
            
            for i, card_name in enumerate(drawn_cards_list):
                try:
                    image_path = get_card_image_path(card_name)
                    logger.debug(f"[Taro Full Handler] Trying to add image for card '{card_name}' from path: {image_path}")
                    
                    if image_path.exists(): # Проверяем, существует ли файл
                        input_media = InputMediaPhoto(media=FSInputFile(image_path))
                        media_list.append(input_media)
                        successfully_added_media += 1
                        logger.debug(f"[Taro Full Handler] Added image for card '{card_name}' to media group.")
                    else:
                       logger.warning(f"[Taro Full Handler] Image file not found for card '{card_name}' at {image_path}. Skipping in media group.")
                except Exception as card_error:
                    logger.error(f"[Taro Full Handler] Error processing image for card '{card_name}': {card_error}", exc_info=True)
            if successfully_added_media > 0:
                logger.info(f"[Taro Full Handler] Sending media group with {successfully_added_media} images to user {user_id}")
                try:
                    await callback.message.answer_media_group(media=media_list)
                    logger.info(f"[Taro Full Handler] Media group sent successfully to user {user_id}")
                except Exception as media_group_error:
                    logger.error(f"[Taro Full Handler] Error sending media group to user {user_id}: {media_group_error}", exc_info=True)
                    await callback.message.answer(text=__("error_sending_images_msg", "Не удалось отправить изображения карт."))
            else:
                 logger.warning(f"[Taro Full Handler] No valid images found for drawn cards {drawn_cards_list}. Sending text only.")
                 await callback.message.answer(text=__("no_card_images_available_msg", "Изображения карт временно недоступны."))
        else:
            logger.warning(
                f"[Taro Full Handler] Expected list of 3 cards, got {type(drawn_cards_list)} "
                f"with length {len(drawn_cards_list) if isinstance(drawn_cards_list, (list, tuple)) else 'N/A'}. "
                f"Skipping image send. Drawn cards data: {drawn_cards_list}"
            )

        logger.info(f"[Taro Full Handler] Sending full prediction text to user {user_id}")
        menu_kb = await get_menu_reply()
        logger.debug(f"[Taro Full Handler] get_menu_reply returned keyboard object: {menu_kb is not None}")
        
        await callback.message.answer(text=full_prediction_text, reply_markup=menu_kb)
        logger.info(f"[Taro Full Handler] Full prediction text sent to user {user_id}")
        
    except Exception as e:
        logger.error(f"[Taro Full Handler] Error in handle_taro_full_spread_callback for user {callback.from_user.id}: {e}", exc_info=True)
        
        if wait_msg:
            try:
                await wait_msg.delete()
                logger.info(f"[Taro Full Handler] Wait message deleted after error for user {callback.from_user.id}")
            except Exception as delete_error:
                logger.warning(f"[Taro Full Handler] Could not delete wait_msg for user {callback.from_user.id}: {delete_error}")
        
        try:
            error_msg = __("error_generating_prediction_msg") 
            menu_kb = await get_menu_reply()
            await callback.message.answer(text=error_msg, reply_markup=menu_kb)
            logger.info(f"[Taro Full Handler] Error message sent to user {callback.from_user.id}")
        except Exception as send_error:
             logger.error(f"[Taro Full Handler] Failed to send error message to user {callback.from_user.id}: {send_error}", exc_info=True)
             
    finally:
        try:
            await callback.answer()
            logger.info(f"[Taro Full Handler] Callback answered for user {callback.from_user.id}")
        except Exception as answer_error:
            logger.warning(f"[Taro Full Handler] Could not answer callback for user {callback.from_user.id}: {answer_error}")
            
        logger.info(f"[Taro Full Handler] !!! FINISHED !!! for user {callback.from_user.id}")

import asyncio
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.i18n import gettext as _
from datetime import datetime, date, timedelta
import re
from database.user.service import find_user_by_id
from logger import bot_logger
from filters.access import ProfileRegistered
from keyboards.inline.callback import EventsCallback
from keyboards.reply.common import get_menu_reply, get_decline_reply
from keyboards.inline.events import get_events_inline, get_date_selection_inline
from gpt.template import load_template, inject_profile_into_template,inject_names_into_template, TemplateType
from gpt.gpt import send_gpt_request
from database.user.models import Subscription
from database.user.service import find_user_by_id
from database.profile.models import Profile
from database.profile.service import find_current_profile_by_user_id, create_profile
from database.predictions.models import Prediction, PredictionType
from database.predictions.service import create_prediction, find_prediction_by_recognition_and_type
from database.db import async_session_maker


class CompatibilityStates(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_second_name = State()

class EventStates(StatesGroup):
    waiting_for_custom_date = State() 

event_router = Router(name="event-router")


async def shorten_event(sub: Subscription, event: str) -> str:
    if not event:
        return ""
    if sub is Subscription.FREELY:
        crop_idx = len(event) // 3
        return event[:crop_idx] + "..."
    return event

async def format_event(sub: Subscription, event: str) -> str:
    short_event = await shorten_event(sub=sub, event=event)
    extra = ""
    if sub is Subscription.FREELY and short_event:
        extra = f'\n\n{_("freely_unavailable_msg")}'
    return short_event + extra



async def make_event(user_id: int, theme: str, target_date: date) -> str:
    bot_logger.info(f"make_event called: user_id={user_id}, theme={theme}, target_date={target_date}")

    # 1. Получаем пользователя
    user = await find_user_by_id(user_id=user_id)
    if not user:
        bot_logger.error(f"User with id {user_id} not found for event calculation.")
        return _("user_not_found_msg")
    bot_logger.info(f"User found: {user.name} (ID: {user.user_id})")

    user_profile = await find_current_profile_by_user_id(user_id=user_id)
    if not user_profile:
        bot_logger.error(f"Profile not found for user_id {user_id}.")
        bot_logger.warning(f"No profile found for user_id {user_id}, creating new profile")
        new_profile = Profile(
            user_id=user_id,
            title=f"Profile_{user_id}",
            birth_date=date(2000, 1, 1),
            birth_time="00:00:00",
            birth_location_name="Не указано"
        )
        try:
            async with async_session_maker() as session:
                user_profile = await create_profile(profile=new_profile, session=session)
                user.current_profile_id = user_profile.id
                session.add(user)
                await session.commit()
                bot_logger.info(f"New profile created for user_id {user_id}: {user_profile.title}")
        except Exception as e:
            bot_logger.error(f"Failed to create profile for user_id {user_id}: {e}", exc_info=True)
            return _("error_profile_creation_msg")
    else:
         bot_logger.info(f"Profile found: {user_profile.title} (ID: {user_profile.id})")

    cache_key = f"{target_date.strftime('%d.%m.%Y')}_{theme}_{user.locale}_{user_profile.id}"
    bot_logger.debug(f"Generated cache key: {cache_key}")

    db_event = await find_prediction_by_recognition_and_type(
        recognition_str=cache_key, prediction_type=PredictionType.EVENT
    )
    
    if db_event and db_event.prediction:
        bot_logger.info(f"Found a valid prediction in DB for key: {cache_key}")
        return await format_event(sub=user.subscription, event=db_event.prediction)
    else:
        if db_event:
            bot_logger.warning(f"Found a poisoned DB entry for key: {cache_key}. Will fetch a new one.")
            
        bot_logger.info(f"No valid prediction in DB. Preparing to call GPT API for key: {cache_key}")
        
        try:
            template = await load_template(
                locale=user.locale, template_type=TemplateType.EVENT
            )
            bot_logger.debug(f"Template loaded for locale {user.locale}")
            
            formatted_date = target_date.strftime("%d.%m.%Y")
            prompt = await inject_profile_into_template(
               extra=f"Дата для анализа: {formatted_date}. Тема: {theme}. Сфокусируйся исключительно на этой одной дате и теме. Не упоминай и не анализируй другие даты или периоды.",
                template=template,
                profile=user_profile,
            )
            bot_logger.debug(f"GPT Prompt prepared (first 100 chars): {prompt[:100] if prompt else 'None'}...")
        except Exception as e:
            bot_logger.error(f"Error preparing GPT prompt for user {user_id}: {e}", exc_info=True)
            return _("error_generating_prediction_msg")

        bot_logger.debug(f"GPT Prompt prepared (len={len(prompt) if prompt else 0}): {prompt[:100] if prompt else 'None'}...")
        try:
            response = await send_gpt_request(prompt=prompt)
            bot_logger.debug(f"GPT Response received: {response is not None}")
        except Exception as e:
            bot_logger.error(f"Error calling GPT API for user {user_id}: {e}", exc_info=True)
            return _("error_generating_prediction_msg")

        if response is None:
            bot_logger.error(f"Failed to get response from GPT API for user {user_id}.")
            return _("error_generating_prediction_msg")

        try:
            await create_prediction(
                Prediction(
                    profile_id=user_profile.id,
                    prediction=response,
                    prediction_type=PredictionType.EVENT,
                    recognition_str=cache_key,
                )
            )
            bot_logger.info(f"Prediction saved to DB for key: {cache_key}")
        except Exception as e:
            bot_logger.error(f"Error saving prediction to DB for user {user_id}: {e}", exc_info=True)
            

        return await format_event(sub=user.subscription, event=response)

async def make_compatibility(user_id: int, name1: str, name2: str) -> str:
    """
    Рассчитывает совместимость по двум именам.
    :param user_id: ID пользователя
    :param name1: Первое имя
    :param name2: Второе имя
    :return: Строка с результатом расчета
    """
    bot_logger.info(f"make_compatibility called: user_id={user_id}, name1={name1}, name2={name2}")
    user = await find_user_by_id(user_id=user_id)
    if not user:
        bot_logger.error(f"User with id {user_id} not found for compatibility calculation.")
        return _("user_not_found_msg")

    normalized_name1 = name1.strip().lower()
    normalized_name2 = name2.strip().lower()
    sorted_names = sorted([normalized_name1, normalized_name2])
    cache_key = f"compatibility_{sorted_names[0]}_{sorted_names[1]}_{user.locale}"
    bot_logger.debug(f"Generated compatibility cache key: {cache_key}")

    db_result = await find_prediction_by_recognition_and_type(
        recognition_str=cache_key, prediction_type=PredictionType.EVENT
    )
    
    if db_result and db_result.prediction:
        bot_logger.info(f"Found a valid compatibility prediction in DB for key: {cache_key}")
        return db_result.prediction 
    else:
        if db_result:
            bot_logger.warning(f"Found a poisoned DB entry for key: {cache_key}. Will fetch a new one.")
            
        bot_logger.info(f"No valid compatibility prediction in DB. Preparing to call GPT API for key: {cache_key}")
        
        try:
            bot_logger.debug("Attempting to load compatibility template...")
            template = await load_template(
                locale=user.locale, template_type=TemplateType.COMPATIBILITY
            )
            bot_logger.debug("Compatibility template loaded successfully.")
            
            bot_logger.debug(f"Injecting names into template: name1='{name1}', name2='{name2}'")
            prompt = await inject_names_into_template(
                name1=name1, name2=name2, template=template
            )
            bot_logger.debug(f"Compatibility GPT Prompt prepared (len={len(prompt) if prompt else 0}). First 150 chars: '{prompt[:150] if prompt else 'None'}...'")
        except Exception as e:
            bot_logger.error(f"Error preparing compatibility prompt for user {user_id}: {e}", exc_info=True)
            return _("error_generating_prediction_msg")

        bot_logger.info("About to call send_gpt_request...")
        try:
            response = await send_gpt_request(prompt=prompt)
            bot_logger.info(f"send_gpt_request completed. Response is None: {response is None}. Response type: {type(response) if response else 'N/A'}. Response length: {len(response) if response else 'N/A'}")
        except Exception as e:
            bot_logger.error(f"Exception during send_gpt_request call for user {user_id}: {e}", exc_info=True)
            return _("error_generating_prediction_msg")

        if response is None or (isinstance(response, str) and not response.strip()):
            bot_logger.error(f"Failed to get a valid response from GPT API for user {user_id} (compatibility).")
            return _("error_generating_prediction_msg")

        try:
            bot_logger.debug("Attempting to save compatibility result to DB...")
            await create_prediction(
                Prediction(
                    profile_id=None,
                    prediction=response,
                    prediction_type=PredictionType.EVENT,
                    recognition_str=cache_key,
                )
            )
            bot_logger.info(f"Compatibility prediction saved to DB for key: {cache_key}")
        except Exception as e:
            bot_logger.error(f"Error saving compatibility prediction to DB for user {user_id}: {e}", exc_info=True)

        return response

@event_router.message(Command("events"), ProfileRegistered())
async def handle_event_cmd(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} using command /events")
    await message.answer(
        text=_("wanna_date_msg"), reply_markup=await get_events_inline()
    )

async def handle_event_theme(callback: CallbackQuery, theme: str):
    await callback.message.answer(
        text=_("choose_date_msg"), 
        reply_markup=await get_date_selection_inline(theme=theme),
    )

@event_router.callback_query(F.data.startswith(EventsCallback.STUDY))
async def handle_study_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} selected 'Study'")
    await handle_event_theme(callback=callback, theme="study")
    await callback.answer()

@event_router.callback_query(F.data.startswith(EventsCallback.MOOD))
async def handle_mood_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} selected 'Mood'")
    await handle_event_theme(callback=callback, theme="mood")
    await callback.answer()

@event_router.callback_query(F.data.startswith(EventsCallback.LOVE))
async def handle_love_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} selected 'Love'")
    await handle_event_theme(callback=callback, theme="love")
    await callback.answer()

@event_router.callback_query(F.data.startswith(EventsCallback.INCOME))
async def handle_income_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} selected 'Income'")
    await handle_event_theme(callback=callback, theme="income")
    await callback.answer()

@event_router.callback_query(F.data.startswith(EventsCallback.SUCCESS))
async def handle_success_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} selected 'Success'")
    await handle_event_theme(callback=callback, theme="success")
    await callback.answer()

@event_router.callback_query(F.data.startswith(EventsCallback.COMPATIBILITY))
async def handle_compatibility_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} selected 'Compatibility'")
    
    await callback.message.answer(
        text=_("send_first_name_msg"),
        reply_markup=await get_decline_reply() 
    )
    
    await state.set_state(CompatibilityStates.waiting_for_first_name)
    
    await callback.answer()


@event_router.callback_query(F.data.startswith(EventsCallback.DURATION_TODAY))
async def handle_duration_today_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} selected 'Today'")
    data_parts = callback.data.split()
    if len(data_parts) < 2:
        await callback.answer("Ошибка: неверные данные для 'Сегодня'.")
        return
        
    theme = data_parts[1]
    target_date = date.today() # Получаем сегодняшнюю дату
    
    user_id = callback.message.chat.id
    wait_msg = await callback.message.answer(text=_("wait_calc_msg"))
    
    # Вызываем обновленную функцию make_event с объектом date
    event_result = await make_event(user_id=user_id, theme=theme, target_date=target_date)
    
    await wait_msg.delete()
    await callback.message.answer(text=event_result, reply_markup=await get_menu_reply())
    await callback.answer()

@event_router.callback_query(F.data.startswith(EventsCallback.DURATION_TOMORROW))
async def handle_duration_tomorrow_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} selected 'Tomorrow'")
    data_parts = callback.data.split()
    if len(data_parts) < 2:
        await callback.answer("Ошибка: неверные данные для 'Завтра'.")
        return
        
    theme = data_parts[1]
    target_date = date.today() + timedelta(days=1) # Получаем завтрашнюю дату
    
    user_id = callback.message.chat.id
    wait_msg = await callback.message.answer(text=_("wait_calc_msg"))
    
    event_result = await make_event(user_id=user_id, theme=theme, target_date=target_date)
    
    await wait_msg.delete()
    await callback.message.answer(text=event_result, reply_markup=await get_menu_reply())
    await callback.answer()

@event_router.callback_query(F.data.startswith(EventsCallback.DURATION_PICK_DATE))
async def handle_duration_pick_date_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} wants to pick a custom date")
    data_parts = callback.data.split()
    if len(data_parts) < 2:
        await callback.answer("Ошибка: неверные данные для 'Выбрать дату'.")
        return
        
    theme = data_parts[1]
    await state.set_state(EventStates.waiting_for_custom_date)
    await state.update_data(theme=theme)
    
    await callback.message.answer(
        text=_("send_date_msg"),
        reply_markup=None 
    )
    await callback.answer()

@event_router.message(CompatibilityStates.waiting_for_first_name)
async def handle_first_name_input(message: Message, state: FSMContext):
    bot_logger.info(f"handle_first_name_input called with message: '{message.text}'")
    try:
        bot_logger.info(f"User {message.from_user.id} entered first name: {message.text}")
        
        if not message.text or len(message.text.strip()) < 2:
            bot_logger.warning(f"Invalid first name entered: '{message.text}'")
            await message.answer(text=_("invalid_name_msg")) # Добавь этот перевод
            return

        await state.update_data(first_name=message.text.strip())
        bot_logger.info("First name saved to state")
        
        msg_text = _("send_second_name_msg")
        bot_logger.info(f"About to send 'send_second_name_msg' message. Translated text: '{msg_text}'")
        reply_markup = await get_decline_reply()
        bot_logger.info("get_decline_reply called successfully")
        
        await message.answer(text=msg_text, reply_markup=reply_markup)
        bot_logger.info("'send_second_name_msg' message sent")

        await state.set_state(CompatibilityStates.waiting_for_second_name)
        bot_logger.info("State changed to waiting_for_second_name")
    except Exception as e:
        bot_logger.error(f"Error in handle_first_name_input for user {message.from_user.id}: {e}", exc_info=True)
        try:
            await message.answer("Произошла ошибка при обработке первого имени. Попробуйте снова.")
        except:
            pass
        
@event_router.message(StateFilter(CompatibilityStates.waiting_for_second_name))
async def handle_second_name_input(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} entered second name: {message.text}")
    
    if not message.text or len(message.text.strip()) < 2:
        await message.answer(text=_("invalid_name_msg")) # Добавь этот перевод
        return

    user_data = await state.get_data()
    first_name = user_data.get('first_name')
    second_name = message.text.strip()
    
    user_id = message.from_user.id

    wait_msg = await message.answer(text=_("wait_calc_msg"))
    
    compatibility_result = await make_compatibility(user_id=user_id, name1=first_name, name2=second_name)
    
    await wait_msg.delete()
    
    await message.answer(text=compatibility_result, reply_markup=await get_menu_reply())
    
    await state.clear()


@event_router.message(StateFilter(EventStates.waiting_for_custom_date))
async def handle_user_custom_date_input(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} entered custom date: {message.text}")
    
    user_data = await state.get_data()
    theme = user_data.get('theme')
    
    if not theme:
        await message.answer("Ошибка: тема не найдена. Попробуйте снова через /events.")
        await state.clear()
        return

    date_pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    if not message.text or not re.match(date_pattern, message.text):
        await message.answer(text=_("date_error_msg")) # Используем существующий перевод ошибки
        return

    try:
        target_date = datetime.strptime(message.text, "%d.%m.%Y").date()
        
        if target_date < date(1900, 1, 1) or target_date > date(2100, 12, 31):
             await message.answer("Пожалуйста, введите корректную дату между 01.01.1900 и 31.12.2100.")
             return # Не очищаем состояние
            
    except ValueError:
        await message.answer(text=_("date_error_msg"))
        return

    user_id = message.from_user.id
    wait_msg = await message.answer(text=_("wait_calc_msg"))
    
    event_result = await make_event(user_id=user_id, theme=theme, target_date=target_date)
    
    await wait_msg.delete()
    await message.answer(text=event_result, reply_markup=await get_menu_reply())
    await state.clear() # Очищаем состояние FSM после успешного расчета

@event_router.message(lambda msg: msg.text == "🔮 Таро")
async def handle_taro_menu_button(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} pressed 'Taro' button from main menu")
    await handle_taro_cmd(message, state)

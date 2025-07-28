# handlers/taro.py
import asyncio
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

# Импортируем состояние из events.py
from handlers.events import CompatibilityStates, make_compatibility

from logger import bot_logger
# Импортируем свою клавиатуру и коллбэки
from keyboards.inline.taro import get_taro_inline
from keyboards.inline.callback import TaroCallback
# Импортируем reply-клавиатуры
from keyboards.reply.common import get_menu_reply, get_decline_reply

taro_router = Router(name="taro")

# --- ХЕНДЛЕРЫ КОМАНД И КНОПОК ---

@taro_router.message(lambda msg: msg.text and msg.text == _("taro_btn"))
async def handle_taro_menu_button(message: Message, state: FSMContext):
    """Обработчик нажатия кнопки 'Таро' в главном меню."""
    bot_logger.info(f"User {message.from_user.id} pressed 'Taro' button from main menu")
    await handle_taro_cmd(message, state)

@taro_router.message(Command("taro"))
async def handle_taro_cmd(message: Message, state: FSMContext):
    """Обработчик команды /taro."""
    bot_logger.info(f"User {message.from_user.id} using command /taro")
    await message.answer(
        text=_("choose_taro_theme_msg"),
        reply_markup=await get_taro_inline()
    )

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

async def handle_taro_theme_selection(callback: CallbackQuery, theme: str):
    """Вспомогательная функция для обработки выбора темы Таро."""
    bot_logger.info(f"User {callback.from_user.id} selected Taro theme: {theme}")
    await callback.message.answer(
        text=_("taro_theme_selected_msg").format(theme=theme),
        reply_markup=await get_menu_reply()
    )
    await callback.answer()

# --- ХЕНДЛЕРЫ ДЛЯ ВЫБОРА ТЕМЫ ТАРО ---

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
        text=_("send_first_name_msg"),
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
        await message.answer(text=_("invalid_name_msg"))
        return

    await state.update_data(first_name=message.text.strip())
    
    await message.answer(
        text=_("send_second_name_msg"),
        reply_markup=await get_decline_reply()
    )
    
    await state.set_state(CompatibilityStates.waiting_for_second_name)

@taro_router.message(StateFilter(CompatibilityStates.waiting_for_second_name))
async def handle_taro_second_name_input(message: Message, state: FSMContext):
    """Обработчик ввода второго имени для Таро-совместимости и запуск расчета."""
    bot_logger.info(f"[Taro] User {message.from_user.id} entered second name: {message.text}")
    
    if not message.text or len(message.text.strip()) < 2:
        await message.answer(text=_("invalid_name_msg"))
        return

    user_data = await state.get_data()
    first_name = user_data.get('first_name')
    second_name = message.text.strip()
    
    user_id = message.from_user.id
    
    wait_msg = await message.answer(text=_("wait_calc_msg"))
    
    try:
        # Вызываем функцию расчета совместимости из events.py
        compatibility_result = await make_compatibility(user_id=user_id, name1=first_name, name2=second_name)
        
        await wait_msg.delete()
        await message.answer(text=compatibility_result, reply_markup=await get_menu_reply())
    except Exception as e:
        bot_logger.error(f"[Taro] Error calculating compatibility for user {user_id}: {e}", exc_info=True)
        await wait_msg.delete()
        await message.answer(text=_("error_generating_prediction_msg"), reply_markup=await get_menu_reply())
        
    finally:
        await state.clear()

# --- ЗАГЛУШКА ДЛЯ НЕОБРАБОТАННЫХ КОЛЛБЭКОВ ---

@taro_router.callback_query(F.data.startswith("taro_"))
async def handle_any_taro_callback(callback: CallbackQuery, state: FSMContext):
    """Заглушка для любых других коллбэков Таро."""
    bot_logger.info(f"User {callback.from_user.id} sent unhandled Taro callback: {callback.data}")
    await callback.answer(
        text=_("taro_feature_coming_soon_msg"),
        show_alert=True
    )
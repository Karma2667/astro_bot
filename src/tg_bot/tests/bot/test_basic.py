import pytest
from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.context import FSMContext

from states.test import SurveyManuallyStates
from utils import get_update, get_message
from locales.translation import get_translation


@pytest.mark.asyncio
async def test_start_command(dispatcher: Dispatcher, bot: Bot):
    result = await dispatcher.feed_raw_update(bot=bot, update=get_update(message=get_message(text='/start')))
    assert result.text == get_translation('welcome')


@pytest.mark.asyncio
async def test_help_command(dispatcher: Dispatcher, bot: Bot):
    result = await dispatcher.feed_update(bot=bot, update=get_update(message=get_message(text='/help')))
    assert result.text == get_translation('help_message')


@pytest.mark.asyncio
async def test_process_register_address(
    dispatcher: Dispatcher,
    bot: Bot,
    memory_storage: MemoryStorage,
    storage_key: StorageKey,
):
    message = get_message(text='/reset')
    state = FSMContext(storage=memory_storage, key=storage_key)
    await state.set_state(SurveyManuallyStates.register_address.state)
    result = await dispatcher.feed_update(bot=bot, update=get_update(message=message))
    assert result.text == get_translation('declined')
    assert await state.get_state() is None
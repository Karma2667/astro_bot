import pytest
import pytest_asyncio
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from mocked_bot import MockedBot

from handlers import all_routers
from middleware import register_middlewares
from utils import TEST_USER, TEST_USER_CHAT


@pytest_asyncio.fixture(scope='session')
async def memory_storage():
    storage = MemoryStorage()
    try:
        yield storage
    finally:
        await storage.close()


@pytest.fixture(scope='session')
def storage_key(bot: MockedBot):
    return StorageKey(chat_id=TEST_USER_CHAT.id, user_id=TEST_USER.id, bot_id=bot.id)


@pytest.fixture(scope='session')
def bot():
    return MockedBot()


@pytest_asyncio.fixture(scope='session')
async def dispatcher(bot, memory_storage):
    dp = Dispatcher(storage=memory_storage)
    register_middlewares(dp) 
    dp.include_routers(*all_routers)
    await dp.emit_startup()
    try:
        yield dp
    finally:
        await dp.emit_shutdown()

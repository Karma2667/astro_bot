import pytest
from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.context import FSMContext

from states.test import SurveyManuallyStates
from keyboards.inline.profile import DOC_IMAGE_OPT_CD, MANUALLY_OPT_CD
from utils import get_update, get_message, get_call
from locales.translation import get_translation


@pytest.mark.asyncio
async def test_handle_register(dispatcher: Dispatcher, bot: Bot, memory_storage: MemoryStorage, storage_key: StorageKey):
    message = get_message(text='/register')
    result = await dispatcher.feed_update(bot=bot, update=get_update(message=message))
    assert result.text == get_translation('register')


@pytest.mark.asyncio
async def test_handle_doc_image_opt(dispatcher: Dispatcher, bot: Bot, memory_storage: MemoryStorage, storage_key: StorageKey):
    message = get_message(text='Some text for doc image option')
    callback = get_call(message=message, data=DOC_IMAGE_OPT_CD)
    result = await dispatcher.feed_update(bot=bot, update=get_update(call=callback))
    assert result.caption == get_translation('send_images_group')


@pytest.mark.asyncio
async def test_handle_manually_opt(dispatcher: Dispatcher, bot: Bot, memory_storage: MemoryStorage, storage_key: StorageKey):
    message = get_message(text='Some text for manually option')
    callback = get_call(message=message, data=MANUALLY_OPT_CD)
    result = await dispatcher.feed_update(bot=bot, update=get_update(call=callback))
    assert result.text == get_translation('send_phone_number')


@pytest.mark.asyncio
async def test_process_phone_number_valid(dispatcher: Dispatcher, bot: Bot, memory_storage: MemoryStorage, storage_key: StorageKey):
    valid_phone_numbers = ['+12345678901', '1234567890', '+441234567890', '12345', '+79561234567', '456789012345678', '+9187654321', '89123456789', '+441234567890', '911234567890123']
    messages = [get_message(text=phone_number) for phone_number in valid_phone_numbers]
    state = FSMContext(storage=memory_storage, key=storage_key)
    for message in messages:
        await state.set_state(SurveyManuallyStates.phone_number.state)
        result = await dispatcher.feed_update(bot=bot, update=get_update(message=message))
        assert result.text == get_translation('send_fio')


@pytest.mark.asyncio
async def test_process_phone_number_invalid(dispatcher: Dispatcher, bot: Bot, memory_storage: MemoryStorage, storage_key: StorageKey):
    invalid_phone_numbers = ['123', 'ab1234567890', '12345678901234567', '+12', '123.456.7890', '123-456-789a', '+12345abc678', '1234567890123@']
    messages = [get_message(text=phone_number) for phone_number in invalid_phone_numbers]
    state = FSMContext(storage=memory_storage, key=storage_key)
    for message in messages:
        await state.set_state(SurveyManuallyStates.phone_number.state)
        result = await dispatcher.feed_update(bot=bot, update=get_update(message=message))
        assert result.text == get_translation('phone_number_incorrect')


@pytest.mark.asyncio
async def test_process_fio_valid(dispatcher: Dispatcher, bot: Bot, memory_storage: MemoryStorage, storage_key: StorageKey):
    valid_fios = ['John Doe', 'Jane Smith', 'Alice Johnson', 'Rob Stark', 'Tywin Lannister']
    for fio in valid_fios:
        message = get_message(text=fio)
        state = FSMContext(storage=memory_storage, key=storage_key)
        await state.update_data(phone_number='+1234567890')
        await state.set_state(SurveyManuallyStates.fio.state)
        result = await dispatcher.feed_update(bot=bot, update=get_update(message=message))
        assert result.text == get_translation('send_citizenship')


@pytest.mark.asyncio
async def test_process_fio_invalid(dispatcher: Dispatcher, bot: Bot, memory_storage: MemoryStorage, storage_key: StorageKey):
    invalid_fios = ['SingleName', 'John', '', '12', 'A']
    for fio in invalid_fios:
        message = get_message(text=fio)
        state = FSMContext(storage=memory_storage, key=storage_key)
        await state.set_state(SurveyManuallyStates.fio.state)
        result = await dispatcher.feed_update(bot=bot, update=get_update(message=message))
        assert result.text == get_translation('fio_incorrect')


@pytest.mark.asyncio
async def test_process_citizenship_valid(dispatcher: Dispatcher, bot: Bot, memory_storage: MemoryStorage, storage_key: StorageKey):
    valid_citizenships = ['Russia', 'USA', 'UK', 'Canada', 'Australia']
    for citizenship in valid_citizenships:
        message = get_message(text=citizenship)
        state = FSMContext(storage=memory_storage, key=storage_key)
        await state.set_state(SurveyManuallyStates.citizenship.state)
        result = await dispatcher.feed_update(bot=bot, update=get_update(message=message))
        assert result.text == get_translation('send_passport_num_ser')


@pytest.mark.asyncio
async def test_process_passport_num_ser_valid(dispatcher: Dispatcher, bot: Bot, memory_storage: MemoryStorage, storage_key: StorageKey):
    valid_num_ser = ['0718 123456', '1234 567890', '8765 432109', '1122 334455']
    for num_ser in valid_num_ser:
        message = get_message(text=num_ser)
        state = FSMContext(storage=memory_storage, key=storage_key)
        await state.set_state(SurveyManuallyStates.passport_num_ser.state)
        result = await dispatcher.feed_update(bot=bot, update=get_update(message=message))
        assert result.text == get_translation('send_passport_department')
        data = await state.get_data()
        assert data['passport_num_ser'] == num_ser


@pytest.mark.asyncio
async def test_process_passport_date_valid(dispatcher: Dispatcher, bot: Bot, memory_storage: MemoryStorage, storage_key: StorageKey):
    valid_dates = ['01.01.2000', '31.12.1999', '15.05.2010']
    for date in valid_dates:
        message = get_message(text=date)
        state = FSMContext(storage=memory_storage, key=storage_key)
        await state.update_data(passport_num_ser='0718 123456')
        await state.set_state(SurveyManuallyStates.passport_date.state)
        result = await dispatcher.feed_update(bot=bot, update=get_update(message=message))
        assert result.text == get_translation('send_department_code')
        data = await state.get_data()
        assert data['passport_date'] == date


@pytest.mark.asyncio
async def test_process_passport_date_invalid(dispatcher: Dispatcher, bot: Bot, memory_storage: MemoryStorage, storage_key: StorageKey):
    invalid_dates = ['invalid_date', '01/01/2000', '2000.01.01']
    for date in invalid_dates:
        message = get_message(text=date)
        state = FSMContext(storage=memory_storage, key=storage_key)
        await state.set_state(SurveyManuallyStates.passport_date.state)
        result = await dispatcher.feed_update(bot=bot, update=get_update(message=message))
        assert result.text == get_translation('passport_date_incorrect')


@pytest.mark.asyncio
async def test_process_department_code_valid(dispatcher: Dispatcher, bot: Bot, memory_storage: MemoryStorage, storage_key: StorageKey):
    valid_codes = ['123-456', '987-654', '111-222']
    for code in valid_codes:
        message = get_message(text=code)
        state = FSMContext(storage=memory_storage, key=storage_key)
        await state.update_data(passport_date='01.01.2000')
        await state.set_state(SurveyManuallyStates.department_code.state)
        result = await dispatcher.feed_update(bot=bot, update=get_update(message=message))
        assert result.text == get_translation('send_register_address')
        data = await state.get_data()
        assert data['department_code'] == code


@pytest.mark.asyncio
async def test_process_register_address(dispatcher: Dispatcher, bot: Bot, memory_storage: MemoryStorage, storage_key: StorageKey):
    message = get_message(text='123 Main St')
    state = FSMContext(storage=memory_storage, key=storage_key)
    await state.set_state(SurveyManuallyStates.register_address.state)
    result = await dispatcher.feed_update(bot=bot, update=get_update(message=message))
    assert result.text.startswith(get_translation('register_finished'))
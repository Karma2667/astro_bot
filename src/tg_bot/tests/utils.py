import datetime

from aiogram.types import User, Chat, Message, CallbackQuery, Update
from config import settings


TEST_USER = User(
    id=123,
    is_bot=False,
    first_name="test",
    last_name="user",
    username="test_user",
    language_code=settings.locales.DEFAULT_LOCALE,
)


TEST_USER_CHAT = Chat(
    id=-123,
    type="private",
    title="test",
    username=TEST_USER.username,
    first_name=TEST_USER.first_name,
    last_name=TEST_USER.last_name,
)


def get_message(text: str):
    return Message(
        message_id=123,
        date=datetime.datetime.now(),
        chat=TEST_USER_CHAT,
        from_user=TEST_USER,
        text=text,
        sender_chat=TEST_USER_CHAT,
    )


def get_call(message: Message, data: str):
    return CallbackQuery(
        id="123",
        from_user=TEST_USER,
        message=message,
        chat_instance="123",
        data=data
    )


def get_update(message: Message = None, call: CallbackQuery = None):
    return Update(
        update_id=12,
        message=message,
        callback_query=call
    )
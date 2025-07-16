from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.enums.chat_type import ChatType


class Private(BaseFilter):
    def __init__(self):
        self.chat_type = ChatType.PRIVATE.value

    async def __call__(self, message: Message) -> bool:
        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type

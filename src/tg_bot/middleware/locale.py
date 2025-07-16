from typing import Any

from aiogram.types import TelegramObject
from aiogram.utils.i18n.middleware import I18nMiddleware

from config import settings
from database.user.service import find_user_by_id


class LocaleMiddleware(I18nMiddleware):
    DEFAULT_LANGUAGE_CODE = settings.locales.DEFAULT_LOCALE

    async def get_locale(self, event: TelegramObject, data: dict[str, Any]) -> str:
        user_id = data.get('event_from_user').id
        user = await find_user_by_id(user_id=user_id)
        if user:
            return user.locale
        return self.DEFAULT_LANGUAGE_CODE
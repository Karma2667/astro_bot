from aiogram import Dispatcher

from bot_ import i18n as _i18n
from middleware.locale import LocaleMiddleware


def register_middlewares(dp: Dispatcher):
    LocaleMiddleware(i18n=_i18n).setup(dp)
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.i18n.core import I18n

from config import settings


bot = Bot(settings.bot.BOT_TOKEN, default=DefaultBotProperties(parse_mode='html'))
dispatcher = Dispatcher(bot=bot)

i18n: I18n = I18n(
    path=settings.locales.LOCALE_PATH, 
    default_locale=settings.locales.DEFAULT_LOCALE, 
    domain=settings.locales.I18N_DOMAIN
)

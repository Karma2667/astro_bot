from bot_ import bot, i18n
from handlers.horoscope import make_horoscope
from database.user.service import find_all_users
from logger import bot_logger


async def send_mailing():
    bot_logger.info("Sending horoscope to all users")
    users = await find_all_users()
    for user in users:
        if user.is_mail_subscribed:
            with i18n.context():
                horoscope = await make_horoscope(user_id=user.user_id, date="today")
                await bot.send_message(chat_id=user.user_id, text=horoscope)

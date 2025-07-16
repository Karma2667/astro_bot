from aiogram.utils.i18n import gettext as _

from datetime import datetime

from bot_ import bot, i18n
from database.user.models import Subscription
from database.user.service import find_all_users, update_user
from logger import bot_logger


async def check_subscription():
    bot_logger.info("Sending horoscope to all users")
    users = await find_all_users()
    for user in users:
        if user.subscription is Subscription.MONTHLY:
            if user.subscription_expiration_date < datetime.now():
                with i18n.context():
                    user.subscription = Subscription.FREELY
                    user.subscription_expiration_date = None
                    await update_user(user_id=user.user_id, updated_user=user)
                    await bot.send_message(
                        chat_id=user.user_id, text=_("subscription_expired_msg")
                    )

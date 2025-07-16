from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from datetime import datetime, timedelta

from logger import bot_logger
from keyboards.reply.common import get_menu_reply
from keyboards.inline.subscription import get_subscription_inline
from keyboards.inline.callback import SubscriptionCallback
from database.user.models import Subscription
from database.user.service import find_user_by_id, update_user


subscription_router = Router(name="subscription")


@subscription_router.message(Command("sub"))
async def handle_subscription_cmd(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} using command /sub")
    user_id = message.chat.id
    user = await find_user_by_id(user_id=user_id)
    if not user.subscription:
        user.subscription = Subscription.FREELY
        await update_user(user_id=user_id, updated_user=user)

    if user.subscription == Subscription.FOREVER:
        await message.answer(
            text=_("subscribed_forever_msg"), reply_markup=await get_menu_reply()
        )
    elif user.subscription == Subscription.MONTHLY:
        await message.answer(
            text=_("subscription_expiration_msg").format(
                user.subscription_expiration_date.strftime("%d.%m.%Y")
            ),
            reply_markup=await get_subscription_inline(),
        )
    else:
        await message.answer(
            text=_("no_subscription_msg"), reply_markup=await get_subscription_inline()
        )


@subscription_router.callback_query(F.data.startswith(SubscriptionCallback.MONTHLY))
async def handle_monthly_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} using callback {callback.data}")
    user_id = callback.message.chat.id
    user = await find_user_by_id(user_id=user_id)
    if user.subscription is Subscription.MONTHLY:
        await callback.message.answer(text=_('subscirbed_montly_msg'), reply_markup=await get_menu_reply())
    else:
        await callback.message.answer_invoice(
            title=_("sub_month_msg"),
            description=_("sub_description_msg"),
            payload="month_sub",
            currency="XTR",
            prices=[LabeledPrice(label=_("sub_month_msg"), amount=250)],
        )
        await state.set_data({"sub_type": Subscription.MONTHLY.value})
    await callback.answer()


@subscription_router.callback_query(F.data.startswith(SubscriptionCallback.FOREVER))
async def handle_forever_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f"User {callback.from_user.id} using callback {callback.data}")
    await callback.message.answer_invoice(
        title=_("sub_forever_msg"),
        description=_("sub_description_msg"),
        payload="forever_sub",
        currency="XTR",
        prices=[LabeledPrice(label=_("sub_forever_msg"), amount=1000)],
    )
    await state.set_data({"sub_type": Subscription.FOREVER.value})
    await callback.answer()


@subscription_router.pre_checkout_query(lambda query: True)
async def pre_checkout_query(pre_checkout_q: PreCheckoutQuery) -> None:
    await pre_checkout_q.answer(ok=True)


@subscription_router.message(F.successful_payment)
async def handle_successful_payment(message: Message, state: FSMContext):
    bot_logger.info(f"User {message.from_user.id} successful payment")
    data = await state.get_data()
    user_id = message.from_user.id
    user = await find_user_by_id(user_id=user_id)
    subscription_type = data["sub_type"]
    user.subscription = Subscription(subscription_type)
    if subscription_type == Subscription.MONTHLY.value:
        user.subscription_expiration_date = datetime.now() + timedelta(days=30)
    elif subscription_type == Subscription.FOREVER.value:
        user.subscription_expiration_date = None
    await update_user(user_id=user_id, updated_user=user)
    await state.clear()
    await message.answer(text=_("sub_success_msg"), reply_markup=await get_menu_reply())

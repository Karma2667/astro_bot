
from aiogram.utils.i18n import gettext as _ # type: ignore
from aiogram.utils.keyboard import InlineKeyboardBuilder # Рекомендуется использовать Builder

from keyboards.inline.callback import HoroscopeCallback

async def get_horo_inline(user_subscription: "Subscription" = None): # <-- Принимает тип подписки
    builder = InlineKeyboardBuilder()
    
    builder.button(text=_("today_btn"), callback_data=HoroscopeCallback.TODAY)
    builder.button(text=_("mail_btn"), callback_data=HoroscopeCallback.MAIL)
    
    if user_subscription is not None:
        if user_subscription != type('Subscription', (), {'FREELY': 'freely'}).FREELY: # Имитация Enum для примера
            builder.button(text=_("month_btn"), callback_data=HoroscopeCallback.MONTH)
            builder.button(text=_("date_btn"), callback_data=HoroscopeCallback.DATE)
    builder.button(text=_("zodiac_compatibility_btn"), callback_data=HoroscopeCallback.ZODIAC_COMPATIBILITY_START)
    
    conditional_buttons_count = 0
    if user_subscription is not None and user_subscription != type('Subscription', (), {'FREELY': 'freely'}).FREELY:
        conditional_buttons_count += 2 # month_btn, date_btn
    
    final_buttons_count = 1 # zodiac_compatibility_btn
    
    if conditional_buttons_count > 0:
        builder.adjust(2, 2, 1) # Максимум 2 кнопки в ряду
    else:
        builder.adjust(2, 1, 1) # today, mail | zodiac_compat | (пусто, так как date/month нет)
        
    if user_subscription is not None and user_subscription != type('Subscription', (), {'FREELY': 'freely'}).FREELY:
         builder.adjust(2, 2, 1) # 2 ряда по 2 кнопки, затем 1 кнопка
    else:
         builder.adjust(2, 1, 1) # 1 ряд из 2 кнопок, затем 1 кнопка, затем 1 кнопка

    return builder.as_markup()

async def get_subscribe_inline():
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_("mail_subscribe_btn"),
        callback_data=HoroscopeCallback.SUBSCRIBE,
    )
    builder.adjust(1) # Одна кнопка в ряду
    return builder.as_markup()

async def get_unsubscribe_inline():
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_("mail_unsubscribe_btn"),
        callback_data=HoroscopeCallback.UNSUBSCRIBE,
    )
    builder.adjust(1) # Одна кнопка в ряду
    return builder.as_markup()

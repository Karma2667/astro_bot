from enum import Enum

class TaroCallback(Enum):
    STUDY = "taro_study"
    MOOD = "taro_mood"
    LOVE = "taro_love"
    COMPATIBILITY = "taro_compatibility"
    INCOME = "taro_income"
    SUCCESS = "taro_success"

    DURATION_TODAY = "taro_duration_today" 
    DURATION_TOMORROW = "taro_duration_tomorrow"
    DURATION_PICK_DATE = "taro_duration_pick_date"

    FULL_SPREAD = "taro_full_spread"


class BasicCallback:
    LANGUAGE = "language"


class ProfileCallback:
    CHANGE_PROFILE = "change_profile"
    CHANGE_DATA = "change_data"
    DELETE_PROFILE = "delete_profile"
    CHANGE_STATUS = "change_status"
    PROFILE_OPTION = "profile_chosen"
    ADD_PROFILE = "add_profile"
    CHANGE_TITLE = "change_title"
    CHANGE_BIRTH_DATE = "change_birth_date"
    CHANGE_BIRTH_TIME = "change_birth_time"
    CHANGE_BIRTH_LOCATION = "change_birth_location"
    CHANGE_LOCATION = "change_location"


class HoroscopeCallback:
    TODAY = "horo_today"
    MONTH = "horo_month"
    DATE = "horo_date"
    MAIL = "horo_mail"
    SUBSCRIBE = "horo_subscribe"
    UNSUBSCRIBE = "horo_unsubscribe"
    ZODIAC_COMPATIBILITY_START = "horo_zcompat_start"


class EventsCallback:
    STUDY = "event_study"
    MOOD = "event_mood"
    LOVE = "event_love"
    COMPATIBILITY = "event_compatibility"
    INCOME = "event_income"
    SUCCESS = "event_success"
    DURATION_TODAY = "event_duration_today" 
    DURATION_TOMORROW = "event_duration_tomorrow"
    DURATION_PICK_DATE = "event_duration_pick_date"

class NumerologyCallback:
    START_ANGEL = "num_angel_start"
    START_BIRTHDATE_ANGEL = "num_birthdate_angel_start"


class SubscriptionCallback:
    FOREVER = "sub_forever"
    MONTHLY = "sub_monthly"


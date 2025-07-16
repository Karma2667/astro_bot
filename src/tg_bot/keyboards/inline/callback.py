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


class EventsCallback:
    STUDY = "event_study"
    MOOD = "event_mood"
    LOVE = "event_love"
    INCOME = "event_income"
    SUCCESS = "event_success"
    DURATION_45 = "event_duration_45"
    DURATION_90 = "event_duration_90"
    DURATION_180 = "event_duration_180"
    DURATION_365 = "event_duration_365"


class SubscriptionCallback:
    FOREVER = "sub_forever"
    MONTHLY = "sub_monthly"

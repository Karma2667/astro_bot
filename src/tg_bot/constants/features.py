FEATURE_MOOD_DIVINATION = "mood_divination"
FEATURE_ANGEL_NUMBERS = "angel_numbers"

FEATURE_ZODIAC_COMPATIBILITY = "zodiac_compatibility"
FEATURE_DAILY_HOROSCOPE = "daily_horoscope" 

FEATURE_EVENT_DIVINATION = "event_divination"
FEATURE_COMPATIBILITY = "compatibility_by_name"

FEATURE_ANGEL_NUMBERS = "angel_numbers"
FEATURE_NUMEROLOGY_MATRIX = "numerology_matrix"

FEATURE_TARO = "taro_divination"

USAGE_LIMITS = {
    FEATURE_DAILY_HOROSCOPE: {  # Общий гороскоп на сегодня
        "freely": 1,  # 1 раз в день
    },
    FEATURE_MOOD_DIVINATION: {  # Гадание на настроение
        "freely": 1,  # 1 раз в день
        # ...
    },
    FEATURE_ZODIAC_COMPATIBILITY: { # Простая совместимость по знакам зодиака
        "freely": 1,  # 1 раз в день
        # ...
    },
    FEATURE_EVENT_DIVINATION: {
        "freely": 1,  # 1 раз в день для бесплатной подписки
        # ... другие подписки позже
    },
    FEATURE_COMPATIBILITY: {
        "freely": 0,  # 0 раз в день для бесплатной подписки (недоступно)
        # ... другие подписки позже
    },
    FEATURE_ANGEL_NUMBERS: {
        "freely": 1,  # <-- ВАЖНО: Убедиться, что это 1
        # ... другие подписки
    },
    FEATURE_NUMEROLOGY_MATRIX: { # Матрица Судьбы
        "freely": 0,  # 0 раз в день (недоступно для бесплатной подписки)
        # ... другие подписки позже
    },
        FEATURE_TARO: { # Гадание Таро (одна карта и полный расклад)
        "freely": 0,  # 0 раз в день (недоступно для бесплатной подписки)
        # ... другие подписки позже
    },
   
}

def get_limit_for_feature(subscription_name: str, feature_type: str) -> int:
    """Возвращает лимит использования функции для данного типа подписки (строка)."""
    return USAGE_LIMITS.get(feature_type, {}).get(subscription_name, 0)

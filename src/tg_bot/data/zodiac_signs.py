# data/zodiac_signs.py
from enum import Enum

class ZodiacSigns(Enum):
    ARIES = "Aries"       # Овен
    TAURUS = "Taurus"     # Телец
    GEMINI = "Gemini"     # Близнецы
    CANCER = "Cancer"     # Рак
    LEO = "Leo"           # Лев
    VIRGO = "Virgo"       # Дева
    LIBRA = "Libra"       # Весы
    SCORPIO = "Scorpio"   # Скорпион
    SAGITTARIUS = "Sagittarius" # Стрелец
    CAPRICORN = "Capricorn"     # Козерог
    AQUARIUS = "Aquarius"       # Водолей
    PISCES = "Pisces"           # Рыбы

# Словарь для проверки и нормализации ввода.
VALID_ZODIAC_SIGNS_LOWER = {
    "овен": ZodiacSigns.ARIES.value,
    "телец": ZodiacSigns.TAURUS.value,
    "близнецы": ZodiacSigns.GEMINI.value,
    "рак": ZodiacSigns.CANCER.value,
    "лев": ZodiacSigns.LEO.value,
    "дева": ZodiacSigns.VIRGO.value,
    "весы": ZodiacSigns.LIBRA.value,
    "скорпион": ZodiacSigns.SCORPIO.value,
    "стрелец": ZodiacSigns.SAGITTARIUS.value,
    "козерог": ZodiacSigns.CAPRICORN.value,
    "водолей": ZodiacSigns.AQUARIUS.value,
    "рыбы": ZodiacSigns.PISCES.value,
    # Алиасы
    "баран": ZodiacSigns.ARIES.value,
    "бык": ZodiacSigns.TAURUS.value,
    "двойняшки": ZodiacSigns.GEMINI.value,
    "ракушка": ZodiacSigns.CANCER.value,
    # ... можно добавить больше алиасов ...
}
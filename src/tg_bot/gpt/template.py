# gpt/template.py
import logging
from enum import Enum
from pathlib import Path

from config import settings, TG_BOT_FOLDER # Импортируем TG_BOT_FOLDER из config

logger = logging.getLogger(__name__)

class TemplateType(Enum):
    EVENT = "event_template.txt"
    HOROSCOPE = "horoscope_template.txt"
    TARO = "taro" # Значение - это папка
    COMPATIBILITY = "compatibility_template.txt"
    ZODIAC_COMPATIBILITY = "zodiac_compatibility.txt" # <-- Исправлено: добавлено .txt

async def load_template(locale: str, template_type: TemplateType, taro_theme: str = None):
    """
    Асинхронно загружает шаблон из файла.

    Args:
        locale (str): Код локали (например, 'ru', 'en').
        template_type (TemplateType): Тип шаблона.
        taro_theme (str, optional): Тема для шаблонов Таро (например, 'love', 'full_study').

    Returns:
        str: Содержимое файла шаблона.

    Raises:
        ValueError: Если переданы некорректные аргументы.
        FileNotFoundError: Если файл шаблона не найден.
        Exception: Если произошла другая ошибка при загрузке.
    """
    try:
        template_path = None
        
        # Обработка типа шаблона
        match template_type:
            case TemplateType.EVENT:
                template_path = (
                    Path(settings.gpt.GPT_TEMPLATES_PATH)
                    / locale
                    / TemplateType.EVENT.value
                )
            case TemplateType.HOROSCOPE:
                template_path = (
                    Path(settings.gpt.GPT_TEMPLATES_PATH)
                    / locale
                    / TemplateType.HOROSCOPE.value
                )
            case TemplateType.COMPATIBILITY:
                template_path = (
                    Path(settings.gpt.GPT_TEMPLATES_PATH)
                    / locale
                    / TemplateType.COMPATIBILITY.value
                )
            case TemplateType.ZODIAC_COMPATIBILITY:
                # Используем путь из config.py, как в handlers/horoscope.py
                template_path = (
                    TG_BOT_FOLDER
                    / "gpt"
                    / "templates"
                    / locale
                    / TemplateType.ZODIAC_COMPATIBILITY.value # "zodiac_compatibility.txt"
                )
            case TemplateType.TARO:
                if not taro_theme:
                    raise ValueError("taro_theme must be provided for TARO template type")
                # Для Таро путь строится как: .../templates/<locale>/taro/<taro_theme>.txt
                template_path = (
                    Path(settings.gpt.GPT_TEMPLATES_PATH)
                    / locale
                    / TemplateType.TARO.value  # "taro" (папка)
                    / f"{taro_theme}.txt"      # <taro_theme>.txt
                )
            case _:
                raise ValueError(f"Unknown template type: {template_type}")

        # Проверяем существование файла
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        # Асинхронное чтение файла (используя aiofiles, как в предыдущих примерах)
        # Если aiofiles не установлен или не используется, можно использовать стандартное open.
        # Для совместимости с handlers/horoscope.py, оставим синхронное чтение,
        # но в будущем можно переписать на async.
        # import aiofiles
        # async with aiofiles.open(template_path, "r", encoding="utf-8") as f:
        #     template_content = await f.read()
        
        # Синхронное чтение
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        logger.debug(f"Successfully loaded template from {template_path}")
        return template_content

    except Exception as e:
        logger.error(f"Error loading template for type '{template_type}', locale '{locale}', taro_theme '{taro_theme}': {e}")
        raise # Повторно возбуждаем исключение, чтобы его мог обработать вызывающий код


async def inject_names_into_template(name1: str, name2: str, template: str) -> str:
    """Подставляет два имени в шаблон."""
    try:
        return template.format(name1=name1, name2=name2)
    except KeyError as e:
        logger.error(f"Missing key in template for inject_names_into_template: {e}")
        raise ValueError(f"Template is missing a required key: {e}") from e
    except Exception as e:
        logger.error(f"Error formatting template in inject_names_into_template: {e}")
        raise

async def inject_profile_into_template(extra: str, template: str, profile: "Profile") -> str: # Используем forward reference для Profile
    """Подставляет данные профиля и дополнительную информацию в шаблон."""
    try:
        return template.format(
            extra_info=extra,
            birth_date=profile.birth_date,
            birth_time=profile.birth_time,
            birth_location=profile.birth_location_name or "Не указано",
        )
    except KeyError as e:
        logger.error(f"Missing key in template for inject_profile_into_template: {e}")
        raise ValueError(f"Template is missing a required key: {e}") from e
    except Exception as e:
        logger.error(f"Error formatting template in inject_profile_into_template: {e}")
        raise

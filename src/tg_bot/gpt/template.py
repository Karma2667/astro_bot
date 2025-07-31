# gpt/template.py
import logging
from enum import Enum
from pathlib import Path

from config import settings
from database.profile.models import Profile

logger = logging.getLogger(__name__)

class TemplateType(Enum):
    EVENT = "event_template.txt"
    HOROSCOPE = "horoscope_template.txt"
    TARO = "taro"
    COMPATIBILITY = "compatibility_template.txt"

async def load_template(locale: str, template_type: TemplateType, taro_theme: str = None):
    try:
        if template_type == TemplateType.TARO:
            if not taro_theme:
                raise ValueError("taro_theme must be provided for TARO template type")
            template_path = (
                Path(settings.gpt.GPT_TEMPLATES_PATH)
                / locale
                / TemplateType.TARO.value 
                / f"{taro_theme}.txt"     
            )
        else:
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
                case _:
                    raise ValueError(f"Unknown template type: {template_type}")

        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        return template

    except Exception as e:
        logger.error(f"Error loading template: {e}")
        raise

async def inject_names_into_template(name1: str, name2: str, template: str) -> str:
    """Подставляет два имени в шаблон."""
    return template.format(name1=name1, name2=name2)

async def inject_profile_into_template(extra: str, template: str, profile: Profile) -> str:
    """Подставляет данные профиля и дополнительную информацию в шаблон."""
    return template.format(
        extra_info=extra,
        birth_date=profile.birth_date,
        birth_time=profile.birth_time,
        birth_location=profile.birth_location_name or "Не указано",
    )

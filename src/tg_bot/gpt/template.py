# gpt/template.py
from enum import Enum
from pathlib import Path

from config import settings
from database.profile.models import Profile


class TemplateType(Enum):
    EVENT = "event_template.txt"
    HOROSCOPE = "horoscope_template.txt"
    COMPATIBILITY = "compatibility_template.txt" # <-- Это есть


async def load_template(locale: str, template_type: TemplateType):
    try:
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
            # === ДОБАВИТЬ ОБРАБОТКУ НОВОГО ТИПА ===
            case TemplateType.COMPATIBILITY:
                template_path = (
                    Path(settings.gpt.GPT_TEMPLATES_PATH)
                    / locale
                    / TemplateType.COMPATIBILITY.value
                )
            # =====================================
            case _: # Этот случай теперь будет только если в Enum добавили значение, но не добавили match
                raise ValueError(f"Unknown template type: {template_type}")

    except FileNotFoundError:
        raise FileNotFoundError(f"Template file not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    return template

async def inject_names_into_template(name1: str, name2: str, template: str) -> str:
    """Подставляет два имени в шаблон."""
    return template.format(name1=name1, name2=name2)



async def inject_profile_into_template(extra: str, template: str, profile: Profile) -> str:
    # Используем метод .format() с именованными аргументами
    return template.format(
        extra_info=extra,
        birth_date=profile.birth_date,
        birth_time=profile.birth_time,
        birth_location=profile.birth_location_name or "Не указано", # Защита от None
    )

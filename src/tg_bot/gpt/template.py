from enum import Enum
from pathlib import Path

from config import settings
from database.profile.models import Profile


class TemplateType(Enum):
    EVENT = "event_template.txt"
    HOROSCOPE = "horoscope_template.txt"


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
            case _:
                raise ValueError(f"Unknown template type: {template_type}")

    except FileNotFoundError:
        raise FileNotFoundError(f"Template file not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    return template


async def inject_profile_into_template(
    extra: str, template: str, profile: Profile
) -> str:
    return template.format(
        extra,
        profile.birth_date,
        profile.birth_time,
        profile.birth_location_name,
    )

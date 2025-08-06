# gpt/template.py
import logging
from enum import Enum
from pathlib import Path

from config import settings, TG_BOT_FOLDER 

logger = logging.getLogger(__name__)

class TemplateType(Enum):
    EVENT = "event_template.txt"

    HOROSCOPE = "horoscope_template.txt"
    FREE_HOROSCOPE = "free_horoscope.txt"
    
    TARO = "taro"

    COMPATIBILITY = "compatibility_template.txt"
    ZODIAC_COMPATIBILITY = "zodiac_compatibility.txt" 
    FREE_ZODIAC_COMPATIBILITY = "free_zodiac_compatibility.txt"

    ANGEL_NUMBERS = "angel_numbers.txt"
    NUMEROLOGY_MATRIX = "numerology_matrix.txt"

async def load_template(locale: str, template_type: TemplateType, taro_theme: str = None):
    try:
        template_path = None

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
            case TemplateType.FREE_HOROSCOPE:
                template_path = (
                    Path(settings.gpt.GPT_TEMPLATES_PATH)
                    / locale
                    / TemplateType.FREE_HOROSCOPE.value
                )
            case TemplateType.FREE_ZODIAC_COMPATIBILITY:
                template_path = (
                    TG_BOT_FOLDER 
                    / "gpt"
                    / "templates"
                    / locale
                    / TemplateType.FREE_ZODIAC_COMPATIBILITY.value
                )
            case TemplateType.COMPATIBILITY:
                template_path = (
                    Path(settings.gpt.GPT_TEMPLATES_PATH)
                    / locale
                    / TemplateType.COMPATIBILITY.value
                )
            case TemplateType.ZODIAC_COMPATIBILITY:
                template_path = (
                    TG_BOT_FOLDER
                    / "gpt"
                    / "templates"
                    / locale
                    / TemplateType.ZODIAC_COMPATIBILITY.value
                )
            case TemplateType.ANGEL_NUMBERS:
                template_path = (
                    TG_BOT_FOLDER
                    / "gpt"
                    / "templates"
                    / locale
                    / TemplateType.ANGEL_NUMBERS.value 
                )
            case TemplateType.TARO:
                if not taro_theme:
                    raise ValueError("taro_theme must be provided for TARO template type")
                template_path = (
                    Path(settings.gpt.GPT_TEMPLATES_PATH)
                    / locale
                    / TemplateType.TARO.value  
                    / f"{taro_theme}.txt"      
                )
            case TemplateType.NUMEROLOGY_MATRIX:
                template_path = (
                    TG_BOT_FOLDER 
                    / "gpt"
                    / "templates"
                    / locale
                    / TemplateType.NUMEROLOGY_MATRIX.value    
                )        
            case _:
                raise ValueError(f"Unknown template type: {template_type}")

        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        logger.debug(f"Successfully loaded template from {template_path}")
        return template_content

    except Exception as e:
        logger.error(f"Error loading template for type '{template_type}', locale '{locale}', taro_theme '{taro_theme}': {e}")
        raise 

async def inject_names_into_template(name1: str, name2: str, template: str) -> str:
    try:
        return template.format(name1=name1, name2=name2)
    except KeyError as e:
        logger.error(f"Missing key in template for inject_names_into_template: {e}")
        raise ValueError(f"Template is missing a required key: {e}") from e
    except Exception as e:
        logger.error(f"Error formatting template in inject_names_into_template: {e}")
        raise

async def inject_profile_into_template(extra: str, template: str, profile: "Profile") -> str: 
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

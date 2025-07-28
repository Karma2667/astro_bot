
from typing import Optional
import google.generativeai as genai
from google.generativeai.types import generation_types
from config import settings
from logger import bot_logger
from enum import Enum

# Инициализация клиента
try:
    genai.configure(api_key=settings.gpt.GEMINI_API_KEY)
    bot_logger.info("Gemini client configured successfully.")
except Exception as e:
    bot_logger.critical(f"Failed to configure Gemini client: {e}", exc_info=True)


class TemplateType(Enum):
    EVENT = "event_template.txt"
    HOROSCOPE = "horoscope_template.txt"
    # === НОВЫЙ ТИП ===
    COMPATIBILITY = "compatibility_template.txt"

async def send_gpt_request(prompt: str) -> Optional[str]:
    bot_logger.info("--- [START] Entering send_gpt_request ---")
    try:
        if not settings.gpt.GEMINI_API_KEY:
            bot_logger.error("CRITICAL: GEMINI_API_KEY is missing or empty!")
            raise ValueError("API key for Gemini is missing in settings")

        bot_logger.info(f"Model selected: {settings.gpt.GPT_MODEL}")
        
        # ЛОГИРУЕМ ТОЧНЫЙ ПРОМПТ, который будет отправлен
        bot_logger.debug(f"--- PROMPT TO BE SENT ---\n{prompt}\n--- END OF PROMPT ---")

        model = genai.GenerativeModel(model_name=settings.gpt.GPT_MODEL)
        
        generation_config = {
            "temperature": 0.9,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 8192, # Увеличим лимит на всякий случай
        }
        
        bot_logger.info("Attempting to call model.generate_content_async...")
        
        # САМЫЙ ВАЖНЫЙ МОМЕНТ
        response = await model.generate_content_async(
            contents=prompt,
            generation_config=generation_config,
        )
        
        bot_logger.info("Call to model.generate_content_async SUCCEEDED. Processing response...")
        bot_logger.debug(f"Raw API Response object: {response}")

        # ПРОВЕРКА НА БЛОКИРОВКУ ФИЛЬТРАМИ БЕЗОПАСНОСТИ (самая частая причина пустого ответа)
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            block_reason = response.prompt_feedback.block_reason.name
            bot_logger.error(f"Request was BLOCKED by safety filters. Reason: {block_reason}")
            # Вы можете захотеть проверить `response.prompt_feedback.safety_ratings`, чтобы увидеть, какой именно фильтр сработал
            bot_logger.error(f"Safety ratings: {response.prompt_feedback.safety_ratings}")
            return None

        # Проверяем, есть ли вообще текст в ответе
        if response and hasattr(response, 'text') and response.text:
             bot_logger.info("Response contains text. Returning it.")
             return response.text
        else:
             # Если текст пустой, но блокировки не было
             bot_logger.warning("Response received, but it's empty. This might be due to a content filter or an issue with the prompt.")
             bot_logger.warning(f"Response parts: {getattr(response, 'parts', 'N/A')}")
             return None # Возвращаем None, чтобы обработчик показал ошибку

    except generation_types.StopCandidateException as e:
        bot_logger.error(f"!!! EXCEPTION in send_gpt_request (StopCandidateException): {e}", exc_info=True)
        return None
    except Exception as e:
        # Логируем ЛЮБОЕ другое исключение с полной трассировкой
        bot_logger.error(f"!!! EXCEPTION in send_gpt_request: {type(e).__name__}: {e}", exc_info=True)
        return None
    finally:
        # Этот блок выполнится всегда, даже если функция выйдет через return или словит ошибку
        bot_logger.info("--- [END] Exiting send_gpt_request ---")

async def inject_names_into_template(name1: str, name2: str, template: str) -> str:
    """Подставляет два имени в шаблон."""
    # Используем метод .format() с именованными аргументами
    return template.format(name1=name1, name2=name2)
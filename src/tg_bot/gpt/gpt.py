import google.generativeai as genai
import asyncio
from config import settings
from logger import bot_logger

# Инициализация клиента
genai.configure(api_key=settings.gpt.GEMINI_API_KEY)

async def send_gpt_request(prompt: str) -> str:
    try:
        if not settings.gpt.GEMINI_API_KEY:
            raise ValueError("API key is missing in settings")
        bot_logger.info(f"Attempting request with model: {settings.gpt.GPT_MODEL}")
        
        # Синхронный вызов с использованием loop
        loop = asyncio.get_event_loop()
        generation_config = {
            "temperature": 0.9,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 200,
        }
        response = await loop.run_in_executor(None, lambda: genai.generate_content(
            model=settings.gpt.GPT_MODEL,
            contents=prompt,
            generation_config=generation_config,
        ))
        return response.text if response and hasattr(response, 'text') else "No response"
    except Exception as e:
        bot_logger.error(f"GPT request error: {str(e)}")
        return "Error generating prediction"

# Закомментированное использование прокси
def get_balance():
    # url = "https://api.proxyapi.ru/proxyapi/balance"
    # headers = {"Authorization": f"Bearer {settings.gpt.OPENAI_API_KEY}"}
    # response = requests.get(url, headers=headers)
    # return round(float(response.json()["balance"]), 2)
    bot_logger.warning("Proxy balance check is disabled. Use direct API only.")
    return 0.0
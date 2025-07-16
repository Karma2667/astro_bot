from openai import AsyncOpenAI
import requests

from config import settings


client = AsyncOpenAI(base_url=settings.gpt.BASE_URL)


async def send_gpt_request(prompt: str) -> str:
    response = await client.chat.completions.create(
        model=settings.gpt.GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def get_balance():
    url = "https://api.proxyapi.ru/proxyapi/balance"
    headers = {"Authorization": f"Bearer {settings.gpt.OPENAI_API_KEY}"}
    response = requests.get(url, headers=headers)
    return round(float(response.json()["balance"]), 2)

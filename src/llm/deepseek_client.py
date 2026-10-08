# -*- coding: utf-8 -*-
"""
Клиент DeepSeek API (через openai SDK).
"""
from openai import OpenAI
from src.config import DEEPSEEK_API_KEY, DEEPSEEK_URL, DEEPSEEK_MODEL


def get_client() -> OpenAI:
    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY не задан в .env")
    return OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com/v1",
    )


def chat(system: str, user: str,
         temperature: float = 0.0,
         max_tokens: int = 2000) -> dict:
    """Возвращает {text, tokens_in, tokens_out, model}."""
    client = get_client()
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return {
        "text": response.choices[0].message.content,
        "tokens_in": response.usage.prompt_tokens,
        "tokens_out": response.usage.completion_tokens,
        "model": DEEPSEEK_MODEL,
    }

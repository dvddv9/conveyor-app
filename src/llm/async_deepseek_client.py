# -*- coding: utf-8 -*-
"""Асинхронный клиент DeepSeek API (через openai SDK)."""
from openai import AsyncOpenAI
from src.config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL


def get_async_client() -> AsyncOpenAI:
    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY не задан в .env")
    return AsyncOpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com/v1",
    )


async def chat(system: str, user: str,
               temperature: float = 0.0,
               max_tokens: int = 2000) -> dict:
    """Асинхронный вызов DeepSeek. Возвращает {text, tokens_in, tokens_out, model}."""
    client = get_async_client()
    response = await client.chat.completions.create(
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

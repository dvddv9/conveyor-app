# -*- coding: utf-8 -*-
"""Асинхронный клиент Ollama (локальный LLM)."""
import ollama
from src.config import OLLAMA_MODEL


async def chat(system: str, user: str,
               temperature: float = 0.0) -> dict:
    """Асинхронный вызов Ollama. Возвращает {text, tokens_in, tokens_out, model}."""
    client = ollama.AsyncClient()
    response = await client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        options={"temperature": temperature},
    )
    return {
        "text": response["message"]["content"],
        "tokens_in": 0,
        "tokens_out": 0,
        "model": OLLAMA_MODEL,
    }

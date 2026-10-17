# -*- coding: utf-8 -*-
"""
Клиент Ollama (локальный LLM).
"""
import ollama
from src.config import OLLAMA_MODEL


def chat(system: str, user: str,
         temperature: float = 0.0) -> dict:
    """Возвращает {text, tokens_in, tokens_out, model}."""
    response = ollama.chat(
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

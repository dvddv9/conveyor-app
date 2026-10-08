# -*- coding: utf-8 -*-
"""
Единый клиент LLM с fallback:
  cloud → DeepSeek API
  local → Ollama
  auto  → облако, при ошибке → локально
"""
from src.storage.mode import get_mode
from src.llm import deepseek_client, ollama_client


def chat(system: str, user: str,
         temperature: float = 0.0,
         max_tokens: int = 2000) -> dict:
    """Возвращает {text, tokens_in, tokens_out, model, mode}."""
    mode = get_mode()

    if mode == "local":
        result = ollama_client.chat(system, user, temperature)
        result["mode"] = "local"
        return result

    if mode == "cloud":
        result = deepseek_client.chat(system, user, temperature, max_tokens)
        result["mode"] = "cloud"
        return result

    # auto
    try:
        result = deepseek_client.chat(system, user, temperature, max_tokens)
        result["mode"] = "cloud"
        return result
    except Exception as e:
        print(f"[Conveyor] DeepSeek недоступен: {e}. Fallback → локально.")
        try:
            result = ollama_client.chat(system, user, temperature)
            result["mode"] = "local"
            return result
        except Exception as e2:
            return {
                "text": f"[Ошибка LLM] cloud: {e}; local: {e2}",
                "tokens_in": 0, "tokens_out": 0,
                "model": "none", "mode": "error",
            }

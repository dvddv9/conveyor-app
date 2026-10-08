# -*- coding: utf-8 -*-
"""
Асинхронный клиент LLM с fallback:
  cloud → DeepSeek API
  local → Ollama
  auto  → облако, при ошибке → локально
"""
from src.storage.mode import get_mode
from src.llm import async_deepseek_client, async_ollama_client


async def async_chat(system: str, user: str,
                     temperature: float = 0.0,
                     max_tokens: int = 2000) -> dict:
    """Асинхронный вызов LLM. Аналог chat() с fallback."""
    mode = get_mode()

    if mode == "local":
        result = await async_ollama_client.chat(system, user, temperature)
        result["mode"] = "local"
        return result

    if mode == "cloud":
        result = await async_deepseek_client.chat(system, user, temperature, max_tokens)
        result["mode"] = "cloud"
        return result

    # auto
    try:
        result = await async_deepseek_client.chat(system, user, temperature, max_tokens)
        result["mode"] = "cloud"
        return result
    except Exception as e:
        print(f"[Conveyor] DeepSeek недоступен: {e}. Fallback → локально.")
        try:
            result = await async_ollama_client.chat(system, user, temperature)
            result["mode"] = "local"
            return result
        except Exception as e2:
            return {
                "text": f"[Ошибка LLM] cloud: {e}; local: {e2}",
                "tokens_in": 0, "tokens_out": 0,
                "model": "none", "mode": "error",
            }

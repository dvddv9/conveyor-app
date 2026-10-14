# -*- coding: utf-8 -*-
"""Unified LLM client with fallback (P2-11)."""
import os

from src.storage.mode import get_mode
from src.llm import deepseek_client, ollama_client
from src.llm import openai_compatible

from src.config import (
    VISHAP_LLM_PROVIDER,
    CUSTOM_BASE_URL, CUSTOM_API_KEY,
    OPENAI_API_KEY,
    DEEPSEEK_API_KEY,
)


def _resolve_provider() -> str:
    """Resolve effective provider (explicit or auto-detected)."""
    explicit = (VISHAP_LLM_PROVIDER or "auto").lower()

    if explicit == "auto":
        mode = get_mode()
        if mode == "local":
            return "ollama"
        if mode == "cloud":
            return "deepseek"

    if explicit in ("deepseek", "openai", "custom", "ollama"):
        return explicit

    if CUSTOM_BASE_URL and CUSTOM_API_KEY:
        return "custom"
    if OPENAI_API_KEY:
        return "openai"
    if DEEPSEEK_API_KEY:
        return "deepseek"
    return "ollama"


def chat(system: str, user: str,
         temperature: float = 0.0,
         max_tokens: int = 2000) -> dict:
    """Returns {text, tokens_in, tokens_out, model, mode}."""
    provider = _resolve_provider()

    if provider == "custom":
        result = openai_compatible.chat(system, user, temperature, max_tokens)
        result["mode"] = "custom"
        return result

    if provider == "openai":
        result = openai_compatible.chat(system, user, temperature, max_tokens)
        result["mode"] = "openai"
        return result

    if provider == "deepseek":
        result = deepseek_client.chat(system, user, temperature, max_tokens)
        result["mode"] = "cloud"
        return result

    if provider == "ollama":
        result = ollama_client.chat(system, user, temperature)
        result["mode"] = "local"
        return result

    try:
        result = deepseek_client.chat(system, user, temperature, max_tokens)
        result["mode"] = "cloud"
        return result
    except Exception as e:
        try:
            result = ollama_client.chat(system, user, temperature)
            result["mode"] = "local"
            return result
        except Exception as e2:
            return {
                "text": f"[LLM error] deepseek: {e}; ollama: {e2}",
                "tokens_in": 0, "tokens_out": 0,
                "model": "none", "mode": "error",
            }


def current_provider() -> str:
    """Return resolved provider name (for diagnostics)."""
    return _resolve_provider()

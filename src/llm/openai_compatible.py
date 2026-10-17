# -*- coding: utf-8 -*-
"""Universal OpenAI-compatible LLM client (P2-11).

Works with any provider exposing the OpenAI /v1/chat/completions API:
- OpenAI (gpt-4o, gpt-4o-mini)
- Anthropic Claude (via OpenAI-compat shim)
- Groq (llama-3.3-70b-versatile, mixtral-8x7b)
- Together, Fireworks, OpenRouter
- LM Studio, vLLM, llama.cpp server (local)
- Ollama (OpenAI-compat mode)
- DeepSeek (already works, but this is generic)
"""
from openai import OpenAI

from src.config import (
    OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL,
    CUSTOM_API_KEY, CUSTOM_MODEL, CUSTOM_BASE_URL,
)


def _resolve_config(
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> tuple[str, str, str]:
    """Resolve (api_key, base_url, model) from params or env.

    Priority: params > CUSTOM_* > OPENAI_*.
    Raises ValueError if any is missing.
    """
    key = api_key or CUSTOM_API_KEY or OPENAI_API_KEY
    url = base_url or CUSTOM_BASE_URL or OPENAI_BASE_URL
    mdl = model or CUSTOM_MODEL or OPENAI_MODEL

    if not key:
        raise ValueError(
            "OpenAI-compatible provider: no API key. "
            "Set CUSTOM_API_KEY or OPENAI_API_KEY."
        )
    if not url:
        raise ValueError(
            "OpenAI-compatible provider: no base URL. "
            "Set CUSTOM_BASE_URL or OPENAI_BASE_URL."
        )
    if not mdl:
        raise ValueError(
            "OpenAI-compatible provider: no model. "
            "Set CUSTOM_MODEL or OPENAI_MODEL."
        )

    return key, url, mdl


def get_client(
    api_key: str | None = None,
    base_url: str | None = None,
) -> OpenAI:
    """Return an OpenAI SDK client bound to the configured endpoint."""
    key, url, _ = _resolve_config(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=key, base_url=url)


def chat(
    system: str,
    user: str,
    temperature: float = 0.0,
    max_tokens: int = 2000,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> dict:
    """Chat with the configured OpenAI-compatible endpoint.

    Returns:
        {
            "text": str,
            "tokens_in": int,
            "tokens_out": int,
            "model": str,
            "mode": "custom",
        }
    """
    key, url, mdl = _resolve_config(api_key=api_key, base_url=base_url, model=model)
    client = OpenAI(api_key=key, base_url=url)

    response = client.chat.completions.create(
        model=mdl,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    text = ""
    if response.choices:
        text = response.choices[0].message.content or ""

    tokens_in = 0
    tokens_out = 0
    if response.usage:
        tokens_in = response.usage.prompt_tokens or 0
        tokens_out = response.usage.completion_tokens or 0

    return {
        "text": text,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "model": mdl,
        "mode": "custom",
    }


def is_configured() -> bool:
    """True if CUSTOM_* or OPENAI_* is set enough to call chat()."""
    try:
        _resolve_config()
        return True
    except ValueError:
        return False


def provider_name() -> str:
    """Return human-readable provider name based on env precedence."""
    if CUSTOM_BASE_URL and CUSTOM_API_KEY:
        return f"custom ({CUSTOM_BASE_URL})"
    if OPENAI_API_KEY:
        return f"openai ({OPENAI_BASE_URL})"
    return "custom (unconfigured)"

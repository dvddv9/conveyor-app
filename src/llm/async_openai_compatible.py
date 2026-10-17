# -*- coding: utf-8 -*-
"""Async universal OpenAI-compatible LLM client (P2-11).

Mirror of src/llm/openai_compatible.py, but async.
Uses AsyncOpenAI for non-blocking calls.
"""
from openai import AsyncOpenAI

from src.llm.openai_compatible import _resolve_config


def get_async_client(
    api_key: str | None = None,
    base_url: str | None = None,
) -> AsyncOpenAI:
    """Return an AsyncOpenAI client bound to the configured endpoint."""
    key, url, _ = _resolve_config(api_key=api_key, base_url=base_url)
    return AsyncOpenAI(api_key=key, base_url=url)


async def achat(
    system: str,
    user: str,
    temperature: float = 0.0,
    max_tokens: int = 2000,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> dict:
    """Async chat with the configured OpenAI-compatible endpoint.

    Returns the same dict shape as sync chat().
    """
    key, url, mdl = _resolve_config(api_key=api_key, base_url=base_url, model=model)
    client = AsyncOpenAI(api_key=key, base_url=url)

    response = await client.chat.completions.create(
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

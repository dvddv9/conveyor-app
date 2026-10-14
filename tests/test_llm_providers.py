# -*- coding: utf-8 -*-
"""Tests for pluggable LLM providers (P2-11).

All tests use mocks — no real API calls.
"""
from unittest.mock import MagicMock, patch
from pathlib import Path

import pytest

from src.llm.openai_compatible import (
    _resolve_config,
    is_configured,
    provider_name,
    chat,
)


# === _resolve_config ===

def test_resolve_config_from_params():
    key, url, mdl = _resolve_config(
        api_key="k", base_url="http://x", model="m"
    )
    assert key == "k"
    assert url == "http://x"
    assert mdl == "m"


def test_resolve_config_missing_api_key(monkeypatch):
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_API_KEY", "")
    monkeypatch.setattr("src.llm.openai_compatible.OPENAI_API_KEY", "")
    with pytest.raises(ValueError, match="no API key"):
        _resolve_config()


def test_resolve_config_missing_base_url(monkeypatch):
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_API_KEY", "")
    monkeypatch.setattr("src.llm.openai_compatible.OPENAI_API_KEY", "")
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_BASE_URL", "")
    monkeypatch.setattr("src.llm.openai_compatible.OPENAI_BASE_URL", "")
    with pytest.raises(ValueError, match="no base URL"):
        _resolve_config(api_key="k", base_url="", model="m")


def test_resolve_config_missing_model(monkeypatch):
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_MODEL", "")
    monkeypatch.setattr("src.llm.openai_compatible.OPENAI_MODEL", "")
    with pytest.raises(ValueError, match="no model"):
        _resolve_config(api_key="k", base_url="http://x", model="")


# === is_configured / provider_name ===

def test_is_configured_false(monkeypatch):
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_API_KEY", "")
    monkeypatch.setattr("src.llm.openai_compatible.OPENAI_API_KEY", "")
    assert is_configured() is False


def test_is_configured_true_with_custom(monkeypatch):
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_API_KEY", "k")
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_BASE_URL", "http://x")
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_MODEL", "m")
    assert is_configured() is True


def test_provider_name_unconfigured(monkeypatch):
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_API_KEY", "")
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_BASE_URL", "")
    monkeypatch.setattr("src.llm.openai_compatible.OPENAI_API_KEY", "")
    assert provider_name() == "custom (unconfigured)"


def test_provider_name_custom(monkeypatch):
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_API_KEY", "k")
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_BASE_URL", "http://groq")
    assert provider_name().startswith("custom (")


def test_provider_name_openai(monkeypatch):
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_API_KEY", "")
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_BASE_URL", "")
    monkeypatch.setattr("src.llm.openai_compatible.OPENAI_API_KEY", "sk-xxx")
    assert provider_name().startswith("openai (")


# === chat (mocked) ===

def _make_mock_response(text="hello", prompt=10, completion=5):
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = text
    mock_resp.usage.prompt_tokens = prompt
    mock_resp.usage.completion_tokens = completion
    return mock_resp


def test_chat_returns_dict_shape(monkeypatch):
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_API_KEY", "k")
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_BASE_URL", "http://x")
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_MODEL", "m")

    with patch("src.llm.openai_compatible.OpenAI") as MockOpenAI:
        instance = MockOpenAI.return_value
        instance.chat.completions.create.return_value = _make_mock_response()

        result = chat("sys", "usr")

    assert set(result.keys()) >= {"text", "tokens_in", "tokens_out", "model", "mode"}
    assert result["text"] == "hello"
    assert result["mode"] == "custom"


def test_chat_tokens_extracted(monkeypatch):
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_API_KEY", "k")
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_BASE_URL", "http://x")
    monkeypatch.setattr("src.llm.openai_compatible.CUSTOM_MODEL", "m")

    with patch("src.llm.openai_compatible.OpenAI") as MockOpenAI:
        instance = MockOpenAI.return_value
        instance.chat.completions.create.return_value = _make_mock_response(
            text="ok", prompt=42, completion=17
        )
        result = chat("s", "u")

    assert result["tokens_in"] == 42
    assert result["tokens_out"] == 17


# === client._resolve_provider ===

def test_resolve_provider_auto_custom_first(monkeypatch):
    from src.llm import client
    monkeypatch.setattr(client, "VISHAP_LLM_PROVIDER", "auto")
    monkeypatch.setattr(client, "CUSTOM_BASE_URL", "http://x")
    monkeypatch.setattr(client, "CUSTOM_API_KEY", "k")
    monkeypatch.setattr(client, "get_mode", lambda: "auto")
    assert client._resolve_provider() == "custom"


def test_resolve_provider_auto_deepseek_third(monkeypatch):
    from src.llm import client
    monkeypatch.setattr(client, "VISHAP_LLM_PROVIDER", "auto")
    monkeypatch.setattr(client, "CUSTOM_BASE_URL", "")
    monkeypatch.setattr(client, "CUSTOM_API_KEY", "")
    monkeypatch.setattr(client, "OPENAI_API_KEY", "")
    monkeypatch.setattr(client, "DEEPSEEK_API_KEY", "sk-xxx")
    monkeypatch.setattr(client, "get_mode", lambda: "auto")
    assert client._resolve_provider() == "deepseek"


def test_resolve_provider_explicit(monkeypatch):
    from src.llm import client
    monkeypatch.setattr(client, "VISHAP_LLM_PROVIDER", "ollama")
    assert client._resolve_provider() == "ollama"


# === .env.example ===

def test_env_example_has_new_vars():
    content = Path(".env.example").read_text(encoding="utf-8")
    assert "VISHAP_LLM_PROVIDER" in content
    assert "CUSTOM_API_KEY" in content
    assert "CUSTOM_BASE_URL" in content
    assert "OPENAI_API_KEY" in content


# === async module ===

def test_async_module_importable():
    from src.llm.async_openai_compatible import achat, get_async_client
    assert callable(achat)
    assert callable(get_async_client)

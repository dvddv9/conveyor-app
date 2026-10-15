# -*- coding: utf-8 -*-
"""Unit tests for src/ui/api_client.py -- centralized HTTP client for UI.

Approach: patch module attributes directly (no reload).
Reason: api_client reads config at import time; reload is unreliable
because src.config caches env values.
"""
from unittest.mock import patch, MagicMock

from src.ui import api_client


# ============================================================
# HEADERS / API_URL -- module attributes
# ============================================================

def test_headers_from_config():
    """api_client.HEADERS derives from CONVEYOR_API_KEY."""
    # In test env, CONVEYOR_API_KEY may or may not be set.
    # Verify the shape: either empty dict or {"X-API-Key": <val>}
    h = api_client.HEADERS
    assert isinstance(h, dict)
    if h:
        assert "X-API-Key" in h


def test_headers_empty_when_no_key():
    with patch.object(api_client, "HEADERS", {}):
        assert api_client.HEADERS == {}


def test_headers_with_key():
    with patch.object(api_client, "HEADERS", {"X-API-Key": "k1"}):
        assert api_client.HEADERS == {"X-API-Key": "k1"}


def test_api_url_is_string():
    assert isinstance(api_client.API_URL, str)
    assert api_client.API_URL.startswith("http")


# ============================================================
# _url helper
# ============================================================

def test_url_joins_with_slash():
    with patch.object(api_client, "API_URL", "http://test:5001"):
        assert api_client._url("/health") == "http://test:5001/health"


def test_url_adds_leading_slash():
    with patch.object(api_client, "API_URL", "http://test:5001"):
        assert api_client._url("health") == "http://test:5001/health"


def test_url_no_double_slash():
    with patch.object(api_client, "API_URL", "http://test:5001"):
        assert "//health" not in api_client._url("/health")


# ============================================================
# get() -- auto headers + timeout
# ============================================================

@patch("src.ui.api_client.requests.get")
def test_get_adds_headers(mock_get):
    with patch.object(api_client, "HEADERS", {"X-API-Key": "k1"}), \
         patch.object(api_client, "API_URL", "http://test:5001"):
        mock_get.return_value = MagicMock()
        api_client.get("/health")
        args, kwargs = mock_get.call_args
        assert kwargs["headers"] == {"X-API-Key": "k1"}


@patch("src.ui.api_client.requests.get")
def test_get_default_timeout(mock_get):
    with patch.object(api_client, "API_URL", "http://test:5001"):
        mock_get.return_value = MagicMock()
        api_client.get("/health")
        args, kwargs = mock_get.call_args
        assert kwargs["timeout"] == 10


@patch("src.ui.api_client.requests.get")
def test_get_custom_timeout(mock_get):
    with patch.object(api_client, "API_URL", "http://test:5001"):
        mock_get.return_value = MagicMock()
        api_client.get("/health", timeout=42)
        args, kwargs = mock_get.call_args
        assert kwargs["timeout"] == 42


@patch("src.ui.api_client.requests.get")
def test_get_custom_headers_override(mock_get):
    with patch.object(api_client, "HEADERS", {"X-API-Key": "k1"}), \
         patch.object(api_client, "API_URL", "http://test:5001"):
        mock_get.return_value = MagicMock()
        api_client.get("/health", headers={"Custom": "yes"})
        args, kwargs = mock_get.call_args
        assert kwargs["headers"] == {"Custom": "yes"}


# ============================================================
# post() -- auto headers + timeout
# ============================================================

@patch("src.ui.api_client.requests.post")
def test_post_adds_headers(mock_post):
    with patch.object(api_client, "HEADERS", {"X-API-Key": "k2"}), \
         patch.object(api_client, "API_URL", "http://test:5001"):
        mock_post.return_value = MagicMock()
        api_client.post("/analyze", json={"x": 1})
        args, kwargs = mock_post.call_args
        assert kwargs["headers"] == {"X-API-Key": "k2"}
        assert kwargs["json"] == {"x": 1}


@patch("src.ui.api_client.requests.post")
def test_post_default_timeout(mock_post):
    with patch.object(api_client, "API_URL", "http://test:5001"):
        mock_post.return_value = MagicMock()
        api_client.post("/analyze")
        args, kwargs = mock_post.call_args
        assert kwargs["timeout"] == 300


@patch("src.ui.api_client.requests.post")
def test_post_custom_timeout(mock_post):
    with patch.object(api_client, "API_URL", "http://test:5001"):
        mock_post.return_value = MagicMock()
        api_client.post("/analyze", timeout=900)
        args, kwargs = mock_post.call_args
        assert kwargs["timeout"] == 900


# ============================================================
# URL construction through get/post
# ============================================================

@patch("src.ui.api_client.requests.get")
def test_get_uses_full_url(mock_get):
    with patch.object(api_client, "API_URL", "http://test:5001"):
        mock_get.return_value = MagicMock()
        api_client.get("/health")
        args, kwargs = mock_get.call_args
        assert args[0] == "http://test:5001/health"


@patch("src.ui.api_client.requests.post")
def test_post_uses_full_url(mock_post):
    with patch.object(api_client, "API_URL", "http://test:5001"):
        mock_post.return_value = MagicMock()
        api_client.post("/analyze")
        args, kwargs = mock_post.call_args
        assert args[0] == "http://test:5001/analyze"

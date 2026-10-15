# -*- coding: utf-8 -*-
"""HTTP client for Vishap FastAPI -- centralizes base URL, headers, timeouts.

Replaces 8 duplicated requests.* calls in streamlit_app.py (v5.10.5).
"""
import requests

from src.config import (
    API_URL,
    CONVEYOR_API_KEY,
    API_TIMEOUT_DEFAULT,
    API_TIMEOUT_LONG,
)

HEADERS = {"X-API-Key": CONVEYOR_API_KEY} if CONVEYOR_API_KEY else {}


def _url(path: str) -> str:
    """Join API_URL and path, ensuring exactly one slash."""
    if not path.startswith("/"):
        path = "/" + path
    return f"{API_URL}{path}"


def get(path: str, **kwargs):
    """GET request with auto headers + default timeout."""
    kwargs.setdefault("headers", HEADERS)
    kwargs.setdefault("timeout", API_TIMEOUT_DEFAULT)
    return requests.get(_url(path), **kwargs)


def post(path: str, **kwargs):
    """POST request with auto headers + long default timeout."""
    kwargs.setdefault("headers", HEADERS)
    kwargs.setdefault("timeout", API_TIMEOUT_LONG)
    return requests.post(_url(path), **kwargs)

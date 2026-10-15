# -*- coding: utf-8 -*-
"""Regression: Streamlit UI uses api_client (centralized X-API-Key).

v5.11.3: UI no longer calls requests.* directly -- everything goes through
src/ui/api_client.py. This file verifies:
  1. api_client exists, defines HEADERS, adds X-API-Key.
  2. streamlit_app.py uses api_client, no direct requests.*.
"""
import ast
import re
from pathlib import Path


UI_PATH = Path("src/ui/streamlit_app.py")
CLIENT_PATH = Path("src/ui/api_client.py")


def _read_ui():
    return UI_PATH.read_text(encoding="utf-8")


def _read_client():
    return CLIENT_PATH.read_text(encoding="utf-8")


# ============================================================
# api_client.py -- centralized headers
# ============================================================

def test_api_client_exists():
    assert CLIENT_PATH.exists(), "src/ui/api_client.py not found"


def test_api_client_defines_headers():
    src = _read_client()
    assert "HEADERS" in src
    assert "X-API-Key" in src


def test_api_client_reads_api_key_from_config():
    src = _read_client()
    assert "CONVEYOR_API_KEY" in src


def test_api_client_syntax_valid():
    ast.parse(_read_client())


def test_api_client_get_post_defined():
    from src.ui import api_client
    assert callable(api_client.get)
    assert callable(api_client.post)
    assert callable(api_client._url)


def test_api_client_headers_shape():
    from src.ui import api_client
    assert isinstance(api_client.HEADERS, dict)
    if api_client.HEADERS:
        assert "X-API-Key" in api_client.HEADERS


# ============================================================
# streamlit_app.py -- uses api_client, no direct requests
# ============================================================

def test_ui_imports_api_client():
    src = _read_ui()
    assert "from src.ui import api_client" in src or "from src.ui.api_client import" in src


def test_ui_has_no_direct_requests():
    src = _read_ui()
    matches = re.findall(r"requests\.(get|post|put|delete)\(", src)
    assert not matches, f"direct requests.* found in UI: {matches}"


def test_ui_uses_api_client_get_or_post():
    src = _read_ui()
    matches = re.findall(r"api_client\.(get|post)\(", src)
    assert len(matches) >= 8, f"expected >=8 api_client calls, found {len(matches)}"


def test_ui_has_no_local_headers_definition():
    src = _read_ui()
    # No `HEADERS = {...}` at module level
    assert not re.search(r"^HEADERS\s*=", src, re.MULTILINE), "HEADERS should be in api_client, not UI"


def test_ui_has_no_local_api_url_definition():
    src = _read_ui()
    # No `API_URL = ...` at module level (moved to config)
    assert not re.search(r"^API_URL\s*=", src, re.MULTILINE), "API_URL should be in config, not UI"


def test_ui_syntax_valid():
    ast.parse(_read_ui())


def test_no_double_comma_in_ui():
    assert ",," not in _read_ui()

# -*- coding: utf-8 -*-
"""Tests for Streamlit UI: async UI, sidebar mode, dataflow rendering, versions.

These are structural checks -- read streamlit_app.py and verify markers.
"""
import ast
from pathlib import Path


UI_PATH = Path("src/ui/streamlit_app.py")


def _read_ui() -> str:
    return UI_PATH.read_text(encoding="utf-8")


# ============================================================
# Version + header
# ============================================================

def test_ui_has_v6_version():
    """UI must contain the version from pyproject.toml (# v6.0.2-fix: read version from pyproject)."""
    import tomllib
    from pathlib import Path as _P
    pyproject = _P(__file__).parent.parent / "pyproject.toml"
    version = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]
    src = _read_ui()
    assert f"V{version}" in src, f"expected V{version} in UI"


def test_ui_no_old_version():
    src = _read_ui()
    assert "V5.8" not in src, "old V5.8 still present"


def test_ui_has_custom_header():
    src = _read_ui()
    assert "vishap-header" in src


def test_ui_has_dragon_emoji():
    src = _read_ui()
    assert "🐉" in src


# ============================================================
# Sidebar LLM mode
# ============================================================

def test_ui_has_sidebar():
    src = _read_ui()
    assert "with st.sidebar" in src


def test_ui_has_sidebar_mode():
    src = _read_ui()
    assert "sidebar_mode" in src


def test_ui_has_llm_mode_header():
    src = _read_ui()
    assert "LLM режим" in src


# ============================================================
# Async UI
# ============================================================

def test_ui_has_async_button():
    src = _read_ui()
    assert "single_async_btn" in src
    assert "⚡ Async" in src


def test_ui_has_async_block_marker():
    src = _read_ui()
    assert "v6.0.1: async UI" in src


def test_ui_async_uses_endpoints():
    src = _read_ui()
    assert "/analyze/async" in src
    assert "/status/" in src
    assert "/report/" in src


def test_ui_has_polling():
    src = _read_ui()
    assert "time.sleep" in src


def test_ui_async_uses_job_id():
    src = _read_ui()
    assert "job_id" in src


def test_ui_has_import_time():
    src = _read_ui()
    # 'import time' must be at top level
    tree = ast.parse(src)
    has_time_import = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "time":
                    has_time_import = True
    assert has_time_import, "import time not found"


# ============================================================
# Dataflow rendering
# ============================================================

def test_ui_has_dataflow_rendering():
    src = _read_ui()
    assert "v6.0.1: dataflow rendering" in src


def test_ui_dataflow_reads_audit():
    src = _read_ui()
    assert 'audit.get("dataflow"' in src


def test_ui_dataflow_shows_path():
    src = _read_ui()
    assert "df_path" in src
    assert "Dataflow" in src


# ============================================================
# Overall structure
# ============================================================

def test_ui_syntax_valid():
    ast.parse(_read_ui())


def test_ui_no_double_comma():
    assert ",," not in _read_ui()


def test_ui_uses_api_client():
    src = _read_ui()
    # all HTTP via api_client, no direct requests
    assert "api_client." in src
    assert "requests." not in src

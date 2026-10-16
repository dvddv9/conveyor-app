# -*- coding: utf-8 -*-
"""Regression: UI badge version must come from pyproject.toml (v6.0.3-chore)."""
from pathlib import Path


UI_PATH = Path("src/ui/streamlit_app.py")


def _read_ui() -> str:
    return UI_PATH.read_text(encoding="utf-8")


def test_ui_badge_no_hardcoded_v600():
    src = _read_ui()
    assert "v6.0.0" not in src, "hardcoded v6.0.0 still in UI"


def test_ui_badge_uses_dynamic_version():
    src = _read_ui()
    assert "__VERSION__" in src, "placeholder __VERSION__ not found"
    assert "_get_version()" in src, "_get_version() not called"

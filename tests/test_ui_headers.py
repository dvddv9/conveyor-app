# -*- coding: utf-8 -*-
"""Regression: Streamlit UI passes X-API-Key to FastAPI."""
import ast
import re
from pathlib import Path


UI_PATH = Path("src/ui/streamlit_app.py")


def _read_ui():
    return UI_PATH.read_text(encoding="utf-8")


def test_ui_defines_api_key_from_env():
    assert 'os.getenv("CONVEYOR_API_KEY"' in _read_ui()


def test_ui_defines_headers_dict():
    src = _read_ui()
    assert "HEADERS" in src
    assert "X-API-Key" in src


def test_all_requests_calls_have_headers():
    src = _read_ui()
    issues = []
    for match in re.finditer(r"requests\.(get|post)\(", src):
        start = match.start()
        depth = 0
        i = match.end() - 1
        n = len(src)
        while i < n:
            c = src[i]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        call_body = src[start:i + 1]
        if 'f"{API_URL}/' in call_body:
            if "headers=HEADERS" not in call_body:
                line_no = src[:start].count("\n") + 1
                issues.append(f"L{line_no}")
    assert not issues, "requests.* missing headers: " + ", ".join(issues)


def test_ui_syntax_valid():
    ast.parse(_read_ui())


def test_no_double_comma_in_ui():
    assert ",," not in _read_ui()


def test_health_check_has_headers():
    match = re.search(r'requests\.get\(f"\{API_URL\}/health"[^)]*\)', _read_ui())
    assert match
    assert "headers=HEADERS" in match.group(0)

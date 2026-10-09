# -*- coding: utf-8 -*-
"""Unit tests for tools — no LLM calls."""
from src.pipeline.orchestrator import (
    detect_pii, detect_compliance, compute_hash, generate_audit_id,
)
from src.pipeline.stages import parse_json_response
from src.tools.fallback_check import REQUIRED, LOSS_THRESHOLD


# === PII ===

def test_detect_pii_email():
    result = detect_pii("contact: user@example.com")
    assert result == {"email": 1}


def test_detect_pii_phone():
    result = detect_pii("tel: +79991234567")
    assert "phone_ru" in result


def test_detect_pii_multiple():
    result = detect_pii("user@example.com and admin@test.org")
    assert result.get("email") == 2


def test_detect_pii_empty():
    result = detect_pii("def foo(): pass")
    assert result == {}


# === Compliance ===

def test_detect_compliance_gdpr():
    result = detect_compliance("we process personal data")
    assert "GDPR" in result


def test_detect_compliance_pii_auto():
    result = detect_compliance("user@example.com", pii={"email": 1})
    assert "GDPR" in result
    assert "152-ФЗ" in result


def test_detect_compliance_no_triggers():
    result = detect_compliance("def foo(): pass")
    assert result == []


# === Hash ===

def test_compute_hash_format():
    h = compute_hash("abc")
    assert h.startswith("sha256:")
    assert len(h) == len("sha256:") + 16


def test_compute_hash_stable():
    assert compute_hash("abc") == compute_hash("abc")


def test_compute_hash_different():
    assert compute_hash("abc") != compute_hash("xyz")


# === Audit ID ===

def test_generate_audit_id_format():
    aid = generate_audit_id()
    assert aid.startswith("audit-")
    parts = aid.split("-")
    assert len(parts) == 5  # audit, YYYY, MM, DD, XXXXXX
    assert len(parts[0]) == 5   # "audit"
    assert len(parts[1]) == 4   # YYYY
    assert len(parts[2]) == 2   # MM
    assert len(parts[3]) == 2   # DD
    assert len(parts[4]) == 6   # XXXXXX


# === JSON parsing ===

def test_parse_json_plain():
    result = parse_json_response('{"level": "D0"}')
    assert result.get("level") == "D0"


def test_parse_json_code_block():
    result = parse_json_response('```json\n{"level": "D0"}\n```')
    assert result.get("level") == "D0"


def test_parse_json_with_markdown():
    result = parse_json_response('Here is result:\n```json\n{"level": "D1"}\n```\nDone.')
    assert result.get("level") == "D1"


def test_parse_json_invalid():
    result = parse_json_response("not json at all")
    assert "_error" in result
    assert result["_error"] == "JSON parse failed"


def test_parse_json_trailing_comma():
    result = parse_json_response('{"level": "D0",}')
    assert result.get("level") == "D0"


# === Fallback check ===

def test_fallback_check_required_d0():
    assert "D0" in REQUIRED
    assert "[CONCLUSION]" in REQUIRED["D0"]


def test_fallback_check_required_d3():
    assert "D3" in REQUIRED
    assert len(REQUIRED["D3"]) > 10


def test_fallback_check_threshold():
    assert LOSS_THRESHOLD == 30.0

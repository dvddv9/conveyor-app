#!/usr/bin/env python3
"""Conveyor V5.7 — audit trail."""
import argparse
import datetime
import hashlib
import json
import re
from pathlib import Path


PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone_ru": re.compile(r"\+7\d{10}|\b8\d{10}\b"),
    "passport_ru": re.compile(r"\b\d{4}\s?\d{6}\b"),
    "snils": re.compile(r"\b\d{3}-?\d{3}-?\d{3}\s?\d{2}\b"),
    "iban": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b"),
}

COMPLIANCE_TRIGGERS = {
    "HIPAA": ["patient", "diagnosis", "medical record", "hipaa", "ehr"],
    "PCI-DSS": ["payment", "card", "cvv", "credit card", "pci"],
    "GDPR": ["personal data", "gdpr", "eu citizen", "right to erasure"],
    "152-ФЗ": ["персональные данные", "152-фз", "оператор данных"],
    "EU AI Act": ["llm", "foundation model", "ai system", "eu ai act"],
}


def compute_hash(material: str) -> str:
    h = hashlib.sha256(material.encode("utf-8", errors="replace"))
    return f"sha256:{h.hexdigest()[:16]}"


def detect_pii(text: str) -> dict:
    found = {}
    for name, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            found[name] = len(matches)
    return found


def detect_compliance(text: str) -> list:
    low = text.lower()
    flags = []
    for flag, triggers in COMPLIANCE_TRIGGERS.items():
        if any(t in low for t in triggers):
            flags.append(flag)
    return flags


def generate_audit_id() -> str:
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    rand = hashlib.md5(
        str(datetime.datetime.utcnow().timestamp()).encode()
    ).hexdigest()[:6]
    return f"audit-{today}-{rand}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", default="audit.json")
    ap.add_argument("--session", default=None)
    ap.add_argument("--model", default=None)
    args = ap.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    material = data.get("material", "")
    stages = data.get("stages", {})

    pii = detect_pii(material)
    compliance = detect_compliance(material)
    critique = "REQUIRES_REVIEW" if (pii or compliance) else "SAFE"

    audit = {
        "audit_id": generate_audit_id(),
        "session_id": args.session or data.get("session_id", "sess-unknown"),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "material_hash": compute_hash(material),
        "material_size": {
            "lines": len(material.splitlines()),
            "chars": len(material),
        },
        "language": stages.get("stage0", {}).get("language", "unknown"),
        "mode": stages.get("stage0", {}).get("level", "unknown"),
        "route": stages.get("stage0", {}).get("route", []),
        "tokens": data.get("tokens", {"input": None, "output": None,
                                       "note": "[ASSUMPTION]"}),
        "model": args.model or data.get("model", "unknown"),
        "critique_verdict": critique,
        "pii_detected": bool(pii),
        "pii_details": pii,
        "compliance_flags": compliance,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z",
    }

    Path(args.output).write_text(
        json.dumps(audit, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(audit, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

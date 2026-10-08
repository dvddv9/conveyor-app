# -*- coding: utf-8 -*-
"""
Conveyor — главный pipeline.
v3: исправлен DeprecationWarning (datetime.utcnow → datetime.now(UTC)).
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, UTC
from pathlib import Path

from src.config import DATA_DIR
from src.pipeline.stages import (
    stage0_orchestrator,
    stage1_scanner,
    stage2_analyst,
    stage3_researcher,
    stage4_synthesizer,
    stage5_transmitter,
)
from src.storage.history import add_entry


# === Audit (встроено из audit_log.py) ===

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
    now = datetime.now(UTC)
    today = now.strftime("%Y-%m-%d")
    rand = hashlib.md5(str(now.timestamp()).encode()).hexdigest()[:6]
    return f"audit-{today}-{rand}"


def run_audit(material: str, session_id: str, model: str = "deepseek-chat") -> dict:
    """Собирает audit-запись."""
    pii = detect_pii(material)
    compliance = detect_compliance(material)
    critique = "REQUIRES_REVIEW" if (pii or compliance) else "SAFE"

    audit = {
        "audit_id": generate_audit_id(),
        "session_id": session_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "material_hash": compute_hash(material),
        "material_size": {
            "lines": len(material.splitlines()),
            "chars": len(material),
        },
        "model": model,
        "critique_verdict": critique,
        "pii_detected": bool(pii),
        "pii_details": pii,
        "compliance_flags": compliance,
    }

    audit_file = DATA_DIR / f"audit_{session_id}.json"
    audit_file.write_text(
        json.dumps(audit, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return audit


# === Pipeline ===

def run_pipeline(material: str, filename: str, verbose: bool = True) -> dict:
    """Запускает полный pipeline Conveyor."""
    session_id = f"sess-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"

    if verbose:
        print(f"=== Conveyor Pipeline ===")
        print(f"Session: {session_id}")
        print(f"File: {filename}")
        print(f"Material: {len(material)} символов")
        print()

    if verbose:
        print("[Stage 0] Orchestrator...")
    stage0 = stage0_orchestrator(material, filename)
    route = stage0.get("route", [])
    level = stage0.get("level", "D3")
    research_first = stage0.get("research_first", False)
    subst_count = stage0.get("subst_count", 0)

    if verbose:
        print(f"  → level: {level}, route: {route}")
        print(f"  → research_first: {research_first}, subst_count: {subst_count}")
        print()

    flags = stage0.get("flags", [])
    if "EMERGENCY_INTERRUPT" in flags:
        if verbose:
            print("[!] EMERGENCY_INTERRUPT — стоп")
        return {
            "session_id": session_id,
            "stage0": stage0,
            "emergency": True,
            "final_markdown": "⛔ INTERRUPTED: EMERGENCY",
        }

    if verbose:
        print("[Stage 1] Scanner...")
    stage1 = stage1_scanner(material, {"stage0": stage0})
    if verbose:
        print()

    if verbose:
        print("[Stage 2] Analyst...")
    stage2 = stage2_analyst(material, {"stage0": stage0, "stage1": stage1})
    risk_nodes = stage2.get("risk_nodes", [])
    if verbose:
        print(f"  → risk nodes: {len(risk_nodes)}")
        print()

    stage3 = None
    if research_first:
        if verbose:
            print("[Stage 3] Researcher...")
        stage3 = stage3_researcher(material, {"stage0": stage0, "stage1": stage1, "stage2": stage2})
        if verbose:
            print()

    if verbose:
        print("[Stage 4] Synthesizer...")
    context_4 = {"stage0": stage0, "stage1": stage1, "stage2": stage2}
    if stage3:
        context_4["stage3"] = stage3
    stage4 = stage4_synthesizer(material, context_4)
    if verbose:
        print(f"  → options: {len(stage4.get('options', []))}")
        print()

    if verbose:
        print("[Stage 5] Transmitter...")
    context_5 = {
        "stage0": stage0, "stage1": stage1, "stage2": stage2,
        "stage4": stage4,
    }
    if stage3:
        context_5["stage3"] = stage3
    final_markdown = stage5_transmitter(material, context_5)
    if verbose:
        print(f"  → финальный Markdown: {len(final_markdown)} символов")
        print()

    # === AUDIT ===
    if verbose:
        print("[Audit] Сбор audit-записи...")
    audit = run_audit(material, session_id)
    if verbose:
        print(f"  → audit_id: {audit['audit_id']}")
        print(f"  → material_hash: {audit['material_hash']}")
        print(f"  → pii_detected: {audit['pii_detected']}")
        print(f"  → compliance_flags: {audit['compliance_flags']}")
        print(f"  → critique_verdict: {audit['critique_verdict']}")
        print()

    audit_block = (
        "\n\n[AUDIT_TRAIL]\n"
        f"audit_id: {audit['audit_id']}\n"
        f"material_hash: {audit['material_hash']}\n"
        f"pii_detected: {str(audit['pii_detected']).lower()}\n"
        f"compliance_flags: {audit['compliance_flags']}\n"
        f"critique_verdict: {audit['critique_verdict']}\n"
    )
    final_markdown = final_markdown + audit_block

    result = {
        "session_id": session_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "filename": filename,
        "material_size": len(material),
        "stage0": stage0,
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3,
        "stage4": stage4,
        "audit": audit,
        "final_markdown": final_markdown,
    }

    add_entry({
        "session_id": session_id,
        "filename": filename,
        "level": level,
        "route": route,
        "material_size": len(material),
    })

    result_file = DATA_DIR / f"result_{session_id}.json"
    result_file.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if verbose:
        print("=== Pipeline завершён ===")
        print(f"Результат: {result_file}")
        print()

    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Путь к файлу")
    ap.add_argument("--quiet", action="store_true", help="Без логов")
    args = ap.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"ERROR: файл не найден: {path}")
        sys.exit(1)

    material = path.read_text(encoding="utf-8", errors="replace")
    result = run_pipeline(material, path.name, verbose=not args.quiet)

    if not args.quiet:
        print("=" * 60)
        print("ФИНАЛЬНЫЙ MARKDOWN:")
        print("=" * 60)
        print(result["final_markdown"][:3000])


if __name__ == "__main__":
    main()

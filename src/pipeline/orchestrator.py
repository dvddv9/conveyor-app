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
from src.tools.fallback_check import REQUIRED as REQUIRED_BLOCKS, LOSS_THRESHOLD
from src.pipeline.cost import sum_stage_costs

MAX_CHARS = 12000   # ~3000 токенов


# === Audit (встроенный compliance-scan) ===

PII_PATTERNS = {
    "email": re.compile(r"(?<![\w%])[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone_ru": re.compile(r"\+7\d{10}|\b8\d{10}\b"),
    "passport_ru": re.compile(r"\b\d{4}\s?\d{6}\b"),
    "snils": re.compile(r"\b\d{3}-\d{3}-\d{3}[ -]?\d{2}\b"),
    "iban": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b"),
    # Secrets
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "aws_secret_key": re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*[\"']?[A-Za-z0-9/+=]{40}[\"']?"),
    "stripe_live_key": re.compile(r"\bsk_live_[A-Za-z0-9]{20,}\b"),
    "stripe_test_key": re.compile(r"\bsk_test_[A-Za-z0-9]{20,}\b"),
    "github_token": re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
    "slack_token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "google_api_key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "private_key": re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "hardcoded_password": re.compile(r"(?i)\bpassword\s*[:=]\s*[\"'][^\"']{8,}[\"']"),
    "hardcoded_secret": re.compile(r"(?i)\b(secret|api_key|access_key|token)\s*[:=]\s*[\"'][^\"']{12,}[\"']"),
}

COMPLIANCE_TRIGGERS = {
    "HIPAA": ["patient", "diagnosis", "medical record", "hipaa", "ehr"],
    "PCI-DSS": ["payment", "card", "cvv", "credit card", "pci"],
    "GDPR": ["personal data", "gdpr", "eu citizen", "right to erasure"],
    "152-ФЗ": ["персональные данные", "152-фз", "оператор данных"],
    "EU AI Act": ["llm", "foundation model", "ai system", "eu ai act"],
    # SECRETS выставляется только через detect_pii (см. ниже),
    # keyword-triggers удалены: они ловили имена переменных, а не секреты.
    # "SECRETS": [...],
}


def compute_hash(material: str) -> str:
    h = hashlib.sha256(material.encode("utf-8", errors="replace"))
    return f"sha256:{h.hexdigest()}"


def detect_pii(text: str) -> dict:
    found = {}
    for name, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            found[name] = len(matches)
    return found


def detect_compliance(text: str, pii: dict | None = None) -> list:
    low = text.lower()
    flags = []
    for flag, triggers in COMPLIANCE_TRIGGERS.items():
        if any(t in low for t in triggers):
            flags.append(flag)

    # PII -> auto-add GDPR + 152-ФЗ
    if pii:
        if any(k in pii for k in ("email", "phone_ru", "passport_ru", "snils", "iban")):
            if "GDPR" not in flags:
                flags.append("GDPR")
            if "152-ФЗ" not in flags:
                flags.append("152-ФЗ")

        # Secrets -> SECRETS flag (critical)
        secret_keys = ("aws_access_key", "aws_secret_key", "stripe_live_key",
                       "stripe_test_key", "github_token", "slack_token",
                       "google_api_key", "private_key", "hardcoded_password",
                       "hardcoded_secret")
        if any(k in pii for k in secret_keys):
            if "SECRETS" not in flags:
                flags.append("SECRETS")

    return flags


def generate_audit_id() -> str:
    now = datetime.now(UTC)
    today = now.strftime("%Y-%m-%d")
    rand = hashlib.md5(str(now.timestamp()).encode()).hexdigest()[:6]
    return f"audit-{today}-{rand}"


def run_audit(material: str, session_id: str, model: str = "deepseek-chat",
              truncated: bool = False, original_size: int = 0) -> dict:
    """Собирает audit-запись."""
    pii = detect_pii(material)
    compliance = detect_compliance(material, pii)
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
        "truncated": truncated,
        "original_size": original_size,
    }

    audit_file = DATA_DIR / f"audit_{session_id}.json"
    audit_file.write_text(
        json.dumps(audit, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return audit


# === Pipeline ===

def run_pipeline(material: str, filename: str, verbose: bool = True,
                 session_suffix: str = "") -> dict:
    """Запускает полный pipeline Conveyor.

    session_suffix: опциональный суффикс для session_id (batch mode).
    """
    # Truncate if too large
    truncated = False
    original_size = len(material)
    if original_size > MAX_CHARS:
        material = material[:MAX_CHARS]
        truncated = True
        if verbose:
            print(f"[!] Материал {original_size} символов > {MAX_CHARS} — обрезан")

    session_id = f"sess-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}{session_suffix}"

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

    # === GATE: EMERGENCY от LLM понижается до WARNING,
    # если audit не нашёл РЕАЛЬНЫХ секретов/PII ===
    if "EMERGENCY_INTERRUPT" in flags:
        _pii = detect_pii(material)
        _comp = detect_compliance(material, _pii)
        _secret_keys = (
            "aws_access_key", "aws_secret_key", "stripe_live_key",
            "stripe_test_key", "github_token", "slack_token",
            "google_api_key", "private_key", "hardcoded_password",
            "hardcoded_secret",
        )
        _has_real_emergency = any(k in _pii for k in _secret_keys)
        if not _has_real_emergency:
            flags = [f for f in flags if f != "EMERGENCY_INTERRUPT"]
            flags.append("WARNING: llm_emergency_downgraded")
            if verbose:
                print("[!] EMERGENCY от LLM понижен до WARNING (audit: SAFE)")
                print(f"    flags: {flags}")

    if "EMERGENCY_INTERRUPT" in flags:
        if verbose:
            print("[!] EMERGENCY_INTERRUPT — стоп (подтверждено audit)")

        # Still run audit — compliance priority
        if verbose:
            print("[Audit] Сбор audit-записи (emergency)...")
        audit = run_audit(material, session_id, truncated=truncated, original_size=original_size)
        if verbose:
            print(f"  → audit_id: {audit['audit_id']}")
            print(f"  → material_hash: {audit['material_hash']}")
            print(f"  → pii_detected: {audit['pii_detected']}")
            print(f"  → compliance_flags: {audit['compliance_flags']}")
            print(f"  → critique_verdict: {audit['critique_verdict']}")
            print()

        emergency_md = (
            "⛔ INTERRUPTED: EMERGENCY\n\n"
            "[EMERGENCY]\n"
            "Stage 0 обнаружил критический риск → pipeline остановлен.\n"
            f"[TRIGGER] flags: {flags}\n"
            f"[REASON] level: {level}, route: {route}\n"
        )
        audit_block = (
            "\n\n[AUDIT_TRAIL]\n"
            f"audit_id: {audit['audit_id']}\n"
            f"material_hash: {audit['material_hash']}\n"
            f"pii_detected: {str(audit['pii_detected']).lower()}\n"
            f"compliance_flags: {audit['compliance_flags']}\n"
            f"critique_verdict: {audit['critique_verdict']}\n"
        )
        emergency_md = emergency_md + audit_block

        add_entry({
            "session_id": session_id,
            "filename": filename,
            "level": level,
            "route": route,
            "material_size": len(material),
            "verdict": audit["critique_verdict"],
            "pii_detected": audit["pii_detected"],
            "material_hash": audit["material_hash"],
        })

        result_file = DATA_DIR / f"result_{session_id}.json"
        result_file.write_text(
            json.dumps({
                "session_id": session_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "filename": filename,
                "material_size": len(material),
                "stage0": stage0,
                "audit": audit,
                "emergency": True,
                "critique_verdict": audit.get("critique_verdict", "SAFE"),
                "cost_usd": 0.0,
                "final_markdown": emergency_md,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        if verbose:
            print("=== Pipeline завершён (EMERGENCY) ===")
            print(f"Результат: {result_file}")
            print()

        return {
            "session_id": session_id,
            "stage0": stage0,
            "audit": audit,
            "emergency": True,
            "final_markdown": emergency_md,
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
        "task_type": stage0.get("task_type", "other"),
    }
    if stage3:
        context_5["stage3"] = stage3
    final_markdown = stage5_transmitter(material, context_5)

    # === AUDIT ===
    if verbose:
        print("[Audit] Сбор audit-записи...")
    audit = run_audit(material, session_id, truncated=truncated, original_size=original_size)
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

    # === COMPLETENESS CHECK (fallback_check integration) ===
    required = REQUIRED_BLOCKS.get(level, [])
    missing = [b for b in required if b not in final_markdown]
    loss_pct = round(len(missing) / len(required) * 100, 1) if required else 0.0
    completeness = {
        "level": level,
        "required_count": len(required),
        "missing": missing,
        "missing_count": len(missing),
        "loss_pct": loss_pct,
        "threshold": LOSS_THRESHOLD,
        "verdict": "ACCEPTABLE" if loss_pct <= LOSS_THRESHOLD else "INCOMPLETE",
    }

    if verbose:
        print(f"[Completeness] level={level}, loss_pct={loss_pct}%, "
              f"missing={len(missing)}, verdict={completeness['verdict']}")
        print()

    completeness_block = (
        "\n\n[COMPLETENESS]\n"
        f"level: {level}\n"
        f"required: {len(required)}\n"
        f"missing: {missing}\n"
        f"loss_pct: {loss_pct}%\n"
        f"verdict: {completeness['verdict']}\n"
    )
    final_markdown = final_markdown + completeness_block

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
        "completeness": completeness,
            "critique_verdict": audit["critique_verdict"],
        "cost_usd": sum_stage_costs([stage0, stage1, stage2, stage3, stage4]),
        "final_markdown": final_markdown,
    }

    add_entry({
        "session_id": session_id,
        "filename": filename,
        "level": level,
        "route": route,
        "material_size": len(material),
        "verdict": audit["critique_verdict"],
        "pii_detected": audit["pii_detected"],
        "material_hash": audit["material_hash"],
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


async def run_pipeline_async(material: str, filename: str, verbose: bool = False,
                              session_suffix: str = "") -> dict:
    """Async pipeline."""
    # Truncate if too large
    truncated = False
    original_size = len(material)
    if original_size > MAX_CHARS:
        material = material[:MAX_CHARS]
        truncated = True

    from src.pipeline.async_stages import (
        async_stage0_orchestrator, async_stage1_scanner, async_stage2_analyst,
        async_stage3_researcher, async_stage4_synthesizer, async_stage5_transmitter,
    )
    session_id = f"sess-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}{session_suffix}"
    stage0 = await async_stage0_orchestrator(material, filename)
    route = stage0.get("route", [])
    level = stage0.get("level", "D3")
    research_first = stage0.get("research_first", False)
    stage1 = await async_stage1_scanner(material, {"stage0": stage0})
    stage2 = await async_stage2_analyst(material, {"stage0": stage0, "stage1": stage1})
    stage3 = None
    if research_first:
        stage3 = await async_stage3_researcher(
            material, {"stage0": stage0, "stage1": stage1, "stage2": stage2})
    context_4 = {"stage0": stage0, "stage1": stage1, "stage2": stage2}
    if stage3:
        context_4["stage3"] = stage3
    stage4 = await async_stage4_synthesizer(material, context_4)
    context_5 = {"stage0": stage0, "stage1": stage1, "stage2": stage2, "stage4": stage4}
    if stage3:
        context_5["stage3"] = stage3
    final_markdown = await async_stage5_transmitter(material, context_5)
    audit = run_audit(material, session_id, truncated=truncated, original_size=original_size)
    final_markdown += (
        "\n\n[AUDIT_TRAIL]\n"
        f"audit_id: {audit['audit_id']}\n"
        f"material_hash: {audit['material_hash']}\n"
        f"pii_detected: {str(audit['pii_detected']).lower()}\n"
        f"compliance_flags: {audit['compliance_flags']}\n"
        f"critique_verdict: {audit['critique_verdict']}\n"
    )
    required = REQUIRED_BLOCKS.get(level, [])
    missing = [b for b in required if b not in final_markdown]
    loss_pct = round(len(missing) / len(required) * 100, 1) if required else 0.0
    completeness = {"level": level, "required_count": len(required), "missing": missing,
                    "missing_count": len(missing), "loss_pct": loss_pct,
                    "threshold": LOSS_THRESHOLD,
                    "verdict": "ACCEPTABLE" if loss_pct <= LOSS_THRESHOLD else "INCOMPLETE"}
    final_markdown += (
        "\n\n[COMPLETENESS]\n"
        f"level: {level}\nrequired: {len(required)}\nmissing: {missing}\n"
        f"loss_pct: {loss_pct}%\nverdict: {completeness['verdict']}\n"
    )
    result = {"session_id": session_id, "timestamp": datetime.now(UTC).isoformat(),
              "filename": filename, "material_size": len(material), "stage0": stage0,
              "stage1": stage1, "stage2": stage2, "stage3": stage3, "stage4": stage4,
              "audit": audit, "completeness": completeness,
              "cost_usd": sum_stage_costs([stage0, stage1, stage2, stage3, stage4]),
              "final_markdown": final_markdown}
    add_entry({"session_id": session_id, "filename": filename, "level": level,
               "route": route, "material_size": len(material),
               "verdict": audit["critique_verdict"], "pii_detected": audit["pii_detected"],
               "material_hash": audit["material_hash"]})
    result_file = DATA_DIR / f"result_{session_id}.json"
    result_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
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

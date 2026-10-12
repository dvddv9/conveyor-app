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
from src.tools.redact import redact_pii  # dogfood P0: pre-LLM PII redaction
from src.tools.sast import run_sast  # dogfood P1: deterministic SAST
from src.tools.sca import run_sca  # dogfood P1: dependency audit
from src.tools.patterns import PII_PATTERNS, COMPLIANCE_TRIGGERS
from src.tools.patterns import CWE_TO_OWASP, cwe_to_owasp
from src.tools.patterns import CRITICAL_RISK_PATTERNS

MAX_CHARS = 12000   # ~3000 токенов


# === Audit (встроенный compliance-scan) ===

# PII_PATTERNS moved to src/tools/patterns.py (dogfood: circular import fix)

# COMPLIANCE_TRIGGERS moved to src/tools/patterns.py




def detect_material_complete(material: str, final_markdown: str = "") -> bool:
    """DEPRECATED (v5.7): use `not truncated` from run_pipeline instead.
    
    Kept for backward compatibility only. Fragile heuristic — may produce
    false positives/negatives. The `truncated` flag is deterministic."""
    markers = ["truncated", "усечён", "усечен", "slice truncated", "слайс усеч"]
    text = (material or "")[:2000] + " " + (final_markdown or "")[:2000]
    low = text.lower()
    for m in markers:
        if m in low:
            return False
    return True

def compute_hash(material: str, context: str = "") -> str:
    """Compute SHA-256 hash of material.
    
    Args:
        material: input text
        context: optional context (filename + timestamp) to disambiguate
                 materials with identical content but different origins.
    
    Note (dogfood finding): without context, different materials with
    identical content would produce the same hash — breaking audit trail
    uniqueness invariant.
    """
    payload = material
    if context:
        payload = f"{context}\n---\n{material}"
    h = hashlib.sha256(payload.encode("utf-8", errors="replace"))
    return f"sha256:{h.hexdigest()}"

def strip_llm_audit_blocks(md: str) -> str:
    """Remove [AUDIT_TRAIL] and [COMPLETENESS] from LLM output (pipeline adds its own)."""
    md = re.sub(
        r'\n*\[AUDIT_TRAIL\].*?(?=\n\[|\Z)',
        '', md, flags=re.DOTALL
    ).strip()
    md = re.sub(
        r'\n*\[COMPLETENESS\].*?(?=\n\[|\Z)',
        '', md, flags=re.DOTALL
    ).strip()
    return md



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




def detect_language(filename: str) -> str:
    """Detect language from filename for SAST tool selection."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return {
        "py": "python", "go": "go", "js": "javascript", "ts": "typescript",
        "java": "java", "rs": "rust",
    }.get(ext, "other")




def detect_cwe(text: str) -> list:
    """Detect CWE IDs mentioned in material (CWE-XXX format).

    Returns list of unique CWE IDs found.
    """
    import re as _re
    matches = _re.findall(r"\bCWE-(\d+)\b", text)
    seen = []
    for m in matches:
        cwe = f"CWE-{m}"
        if cwe not in seen:
            seen.append(cwe)
    return seen


def map_cwe_to_owasp(cwe_ids: list, year: str = "2025") -> list:
    """Map list of CWE IDs to unique OWASP Top 10 categories."""
    owasp = []
    for cwe in cwe_ids:
        cat = cwe_to_owasp(cwe, year=year)
        if cat and cat not in owasp:
            owasp.append(cat)
    return owasp


def run_audit(material: str, session_id: str, model: str = "deepseek-chat",
              truncated: bool = False, original_size: int = 0,
              material_hash_full: str = None,
              force_emergency: bool = False,
              context: str = "",
              redaction_map: dict = None,
              sast_result: dict = None,
              sca_result: dict = None) -> dict:
    """Собирает audit-запись."""
    pii = detect_pii(material)
    compliance = detect_compliance(material, pii)
    critique = "REQUIRES_REVIEW" if (pii or compliance) else "SAFE"
    risk_verdict = "EMERGENCY" if force_emergency else "SAFE"
    cwe_ids = detect_cwe(material)
    owasp_categories = map_cwe_to_owasp(cwe_ids, year="2025")

    audit = {
        "audit_id": generate_audit_id(),
        "session_id": session_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "material_hash": compute_hash(material, context=context),
        "material_hash_full": material_hash_full or compute_hash(material, context=context),
        "material_size": {
            "lines": len(material.splitlines()),
            "chars": len(material),
        },
        "model": model,
        "critique_verdict": critique,
        "risk_verdict": risk_verdict,
        "cwe_ids": cwe_ids,
        "owasp_categories": owasp_categories,
        "pii_detected": bool(pii),
        "pii_details": pii,
        "compliance_flags": compliance,
        "redaction_applied": bool(redaction_map),
        "redaction_map": redaction_map or {},
        "sast_findings": (sast_result or {}).get("total_findings", 0),
        "sast_high_priority": (sast_result or {}).get("high_priority", 0),
        "sast_tools": {
            "bandit": ((sast_result or {}).get("bandit") or {}).get("summary", {}),
            "semgrep": ((sast_result or {}).get("semgrep") or {}).get("summary", {}),
        } if sast_result else {},
        "sca_vulnerabilities": ((sca_result or {}).get("pip_audit") or {}).get("summary", {}).get("total", 0),
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
    session_id = f"sess-{datetime.now(UTC).strftime('%Y-%m-%d-%H%M%S')}{session_suffix}"
    material_hash_full = compute_hash(material, context=f"{filename}:{session_id}")  # hash BEFORE truncation
    if original_size > MAX_CHARS:
        material = material[:MAX_CHARS]
        truncated = True
        if verbose:
            print(f"[!] Материал {original_size} символов > {MAX_CHARS} — обрезан")


    if verbose:
        print(f"=== Conveyor Pipeline ===")
        print(f"Session: {session_id}")
        print(f"File: {filename}")
        print(f"Material: {len(material)} символов")
        print()

    if verbose:
        print("[Stage 0] Orchestrator...")
    # === DOGFOOD P0: redact PII/secrets BEFORE any LLM call ===
    material_original = material
    material, redaction_map = redact_pii(material)
    if redaction_map:
        if verbose:
            print(f"[Redact] PII/secrets redacted: {redaction_map}")
        # Audit on ORIGINAL material (for compliance verdict)
        original_audit_pii = detect_pii(material_original)
        original_audit_compliance = detect_compliance(material_original, original_audit_pii)
    else:
        original_audit_pii = {}
        original_audit_compliance = []

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
        _has_secrets_or_pii = any(k in _pii for k in _secret_keys) or bool(_pii) or bool(_comp)

        # Dogfood P0 fix: also check CRITICAL_RISK_PATTERNS (RCE, SQLi, path traversal).
        # Before: GATE downgraded EMERGENCY if only SECRETS/PII were absent —
        # which incorrectly silenced RCE, SQLi, path traversal.
        _critical_hits = []
        for _risk_name, _risk_pattern in CRITICAL_RISK_PATTERNS.items():
            if _risk_pattern.search(material):
                _critical_hits.append(_risk_name)

        _has_real_emergency = _has_secrets_or_pii or bool(_critical_hits)

        if not _has_real_emergency:
            flags = [f for f in flags if f != "EMERGENCY_INTERRUPT"]
            flags.append("WARNING: llm_emergency_downgraded")
            if verbose:
                print("[!] EMERGENCY от LLM понижен до WARNING (audit: SAFE, no critical patterns)")
                print(f"    flags: {flags}")
        else:
            if verbose:
                reason = []
                if _has_secrets_or_pii:
                    reason.append("secrets/PII")
                if _critical_hits:
                    reason.append(f"critical patterns: {_critical_hits}")
                print(f"[!] EMERGENCY подтверждён audit ({', '.join(reason)})")

    if "EMERGENCY_INTERRUPT" in flags:
        if verbose:
            print("[!] EMERGENCY_INTERRUPT — стоп (подтверждено audit)")

        # Still run audit — compliance priority
        if verbose:
            print("[Audit] Сбор audit-записи (emergency)...")
        audit = run_audit(material_original, session_id, truncated=truncated, original_size=original_size, material_hash_full=material_hash_full, force_emergency=True, context=f"{filename}:{session_id}", redaction_map=redaction_map if "redaction_map" in dir() else {}, sast_result=_sast_result if "_sast_result" in dir() else None, sca_result=_sca_result if "_sca_result" in dir() else None)
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
        f"material_hash_full: {audit.get('material_hash_full', audit['material_hash'])}\n"
            f"pii_detected: {str(audit['pii_detected']).lower()}\n"
            f"compliance_flags: {audit['compliance_flags']}\n"
            f"critique_verdict: {audit['critique_verdict']}\n"
        f"risk_verdict: {audit.get('risk_verdict', 'SAFE')}\n"
        f"cwe_ids: {audit.get('cwe_ids', [])}\n"
        f"owasp_categories: {audit.get('owasp_categories', [])}\n"
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

    # === Dogfood P1: deterministic SAST/SCA before Stage 2 ===
    _lang = detect_language(filename)
    _sast_result = None
    _sca_result = None
    if _lang in ("python", "go", "javascript", "typescript", "java", "rust"):
        try:
            _sast_result = run_sast(filename, language=_lang)
            if verbose:
                print(f"[SAST] {_lang}: {_sast_result.get('total_findings', 0)} findings "
                      f"({_sast_result.get('high_priority', 0)} high)")
        except Exception as _e:
            if verbose:
                print(f"[SAST] error: {_e}")
    if filename.endswith("requirements.txt"):
        try:
            _sca_result = run_sca(filename)
            if verbose:
                _n = _sca_result.get("pip_audit", {}).get("summary", {}).get("total", 0)
                print(f"[SCA] pip-audit: {_n} vulnerabilities")
        except Exception as _e:
            if verbose:
                print(f"[SCA] error: {_e}")
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
    # Strip any [AUDIT_TRAIL]/[COMPLETENESS] from LLM output (pipeline adds its own)
    final_markdown = strip_llm_audit_blocks(final_markdown)

    # === AUDIT ===
    if verbose:
        print("[Audit] Сбор audit-записи...")
    force_emergency = bool(stage4.get('force_emergency', False))

    audit = run_audit(material_original, session_id, truncated=truncated, original_size=original_size, material_hash_full=material_hash_full, force_emergency=force_emergency, context=f"{filename}:{session_id}", redaction_map=redaction_map, sast_result=_sast_result if "_sast_result" in dir() else None, sca_result=_sca_result if "_sca_result" in dir() else None)
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
        f"material_hash_full: {audit.get('material_hash_full', audit['material_hash'])}\n"
        f"pii_detected: {str(audit['pii_detected']).lower()}\n"
        f"compliance_flags: {audit['compliance_flags']}\n"
        f"critique_verdict: {audit['critique_verdict']}\n"
        f"risk_verdict: {audit.get('risk_verdict', 'SAFE')}\n"
        f"cwe_ids: {audit.get('cwe_ids', [])}\n"
        f"owasp_categories: {audit.get('owasp_categories', [])}\n"
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
        "material_complete": not truncated,   # deterministic: flag from run_pipeline
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
        f"material_complete: {completeness.get('material_complete', not truncated)}\n"
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
    session_id = f"sess-{datetime.now(UTC).strftime('%Y-%m-%d-%H%M%S')}{session_suffix}"
    material_hash_full = compute_hash(material, context=f"{filename}:{session_id}")  # hash BEFORE truncation
    if original_size > MAX_CHARS:
        material = material[:MAX_CHARS]
        truncated = True

    from src.pipeline.async_stages import (
        async_stage0_orchestrator, async_stage1_scanner, async_stage2_analyst,
        async_stage3_researcher, async_stage4_synthesizer, async_stage5_transmitter,
    )
    # === DOGFOOD P0: redact PII/secrets BEFORE any LLM call ===
    material_original = material
    material, redaction_map = redact_pii(material)
    if redaction_map:
        original_audit_pii = detect_pii(material_original)
        original_audit_compliance = detect_compliance(material_original, original_audit_pii)
    else:
        original_audit_pii = {}
        original_audit_compliance = []

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
    # Strip any [AUDIT_TRAIL]/[COMPLETENESS] from LLM output (pipeline adds its own)
    final_markdown = strip_llm_audit_blocks(final_markdown)
    force_emergency = bool(stage4.get('force_emergency', False))

    audit = run_audit(material_original, session_id, truncated=truncated, original_size=original_size, material_hash_full=material_hash_full, force_emergency=force_emergency, context=f"{filename}:{session_id}", redaction_map=redaction_map, sast_result=_sast_result if "_sast_result" in dir() else None, sca_result=_sca_result if "_sca_result" in dir() else None)
    final_markdown += (
        "\n\n[AUDIT_TRAIL]\n"
        f"audit_id: {audit['audit_id']}\n"
        f"material_hash: {audit['material_hash']}\n"
        f"material_hash_full: {audit.get('material_hash_full', audit['material_hash'])}\n"
        f"pii_detected: {str(audit['pii_detected']).lower()}\n"
        f"compliance_flags: {audit['compliance_flags']}\n"
        f"critique_verdict: {audit['critique_verdict']}\n"
        f"risk_verdict: {audit.get('risk_verdict', 'SAFE')}\n"
        f"cwe_ids: {audit.get('cwe_ids', [])}\n"
        f"owasp_categories: {audit.get('owasp_categories', [])}\n"
    )
    required = REQUIRED_BLOCKS.get(level, [])
    missing = [b for b in required if b not in final_markdown]
    loss_pct = round(len(missing) / len(required) * 100, 1) if required else 0.0
    completeness = {"level": level, "required_count": len(required), "missing": missing,
                    "missing_count": len(missing), "loss_pct": loss_pct,
                    "material_complete": not truncated,   # deterministic: flag from run_pipeline
                    "threshold": LOSS_THRESHOLD,
                    "verdict": "ACCEPTABLE" if loss_pct <= LOSS_THRESHOLD else "INCOMPLETE"}
    final_markdown += (
        "\n\n[COMPLETENESS]\n"
        f"level: {level}\nrequired: {len(required)}\nmissing: {missing}\n"
        f"loss_pct: {loss_pct}%\n"
        f"material_complete: {completeness.get('material_complete', not truncated)}\n"
        f"verdict: {completeness['verdict']}\n"
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

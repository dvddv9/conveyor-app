# -*- coding: utf-8 -*-
"""SARIF 2.1.0 output — standard format for security findings.

Dogfood P1: integrate with GitHub Code Scanning / Azure DevOps / IDE.
SARIF spec: https://docs.oasis-open.org/sarif/sarif/v2.1.0/
"""
import json
from datetime import datetime, timezone
from pathlib import Path


def _severity_to_sarif_level(severity: str) -> str:
    """Map tool severity to SARIF level."""
    s = (severity or "").lower()
    return {
        "high": "error",
        "critical": "error",
        "medium": "warning",
        "moderate": "warning",
        "low": "note",
        "info": "note",
    }.get(s, "warning")


def to_sarif(audit: dict, sast_result: dict = None, sca_result: dict = None,
             source_file: str = "input") -> dict:
    """Convert Vishap audit + SAST/SCA results to SARIF 2.1.0.

    Args:
        audit: audit dict from run_audit
        sast_result: dict from src.tools.sast.run_sast
        sca_result: dict from src.tools.sca.run_sca
        source_file: filename for SARIF artifacts

    Returns:
        SARIF JSON as dict.
    """
    rules = []
    results = []

    # === SAST findings (Bandit, Semgrep) ===
    if sast_result:
        for tool_name in ("bandit", "semgrep"):
            tool_result = sast_result.get(tool_name)
            if not tool_result or not tool_result.get("available"):
                continue

            for i, f in enumerate(tool_result.get("findings", [])):
                rule_id = f.get("test_id") or f.get("check_id") or f"{tool_name}_unknown"
                rule_id_full = f"{tool_name}/{rule_id}"

                rules.append({
                    "id": rule_id_full,
                    "name": rule_id,
                    "shortDescription": {"text": f.get("msg", "")[:200]},
                    "defaultConfiguration": {
                        "level": _severity_to_sarif_level(f.get("severity", "")),
                    },
                    "properties": {
                        "source": tool_name,
                        "severity": f.get("severity", ""),
                        "confidence": f.get("confidence", ""),
                    },
                })

                results.append({
                    "ruleId": rule_id_full,
                    "level": _severity_to_sarif_level(f.get("severity", "")),
                    "message": {"text": f.get("msg", "")},
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {"uri": source_file},
                            "region": {"startLine": f.get("line", 1) or 1},
                        }
                    }],
                })

    # === SCA vulnerabilities (pip-audit) ===
    if sca_result:
        pa = sca_result.get("pip_audit")
        if pa and pa.get("available"):
            for v in pa.get("vulnerabilities", []):
                rule_id = f"pip-audit/{v.get('id', 'UNKNOWN')}"
                rules.append({
                    "id": rule_id,
                    "name": v.get("id", ""),
                    "shortDescription": {
                        "text": f"{v.get('name', '')}=={v.get('version', '')}: {v.get('description', '')[:150]}"
                    },
                    "defaultConfiguration": {"level": "error"},
                    "properties": {
                        "source": "pip-audit",
                        "package": v.get("name", ""),
                        "version": v.get("version", ""),
                        "fix_versions": v.get("fix_versions", []),
                    },
                })
                results.append({
                    "ruleId": rule_id,
                    "level": "error",
                    "message": {
                        "text": f"{v.get('name', '')}=={v.get('version', '')}: {v.get('id', '')}"
                    },
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {"uri": "requirements.txt"},
                        }
                    }],
                })

    # === Vishap audit metadata as SARIF properties ===
    sarif = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "Vishap",
                    "version": "5.9.0",
                    "informationUri": "https://github.com/dvddv9/vishap",
                    "rules": rules,
                }
            },
            "results": results,
            "invocations": [{
                "executionSuccessful": True,
                "startTimeUtc": datetime.now(timezone.utc).isoformat(),
            }],
            "properties": {
                "vishap": {
                    "audit_id": audit.get("audit_id", ""),
                    "session_id": audit.get("session_id", ""),
                    "material_hash": audit.get("material_hash", ""),
                    "material_hash_full": audit.get("material_hash_full", ""),
                    "critique_verdict": audit.get("critique_verdict", ""),
                    "risk_verdict": audit.get("risk_verdict", ""),
                    "pii_detected": audit.get("pii_detected", False),
                    "compliance_flags": audit.get("compliance_flags", []),
                    "sast_findings": audit.get("sast_findings", 0),
                    "sca_vulnerabilities": audit.get("sca_vulnerabilities", 0),
                },
            },
        }],
    }

    return sarif


def write_sarif(sarif: dict, output_path: str) -> str:
    """Write SARIF JSON to file. Returns path."""
    p = Path(output_path)
    p.write_text(json.dumps(sarif, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(p)

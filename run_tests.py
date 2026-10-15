# -*- coding: utf-8 -*-
"""Run Vishap tests.

Usage:
    python run_tests.py          # unit + mock (fast, no LLM)
    python run_tests.py --all    # all tests (includes real LLM)
"""
import subprocess
import sys


def run(path):
    print(f"\n=== {path} ===")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", path],
        cwd="C:/AI/conveyor_app",
    )
    return result.returncode


def main():
    rc = 0
    rc |= run("tests/test_tools.py")
    rc |= run("tests/test_patterns.py")
    rc |= run("tests/test_pipeline_mock.py")
    rc |= run("tests/test_baseline.py")
    rc |= run("tests/test_diff.py")
    rc |= run("tests/test_sbom.py")
    rc |= run("tests/test_sarif.py")
    rc |= run("tests/test_quality_gate.py")
    rc |= run("tests/test_deps.py")
    rc |= run("tests/test_reachability.py")
    rc |= run("tests/test_dataflow.py")
    rc |= run("tests/test_compliance.py")
    rc |= run("tests/test_runbook.py")
    rc |= run("tests/test_security_md.py")
    rc |= run("tests/test_llm_providers.py")
    rc |= run("tests/test_anomaly.py")
    rc |= run("tests/test_async_imports.py")
    rc |= run("tests/test_ui_headers.py")
    rc |= run("tests/test_api_client.py")
    rc |= run("tests/test_risk_verdict.py")
    rc |= run("tests/test_risk_verdict_security.py")
    rc |= run("tests/test_verdict.py")
    rc |= run("tests/test_anomaly_density.py")
    rc |= run("tests/test_pii_copyright.py")
    rc |= run("tests/test_anomaly_code.py")

    if "--all" in sys.argv:
        print("\n[--all] E2E tests (real LLM, slow, uses API):")
        rc |= run("tests/test_e2e.py")

    sys.exit(rc)


if __name__ == "__main__":
    main()
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
    rc |= run("tests/test_compliance.py")

    if "--all" in sys.argv:
        print("\n[--all] E2E tests (real LLM, slow, uses API):")
        rc |= run("tests/test_e2e.py")

    sys.exit(rc)


if __name__ == "__main__":
    main()
# -*- coding: utf-8 -*-
"""Run Conveyor tests.

Usage:
    python run_tests.py          # unit + mock (fast, no LLM)
    python run_tests.py --all    # all tests (includes real LLM)
"""
import subprocess
import sys


def run(path):
    print(f"\n=== {path} ===")
    result = subprocess.run(
        ["pytest", "-v", path],
        cwd="C:/AI/conveyor_app",
    )
    return result.returncode


def main():
    rc = 0
    rc |= run("tests/test_tools.py")
    rc |= run("tests/test_pipeline_mock.py")

    if "--all" in sys.argv:
        print("\n[--all] Real LLM tests (slow, uses API):")
        rc |= run("tests/test_pipeline_real.py")

    sys.exit(rc)


if __name__ == "__main__":
    main()

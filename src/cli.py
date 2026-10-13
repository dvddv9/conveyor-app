# -*- coding: utf-8 -*-
"""Vishap CLI entry point.

Usage:
    vishap analyze <file>
    vishap analyze <file> --save-baseline .vishap-baseline.json
    vishap analyze <file> --baseline .vishap-baseline.json
    vishap info
    vishap --version
"""
import argparse
import sys
from pathlib import Path

from src.config import APP_NAME
from src.pipeline.orchestrator import run_pipeline


def cmd_analyze(args):
    """Analyze a file."""
    path = Path(args.input)
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)

    material = path.read_text(encoding="utf-8", errors="replace")
    result = run_pipeline(
        material, path.name,
        verbose=not args.quiet,
        baseline_path=args.baseline,
        save_baseline_path=args.save_baseline,
    )

    md = result.get("final_markdown", "")
    audit = result.get("audit", {})
    stats = result.get("baseline_stats") or {}

    if args.output:
        Path(args.output).write_text(md, encoding="utf-8")
        print(f"Written: {args.output}")
    else:
        print(md)
        print()
        print(f"audit_id:      {audit.get('audit_id')}")
        print(f"material_hash: {audit.get('material_hash')}")
        print(f"verdict:       {audit.get('critique_verdict')} / {audit.get('risk_verdict')}")

    # Baseline summary (only if used)
    if stats.get("baseline_saved"):
        print(f"baseline_saved: {stats.get('baseline_saved_count', 0)} fingerprints "
              f"-> {stats.get('baseline_save_path', '')}")
    if stats.get("baseline_used"):
        print(f"baseline:      new={stats.get('baseline_new', 0)} "
              f"known={stats.get('baseline_known', 0)} "
              f"total={stats.get('baseline_total', 0)}")


def cmd_info(args):
    """Show info."""
    print(f"{APP_NAME} V5.9 - 6-stage LLM pipeline")
    print("Pipeline: Stage 0-5 (Orchestrator > Scanner > Analyst > Researcher > Synthesizer > Transmitter)")
    print("Features: audit trail, PII redaction, compliance flags, SAST/SCA, SARIF, retry, fallback, baseline")
    print()
    print("Commands:")
    print("  vishap analyze <file>   - analyze a file")
    print("  vishap info             - this help")
    print()
    print("Options for analyze:")
    print("  --save-baseline PATH    - save fingerprints of findings to PATH")
    print("  --baseline PATH         - compare against baseline, report only new findings")
    print("  --output, -o PATH       - write markdown report to file")
    print("  --quiet                 - suppress logs")
    print()
    print("API: python -m src.main   - FastAPI on :5001")
    print("UI:  streamlit run src/ui/streamlit_app.py  - Streamlit on :8501")


def main():
    ap = argparse.ArgumentParser(prog="vishap", description=f"{APP_NAME} V5.9")
    ap.add_argument("--version", action="version", version=f"{APP_NAME} V5.9")

    sub = ap.add_subparsers(dest="command")

    p_analyze = sub.add_parser("analyze", help="Analyze a file")
    p_analyze.add_argument("input", help="Path to file")
    p_analyze.add_argument("--quiet", action="store_true")
    p_analyze.add_argument("--output", "-o", help="Output markdown path")
    p_analyze.add_argument(
        "--save-baseline", metavar="PATH",
        help="Save fingerprints of findings to PATH (baseline v1.0)",
    )
    p_analyze.add_argument(
        "--baseline", metavar="PATH",
        help="Compare against baseline; report only new findings",
    )
    p_analyze.set_defaults(func=cmd_analyze)

    p_info = sub.add_parser("info", help="Show info")
    p_info.set_defaults(func=cmd_info)

    args = ap.parse_args()
    if not args.command:
        ap.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()

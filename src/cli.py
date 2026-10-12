# -*- coding: utf-8 -*-
"""Vishap CLI entry point.

Usage:
    vishap analyze <file>
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
    result = run_pipeline(material, path.name, verbose=not args.quiet)

    md = result.get("final_markdown", "")
    audit = result.get("audit", {})

    if args.output:
        Path(args.output).write_text(md, encoding="utf-8")
        print(f"Written: {args.output}")
    else:
        print(md)
        print()
        print(f"audit_id:      {audit.get('audit_id')}")
        print(f"material_hash: {audit.get('material_hash')}")
        print(f"verdict:       {audit.get('critique_verdict')} / {audit.get('risk_verdict')}")


def cmd_info(args):
    """Show info."""
    print(f"{APP_NAME} V5.8 - 6-stage LLM pipeline")
    print("Pipeline: Stage 0-5 (Orchestrator > Scanner > Analyst > Researcher > Synthesizer > Transmitter)")
    print("Features: audit trail, PII redaction, compliance flags, SAST/SCA, SARIF, retry, fallback")
    print()
    print("Commands:")
    print("  vishap analyze <file>   - analyze a file")
    print("  vishap info             - this help")
    print()
    print("API: python -m src.main   - FastAPI on :5001")
    print("UI:  streamlit run src/ui/streamlit_app.py  - Streamlit on :8501")


def main():
    ap = argparse.ArgumentParser(prog="vishap", description=f"{APP_NAME} V5.8")
    ap.add_argument("--version", action="version", version=f"{APP_NAME} V5.8")

    sub = ap.add_subparsers(dest="command")

    p_analyze = sub.add_parser("analyze", help="Analyze a file")
    p_analyze.add_argument("input", help="Path to file")
    p_analyze.add_argument("--quiet", action="store_true")
    p_analyze.add_argument("--output", "-o", help="Output markdown path")
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

# -*- coding: utf-8 -*-
"""Conveyor CLI — entry point."""
import argparse
import sys
from pathlib import Path


def cmd_analyze(args):
    from src.pipeline.orchestrator import run_pipeline
    path = Path(args.input)
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        sys.exit(1)
    material = path.read_text(encoding="utf-8", errors="replace")
    result = run_pipeline(material, path.name, verbose=not args.quiet)
    if not args.quiet:
        print("=" * 60)
        print("FINAL MARKDOWN:")
        print("=" * 60)
        print(result["final_markdown"][:3000])


def cmd_info(args):
    print("Conveyor V5.7 — 6-stage LLM pipeline")
    print("Pipeline: Stage 0-5 (Orchestrator → Scanner → Analyst → Researcher → Synthesizer → Transmitter)")
    print("Features: audit trail, PII detection, compliance flags, retry, fallback")
    print()
    print("Commands:")
    print("  conveyor analyze <file>   — analyze a file")
    print("  conveyor info             — this help")
    print()
    print("API: python -m src.main   — FastAPI on :5001")
    print("UI:  streamlit run src/ui/streamlit_app.py  — Streamlit on :8501")


def main():
    ap = argparse.ArgumentParser(prog="conveyor", description="Conveyor V5.7")
    sub = ap.add_subparsers(dest="command")
    p_analyze = sub.add_parser("analyze", help="Analyze a file")
    p_analyze.add_argument("input", help="Path to file")
    p_analyze.add_argument("--quiet", action="store_true")
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

"""
Agentic AI Tester — Capstone Project
======================================
CLI entry point that drives the multi-agent LangGraph pipeline.

Usage:
    python main.py                              # default SRS + URL
    python main.py --pdf specs/Other.pdf        # different SRS
    python main.py --url https://example.com/   # different target
"""

import argparse
import os
import sys

from config.settings import DEFAULT_TARGET_URL, SPECS_DIR
from orchestrator.workflow import run_pipeline


def main():
    ap = argparse.ArgumentParser(
        description="Agentic AI Tester — multi-agent Playwright test generation pipeline",
    )
    ap.add_argument(
        "--pdf",
        default=os.path.join(SPECS_DIR, "SpecificationDoc.pdf"),
        help="Path to the SRS PDF document (default: specs/SpecificationDoc.pdf)",
    )
    ap.add_argument(
        "--url",
        default=DEFAULT_TARGET_URL,
        help="Target URL the tests will run against",
    )
    args = ap.parse_args()

    # ── validate inputs ──────────────────────────────────────
    if not os.path.exists(args.pdf):
        print(f"  ERROR: PDF not found at '{args.pdf}'")
        sys.exit(1)

    # ── banner ───────────────────────────────────────────────
    print()
    print("=" * 60)
    print("   AGENTIC AI TESTER  —  Capstone Pipeline")
    print("=" * 60)
    print(f"   PDF  :  {args.pdf}")
    print(f"   URL  :  {args.url}")
    print("=" * 60)

    # ── run ──────────────────────────────────────────────────
    result = run_pipeline(args.pdf, args.url)

    # ── final summary ────────────────────────────────────────
    iterations = result.get("iteration", 0)
    report = result.get("audit_report", {})
    verdict = report.get("verdict", "UNKNOWN")
    coverage = report.get("coverage_pct", "?")

    print()
    print("=" * 60)
    print("   PIPELINE COMPLETE")
    print("=" * 60)
    print(f"   Iterations :  {iterations}")
    print(f"   Verdict    :  {verdict}")
    print(f"   Coverage   :  {coverage}%")
    print(f"   Output     :  output/generated_tests.py")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
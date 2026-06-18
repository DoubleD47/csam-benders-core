"""
Generate Markdown + PDF sweep report (standalone).

Usually run automatically after analyze_sweep, but can be invoked directly:

  python -m experiment_scripts.sweep_report
  python -m experiment_scripts.sweep_report --sweep-dir experiments/sweeps/2026-06-18_quick
"""

from __future__ import annotations

import argparse

from experiment_scripts.analyze_sweep import analyze_sweep, find_latest_sweep
from experiment_scripts.report_utils import generate_sweep_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate sweep Markdown/PDF report")
    parser.add_argument("--sweep-dir", type=str, default=None)
    parser.add_argument(
        "--analyze-first",
        action="store_true",
        help="Run analyze_sweep before generating the report",
    )
    args = parser.parse_args()

    sweep_dir = args.sweep_dir or find_latest_sweep()
    if sweep_dir is None:
        raise SystemExit("No sweep directory found.")

    if args.analyze_first:
        analyze_sweep(sweep_dir)

    files = generate_sweep_report(sweep_dir)
    print(f"Markdown: {files.get('markdown')}")
    print(f"PDF:      {files.get('pdf') or '(install fpdf2 for PDF output)'}")


if __name__ == "__main__":
    main()
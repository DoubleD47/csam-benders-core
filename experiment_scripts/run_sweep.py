"""
Factorial parameter sweep for CSAM deployment experiments.

Runs every combination of factor levels defined in sweep_utils (full factorial).
Each scenario calls run_single_experiment, which writes a full experiment folder
under experiments/<run_id>/ and returns a summary dict.

Sweep outputs (under experiments/sweeps/<timestamp>_<name>/):
  configs/   — one JSON per scenario (input parameters)
  results/   — one JSON per scenario (config + solver summary)
  logs/      — sweep-level log
  sweep_manifest.json — factor grid + scenario list + run metadata

Usage:
  python -m experiment_scripts.run_sweep --quick
  python -m experiment_scripts.run_sweep --max-scenarios 10
  python -m experiment_scripts.run_sweep --sweep-name my_study

For the older multi-dimensional prototype, see run_complex_sweep.py (deprecated).
"""

from __future__ import annotations

import argparse
import sys
import traceback
from datetime import datetime
from pathlib import Path

from model.parameters import get_default_params

from experiment_scripts.run_single import run_single_experiment
from experiment_scripts.sweep_utils import (
    build_scenarios,
    count_scenarios,
    create_sweep_dir,
    get_factor_grid,
    apply_factors,
    merge_result,
    save_json,
)


def run_sweep(
    quick: bool = False,
    max_scenarios: int | None = None,
    sweep_name: str | None = None,
    custom_grid: dict | None = None,
    analyze_after: bool = True,
) -> Path:
    grid = custom_grid or get_factor_grid(quick=quick)
    scenarios = build_scenarios(grid, max_scenarios=max_scenarios)
    sweep_dir = create_sweep_dir(sweep_name)

    manifest = {
        "created_at": datetime.now().isoformat(),
        "factor_grid": grid,
        "scenario_count": len(scenarios),
        "full_factorial_size": count_scenarios(grid),
        "truncated": max_scenarios is not None and len(scenarios) < count_scenarios(grid),
        "scenarios": [s["name"] for s in scenarios],
        "status": "running",
    }
    save_json(sweep_dir / "sweep_manifest.json", manifest)

    log_path = sweep_dir / "logs" / "sweep.log"
    base_params = get_default_params()
    completed = []
    failed = []

    print(f"Sweep directory: {sweep_dir}")
    print(f"Factor grid ({count_scenarios(grid)} full factorial combinations):")
    for key, values in grid.items():
        print(f"  {key}: {values}")
    print(f"Running {len(scenarios)} scenario(s)...\n")

    with open(log_path, "a", encoding="utf-8") as log:
        for i, factors in enumerate(scenarios, start=1):
            name = factors["name"]
            line = f"[{i}/{len(scenarios)}] {name}"
            print(line)
            log.write(line + "\n")
            log.flush()

            params = apply_factors(base_params, factors)
            save_json(sweep_dir / "configs" / f"{name}.json", factors)

            try:
                summary = run_single_experiment(params)
                record = merge_result(factors, summary)
                save_json(sweep_dir / "results" / f"{name}_summary.json", record)
                completed.append(name)
                print(
                    f"   objective={summary.get('objective', 0):.0f} | "
                    f"deployed={summary.get('deployed_facilities', [])} | "
                    f"unmet={summary.get('unmet_demand_pct', 0):.1f}%\n"
                )
            except Exception as exc:
                failed.append({"scenario": name, "error": str(exc)})
                print(f"   FAILED: {exc}\n")
                log.write(traceback.format_exc() + "\n")
                log.flush()

    manifest["status"] = "completed"
    manifest["completed"] = completed
    manifest["failed"] = failed
    save_json(sweep_dir / "sweep_manifest.json", manifest)

    print(f"Sweep finished: {len(completed)} ok, {len(failed)} failed")
    print(f"Results → {sweep_dir}")

    if analyze_after and completed:
        print("\nRunning post-sweep analysis and report generation...")
        from experiment_scripts.analyze_sweep import analyze_sweep
        analyze_sweep(sweep_dir)

    return sweep_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Factorial CSAM deployment sweep")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Use a small pilot factor grid (4 scenarios)",
    )
    parser.add_argument(
        "--max-scenarios",
        type=int,
        default=None,
        help="Cap number of scenarios (truncates factorial order)",
    )
    parser.add_argument(
        "--sweep-name",
        type=str,
        default=None,
        help="Suffix for sweep folder name",
    )
    parser.add_argument(
        "--no-analyze",
        action="store_true",
        help="Skip post-sweep analysis and report generation",
    )
    args = parser.parse_args()
    run_sweep(
        quick=args.quick,
        max_scenarios=args.max_scenarios,
        sweep_name=args.sweep_name,
        analyze_after=not args.no_analyze,
    )


if __name__ == "__main__":
    main()
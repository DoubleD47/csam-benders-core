"""
Benders iteration sensitivity study.

Useful now that dual-based optimality cuts are implemented — shows how many
master iterations are needed for convergence at a fixed parameter setting.

Usage:
  python -m experiment_scripts.iterations_study
  python -m experiment_scripts.iterations_study --max-iters 5 10 20 30
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from model.parameters import get_default_params
from experiment_scripts.run_single import run_single_experiment


def run_iteration_study(max_iters_list: list[int] | None = None) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_iteration_study")
    study_dir = Path("experiments") / "sweeps" / timestamp
    (study_dir / "results").mkdir(parents=True, exist_ok=True)
    (study_dir / "visualizations").mkdir(exist_ok=True)

    base_params = get_default_params()
    base_params["MAX_CSAM_FACILITIES"] = 3
    base_params["SEED"] = 456
    base_params["EXPERIMENT_NAME"] = "iteration_study"

    max_iters_list = max_iters_list or [5, 10, 15, 20, 30]
    results = []

    for max_iters in max_iters_list:
        print(f"\n=== MAX_ITER = {max_iters} ===")
        params = base_params.copy()
        params["MAX_ITER"] = max_iters
        params["scenario_name"] = f"maxiter_{max_iters}"

        summary = run_single_experiment(params)
        results.append(
            {
                "max_iter_setting": max_iters,
                "objective": summary.get("objective"),
                "actual_iterations": summary.get("iterations"),
                "deployed_count": summary.get("deployed_count"),
                "deployed_facilities": summary.get("deployed_facilities"),
                "unmet_demand_pct": summary.get("unmet_demand_pct"),
                "runtime_seconds": summary.get("runtime_seconds"),
                "run_id": summary.get("run_id"),
            }
        )

    out = study_dir / "results" / "iteration_study_summary.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nIteration study completed → {study_dir}")
    return study_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Benders iteration sensitivity study")
    parser.add_argument(
        "--max-iters",
        type=int,
        nargs="+",
        default=None,
        help="List of MAX_ITER values to test",
    )
    args = parser.parse_args()
    run_iteration_study(args.max_iters)


if __name__ == "__main__":
    main()
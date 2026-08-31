"""
Build a master CSV and site-frequency table from a factorial sweep.

Does not re-solve. Reads experiments/sweeps/<sweep>/results/*_summary.json.

Usage:
  python -m experiment_scripts.summarize_sweep
  python -m experiment_scripts.summarize_sweep --sweep-dir experiments/sweeps/2026-06-18_full_factorial
  python -m experiment_scripts.summarize_sweep --analyze
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiment_scripts.analyze_sweep import analyze_sweep, find_latest_sweep, load_sweep_results


MASTER_COLUMNS = [
    "scenario",
    "status",
    "feasible",
    "MAX_CSAM_FACILITIES",
    "demand_mean",
    "demand_variance",
    "F_cost",
    "SEED",
    "objective",
    "subproblem_cost",
    "deployment_cost",
    "deployed_count",
    "deployed_facilities",
    "budget_slack",
    "total_demand",
    "unmet_demand",
    "unmet_demand_pct",
    "unmet_in",
    "unmet_queue",
    "iterations",
    "runtime_seconds",
    "run_id",
    "experiment_dir",
]


def _site_frequency(df: pd.DataFrame) -> pd.DataFrame:
    """Count how often each site is chosen among feasible scenarios."""
    feasible = df[df["feasible"]] if "feasible" in df.columns else df
    n = len(feasible)
    counts: dict[str, int] = {}
    for deployed in feasible.get("deployed_facilities", pd.Series(dtype=object)):
        if not isinstance(deployed, list):
            continue
        for m in deployed:
            counts[m] = counts.get(m, 0) + 1
    rows = []
    for node, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        rows.append(
            {
                "node": node,
                "feasible_scenarios_deployed": count,
                "feasible_n": n,
                "deployment_pct": 100.0 * count / n if n else 0.0,
            }
        )
    return pd.DataFrame(rows)


def _master_table(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "deployed_facilities" in out.columns:
        out["deployed_facilities"] = out["deployed_facilities"].apply(
            lambda xs: ",".join(xs) if isinstance(xs, list) else ""
        )
    if {"MAX_CSAM_FACILITIES", "deployed_count"} <= set(out.columns):
        out["budget_slack"] = pd.to_numeric(out["MAX_CSAM_FACILITIES"], errors="coerce") - pd.to_numeric(
            out["deployed_count"], errors="coerce"
        )
    keep = [c for c in MASTER_COLUMNS if c in out.columns]
    extra = [c for c in out.columns if c not in keep and c not in ("objective_raw",)]
    return out[keep + extra]


def summarize_sweep(sweep_dir: Path | None = None, analyze: bool = False) -> Path:
    sweep_dir = Path(sweep_dir) if sweep_dir else find_latest_sweep()
    if sweep_dir is None or not sweep_dir.exists():
        raise FileNotFoundError("No sweep directory found under experiments/sweeps/")

    df = load_sweep_results(sweep_dir)
    viz_dir = sweep_dir / "visualizations"
    viz_dir.mkdir(exist_ok=True)

    master = _master_table(df)
    master_path = viz_dir / "sweep_results_table.csv"
    master.to_csv(master_path, index=False)

    freq = _site_frequency(df)
    freq_path = viz_dir / "site_frequency.csv"
    freq.to_csv(freq_path, index=False)

    n_feas = int(df["feasible"].sum()) if "feasible" in df.columns else len(df)
    print(f"Sweep: {sweep_dir}")
    print(f"Rows: {len(df)} | feasible: {n_feas} | infeasible: {len(df) - n_feas}")
    print(f"Master CSV → {master_path}")
    print(f"Site frequency → {freq_path}")
    if not freq.empty:
        print(freq.to_string(index=False))

    if analyze:
        analyze_sweep(sweep_dir)

    return viz_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Master CSV + site frequency for a CSAM sweep")
    parser.add_argument(
        "--sweep-dir",
        type=str,
        default=None,
        help="Path to sweep folder (default: latest under experiments/sweeps/)",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Also run analyze_sweep (figures + report) after writing tables",
    )
    args = parser.parse_args()
    summarize_sweep(args.sweep_dir, analyze=args.analyze)


if __name__ == "__main__":
    main()

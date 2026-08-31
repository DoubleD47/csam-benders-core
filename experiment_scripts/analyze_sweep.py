"""
Analyze a factorial sweep and generate publication-style figures.

Reads experiments/sweeps/<sweep>/results/*_summary.json, builds aggregate
tables, and writes visualizations to the sweep's visualizations/ folder.

Usage:
  python -m experiment_scripts.analyze_sweep
  python -m experiment_scripts.analyze_sweep --sweep-dir experiments/sweeps/2026-06-18_factorial_v1
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd

# Repo root on path for visualization_scripts import
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from visualization_scripts.sweep_plots import (
    build_summary_table,
    plot_demand_vs_repair_heatmap,
    plot_deployment_count_bars,
    plot_deployment_frequency,
    plot_movement_heatmap,
    plot_movement_sankey,
    plot_objective_by_factor,
    plot_repair_heatmap,
    plot_unmet_demand_bars,
)


def find_latest_sweep() -> Path | None:
    sweep_root = REPO_ROOT / "experiments" / "sweeps"
    if not sweep_root.exists():
        return None
    folders = [
        p for p in sweep_root.iterdir()
        if p.is_dir() and (p / "results").exists()
    ]
    folders = sorted(folders, key=lambda p: p.stat().st_mtime, reverse=True)
    return folders[0] if folders else None


def _is_finite_number(value) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def prepare_results_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Flag infeasible cells and keep raw objective separate from plottable cost.

    Benders writes objective=inf when no feasible subproblem (incumbent) was
    found. Those rows are not "zero unmet" and must not enter cost averages.
    """
    out = df.copy()
    raw = pd.to_numeric(out.get("objective"), errors="coerce")
    out["objective_raw"] = out.get("objective")
    finite_mask = raw.apply(_is_finite_number)
    out["feasible"] = finite_mask & (out.get("subproblem_cost").notna() if "subproblem_cost" in out.columns else True)
    out["status"] = out["feasible"].map({True: "feasible", False: "infeasible_no_incumbent"})
    out["objective"] = raw.where(out["feasible"])
    if "unmet_demand_pct" in out.columns:
        out.loc[~out["feasible"], "unmet_demand_pct"] = pd.NA
    if "deployed_count" in out.columns:
        out.loc[~out["feasible"], "deployed_count"] = pd.NA
        out.loc[~out["feasible"], "deployed_facilities"] = out.loc[~out["feasible"], "deployed_facilities"].apply(
            lambda _: []
        )
    return out


def load_sweep_results(sweep_dir: Path) -> pd.DataFrame:
    records = []
    results_dir = sweep_dir / "results"
    for path in sorted(results_dir.glob("*_summary.json")):
        with open(path, encoding="utf-8") as f:
            records.append(json.load(f))
    if not records:
        raise FileNotFoundError(f"No result files in {results_dir}")
    return prepare_results_frame(pd.DataFrame(records))


def load_flows(repo_root: Path, record: dict) -> pd.DataFrame:
    flow_files = record.get("flow_files") or {}
    regular = flow_files.get("regular")
    if not regular:
        return pd.DataFrame()
    path = repo_root / regular
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def aggregate_flows(df: pd.DataFrame, repo_root: Path) -> pd.DataFrame:
    frames = []
    feasible = df[df["feasible"]] if "feasible" in df.columns else df
    for _, row in feasible.iterrows():
        flows = load_flows(repo_root, row.to_dict())
        if not flows.empty:
            flows["scenario"] = row.get("scenario")
            frames.append(flows)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def analyze_sweep(sweep_dir: Path | None = None) -> Path:
    sweep_dir = Path(sweep_dir) if sweep_dir else find_latest_sweep()
    if sweep_dir is None or not sweep_dir.exists():
        raise FileNotFoundError("No sweep directory found under experiments/sweeps/")

    print(f"Analyzing sweep: {sweep_dir}\n")
    df = load_sweep_results(sweep_dir)
    n_feas = int(df["feasible"].sum()) if "feasible" in df.columns else len(df)
    n_inf = len(df) - n_feas
    print(f"Scenarios: {len(df)} | feasible: {n_feas} | infeasible (no incumbent): {n_inf}")

    viz_dir = sweep_dir / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    finite_df = df[df["feasible"]].copy() if "feasible" in df.columns else df

    # --- Summary tables ---
    table_path = build_summary_table(df, viz_dir)
    print(f"Results table → {table_path}")
    preview_cols = [c for c in ["scenario", "status", "objective", "deployed_count", "unmet_demand_pct"] if c in df.columns]
    print(df[preview_cols].head(10).to_string(index=False))

    # --- Factor-level objective plots (feasible cells only) ---
    for factor in ("MAX_CSAM_FACILITIES", "demand_mean", "demand_variance", "F_cost", "SEED"):
        p = plot_objective_by_factor(finite_df, factor, viz_dir)
        if p:
            print(f"Saved {p.name}")

    # --- Deployment & unmet demand bars ---
    plot_deployment_frequency(finite_df, viz_dir)
    plot_deployment_count_bars(finite_df, viz_dir)
    plot_unmet_demand_bars(finite_df, viz_dir)
    print("Saved deployment_frequency.png, deployment_count_by_scenario.png, unmet_demand_by_scenario.png")

    # --- Flow-based figures (aggregate + representative scenario) ---
    all_flows = aggregate_flows(df, REPO_ROOT)
    if not all_flows.empty:
        plot_repair_heatmap(all_flows, viz_dir, title_suffix=" (all scenarios)")
        plot_movement_heatmap(all_flows, viz_dir, title_suffix=" (all scenarios)")
        sankey = plot_movement_sankey(all_flows, viz_dir, title_suffix=" (all scenarios)")
        if sankey:
            print(f"Saved movement visualizations → {sankey}")

    # Representative: scenario with median finite objective
    if "objective" in finite_df.columns and len(finite_df) > 0:
        med_idx = (finite_df["objective"] - finite_df["objective"].median()).abs().idxmin()
        rep = finite_df.loc[med_idx]
        rep_flows = load_flows(REPO_ROOT, rep.to_dict())
        if not rep_flows.empty:
            plot_repair_heatmap(rep_flows, viz_dir, title_suffix=f" ({rep['scenario']})")
            plot_movement_heatmap(rep_flows, viz_dir, title_suffix=f" ({rep['scenario']})")
            plot_movement_sankey(rep_flows, viz_dir, title_suffix=f" ({rep['scenario']})")

            repair = rep_flows[rep_flows["to"] == "ss"].copy()
            repair["location"] = repair["from"].str.extract(r"(m\d+)")
            repair["commodity"] = repair["l"] + "/" + repair["k"]
            repair_pivot = repair.pivot_table(
                index="location", columns="commodity", values="flow", aggfunc="sum", fill_value=0
            )
            # Demand proxy from source injection in flows
            demand = rep_flows[rep_flows["from"] == "source"].copy()
            demand["location"] = demand["to"].str.extract(r"(m\d+)")
            demand["commodity"] = demand["l"] + "/" + demand["k"]
            demand_pivot = demand.pivot_table(
                index="location", columns="commodity", values="flow", aggfunc="sum", fill_value=0
            )
            plot_demand_vs_repair_heatmap(
                demand_pivot, repair_pivot, viz_dir, title_suffix=f" ({rep['scenario']})"
            )

    try:
        from experiment_scripts.report_utils import generate_sweep_report
        report_files = generate_sweep_report(sweep_dir)
        print(f"Sweep report → {report_files.get('markdown', '')}")
        if report_files.get("pdf"):
            print(f"Sweep PDF    → {report_files['pdf']}")
    except Exception as exc:
        print(f"Sweep report skipped: {exc}")

    print(f"\nAnalysis complete → {viz_dir}")
    return viz_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze factorial sweep results")
    parser.add_argument(
        "--sweep-dir",
        type=str,
        default=None,
        help="Path to sweep folder (default: latest under experiments/sweeps/)",
    )
    args = parser.parse_args()
    analyze_sweep(args.sweep_dir)


if __name__ == "__main__":
    main()

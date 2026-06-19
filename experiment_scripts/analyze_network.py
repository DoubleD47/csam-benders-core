"""
Inspect network structure for the latest single run or a sweep scenario.

Rebuilds the network from parameters, saves arc/node lists for inspection,
and optionally targets a specific sweep config.

Usage:
  python -m experiment_scripts.analyze_network
  python -m experiment_scripts.analyze_network --config experiments/sweeps/.../configs/csam3_dm10.0_ds1.0_F100_s456.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path

import pandas as pd

from model.parameters import get_default_params, generate_demand
from model.network import build_network
from experiment_scripts.sweep_utils import apply_factors


def analyze_network(output_dir: str | Path, params: dict) -> Path:
    output_dir = Path(output_dir)
    viz_dir = output_dir / "visualizations"
    viz_dir.mkdir(parents=True, exist_ok=True)

    C = [(l, k) for l in params["L"] for k in params["K"]]
    D = generate_demand(
        params["M"],
        params["T"],
        C,
        mean=params.get("demand_mean", 10.0),
        variance=params.get("demand_variance", 9.0),
        scale=params.get("demand_scale", 1.0),
        seed=params["SEED"],
    )
    net = build_network(
        params["M"],
        params["traditional_m_dict"],
        params["L"],
        params["K"],
        params["T"],
        D=D,
        seed=params["SEED"],
    )

    arcs_df = pd.DataFrame(net["regular_arcs"], columns=["from", "to", "t", "c"])
    arcs_df.to_csv(viz_dir / "arcs_list.csv", index=False)

    nodes_df = pd.DataFrame(net["nodes"], columns=["type", "t", "c"])
    nodes_df.to_csv(viz_dir / "nodes_list.csv", index=False)

    summary = {
        "nodes": len(net["nodes"]),
        "regular_arcs": len(net["regular_arcs"]),
        "qq_arcs": len(net["qq_arcs"]),
        "total_demand": sum(D.values()),
    }
    with open(viz_dir / "network_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Network: {summary['nodes']} nodes, {summary['regular_arcs']} regular arcs")
    print(f"Saved → {viz_dir}")
    return viz_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze network structure")
    parser.add_argument("--config", type=str, default=None, help="Sweep config JSON to rebuild from")
    parser.add_argument("--output-dir", type=str, default=None, help="Where to write inspection files")
    args = parser.parse_args()

    base = get_default_params()

    if args.config:
        with open(args.config, encoding="utf-8") as f:
            factors = json.load(f)
        params = apply_factors(base, factors)
        out = args.output_dir or Path("experiments") / "network_inspection" / factors["name"]
    else:
        # Latest single run
        runs = glob.glob("experiments/*run_maxCSAM*") + glob.glob("experiments/*sweep_*")
        if not runs:
            params = base
            out = args.output_dir or "experiments/network_inspection/default"
        else:
            latest = max(runs, key=os.path.getctime)
            out = args.output_dir or latest
            with open(Path(latest) / "summary.json", encoding="utf-8") as f:
                summary = json.load(f)
            params = base.copy()
            for key in ("MAX_CSAM_FACILITIES", "demand_mean", "demand_variance", "SEED", "F_cost"):
                if key in summary:
                    params[key] = summary[key]
            if "F_cost" in summary:
                params["F"] = {m: summary["F_cost"] for m in params["M"]}
            print(f"Using parameters from: {latest}")

    analyze_network(out, params)


if __name__ == "__main__":
    main()
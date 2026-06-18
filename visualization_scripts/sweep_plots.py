"""
Publication-style figures for factorial sweep analysis.

Called by experiment_scripts/analyze_sweep.py. Outputs PNG + CSV tables
into the sweep's visualizations/ folder.
"""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")


def _extract_node(label: str) -> str | None:
    """Extract main node id (m1..m10) from arc endpoint string."""
    match = re.match(r"(m\d+)", str(label))
    return match.group(1) if match else None


def plot_deployment_frequency(df: pd.DataFrame, out_dir: Path) -> Path:
    """Bar chart: how often each location is deployed across scenarios."""
    counts: dict[str, int] = {}
    for deployed in df.get("deployed_facilities", pd.Series(dtype=object)):
        if not isinstance(deployed, list):
            continue
        for m in deployed:
            counts[m] = counts.get(m, 0) + 1

    if not counts:
        return out_dir / "deployment_frequency.png"

    freq = pd.Series(counts).sort_values(ascending=False)
    freq.to_csv(out_dir / "deployment_frequency.csv", header=["count"])

    fig, ax = plt.subplots(figsize=(10, 5))
    freq.plot(kind="bar", ax=ax, color="steelblue", edgecolor="black")
    ax.set_title("CSAM Deployment Frequency Across Sweep Scenarios")
    ax.set_xlabel("Main Node")
    ax.set_ylabel("Scenarios Deployed")
    ax.set_ylim(0, len(df))
    fig.tight_layout()
    path = out_dir / "deployment_frequency.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def plot_objective_by_factor(df: pd.DataFrame, factor: str, out_dir: Path) -> Path | None:
    """Box/strip of objective grouped by a single factor level."""
    if factor not in df.columns or "objective" not in df.columns:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=df, x=factor, y="objective", ax=ax, color="lightgray")
    sns.stripplot(data=df, x=factor, y="objective", ax=ax, color="navy", alpha=0.5, size=4)
    ax.set_title(f"Objective by {factor}")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    path = out_dir / f"objective_by_{factor}.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def plot_deployment_count_bars(df: pd.DataFrame, out_dir: Path) -> Path:
    """Bar chart of deployed_count by scenario (sorted)."""
    plot_df = df.sort_values("deployed_count", ascending=False).head(30)
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(range(len(plot_df)), plot_df["deployed_count"], color="teal", edgecolor="black")
    ax.set_xticks(range(len(plot_df)))
    ax.set_xticklabels(plot_df["scenario"], rotation=60, ha="right", fontsize=7)
    ax.set_ylabel("CSAM Facilities Deployed")
    ax.set_title("Deployments per Scenario (top 30)")
    fig.tight_layout()
    path = out_dir / "deployment_count_by_scenario.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def plot_unmet_demand_bars(df: pd.DataFrame, out_dir: Path) -> Path:
    """Unmet demand % by scenario."""
    plot_df = df.sort_values("unmet_demand_pct", ascending=False).head(30)
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(range(len(plot_df)), plot_df["unmet_demand_pct"], color="indianred", edgecolor="black")
    ax.set_xticks(range(len(plot_df)))
    ax.set_xticklabels(plot_df["scenario"], rotation=60, ha="right", fontsize=7)
    ax.set_ylabel("Unmet Demand (%)")
    ax.set_title("Unmet Demand by Scenario (top 30)")
    fig.tight_layout()
    path = out_dir / "unmet_demand_by_scenario.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def plot_repair_heatmap(flows_df: pd.DataFrame, out_dir: Path, title_suffix: str = "") -> Path | None:
    """
    Heatmap: location x commodity — serviced repair volume (queue -> ss).
    """
    if flows_df.empty:
        return None

    repair = flows_df[flows_df["to"] == "ss"].copy()
    repair = repair[repair["from"].str.contains("_q_", na=False)]
    if repair.empty:
        return None

    repair["location"] = repair["from"].map(_extract_node)
    repair["commodity"] = repair["l"] + "/" + repair["k"]
    pivot = repair.pivot_table(
        index="location", columns="commodity", values="flow", aggfunc="sum", fill_value=0
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(pivot, ax=ax, cmap="YlOrRd", linewidths=0.3)
    ax.set_title(f"Repair Volume by Location & Commodity{title_suffix}")
    ax.set_xlabel("Commodity (l/k)")
    ax.set_ylabel("Location")
    fig.tight_layout()
    path = out_dir / f"repair_heatmap{title_suffix.replace(' ', '_')}.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    pivot.to_csv(out_dir / f"repair_by_location_commodity{title_suffix.replace(' ', '_')}.csv")
    return path


def plot_demand_vs_repair_heatmap(
    demand_by_loc_comm: pd.DataFrame,
    repair_by_loc_comm: pd.DataFrame,
    out_dir: Path,
    title_suffix: str = "",
) -> Path | None:
    """Side-by-side heatmaps: injected demand vs completed repair."""
    if demand_by_loc_comm.empty and repair_by_loc_comm.empty:
        return None

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    if not demand_by_loc_comm.empty:
        sns.heatmap(demand_by_loc_comm, ax=axes[0], cmap="Blues", linewidths=0.3)
        axes[0].set_title("Demand by Location & Commodity")
    if not repair_by_loc_comm.empty:
        sns.heatmap(repair_by_loc_comm, ax=axes[1], cmap="YlOrRd", linewidths=0.3)
        axes[1].set_title("Repair by Location & Commodity")
    fig.suptitle(f"Demand vs Repair{title_suffix}")
    fig.tight_layout()
    path = out_dir / f"demand_vs_repair{title_suffix.replace(' ', '_')}.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def plot_movement_heatmap(flows_df: pd.DataFrame, out_dir: Path, title_suffix: str = "") -> Path | None:
    """Location-to-location movement matrix (_in -> _in arcs)."""
    if flows_df.empty:
        return None

    move = flows_df[
        flows_df["from"].str.endswith("_in", na=False)
        & flows_df["to"].str.endswith("_in", na=False)
    ].copy()
    if move.empty:
        return None

    move["from_loc"] = move["from"].map(_extract_node)
    move["to_loc"] = move["to"].map(_extract_node)
    move = move.dropna(subset=["from_loc", "to_loc"])
    pivot = move.pivot_table(
        index="from_loc", columns="to_loc", values="flow", aggfunc="sum", fill_value=0
    )

    fig, ax = plt.subplots(figsize=(8, 7))
    sns.heatmap(pivot, ax=ax, cmap="Purples", linewidths=0.3)
    ax.set_title(f"Inter-Location Demand Movement{title_suffix}")
    fig.tight_layout()
    path = out_dir / f"movement_heatmap{title_suffix.replace(' ', '_')}.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    pivot.to_csv(out_dir / f"movement_matrix{title_suffix.replace(' ', '_')}.csv")
    return path


def plot_movement_sankey(flows_df: pd.DataFrame, out_dir: Path, title_suffix: str = "") -> Path | None:
    """Sankey diagram for inter-location _in -> _in flows (requires plotly)."""
    if flows_df.empty:
        return None

    move = flows_df[
        flows_df["from"].str.endswith("_in", na=False)
        & flows_df["to"].str.endswith("_in", na=False)
    ].copy()
    if move.empty:
        return None

    move["from_loc"] = move["from"].map(_extract_node)
    move["to_loc"] = move["to"].map(_extract_node)
    agg = (
        move.groupby(["from_loc", "to_loc"], as_index=False)["flow"]
        .sum()
        .sort_values("flow", ascending=False)
        .head(40)
    )
    agg.to_csv(out_dir / f"movement_edges{title_suffix.replace(' ', '_')}.csv", index=False)

    try:
        import plotly.graph_objects as go
    except ImportError:
        return out_dir / f"movement_edges{title_suffix.replace(' ', '_')}.csv"

    nodes = sorted(set(agg["from_loc"]) | set(agg["to_loc"]))
    idx = {n: i for i, n in enumerate(nodes)}
    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(label=nodes, pad=15, thickness=20),
                link=dict(
                    source=[idx[r.from_loc] for r in agg.itertuples()],
                    target=[idx[r.to_loc] for r in agg.itertuples()],
                    value=agg["flow"].tolist(),
                ),
            )
        ]
    )
    fig.update_layout(title_text=f"Demand Movement Between Locations{title_suffix}")
    path = out_dir / f"movement_sankey{title_suffix.replace(' ', '_')}.html"
    fig.write_html(str(path))
    return path


def build_summary_table(df: pd.DataFrame, out_dir: Path) -> Path:
    """Aggregate statistics table across all scenarios."""
    numeric_cols = [
        "objective",
        "deployed_count",
        "unmet_demand_pct",
        "runtime_seconds",
        "iterations",
    ]
    rows = []
    for col in numeric_cols:
        if col not in df.columns:
            continue
        rows.append(
            {
                "metric": col,
                "mean": df[col].mean(),
                "std": df[col].std(),
                "min": df[col].min(),
                "max": df[col].max(),
            }
        )

    # Deployment frequency per node
    all_deployments = []
    for deployed in df.get("deployed_facilities", pd.Series(dtype=object)):
        if isinstance(deployed, list):
            all_deployments.extend(deployed)
    if all_deployments:
        freq = pd.Series(all_deployments).value_counts(normalize=True) * 100
        freq_df = freq.reset_index()
        freq_df.columns = ["node", "deployment_pct"]
        freq_df.to_csv(out_dir / "deployment_pct_by_node.csv", index=False)

    stats = pd.DataFrame(rows)
    stats.to_csv(out_dir / "summary_statistics.csv", index=False)

    # Per-scenario master table
    keep = [
        c
        for c in [
            "scenario",
            "MAX_CSAM_FACILITIES",
            "demand_mean",
            "demand_scale",
            "F_cost",
            "SEED",
            "objective",
            "deployed_count",
            "deployed_facilities",
            "unmet_demand_pct",
            "total_demand",
            "iterations",
            "runtime_seconds",
            "experiment_dir",
        ]
        if c in df.columns
    ]
    df[keep].to_csv(out_dir / "sweep_results_table.csv", index=False)
    return out_dir / "sweep_results_table.csv"
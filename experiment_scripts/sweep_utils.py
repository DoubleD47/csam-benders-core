"""
Shared helpers for factorial parameter sweeps.

Factor grid keys:
  - MAX_CSAM_FACILITIES: deployment budget (master problem)
  - demand_mean: center of uniform demand draw (see generate_demand)
  - demand_scale: multiplier on demand range
  - F_cost: uniform CSAM opening cost applied to every main node
  - SEED: RNG seed for demand generation
"""

from __future__ import annotations

import copy
import itertools
import json
from datetime import datetime
from pathlib import Path
from typing import Any


# Pilot grid — F_cost sensitivity (5 scenarios) for tuning opening-cost range before full factorial
QUICK_FACTOR_GRID: dict[str, list[Any]] = {
    "MAX_CSAM_FACILITIES": [3],
    "demand_mean": [10.0],
    "demand_scale": [1.0],
    "F_cost": [25, 50, 100, 200, 400],
    "SEED": [456],
}

# Publication-style grid — adjust before long runs; full product can be large
DEFAULT_FACTOR_GRID: dict[str, list[Any]] = {
    "MAX_CSAM_FACILITIES": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "demand_mean": [8.0, 10.0, 12.0],
    "demand_scale": [0.8, 1.0, 1.2],
    "F_cost": [25, 50, 100, 200, 400],  # tuned from quick F sensitivity runs
    "SEED": [42, 123, 456, 789, 1011],
}


def get_factor_grid(quick: bool = False) -> dict[str, list[Any]]:
    return copy.deepcopy(QUICK_FACTOR_GRID if quick else DEFAULT_FACTOR_GRID)


def count_scenarios(grid: dict[str, list[Any]]) -> int:
    n = 1
    for values in grid.values():
        n *= len(values)
    return n


def scenario_name(factors: dict[str, Any]) -> str:
    """Compact, filesystem-safe scenario identifier."""
    return (
        f"csam{factors['MAX_CSAM_FACILITIES']}"
        f"_dm{factors['demand_mean']}"
        f"_ds{factors['demand_scale']}"
        f"_F{factors['F_cost']}"
        f"_s{factors['SEED']}"
    )


def build_scenarios(
    grid: dict[str, list[Any]],
    max_scenarios: int | None = None,
) -> list[dict[str, Any]]:
    """Full factorial over grid keys (itertools.product)."""
    keys = list(grid.keys())
    scenarios = []
    for combo in itertools.product(*(grid[k] for k in keys)):
        factors = dict(zip(keys, combo))
        factors["name"] = scenario_name(factors)
        scenarios.append(factors)
        if max_scenarios is not None and len(scenarios) >= max_scenarios:
            break
    return scenarios


def apply_factors(base_params: dict[str, Any], factors: dict[str, Any]) -> dict[str, Any]:
    """Deep-copy base params and apply sweep factor levels."""
    params = copy.deepcopy(base_params)
    params["MAX_CSAM_FACILITIES"] = factors["MAX_CSAM_FACILITIES"]
    params["demand_mean"] = factors["demand_mean"]
    params["demand_scale"] = factors["demand_scale"]
    params["SEED"] = factors["SEED"]
    params["F_cost"] = factors["F_cost"]
    params["F"] = {m: factors["F_cost"] for m in params["M"]}
    params["scenario_name"] = factors["name"]
    params["EXPERIMENT_NAME"] = f"sweep_{factors['name']}"
    return params


def create_sweep_dir(sweep_name: str | None = None) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d")
    suffix = sweep_name or "factorial_v1"
    sweep_dir = Path("experiments") / "sweeps" / f"{timestamp}_{suffix}"
    for sub in ("configs", "results", "logs", "visualizations", "reports"):
        (sweep_dir / sub).mkdir(parents=True, exist_ok=True)
    return sweep_dir


def save_json(path: Path, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def merge_result(config: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    """Combine sweep config with solver summary for analysis."""
    return {
        "scenario": config.get("name"),
        "MAX_CSAM_FACILITIES": config.get("MAX_CSAM_FACILITIES"),
        "demand_mean": config.get("demand_mean"),
        "demand_scale": config.get("demand_scale"),
        "F_cost": config.get("F_cost"),
        "SEED": config.get("SEED"),
        **summary,
    }
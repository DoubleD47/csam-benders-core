# CSAM Deployment Optimization via Benders Decomposition

This project solves a multi-period facility deployment problem for **Cold-Spray Additive Manufacturing (CSAM)** mobile repair units that supplement existing traditional repair infrastructure. The model uses **Benders decomposition** with dual-based optimality cuts on a time-expanded network flow formulation.

---

## Model Overview

The problem routes repair demand of type **(l, k)** across a network of main nodes (traditional repair sites).

| Symbol | Meaning |
|--------|---------|
| `l1` | Flexible repair — CSAM or matching traditional site |
| `l2` | Restricted repair — must use the designated traditional facility |
| `k` | Repair class (k1–k5) |
| `y_m` | Binary: deploy mobile CSAM at main node `m` |

Demand enters at main nodes, can move between locations, queues for service, carries over across periods, and can be written off at differentiated penalties in the final period.

**Repair costs** (configurable in `model/parameters.py`):

- `C_service_l1` — cold spray / CSAM repair (`q_l1 → ss`)
- `C_service_l2` — traditional repair (`q_l2 → ss`)

---

## Project Structure

```
csam-benders-core/
├── model/
│   ├── parameters.py      # Default parameters & demand generation
│   ├── network.py         # Time-expanded network builder
│   └── core.py            # Benders master/subproblem solver
├── experiment_scripts/
│   ├── run_single.py      # Single experiment
│   ├── run_sweep.py       # Factorial parameter sweep
│   ├── analyze_sweep.py   # Aggregate analysis + figures
│   ├── sweep_report.py    # Standalone sweep report generator
│   ├── report_utils.py    # Markdown/PDF report helpers
│   ├── sweep_utils.py     # Factor grids & scenario naming
│   ├── analyze_network.py # Network structure inspection
│   └── iterations_study.py
├── visualization_scripts/
│   ├── network_viz.py     # Static network diagram
│   └── sweep_plots.py     # Sweep figures (called by analyze_sweep)
├── experiments/
│   ├── <run_id>/          # Per-run outputs (single or sweep scenario)
│   └── sweeps/
│       └── YYYY-MM-DD_<name>/
│           ├── configs/
│           ├── results/
│           ├── logs/
│           ├── visualizations/
│           └── reports/
├── requirements.txt
└── README.md
```

---

## Setup

```bash
git clone https://github.com/DoubleD47/csam-benders-core.git
cd csam-benders-core

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
```

Set `PYTHONPATH` to the repo root if imports fail:

```bash
# Windows PowerShell
$env:PYTHONPATH="C:\path\to\csam-benders-core"

# Linux/Mac
export PYTHONPATH=/path/to/csam-benders-core
```

---

## Single Experiment

```bash
python -m experiment_scripts.run_single \
  --max_csam 3 \
  --seed 456 \
  --demand_scale 1.0 \
  --demand_mean 10.0 \
  --F_cost 100
```

**Outputs** in `experiments/<timestamp>_run_maxCSAM<N>/`:

| File | Description |
|------|-------------|
| `summary.json` | Objective, deployments, unmet demand %, flow paths |
| `full_log.txt` | Complete solver log |
| `visualizations/flows_regular.csv` | Non-zero arc flows |
| `visualizations/flows_qq.csv` | Queue carry-over flows |
| `reports/run_report.md` | Human-readable run summary |
| `reports/run_report.pdf` | PDF version (requires `fpdf2`) |

Edit default parameters in `model/parameters.py` (`T`, `MAX_ITER`, costs, capacities).

**Time periods (`T`):** `T = [1, 2, …, 12]` models **12 weekly periods** (one quarter). Demand is injected each week; service can occur each week. Queue carry-over arcs link consecutive weeks only (`t → t+1`), so 12 periods imply **11 carry-over intervals** — that is expected and does not mean you are missing a week. You do **not** need `T=0` unless you want a separate “week zero” pre-positioning period. For an 11-week horizon, use `T = list(range(1, 12))`.

---

## Factorial Parameter Sweep

Sweeps vary these factors (defined in `experiment_scripts/sweep_utils.py`):

- `MAX_CSAM_FACILITIES` — deployment budget (1–10 in full grid)
- `demand_mean` — center of demand draw
- `demand_scale` — demand multiplier
- `F_cost` — uniform CSAM opening cost
- `SEED` — RNG seed

```bash
# Pilot sweep (4 scenarios) — recommended first
python -m experiment_scripts.run_sweep --quick --sweep-name quick

# Truncated factorial
python -m experiment_scripts.run_sweep --max-scenarios 20 --sweep-name pilot_study

# Full factorial (1,350 scenarios with default grid — long run!)
python -m experiment_scripts.run_sweep --sweep-name full_factorial
```

By default, `run_sweep` automatically runs `analyze_sweep` (figures + sweep report) when scenarios complete. Use `--no-analyze` to skip.

**Sweep outputs** in `experiments/sweeps/<timestamp>_<name>/`:

| Path | Description |
|------|-------------|
| `configs/<scenario>.json` | Input parameters per scenario |
| `results/<scenario>_summary.json` | Merged config + solver summary |
| `sweep_manifest.json` | Factor grid, scenario list, pass/fail |
| `visualizations/*.png` | Bar charts, heatmaps, factor plots |
| `visualizations/sweep_results_table.csv` | Master results table |
| `reports/sweep_report.md` | Aggregate sweep report |
| `reports/sweep_report.pdf` | PDF with embedded figures |

Each scenario also creates its own folder under `experiments/<run_id>/` with per-run reports.

---

## Analysis & Reports

```bash
# Analyze latest sweep (figures + Markdown/PDF report)
python -m experiment_scripts.analyze_sweep

# Analyze a specific sweep folder
python -m experiment_scripts.analyze_sweep \
  --sweep-dir experiments/sweeps/2026-06-18_quick

# Regenerate sweep report only
python -m experiment_scripts.sweep_report --analyze-first

# Inspect network structure
python -m experiment_scripts.analyze_network
```

**Figures produced by `analyze_sweep`:**

- Deployment frequency across scenarios
- Objective by factor level (MAX_CSAM, demand_scale, F_cost, seed)
- Unmet demand % by scenario
- Repair heatmap (location × commodity)
- Inter-location movement heatmap + Sankey diagram (HTML)
- Demand vs. repair side-by-side heatmap (representative scenario)

---

## Other Scripts

```bash
# Benders iteration sensitivity (now meaningful with optimality cuts)
python -m experiment_scripts.iterations_study

# Deprecated wrapper — redirects to run_sweep --quick
python -m experiment_scripts.run_complex_sweep

# Static network diagram (one period)
python -m visualization_scripts.network_viz
```

---

## Key Features

- Time-expanded multi-commodity network flow
- Flexible l1 vs. restricted l2 repair routing
- Differentiated write-off costs (`C_dummy_in`, `C_dummy_queue`)
- Differentiated repair costs (`C_service_l1`, `C_service_l2`)
- Queue carry-over penalties
- Benders decomposition with dual-based optimality cuts on l1 capacity
- Factorial sweeps with publication-style figures and Markdown/PDF reports

---

## Tuning the Factor Grid

Edit `QUICK_FACTOR_GRID` and `DEFAULT_FACTOR_GRID` in `experiment_scripts/sweep_utils.py` before large runs. The default full factorial is **1,350 scenarios** — always pilot with `--quick` first.

---

## License & Citation

See repository for license details. If you use this code in academic work, please cite the associated research project.
"""
DEPRECATED — use run_sweep.py instead.

This script was an early prototype for multi-dimensional sweeps over
MAX_CSAM × U_l1 × C_dummy before the model had dual-based optimality cuts
and before sweep_utils standardized factorial storage.

Kept as a thin wrapper so old muscle memory still works:
  python -m experiment_scripts.run_complex_sweep
"""

from experiment_scripts.run_sweep import run_sweep


def run_complex_sweep():
    print("Note: run_complex_sweep is deprecated. Using run_sweep with --quick.\n")
    return run_sweep(quick=True, sweep_name="legacy_complex_sweep")


if __name__ == "__main__":
    run_complex_sweep()
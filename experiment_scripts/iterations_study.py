import json
import os
from datetime import datetime
from model.parameters import get_default_params
from experiment_scripts.run_single import run_single_experiment

def run_iteration_study():
    timestamp = datetime.now().strftime("%Y-%m-%d_iteration_study")
    study_dir = f"experiments/sweeps/{timestamp}"
    
    os.makedirs(f"{study_dir}/results", exist_ok=True)
    os.makedirs(f"{study_dir}/visualizations", exist_ok=True)
    
    base_params = get_default_params()
    base_params["MAX_CSAM_FACILITIES"] = 5
    base_params["U_l1"] = 100
    base_params["C_dummy"] = 5000
    
    max_iters_list = [5, 10, 20, 30, 50, 100]
    results = []
    
    for max_iters in max_iters_list:
        print(f"\n=== Testing Max Iterations = {max_iters} ===")
        params = base_params.copy()
        params["MAX_BENDERS_ITERATIONS"] = max_iters   # You may need to add this control in core.py
        
        summary = run_single_experiment(params)
        
        results.append({
            "max_iterations": max_iters,
            "objective": summary.get("objective"),
            "actual_iterations": summary.get("iterations", "?"),
            "deployed": summary.get("deployed_count", 0),
            "runtime": summary.get("runtime_seconds", 0)
        })
    
    # Save results
    with open(f"{study_dir}/results/iteration_study_summary.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nIteration study completed → {study_dir}")
    return results

if __name__ == "__main__":
    run_iteration_study()
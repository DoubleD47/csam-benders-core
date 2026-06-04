import json
import os
from datetime import datetime
from model.parameters import get_default_params
from experiment_scripts.run_single import run_single_experiment

def run_sweep():
    timestamp = datetime.now().strftime("%Y-%m-%d_sweep_v1")
    sweep_base = f"experiments/sweeps/{timestamp}"
    
    os.makedirs(f"{sweep_base}/configs", exist_ok=True)
    os.makedirs(f"{sweep_base}/results", exist_ok=True)
    os.makedirs(f"{sweep_base}/visualizations", exist_ok=True)

    base_params = get_default_params()
    
    scenarios = [
        {"name": "low",  "MAX_CSAM_FACILITIES": 2,  "U_l1": 60,   "C_dummy": 3000,  "demand_scale": 1.0},
        {"name": "med",  "MAX_CSAM_FACILITIES": 5,  "U_l1": 100,  "C_dummy": 6000,  "demand_scale": 1.0},
        {"name": "high", "MAX_CSAM_FACILITIES": 8,  "U_l1": 160,  "C_dummy": 12000, "demand_scale": 1.2},
    ]
    
    print(f"Starting sweep with {len(scenarios)} scenarios...\n")
    
    for scen in scenarios:
        params = base_params.copy()
        params.update(scen)
        params['EXPERIMENT_NAME'] = f"sweep_{scen['name']}"
        
        print(f"=== Running {scen['name']} ===")
        summary = run_single_experiment(params)
        
        # Save config and result
        with open(f"{sweep_base}/configs/{scen['name']}.json", "w") as f:
            json.dump(params, f, indent=2)
        
        with open(f"{sweep_base}/results/{scen['name']}_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"   Objective: {summary.get('objective', 'N/A'):.0f} | Deployed: {summary.get('deployed_count', 0)}\n")
    
    print(f"\nSweep completed! Results saved in: {sweep_base}")
    return sweep_base

if __name__ == "__main__":
    run_sweep()
import json
import os
from datetime import datetime
from model.parameters import get_default_params
# from experiment_scripts.run_single import solve_benders   # adjust import as needed

def run_sweep():
    timestamp = datetime.now().strftime("%Y-%m-%d_sweep_v1")
    sweep_dir = f"experiments/sweeps/{timestamp}"
    
    os.makedirs(f"{sweep_dir}/configs", exist_ok=True)
    os.makedirs(f"{sweep_dir}/results", exist_ok=True)
    os.makedirs(f"{sweep_dir}/logs", exist_ok=True)
    os.makedirs(f"{sweep_dir}/visualizations", exist_ok=True)
    
    base_params = get_default_params()
    
    scenarios = [
        {"name": "low",  "MAX_CSAM_FACILITIES": 2,  "U_l1": 60,   "C_dummy": 3000},
        {"name": "med",  "MAX_CSAM_FACILITIES": 5,  "U_l1": 100,  "C_dummy": 6000},
        {"name": "high", "MAX_CSAM_FACILITIES": 8,  "U_l1": 160,  "C_dummy": 10000},
    ]
    
    for scen in scenarios:
        params = base_params.copy()
        params.update(scen)
        params['EXPERIMENT_NAME'] = f"{scen['name']}"
        
        print(f"\n=== Running {scen['name']} scenario ===")
        
        # TODO: Call your solver here and capture summary
        # summary = solve_benders(params)
        
        # For now, placeholder:
        summary = {"objective": 999999, "deployed_count": 0, **scen}
        
        # Save config
        with open(f"{sweep_dir}/configs/{scen['name']}.json", "w") as f:
            json.dump(params, f, indent=2)
        
        # Save result
        with open(f"{sweep_dir}/results/{scen['name']}_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
    
    print(f"\nSweep completed! Results in: {sweep_dir}")

if __name__ == "__main__":
    run_sweep()
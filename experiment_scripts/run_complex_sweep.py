import json
import os
from datetime import datetime
from model.parameters import get_default_params
# Adjust this import to match your current run_single structure
from experiment_scripts.run_single import run_single_experiment  

def run_complex_sweep():
    timestamp = datetime.now().strftime("%Y-%m-%d_complex_sweep_v1")
    sweep_dir = f"experiments/sweeps/{timestamp}"
    
    os.makedirs(f"{sweep_dir}/configs", exist_ok=True)
    os.makedirs(f"{sweep_dir}/results", exist_ok=True)
    os.makedirs(f"{sweep_dir}/logs", exist_ok=True)
    os.makedirs(f"{sweep_dir}/visualizations", exist_ok=True)
    
    base_params = get_default_params()
    
    scenarios = []
    
    # Multi-dimensional sweep
    for max_csam in [3, 6, 10]:
        for u_l1 in [50, 100, 200]:
            for c_dummy in [2000, 5000, 15000]:
                name = f"csam{max_csam}_u{u_l1}_cd{c_dummy}"
                scenarios.append({
                    "name": name,
                    "MAX_CSAM_FACILITIES": max_csam,
                    "U_l1": u_l1,
                    "C_dummy": c_dummy,
                    "T": [1,2,3,4]   # You can vary this too
                })
    
    print(f"Running {len(scenarios)} scenarios...")
    
    for i, scen in enumerate(scenarios):
        print(f"\n--- Scenario {i+1}/{len(scenarios)}: {scen['name']} ---")
        params = base_params.copy()
        params.update(scen)
        
        summary = run_single_experiment(params)   # Your existing runner
        
        # Save files
        with open(f"{sweep_dir}/configs/{scen['name']}.json", "w") as f:
            json.dump(params, f, indent=2)
        
        with open(f"{sweep_dir}/results/{scen['name']}_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
    
    print(f"\nComplex sweep completed! → {sweep_dir}")
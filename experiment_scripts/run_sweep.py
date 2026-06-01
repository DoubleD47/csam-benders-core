import json
from model.parameters import get_default_params
from scripts.run_single import solve_benders  # adjust import if needed

def run_small_sweep():
    base_params = get_default_params()
    
    scenarios = [
        {"MAX_CSAM_FACILITIES": 2, "U_l1": 60,  "C_dummy": 3000, "name": "low"},
        {"MAX_CSAM_FACILITIES": 5, "U_l1": 100, "C_dummy": 6000, "name": "med"},
        {"MAX_CSAM_FACILITIES": 8, "U_l1": 160, "C_dummy": 10000, "name": "high"},
    ]
    
    results = []
    for scen in scenarios:
        params = base_params.copy()
        params.update(scen)
        params['EXPERIMENT_NAME'] = f"sweep_{scen['name']}"
        
        print(f"\n=== Running {scen['name']} scenario ===")
        summary = solve_benders(params)  # or however you call it
        
        results.append({
            "scenario": scen['name'],
            "max_csam": scen["MAX_CSAM_FACILITIES"],
            "u_l1": scen["U_l1"],
            "c_dummy": scen["C_dummy"],
            "objective": summary.get("objective"),
            "deployed": summary.get("deployed_count"),
            "deployed_list": summary.get("deployed_facilities")
        })
    
    with open("experiments/sweep_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nSweep completed. Results saved to sweep_results.json")

if __name__ == "__main__":
    run_small_sweep()
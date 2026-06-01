import json
import glob
import pandas as pd
from datetime import datetime

def analyze_latest_sweep():
    sweep_folders = sorted(glob.glob("experiments/sweeps/*"), reverse=True)
    if not sweep_folders:
        print("No sweep folders found.")
        return
    
    latest = sweep_folders[0]
    print(f"Analyzing latest sweep: {latest}\n")
    
    results = []
    for res_file in glob.glob(f"{latest}/results/*_summary.json"):
        with open(res_file, 'r') as f:
            data = json.load(f)
        results.append({
            "scenario": data.get("name", "unknown"),
            "max_csam": data.get("MAX_CSAM_FACILITIES"),
            "u_l1": data.get("U_l1"),
            "c_dummy": data.get("C_dummy"),
            "objective": round(data.get("objective", float('inf')), 2),
            "deployed": data.get("deployed_count", 0),
        })
    
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    df.to_csv(f"{latest}/visualizations/sweep_summary_{timestamp}.csv", index=False)
    print(f"\nSummary saved in {latest}/visualizations/")

if __name__ == "__main__":
    analyze_latest_sweep()
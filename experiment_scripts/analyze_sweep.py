import json
import glob
import pandas as pd
from datetime import datetime

def analyze_sweep(experiment_pattern="sweep_*"):
    """
    Analyze all sweep experiments.
    We can change the pattern to be more specific if needed.
    """
    results = []
    
    # Find all sweep-related experiment folders
    folders = glob.glob(f"experiments/*{experiment_pattern}*")
    
    print(f"Found {len(folders)} experiment folders matching pattern '{experiment_pattern}'\n")
    
    for folder in sorted(folders):
        try:
            summary_path = f"{folder}/summary.json"
            with open(summary_path, 'r') as f:
                data = json.load(f)
            
            run_id = data.get("run_id", folder.split("\\")[-1])
            
            results.append({
                "run_id": run_id,
                "scenario": data.get("scenario", "unknown"),
                "max_csam": data.get("max_csam_facilities", "?"),
                "u_l1": data.get("u_l1", "?"),           # Add if you store it
                "c_dummy": data.get("c_dummy", "?"),
                "objective": round(data.get("objective", float('inf')), 2),
                "deployed_count": data.get("deployed_count", 0),
                "deployed_facilities": data.get("deployed_facilities", []),
                "iterations": data.get("iterations", "?"),
                "runtime_seconds": round(data.get("runtime_seconds", 0), 2)
            })
        except Exception as e:
            print(f"  Warning: Could not read {folder}/summary.json — {e}")
    
    if not results:
        print("No results found.")
        return
    
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    
    # Save outputs
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    df.to_csv(f"experiments/sweep_summary_{timestamp}.csv", index=False)
    df.to_json(f"experiments/sweep_summary_{timestamp}.json", orient="records", indent=2)
    
    print(f"\nSummary saved to:")
    print(f"   experiments/sweep_summary_{timestamp}.csv")
    print(f"   experiments/sweep_summary_{timestamp}.json")

if __name__ == "__main__":
    analyze_sweep()          # default: all sweep_* folders
    # analyze_sweep("low")   # example: only low scenarios
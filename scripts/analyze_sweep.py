import json
import glob
import pandas as pd

def analyze_sweep():
    results = []
    for folder in glob.glob("experiments/*sweep_*"):
        try:
            with open(f"{folder}/summary.json") as f:
                data = json.load(f)
            results.append({
                "scenario": data["run_id"],
                "max_csam": data.get("max_csam_facilities", "?"),
                "objective": data["objective"],
                "deployed": data["deployed_count"],
                "facilities": data.get("deployed_facilities", [])
            })
        except:
            pass
    
    df = pd.DataFrame(results)
    print(df)
    df.to_csv("experiments/sweep_summary.csv", index=False)
    print("\nSummary saved to sweep_summary.csv")

if __name__ == "__main__":
    analyze_sweep()
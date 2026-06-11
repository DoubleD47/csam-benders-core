import json
from model.parameters import get_default_params
from model.network import build_network
import pandas as pd

#This script is for analyzing the network structure of the latest experiment run, especially after changes to the network construction logic. It rebuilds the network and saves an arc list for inspection.

def analyze_latest_run():
    # Find latest experiment
    import glob
    latest = max(glob.glob("experiments/*run_maxCSAM*"), key=os.path.getctime)
    print(f"Analyzing: {latest}")

    # Rebuild network for inspection
    params = get_default_params()
    C = [(l, k) for l in params['L'] for k in params['K']]
    D = generate_demand(params['M'], params['T'], C, scale=2.0)
    net = build_network(params['M'], params['traditional_m_dict'], params['L'], params['K'], params['T'], D=D)

    # Save arc list for inspection
    arcs_df = pd.DataFrame(net['regular_arcs'], columns=['from', 'to', 't', 'c'])
    arcs_df.to_csv(f"{latest}/visualizations/arcs_list.csv", index=False)
    print(f"Saved {len(arcs_df)} arcs to visualizations/arcs_list.csv")

    # Node summary
    nodes_df = pd.DataFrame(net['nodes'], columns=['type', 't', 'c'])
    print(nodes_df['type'].value_counts())

if __name__ == "__main__":
    analyze_latest_run()
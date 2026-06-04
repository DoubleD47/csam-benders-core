import argparse
import os
from datetime import datetime
from model.parameters import get_default_params, generate_demand
from model.network import build_network
from model.core import solve_benders

def run_single_experiment(params=None):
    if params is None:
        params = get_default_params()
    
    # Apply command-line style overrides if passed as dict
    experiment_name = params.get('EXPERIMENT_NAME', "default_run")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = f"experiments/{timestamp}_{experiment_name}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate demand
    C = [(l, k) for l in params['L'] for k in params['K']]
    D = generate_demand(
        params['M'], 
        params['T'], 
        C,
        mean=params.get('demand_mean', 10.0),
        scale=params.get('demand_scale', 1.0),
        seed=params['SEED']
    )
    
    # Build network
    net = build_network(
        params['M'],
        params['traditional_m_dict'],
        params['L'],
        params['K'],
        params['T'],
        D=D,
        seed=params['SEED']
    )
    
    # Solve with Benders
    summary = solve_benders(params, net, output_dir=output_dir)
    
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max_csam", type=int, default=3)
    parser.add_argument("--u_l1", type=int, default=80)
    parser.add_argument("--c_dummy", type=float, default=5000)
    parser.add_argument("--seed", type=int, default=456)
    parser.add_argument("--demand_scale", type=float, default=1.0)
    
    args = parser.parse_args()
    
    params = get_default_params()
    params['MAX_CSAM_FACILITIES'] = args.max_csam
    params['U_l1'] = args.u_l1
    params['C_dummy'] = args.c_dummy
    params['SEED'] = args.seed
    params['demand_scale'] = args.demand_scale
    params['EXPERIMENT_NAME'] = f"run_maxCSAM{args.max_csam}"
    
    summary = run_single_experiment(params)
    print("\n=== Experiment Completed ===")
    print(f"Final Objective: {summary.get('objective')}")
    print(f"Deployed Facilities: {summary.get('deployed_facilities', [])}")
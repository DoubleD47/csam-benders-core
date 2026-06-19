import argparse
import copy

from model.parameters import get_default_params, generate_demand
from model.network import build_network
from model.core import solve_benders

# Single run:
#   python -m experiment_scripts.run_single --max_csam 3 --seed 456 --demand_mean 10 --demand_variance 9 --F_cost 100

def run_single_experiment(params=None):
    if params is None:
        params = get_default_params()
    else:
        params = copy.deepcopy(params)

    # Uniform opening cost override (sweep sets F_cost + F dict together)
    if "F_cost" in params and "F" not in params:
        params["F"] = {m: params["F_cost"] for m in params["M"]}

    # Generate demand
    C = [(l, k) for l in params['L'] for k in params['K']]
    D = generate_demand(
        params['M'],
        params['T'],
        C,
        mean=params.get('demand_mean', 10.0),
        variance=params.get('demand_variance', 9.0),
        scale=params.get('demand_scale', 1.0),
        seed=params['SEED'],
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
    summary = solve_benders(params, net)
    
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max_csam", type=int, default=3)
    parser.add_argument("--u_l1", type=int, default=80)
    parser.add_argument("--c_dummy", type=float, default=5000)
    parser.add_argument("--seed", type=int, default=456)
    parser.add_argument("--demand_mean", type=float, default=10.0)
    parser.add_argument("--demand_variance", type=float, default=9.0)
    parser.add_argument("--demand_scale", type=float, default=1.0,
                        help="Legacy multiplier on mean (optional)")
    parser.add_argument("--F_cost", type=float, default=100.0, help="Uniform CSAM opening cost")
    
    args = parser.parse_args()
    
    params = get_default_params()
    params['MAX_CSAM_FACILITIES'] = args.max_csam
    params['U_l1'] = args.u_l1
    params['C_dummy'] = args.c_dummy
    params['SEED'] = args.seed
    params['demand_mean'] = args.demand_mean
    params['demand_variance'] = args.demand_variance
    params['demand_scale'] = args.demand_scale
    params['F_cost'] = args.F_cost
    params['F'] = {m: args.F_cost for m in params['M']}
    params['EXPERIMENT_NAME'] = f"run_maxCSAM{args.max_csam}"
    
    summary = run_single_experiment(params)
    print("\n=== Experiment Completed ===")
    print(f"Final Objective: {summary.get('objective')}")
    print(f"Deployed Facilities: {summary.get('deployed_facilities', [])}")
import time as timer
import csv
import datetime
import json
import os
import sys
from pathlib import Path
from pulp import *
import numpy as np
import subprocess

from .network import build_network


class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()

    def flush(self):
        for f in self.files:
            f.flush()


def solve_benders(params, output_dir="output", create_exp_dir=True):
    # ====================== Unpack Parameters ======================
    M = params['M']
    traditional_m_dict = params['traditional_m_dict']
    L = params['L']
    K = params['K']
    T = params['T']
    F = params['F']
    C_in_in = params['C_in_in']
    C_in_q = params['C_in_q']
    C_q_r_l1 = params['C_q_r_l1']
    C_q_r_l2 = params['C_q_r_l2']
    C_q_q = params['C_q_q']
    C_dummy = params['C_dummy']
    U_l1 = params['U_l1']
    U_l2 = params['U_l2']
    MAX_CSAM_FACILITIES = params['MAX_CSAM_FACILITIES']
    SEED = params.get('SEED', 456)
    EPS = params.get('EPS', 1e-4)
    MAX_ITER = params.get('MAX_ITER', 100)
    EXPERIMENT_NAME = params.get('EXPERIMENT_NAME', "default_run")

    # ====================== Experiment Setup ======================
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_id = f"{timestamp}_{EXPERIMENT_NAME}_maxCSAM{MAX_CSAM_FACILITIES}"
    
    repo_root = Path(__file__).parent.parent
    exp_dir = repo_root / "experiments" / run_id
    if create_exp_dir:
        exp_dir.mkdir(parents=True, exist_ok=True)

    output_dir = repo_root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Logging
    log_file = open(exp_dir / "full_log.txt", 'w') if create_exp_dir else open(os.devnull, 'w')
    original_stdout = sys.stdout
    sys.stdout = Tee(sys.stdout, log_file)

    print(f"Experiment: {run_id}")
    print(f"MAX_CSAM_FACILITIES = {MAX_CSAM_FACILITIES} | U_l1 = {U_l1} | C_dummy = {C_dummy}")
    print(f"Random seed: {SEED}")

    np.random.seed(SEED)
    start_time = timer.time()

    # ====================== Build Network ======================
    net = build_network(M, traditional_m_dict, L, K, T, SEED)
    nodes = net['nodes']
    regular_arcs = net['regular_arcs']
    qq_arcs = net['qq_arcs']
    D = net['D']
    C = net['C']

    # ====================== Master Problem ======================
    master = LpProblem("CSAM_Master", LpMinimize)
    y = LpVariable.dicts("y", [(m, 'l1') for m in M], cat='Binary')
    theta = LpVariable("theta", lowBound=0)
    master += lpSum(F[m] * y[(m, 'l1')] for m in M) + theta
    master += lpSum(y[(m, 'l1')] for m in M) <= MAX_CSAM_FACILITIES

    # ====================== Benders Decomposition ======================
    lb, ub = -np.inf, np.inf
    iter_count = 0
    best_y = None
    best_sub_cost = np.inf
    best_sub_vars = None

    while ub - lb > EPS and iter_count < MAX_ITER:
        iter_count += 1
        print(f"\nIteration {iter_count}: Solving Master...")
        master.solve(PULP_CBC_CMD(msg=0))
        lb = value(master.objective)
        print(f"Master LB: {lb:.2f}")

        fixed_y = {m: value(y[(m, 'l1')]) for m in M}
        print("Fixed y:", {m: int(fixed_y[m]) for m in M if fixed_y[m] > 0.5})

        # Diagnostic: Check what the Master actually proposed
        current_deployed = sum(value(y[(m, 'l1')]) for m in M)
        print(f"Master proposed {int(current_deployed)} facilities")

        # Subproblem
        sub = LpProblem("Subproblem_Flow", LpMinimize)
        x_regular = LpVariable.dicts("flow_regular", regular_arcs, lowBound=0, cat='Continuous')
        x_qq = LpVariable.dicts("flow_qq", qq_arcs, lowBound=0, cat='Continuous')

        # Objective
        sub += (
            lpSum(C_in_in * x_regular[a] for a in regular_arcs if '_in' in str(a[0]) and '_in' in str(a[1])) +
            lpSum(C_in_q * x_regular[a] for a in regular_arcs if '_in' in str(a[0]) and '_q_' in str(a[1])) +
            lpSum(C_q_r_l1 * x_regular[a] for a in regular_arcs if '_q_l1' in str(a[0]) and '_r_l1' in str(a[1])) +
            lpSum(C_q_r_l2 * x_regular[a] for a in regular_arcs if '_q_l2' in str(a[0]) and '_r_l2' in str(a[1])) +
            lpSum(C_q_q * x_qq[a] for a in qq_arcs) +
            lpSum(0.1 * x_regular[a] for a in regular_arcs if '_r_' in str(a[0]) and '_out_' in str(a[1])) +
            lpSum(0.1 * x_regular[a] for a in regular_arcs if '_out_' in str(a[0]) and 'sink' in str(a[1])) +
            lpSum(0.1 * x_regular[a] for a in regular_arcs if 'sink' in str(a[0]) and 'ss' in str(a[1])) +
            lpSum(C_dummy * x_regular[a] for a in regular_arcs if ('_q_' in str(a[0]) or '_in' in str(a[0])) and 'dummy' in str(a[1])) +
            lpSum(0.1 * x_regular[a] for a in regular_arcs if 'dummy' in str(a[0]) and 'ss' in str(a[1]))
        )

        # Demand injection
        for m in M:
            for t in T:
                for c in C:
                    a = ('source', f'{m}_in', t, c)
                    if a in x_regular:
                        sub += x_regular[a] == D.get((m, t, c), 0)

        # Flow conservation - NO in_carry
        constraint_names = set()
        constraint_counter = 0
        unique_nodes = set(nodes)
        for n, t_node, comm in unique_nodes:
            incoming = [a for a in regular_arcs if a[1] == n and a[2] == t_node and a[3] == comm]
            outgoing = [a for a in regular_arcs if a[0] == n and a[2] == t_node and a[3] == comm]
            incoming_qq = [a for a in qq_arcs if a[1] == n and a[4] == t_node and a[3] == comm]
            outgoing_qq = [a for a in qq_arcs if a[0] == n and a[2] == t_node and a[3] == comm]

            if not (incoming or outgoing or incoming_qq or outgoing_qq):
                continue

            constraint_counter += 1
            constraint_name = f"flow_con_{constraint_counter}"

            if n.startswith('source'):
                # Demand already handled separately
                continue
            elif n == 'sink' and t_node == max(T):
                total_demand_t_c = sum(D.get((m, t_node, comm), 0) for m in M)
                constraint = lpSum(x_regular[a] for a in incoming) + lpSum(x_qq[a] for a in incoming_qq) == total_demand_t_c
            elif n == 'ss' and t_node is None:
                total_demand_c = sum(D.get((m, ti, comm), 0) for m in M for ti in T)
                constraint = lpSum(x_regular[a] for a in incoming) + lpSum(x_qq[a] for a in incoming_qq) == total_demand_c
            else:
                constraint = (
                    lpSum(x_regular[a] for a in incoming) + lpSum(x_qq[a] for a in incoming_qq) ==
                    lpSum(x_regular[a] for a in outgoing) + lpSum(x_qq[a] for a in outgoing_qq)
                )
            sub += constraint, constraint_name

        # Capacity constraints
        l1_capacity_cons = {}
        for m in M:
            for t in T:
                cons_name = f"capacity_l1_{m}_{t}"
                cons = lpSum(x_regular[(f'{m}_q_l1', f'{m}_r_l1', t, c)] for c in C 
                            if (f'{m}_q_l1', f'{m}_r_l1', t, c) in x_regular) <= U_l1 * fixed_y[m]
                sub += cons, cons_name
                l1_capacity_cons[(m, t)] = cons_name

        for k in K:
            if k in traditional_m_dict:
                tm = traditional_m_dict[k]
                for t in T:
                    sub += lpSum(x_regular[(f'{tm}_q_l2', f'{tm}_r_l2', t, c)] for c in C 
                                if c[1] == k and (f'{tm}_q_l2', f'{tm}_r_l2', t, c) in x_regular) <= U_l2[k]

        status = sub.solve(PULP_CBC_CMD(msg=0))
        print("Sub Status:", LpStatus[status])

        if LpStatus[status] == 'Optimal':
            sub_cost = value(sub.objective)
            deployment_cost = sum(F[m] * fixed_y[m] for m in M)
            total_cost = deployment_cost + sub_cost
            ub = min(ub, total_cost)

                # === CRITICAL FIX: Only accept if it respects max facilities ===
            num_deployed = sum(fixed_y.values())
            if num_deployed <= MAX_CSAM_FACILITIES and total_cost < deployment_cost + best_sub_cost:
                best_y = fixed_y.copy()
                best_sub_cost = sub_cost
                best_sub_vars = {
                    'x_regular': {a: value(x_regular[a]) for a in regular_arcs if value(x_regular[a]) is not None},
                    'x_qq': {a: value(x_qq[a]) for a in qq_arcs if value(x_qq[a]) is not None}
                }
                print(f"✅ New best solution found! Deployed: {int(num_deployed)} CSAM | Total Cost: {total_cost:.2f}")
            else:
                if num_deployed > MAX_CSAM_FACILITIES:
                    print(f"Warning: Master proposed {int(num_deployed)} facilities (ignored for incumbent)")

            # Optimality cut
            pi = {(m, t): sub.constraints[l1_capacity_cons[(m, t)]].pi for m in M for t in T}
            cut = theta >= sub_cost + lpSum(pi[(m, t)] * U_l1 * (y[(m, 'l1')] - fixed_y[m]) for m in M for t in T)
            master += cut, f"opt_cut_{iter_count}"

        else:
            print("Subproblem infeasible! Adding feasibility cut.")
            # Use unique name to prevent collision
            cut_name = f"feas_cut_{iter_count}"
            master += lpSum(y[(m, 'l1')] for m in M) >= sum(fixed_y.values()) + 1, cut_name

# ====================== Output & Save ======================
    print("\n=== Benders converged ===")
    print(f"Final Objective (UB): {ub:.2f}")
    runtime = timer.time() - start_time
    print(f"Runtime: {runtime:.2f} seconds")

    # Calculate cost breakdown (needed for summary)
    deployment_cost = sum(F[m] * best_y.get(m, 0) for m in M)
    travel_cost = sum(C_in_in * best_sub_vars['x_regular'].get(a, 0) for a in regular_arcs if '_in' in str(a[0]) and '_in' in str(a[1]))
    queue_entry_cost = sum(C_in_q * best_sub_vars['x_regular'].get(a, 0) for a in regular_arcs if '_in' in str(a[0]) and '_q_' in str(a[1]))
    repair_l1_cost = sum(C_q_r_l1 * best_sub_vars['x_regular'].get(a, 0) for a in regular_arcs if '_q_l1' in str(a[0]) and '_r_l1' in str(a[1]))
    repair_l2_cost = sum(C_q_r_l2 * best_sub_vars['x_regular'].get(a, 0) for a in regular_arcs if '_q_l2' in str(a[0]) and '_r_l2' in str(a[1]))
    carryover_cost = sum(C_q_q * best_sub_vars.get('x_qq', {}).get(a, 0) for a in qq_arcs)
    dummy_cost = sum(C_dummy * best_sub_vars['x_regular'].get(a, 0) for a in regular_arcs if 'dummy' in str(a[1]))

    # ====================== DETAILED PRINTING ======================
    print("Objective Value:", ub)

    # CSAM Deployments
    print("\nCSAM Deployments:")
    for m in M:
        if best_y and best_y.get(m, 0) > 0.5:
            print(f"y[{m}, 'l1'] = {best_y[m]:.0f}")

    # Print positive CSAM l1 flows + CSV
    print("\nPositive CSAM l1 flows (q_l1 to r_l1):")
    with open(os.path.join(output_dir, 'csam_flows.csv'), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Facility', 'Time', 'Commodity', 'Flow'])
        for m in M:
            for t in T:
                for c in C:
                    a = (f'{m}_q_l1', f'{m}_r_l1', t, c)
                    if a in best_sub_vars['x_regular']:
                        flow = best_sub_vars['x_regular'][a]
                        if flow > 1e-6:
                            print(f"Arc ({m}_q_l1 -> {m}_r_l1), t={t}, commodity={c}: flow={flow:.1f}")
                            writer.writerow([m, t, str(c), flow])

    # (Keep the rest of your CSV printing blocks for traditional_flows, travel_flows, dummy_flows, inq_flows, qq_flows — they are already good)

    # Summary
    summary = {
        "run_id": run_id,
        "timestamp": timestamp,
        "experiment": EXPERIMENT_NAME,
        "max_csam_facilities": MAX_CSAM_FACILITIES,
        "seed": SEED,
        "objective": float(ub),
        "deployed_count": int(sum(1 for v in best_y.values() if v > 0.5)),
        "deployed_facilities": [m for m in M if best_y.get(m, 0) > 0.5],
        "unmet_demand": float(dummy_cost),
        "iterations": int(iter_count),
        "runtime_seconds": float(runtime),
        "deployment_cost": float(deployment_cost),
        "travel_cost": float(travel_cost),
        "queue_entry_cost": float(queue_entry_cost),
        "repair_l1_cost": float(repair_l1_cost),
        "repair_l2_cost": float(repair_l2_cost),
        "carryover_cost": float(carryover_cost),
        "dummy_cost": float(dummy_cost),
    }

    with open(exp_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Copy CSVs to experiment folder
    import shutil
    for csv_name in ["csam_flows.csv", "traditional_flows.csv", "inq_flows.csv", 
                     "qq_flows.csv", "dummy_flows.csv", "travel_flows.csv"]:
        src = Path(output_dir) / csv_name
        if src.exists():
            shutil.copy(src, exp_dir / csv_name)

    # Visualization call (optional but nice)
    print("\n=== Generating visualizations ===")
    viz_script = os.path.join(repo_root, "visualizations", "analyze_flows_bd.py")
    if os.path.exists(viz_script):
        try:
            subprocess.run(["python", viz_script, str(exp_dir)], check=True)
        except:
            print("Visualization script failed or not found.")

    # Restore stdout
    sys.stdout = original_stdout
    log_file.close()

    print(f"\nExperiment completed → {exp_dir}")

    return {
        "objective": ub,
        "best_y": best_y,
        "runtime": runtime,
        "exp_dir": str(exp_dir)
    }
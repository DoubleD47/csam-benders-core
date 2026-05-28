import time as timer
import csv
import datetime
import json
import os
import sys
from pathlib import Path
from pulp import *
import numpy as np

from .network import build_network


class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            try:
                f.write(obj)
            except UnicodeEncodeError:
                f.write(obj.encode('ascii', 'replace').decode('ascii'))
            f.flush()

    def flush(self):
        for f in self.files:
            f.flush()


def solve_benders(params, output_dir="output"):
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
    MAX_ITER = params.get('MAX_ITER', 30)
    EXPERIMENT_NAME = params.get('EXPERIMENT_NAME', "default_run")

    # ====================== Experiment Setup ======================
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_id = f"{timestamp}_{EXPERIMENT_NAME}_maxCSAM{MAX_CSAM_FACILITIES}"
    
    repo_root = Path(__file__).parent.parent
    exp_dir = repo_root / "experiments" / run_id
    exp_dir.mkdir(parents=True, exist_ok=True)

    output_dir = repo_root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Logging
    log_file = open(exp_dir / "full_log.txt", 'w', encoding='utf-8')
    original_stdout = sys.stdout
    sys.stdout = Tee(sys.stdout, log_file)

    print(f"Experiment: {run_id}")
    print(f"MAX_CSAM_FACILITIES = {MAX_CSAM_FACILITIES} | U_l1 = {U_l1} | C_dummy = {C_dummy}")
    print(f"Random seed: {SEED}\n")

    np.random.seed(SEED)
    start_time = timer.time()

    # ====================== Build Network ======================
    net = build_network(M, traditional_m_dict, L, K, T, SEED)
    nodes = net['nodes']
    regular_arcs = net['regular_arcs']
    qq_arcs = net['qq_arcs']
    D = net['D']
    C = net['C']

    # ====================== Benders Decomposition ======================
    lb, ub = -np.inf, np.inf
    iter_count = 0
    best_y = None
    best_sub_cost = np.inf
    best_sub_vars = None

    # Master created once (original style)
    master = LpProblem("CSAM_Master", LpMinimize)
    y = LpVariable.dicts("y", [(m, 'l1') for m in M], cat='Binary')
    theta = LpVariable("theta", lowBound=0)

    master += lpSum(F[m] * y[(m, 'l1')] for m in M) + theta, "objective"
    master += lpSum(y[(m, 'l1')] for m in M) <= MAX_CSAM_FACILITIES, "max_csam_limit"

    while ub - lb > EPS and iter_count < MAX_ITER:
        iter_count += 1
        print(f"\n--- Iteration {iter_count} ---")
        master.solve(PULP_CBC_CMD(msg=0))
        lb = value(master.objective)
        print(f"Master LB: {lb:.2f}")

        fixed_y = {m: value(y[(m, 'l1')]) for m in M}
        print("Fixed y:", {m: int(fixed_y[m]) for m in M if fixed_y[m] > 0.5})

        # ====================== Subproblem ======================
        sub = LpProblem("Subproblem_Flow", LpMinimize)
        x_regular = LpVariable.dicts("flow_regular", regular_arcs, lowBound=0, cat='Continuous')
        x_qq = LpVariable.dicts("flow_qq", qq_arcs, lowBound=0, cat='Continuous')

        # Objective - Match original as closely as possible
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

        # Flow conservation - Match original exactly
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
            constraint_name = f"flow_conservation_{constraint_counter}_{n.replace('_', '-')}_{t_node if t_node else 'None'}_{comm[0]}_{comm[1]}"
            constraint_names.add(constraint_name)

            if n.startswith('source'):
                total_demand_t_c = sum(D.get((m, t_node, comm), 0) for m in M)
                constraint = lpSum(x_regular[a] for a in outgoing) + lpSum(x_qq[a] for a in outgoing_qq) == total_demand_t_c
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

        # Capacity constraints (TEMPORARILY RELAXED for diagnosis)
        print("  → Using relaxed capacity for diagnosis...")
        for m in M:
            for t in T:
                sub += lpSum(x_regular.get((f'{m}_q_l1', f'{m}_r_l1', t, c), 0) for c in C) <= U_l1 * 1000  # very large

        for k in K:
            if k in traditional_m_dict:
                tm = traditional_m_dict[k]
                for t in T:
                    sub += lpSum(x_regular.get((f'{tm}_q_l2', f'{tm}_r_l2', t, c), 0) for c in C if c[1] == k) <= 10000
        status = sub.solve(PULP_CBC_CMD(msg=0))
        print("Sub Status:", LpStatus[status])

        if LpStatus[status] == 'Optimal':
            sub_cost = value(sub.objective)
            deployment_cost = sum(F[m] * fixed_y.get(m, 0) for m in M)
            total_cost = deployment_cost + sub_cost
            ub = min(ub, total_cost)

            if total_cost < best_sub_cost:
                best_y = fixed_y.copy()
                best_sub_cost = sub_cost
                best_sub_vars = {
                    'x_regular': {a: value(x_regular[a]) for a in regular_arcs},
                    'x_qq': {a: value(x_qq[a]) for a in qq_arcs}
                }
                print(f"New best UB: {ub:.2f} with {sum(best_y.values()):.0f} CSAM facilities")

            # Optimality cut using duals (original style)
            pi = {(m, t): sub.constraints[l1_capacity_cons[(m, t)]].pi for m in M for t in T}
            cut = theta >= sub_cost + lpSum(pi[(m, t)] * U_l1 * (y[(m, 'l1')] - fixed_y.get(m, 0)) for m in M for t in T)
            master += cut, f"opt_cut_{iter_count}"

        else:
            print("Subproblem infeasible! Adding strong feasibility cut.")
            min_facilities = min(iter_count, MAX_CSAM_FACILITIES)
            master += lpSum(y[(m, 'l1')] for m in M) >= min_facilities, f"feas_cut_{iter_count}"
            print(f"Added feasibility cut: at least {min_facilities} facilities")
            
    # ====================== Output & Save ======================
    print("\n=== Benders converged ===")
    print(f"Final Objective (UB): {ub:.2f}")
    runtime = timer.time() - start_time
    print(f"Runtime: {runtime:.2f} seconds")

    if best_y is None:
        best_y = {m: 0 for m in M}

    # TODO: Add your CSV writing and summary.json code here later

    sys.stdout = original_stdout
    log_file.close()

    print(f"Experiment completed → {exp_dir}")
    return {"objective": ub, "best_y": best_y, "runtime": runtime, "exp_dir": str(exp_dir)}
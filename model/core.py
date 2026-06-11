from re import sub
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


def solve_benders(params, net=None, output_dir="experiments"):
    # ====================== Unpack Parameters ======================
    M = params['M']
    traditional_m_dict = params['traditional_m_dict']
    L = params['L']
    K = params['K']
    T = params['T']
    F = params['F']
    C_in_q = params['C_in_q']
    C_q_q = params['C_q_q']
    C_service = params.get('C_service', 10.0)
    C_dummy = params['C_dummy']
    U_l1 = params['U_l1']
    U_l2 = params['U_l2']
    MAX_CSAM_FACILITIES = params['MAX_CSAM_FACILITIES']
    SEED = params.get('SEED', 456)
    EPS = params.get('EPS', 1e-4)
    MAX_ITER = params.get('MAX_ITER', 50)
    EXPERIMENT_NAME = params.get('EXPERIMENT_NAME', "default_run")

    # ====================== Experiment Setup ======================
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_id = f"{timestamp}_{EXPERIMENT_NAME}_maxCSAM{MAX_CSAM_FACILITIES}"
    
    repo_root = Path(__file__).parent.parent
    exp_dir = repo_root / "experiments" / run_id
    exp_dir.mkdir(parents=True, exist_ok=True)

    # Logging
    log_file = open(exp_dir / "full_log.txt", 'w', encoding='utf-8')
    original_stdout = sys.stdout
    sys.stdout = Tee(sys.stdout, log_file)

    print(f"Experiment: {run_id}")
    print(f"MAX_CSAM_FACILITIES = {MAX_CSAM_FACILITIES} | U_l1 = {U_l1} | C_dummy = {C_dummy}")
    print(f"Random seed: {SEED}\n")

    np.random.seed(SEED)
    start_time = timer.time()

    # Build network (use passed net or build new)
    if net is None:
        net = build_network(M, traditional_m_dict, L, K, T, seed=SEED)
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
        print("  Fixed y:", {m: int(v) for m, v in fixed_y.items() if v > 0.5})

        # ====================== Subproblem ======================
        sub = LpProblem("Subproblem_Flow", LpMinimize)
        x_regular = LpVariable.dicts("flow_regular", regular_arcs, lowBound=0, cat='Continuous')
        x_qq = LpVariable.dicts("flow_qq", qq_arcs, lowBound=0, cat='Continuous')

        print(f"  [DEBUG] Number of regular arcs: {len(regular_arcs)}")
        print(f"  [DEBUG] Number of qq arcs: {len(qq_arcs)}")

        # ====================== Objective ======================
        max_t = max(T)  # Make sure max_t is defined in this scope

        sub += (
            # Queue entry cost
            lpSum(C_in_q * x_regular[a] for a in regular_arcs if a[0].endswith('_in') and a[1].endswith('_q')) +
            # Queue carry-over cost
            lpSum(C_q_q * x_qq[a] for a in qq_arcs) +
            # Normal service cost (from queues to ss)
            lpSum(C_service * x_regular[a] for a in regular_arcs if a[1] == 'ss' and ('_q_l1' in a[0] or '_q_l2' in a[0])) +
            # High dummy/write-off cost (last period only, direct to ss)
            lpSum(C_dummy * x_regular[a] for a in regular_arcs 
                  if a[1] == 'ss' and a[2] == max_t and 
                  (a[0].endswith('_in') or a[0].endswith('_q_l1') or a[0].endswith('_q_l2'))) +
            0
        ), "SubObjective"

        # Demand injection
        total_demand = 0
        for m in M:
            for t in T:
                for c in C:
                    a = ('source', f'{m}_in', t, c)
                    if a in x_regular:
                        demand = D.get((m, t, c), 0)
                        sub += x_regular[a] == demand, f"demand_{m}_{t}_{c}"
                        total_demand += demand
        print(f"  [DEBUG] Total demand injected: {total_demand:.1f}")

        # Flow conservation (updated for new nodes)
        print("  [DEBUG] Starting flow conservation setup...")
        unbalanced_nodes = []
        constraint_counter = 0

        for n, t_node, comm in set(nodes):
            incoming = [a for a in regular_arcs if a[1] == n and a[2] == t_node and a[3] == comm]
            outgoing = [a for a in regular_arcs if a[0] == n and a[2] == t_node and a[3] == comm]
            incoming_qq = [a for a in qq_arcs if a[1] == n and a[4] == t_node and a[3] == comm]
            outgoing_qq = [a for a in qq_arcs if a[0] == n and a[2] == t_node and a[3] == comm]

            in_count = len(incoming) + len(incoming_qq)
            out_count = len(outgoing) + len(outgoing_qq)

            # Unbalanced nodes filtering (allow source, ss, dummy, and _in nodes with dummy in last period)
            if in_count != out_count and not (
                n.startswith('source') or 
                n in ['ss', 'dummy'] or 
                n.endswith('_in')   # allow _in nodes if they have dummy in last period
            ):
                unbalanced_nodes.append((n, t_node, comm, in_count, out_count))

            if not (incoming or outgoing or incoming_qq or outgoing_qq):
                continue

            constraint_counter += 1
            if n.startswith('source'):
                continue
            elif n == 'ss' and t_node is None:
                total_d = sum(D.get((m, ti, comm), 0) for m in M for ti in T)
                sub += (lpSum(x_regular[a] for a in incoming) + lpSum(x_qq[a] for a in incoming_qq) == total_d), f"ss_{comm}"
            else:
                sub += (
                    lpSum(x_regular[a] for a in incoming) + lpSum(x_qq[a] for a in incoming_qq) ==
                    lpSum(x_regular[a] for a in outgoing) + lpSum(x_qq[a] for a in outgoing_qq)
                ), f"flow_{constraint_counter}"

        print(f"  [DEBUG] Flow conservation constraints added: {constraint_counter}")
        print(f"  [DEBUG] Unbalanced nodes found: {len(unbalanced_nodes)}")

# ====================== Capacity Constraints ======================
        print("  [DEBUG] Adding capacity constraints...")

        # l1 capacity: flows leaving any q_l1 to ss
        for m in M:
            for t in T:
                l1_flow = lpSum(x_regular.get((f'{m}_q_l1', 'ss', t, c), 0) for c in C if c[0] == 'l1')
                sub += l1_flow <= U_l1 * fixed_y.get(m, 0), f"cap_l1_{m}_{t}"

        # l2 capacity: only meaningful at traditional locations (including l1 crossover)
        for k, tm in traditional_m_dict.items():
            for t in T:
                l2_flow = lpSum(x_regular.get((f'{tm}_q_l2', 'ss', t, c), 0) for c in C if c[1] == k)
                sub += l2_flow <= U_l2.get(k, 0), f"cap_l2_{tm}_{t}"
                
        # Solve subproblem
        print("  [DEBUG] Solving subproblem...")
        status = sub.solve(PULP_CBC_CMD(msg=0))
        print("Sub Status:", LpStatus[status])

        if LpStatus[status] == 'Optimal':
            print("  [DEBUG] Subproblem solved optimally. Recording key flows...")

            # Sample flows from _in to q_l1
            sample_in_flows = 0
            for m in list(M)[:3]:   # first few nodes
                for t in T:
                    for c in list(C)[:3]:  # first few commodities
                        a = (f'{m}_in', f'{m}_q_l1', t, c)
                        if a in x_regular:
                            flow = value(x_regular[a])
                            if flow > 0.01:
                                sample_in_flows += 1
            print(f"  [DEBUG] Positive in -> q_l1 flows (sample): {sample_in_flows}")

            # Total dummy usage
            dummy_flow = sum(value(x_regular.get(a, 0)) for a in regular_arcs if a[0] == 'dummy')
            print(f"  [DEBUG] Total dummy usage: {dummy_flow:.1f} / {total_demand:.1f} demand")

        if LpStatus[status] == 'Optimal':
            sub_cost = value(sub.objective)
            deployment_cost = sum(F[m] * fixed_y.get(m, 0) for m in M)
            total_cost = deployment_cost + sub_cost
            ub = min(ub, total_cost)

            if total_cost < best_sub_cost:
                best_y = fixed_y.copy()
                best_sub_cost = sub_cost
                print(f"New best UB: {ub:.2f} with {sum(1 for v in best_y.values() if v > 0.5):.0f} CSAM facilities")

            # TODO: Add proper optimality cut later (dual-based)
        else:
            print("Subproblem infeasible! Adding strong feasibility cut.")
            master += lpSum(y[(m, 'l1')] for m in M) >= min(iter_count, MAX_CSAM_FACILITIES), f"feas_cut_{iter_count}"

    # ====================== Output ======================
    print("\n=== Benders converged ===")
    print(f"Final Objective (UB): {ub:.2f}")
    runtime = timer.time() - start_time
    print(f"Runtime: {runtime:.2f} seconds")

    print("\nCSAM Deployments:")
    deployed = [m for m in M if best_y and best_y.get(m, 0) > 0.5]
    for m in deployed:
        print(f"y[{m}, 'l1'] = 1")

    summary = {
        "run_id": run_id,
        "max_csam_facilities": MAX_CSAM_FACILITIES,
        "seed": SEED,
        "objective": float(ub),
        "deployed_count": len(deployed),
        "deployed_facilities": deployed,
        "iterations": iter_count,
        "runtime_seconds": float(runtime)
    }

    with open(exp_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nExperiment completed → {exp_dir}")

    sys.stdout = original_stdout
    log_file.close()

    return summary
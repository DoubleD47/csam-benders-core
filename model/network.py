import numpy as np
from collections import defaultdict

def build_network(M, traditional_m_dict, L, K, T, seed=456):
    np.random.seed(seed)
    C = [(l, k) for l in L for k in K]
    
    nodes = []
    regular_arcs = []
    qq_arcs = []

    for t in T:
        for c in C:
            nodes.append(('source', t, c))
            nodes.append(('sink', t, c))
            if t == max(T):
                nodes.append(('dummy', t, c))
            nodes.append(('ss', None, c))
            for m in M:
                nodes.append((f'{m}_in', t, c))
                nodes.extend([(f'{m}_q_l1', t, c), (f'{m}_r_l1', t, c), (f'{m}_out_l1', t, c)])
                if m == traditional_m_dict.get(c[1]):
                    nodes.extend([(f'{m}_q_l2', t, c), (f'{m}_r_l2', t, c), (f'{m}_out_l2', t, c)])

    # Regular arcs (same as bd_1.py)
    for t in T:
        for c in C:
            for m in M:
                regular_arcs.append(('source', f'{m}_in', t, c))
                for m1 in M:
                    for m2 in M:
                        if m1 != m2:
                            regular_arcs.append((f'{m1}_in', f'{m2}_in', t, c))
                regular_arcs.append((f'{m}_in', f'{m}_q_l1', t, c))
                if m == traditional_m_dict.get(c[1]):
                    regular_arcs.append((f'{m}_in', f'{m}_q_l2', t, c))
                regular_arcs.append((f'{m}_q_l1', f'{m}_r_l1', t, c))
                regular_arcs.append((f'{m}_r_l1', f'{m}_out_l1', t, c))
                regular_arcs.append((f'{m}_out_l1', 'sink', t, c))
                if m == traditional_m_dict.get(c[1]):
                    regular_arcs.append((f'{m}_q_l2', f'{m}_r_l2', t, c))
                    regular_arcs.append((f'{m}_r_l2', f'{m}_out_l2', t, c))
                    regular_arcs.append((f'{m}_out_l2', 'sink', t, c))
                regular_arcs.append(('sink', 'ss', t, c))
                if t == max(T):
                    regular_arcs.append((f'{m}_q_l1', 'dummy', t, c))
                    if m == traditional_m_dict.get(c[1]):
                        regular_arcs.append((f'{m}_q_l2', 'dummy', t, c))
                    regular_arcs.append((f'{m}_in', 'dummy', t, c))
            regular_arcs.append(('dummy', 'ss', t, c))

    # Queue carry-over
    for t in range(min(T), max(T)):
        for c in C:
            for m in M:
                qq_arcs.append((f'{m}_q_l1', f'{m}_q_l1', t, c, t+1))
                if m == traditional_m_dict.get(c[1]):
                    qq_arcs.append((f'{m}_q_l2', f'{m}_q_l2', t, c, t+1))

    D = {(m, t, c): np.random.uniform(5, 15) for m in M for t in T for c in C}
    
    return {
        'nodes': nodes,
        'regular_arcs': regular_arcs,
        'qq_arcs': qq_arcs,
        'D': D,
        'C': C
    }
import numpy as np
from collections import defaultdict

def build_network(M, traditional_m_dict, L, K, T, seed=456):
    np.random.seed(seed)
    C = [(l, k) for l in L for k in K]
    
    nodes = []
    regular_arcs = []
    qq_arcs = []

    max_t = max(T)

    for t in T:
        for c in C:
            nodes.append(('source', t, c))
            nodes.append(('sink', t, c))
            if t == max_t:
                nodes.append(('dummy', t, c))
            nodes.append(('ss', None, c))

            for m in M:
                nodes.append((f'{m}_in', t, c))
                nodes.extend([(f'{m}_q_l1', t, c), (f'{m}_r_l1', t, c), (f'{m}_out_l1', t, c)])
                if m == traditional_m_dict.get(c[1]):
                    nodes.extend([(f'{m}_q_l2', t, c), (f'{m}_r_l2', t, c), (f'{m}_out_l2', t, c)])

    for t in T:
        for c in C:
            for m in M:
                regular_arcs.append(('source', f'{m}_in', t, c))

                # Inter-node movement
                for m2 in M:
                    if m != m2:
                        regular_arcs.append((f'{m}_in', f'{m2}_in', t, c))

                # Enter queues
                regular_arcs.append((f'{m}_in', f'{m}_q_l1', t, c))
                if m == traditional_m_dict.get(c[1]):
                    regular_arcs.append((f'{m}_in', f'{m}_q_l2', t, c))

                # l1 processing
                regular_arcs.append((f'{m}_q_l1', f'{m}_r_l1', t, c))
                regular_arcs.append((f'{m}_r_l1', f'{m}_out_l1', t, c))
                regular_arcs.append((f'{m}_out_l1', 'sink', t, c))

                # l1 to l2 crossover (important for l1 demand at l2 facilities)
                if m in traditional_m_dict.values():
                    regular_arcs.append((f'{m}_q_l1', f'{m}_q_l2', t, c))

                # l2 processing
                if m == traditional_m_dict.get(c[1]):
                    regular_arcs.append((f'{m}_q_l2', f'{m}_r_l2', t, c))
                    regular_arcs.append((f'{m}_r_l2', f'{m}_out_l2', t, c))
                    regular_arcs.append((f'{m}_out_l2', 'sink', t, c))

                # Dummy arcs ONLY in last period
                if t == max_t:
                    regular_arcs.append((f'{m}_q_l1', 'dummy', t, c))
                    if m == traditional_m_dict.get(c[1]):
                        regular_arcs.append((f'{m}_q_l2', 'dummy', t, c))
                    regular_arcs.append((f'{m}_in', 'dummy', t, c))

                regular_arcs.append(('sink', 'ss', t, c))
                if t == max_t:
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
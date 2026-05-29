import numpy as np
from collections import defaultdict

def build_network(M, traditional_m_dict, L, K, T, seed=456):
    np.random.seed(seed)
    C = [(l, k) for l in L for k in K]
    
    nodes = []
    regular_arcs = []
    qq_arcs = []

    max_t = max(T)
    l2_locations = set(traditional_m_dict.values())

    for t in T:
        for c in C:
            l, k = c
            nodes.append(('source', t, c))
            nodes.append(('sink', t, c))
            if t == max_t:
                nodes.append(('dummy', t, c))
            nodes.append(('ss', None, c))  # super sink per c

            for m in M:
                nodes.append((f'{m}_in', t, c))
                
                # l1 queue/repair always available (but capacity controlled by y later)
                nodes.extend([(f'{m}_q_l1', t, c), (f'{m}_r_l1', t, c), (f'{m}_out_l1', t, c)])
                
                # l2 only at traditional locations, and only for matching k or l1 crossover
                if m in l2_locations:
                    if l == 'l2' or (l == 'l1' and m == traditional_m_dict.get(k)):
                        nodes.extend([(f'{m}_q_l2', t, c), (f'{m}_r_l2', t, c), (f'{m}_out_l2', t, c)])

    # === Arcs ===
    for t in T:
        for c in C:
            l, k = c
            matching_m_for_k = traditional_m_dict.get(k)
            
            for m in M:
                # Source injection
                regular_arcs.append(('source', f'{m}_in', t, c))

                # Inter-node movement (only for l1 demands? User said l1 may travel)
                if l == 'l1':
                    for m2 in M:
                        if m != m2:
                            regular_arcs.append((f'{m}_in', f'{m2}_in', t, c))

                # Enter queues
                regular_arcs.append((f'{m}_in', f'{m}_q_l1', t, c))
                
                # l2 queue entry - stricter
                if m == matching_m_for_k:
                    if l == 'l2' or (l == 'l1'):  # allow l1 crossover at matching m
                        regular_arcs.append((f'{m}_in', f'{m}_q_l2', t, c))

                # l1 processing
                regular_arcs.append((f'{m}_q_l1', f'{m}_r_l1', t, c))
                regular_arcs.append((f'{m}_r_l1', f'{m}_out_l1', t, c))
                regular_arcs.append((f'{m}_out_l1', 'sink', t, c))

                # l2 processing (only if node exists for this c)
                if m == matching_m_for_k and f'{m}_q_l2' in [n[0] for n in nodes if n[1]==t and n[2]==c]:
                    regular_arcs.append((f'{m}_q_l2', f'{m}_r_l2', t, c))
                    regular_arcs.append((f'{m}_r_l2', f'{m}_out_l2', t, c))
                    regular_arcs.append((f'{m}_out_l2', 'sink', t, c))

                # Dummy exits (last period)
                if t == max_t:
                    regular_arcs.append((f'{m}_q_l1', 'dummy', t, c))
                    if m == matching_m_for_k:
                        regular_arcs.append((f'{m}_q_l2', 'dummy', t, c))
                    regular_arcs.append((f'{m}_in', 'dummy', t, c))  # stranded at in

                # Sinks to super-sink
                regular_arcs.append(('sink', 'ss', t, c))
                if t == max_t:
                    regular_arcs.append(('dummy', 'ss', t, c))

    # Queue carry-over (only same c)
    for t in range(min(T), max(T)):
        for c in C:
            for m in M:
                qq_arcs.append((f'{m}_q_l1', f'{m}_q_l1', t, c, t+1))
                if m == traditional_m_dict.get(c[1]):
                    qq_arcs.append((f'{m}_q_l2', f'{m}_q_l2', t, c, t+1))

    D = {(m, t, c): np.random.uniform(5, 15) for m in M for t in T for c in C}
    
    return {
        'nodes': list(set(nodes)),  # dedup
        'regular_arcs': regular_arcs,
        'qq_arcs': qq_arcs,
        'D': D,
        'C': C
    }
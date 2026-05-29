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

    # === Node Creation ===
    for t in T:
        for c in C:
            l, k = c
            nodes.append(('source', t, c))
            nodes.append(('sink', t, c))
            if t == max_t:
                nodes.append(('dummy', t, c))
            nodes.append(('ss', None, c))  # global super sink per c

            for m in M:
                nodes.append((f'{m}_in', t, c))
                
                # l1 always available
                nodes.extend([(f'{m}_q_l1', t, c), (f'{m}_r_l1', t, c), (f'{m}_out_l1', t, c)])
                
                # l2 only at traditional locations + only for allowed c
                if m in l2_locations:
                    if l == 'l2' or (l == 'l1' and m == traditional_m_dict.get(k)):
                        nodes.extend([(f'{m}_q_l2', t, c), (f'{m}_r_l2', t, c), (f'{m}_out_l2', t, c)])

    # === Arcs ===
    for t in T:
        for c in C:
            l, k = c
            matching_m = traditional_m_dict.get(k)
            
            for m in M:
                # 1. Source injection to any _in
                regular_arcs.append(('source', f'{m}_in', t, c))

                # 2. Travel between _in nodes (all c allowed)
                for m2 in M:
                    if m != m2:
                        regular_arcs.append((f'{m}_in', f'{m2}_in', t, c))

                # 3. Enter l1 queue (anywhere)
                regular_arcs.append((f'{m}_in', f'{m}_q_l1', t, c))

                # 4. Enter l2 queue (very restricted)
                if m == matching_m and f'{m}_q_l2' in {n[0] for n in nodes if n[1] == t and n[2] == c}:
                    regular_arcs.append((f'{m}_in', f'{m}_q_l2', t, c))

                # 5. l1 processing chain
                regular_arcs.append((f'{m}_q_l1', f'{m}_r_l1', t, c))
                regular_arcs.append((f'{m}_r_l1', f'{m}_out_l1', t, c))
                regular_arcs.append((f'{m}_out_l1', 'sink', t, c))

                # 6. l2 processing chain
                if m == matching_m and f'{m}_q_l2' in {n[0] for n in nodes if n[1] == t and n[2] == c}:
                    regular_arcs.append((f'{m}_q_l2', f'{m}_r_l2', t, c))
                    regular_arcs.append((f'{m}_r_l2', f'{m}_out_l2', t, c))
                    regular_arcs.append((f'{m}_out_l2', 'sink', t, c))

                # 7. l1 → l2 crossover at matching location
                if l == 'l1' and m == matching_m and f'{m}_q_l2' in {n[0] for n in nodes if n[1] == t and n[2] == c}:
                    regular_arcs.append((f'{m}_q_l1', f'{m}_q_l2', t, c))

                # 8. Dummy exits (LAST period ONLY)
                if t == max_t:
                    regular_arcs.append((f'{m}_in', 'dummy', t, c))
                    regular_arcs.append((f'{m}_q_l1', 'dummy', t, c))
                    if m == matching_m and f'{m}_q_l2' in {n[0] for n in nodes if n[1] == t and n[2] == c}:
                        regular_arcs.append((f'{m}_q_l2', 'dummy', t, c))

                # 9. Sink → super-sink (every period)
                regular_arcs.append(('sink', 'ss', t, c))
                if t == max_t:
                    regular_arcs.append(('dummy', 'ss', t, c))

    # === Queue carry-over arcs ===
    for i in range(len(T)-1):
        t_curr = T[i]
        t_next = T[i+1]
        for c in C:
            for m in M:
                qq_arcs.append((f'{m}_q_l1', f'{m}_q_l1', t_curr, c, t_next))
                if m == traditional_m_dict.get(c[1]):
                    qq_arcs.append((f'{m}_q_l2', f'{m}_q_l2', t_curr, c, t_next))

    D = {(m, t, c): np.random.uniform(5, 15) for m in M for t in T for c in C}
    
    return {
        'nodes': list(set(nodes)),
        'regular_arcs': regular_arcs,
        'qq_arcs': qq_arcs,
        'D': D,
        'C': C
    }
import numpy as np

def build_network(M, traditional_m_dict, L, K, T, D=None, seed=456):
    np.random.seed(seed)
    C = [(l, k) for l in L for k in K]
    
    nodes = set()
    regular_arcs = []
    qq_arcs = []

    max_t = max(T)
    l2_locations = set(traditional_m_dict.values())

    # === Create Nodes ===
    for t in T:
        for c in C:
            nodes.add(('source', t, c))
            nodes.add(('ss', None, c))
            if t == max_t:
                nodes.add(('dummy', t, c))

            for m in M:
                nodes.add((f'{m}_in', t, c))
                nodes.add((f'{m}_q_l1', t, c))
                # l2 queue only when allowed
                if m in l2_locations and (c[0] == 'l2' or (c[0] == 'l1' and m == traditional_m_dict.get(c[1]))):
                    nodes.add((f'{m}_q_l2', t, c))

    nodes = list(nodes)

    # === Arcs ===
    for t in T:
        for c in C:
            l, k = c
            matching_m = traditional_m_dict.get(k)

            for m in M:
                # Source -> in
                regular_arcs.append(('source', f'{m}_in', t, c))

                # Travel between ins
                for m2 in M:
                    if m != m2:
                        regular_arcs.append((f'{m}_in', f'{m2}_in', t, c))

                # Enter queues
                regular_arcs.append((f'{m}_in', f'{m}_q_l1', t, c))
                if m == matching_m and f'{m}_q_l2' in [n[0] for n in nodes if n[1] == t and n[2] == c]:
                    regular_arcs.append((f'{m}_in', f'{m}_q_l2', t, c))

                # Service arcs q -> ss
                regular_arcs.append((f'{m}_q_l1', 'ss', t, c))
                if f'{m}_q_l2' in [n[0] for n in nodes if n[1] == t and n[2] == c]:
                    regular_arcs.append((f'{m}_q_l2', 'ss', t, c))

                # Dummy arcs (last period)
                if t == max_t:
                    regular_arcs.append((f'{m}_q_l1', 'dummy', t, c))
                    regular_arcs.append((f'{m}_in', 'dummy', t, c))
                    if f'{m}_q_l2' in [n[0] for n in nodes if n[1] == t and n[2] == c]:
                        regular_arcs.append((f'{m}_q_l2', 'dummy', t, c))

    # Queue carry-over
    for i in range(len(T)-1):
        tc = T[i]
        tn = T[i+1]
        for c in C:
            for m in M:
                qq_arcs.append((f'{m}_q_l1', f'{m}_q_l1', tc, c, tn))
                if m in l2_locations and (c[0] == 'l2' or (c[0] == 'l1' and m == traditional_m_dict.get(c[1]))):
                    qq_arcs.append((f'{m}_q_l2', f'{m}_q_l2', tc, c, tn))

    # Dummy -> ss
    for c in C:
        regular_arcs.append(('dummy', 'ss', max_t, c))

    if D is None:
        D = {(m, t, c): np.random.uniform(5, 15) for m in M for t in T for c in C}

    print(f"[DEBUG] Built network: {len(nodes)} nodes, {len(regular_arcs)} regular arcs, {len(qq_arcs)} qq arcs")
    
    return {
        'nodes': nodes,
        'regular_arcs': regular_arcs,
        'qq_arcs': qq_arcs,
        'D': D,
        'C': C
    }
import numpy as np

def build_network(M, traditional_m_dict, L, K, T, D=None, seed=456):
    np.random.seed(seed)
    C = [(l, k) for l in L for k in K]

    nodes = set()
    regular_arcs = []
    qq_arcs = []

    max_t = max(T)

    # Nodes
    for t in T:
        for c in C:
            nodes.add(('source', t, c))
            nodes.add(('ss', None, c))

            for m in M:
                nodes.add((f'{m}_in', t, c))
                nodes.add((f'{m}_q_l1', t, c))
                nodes.add((f'{m}_q_l2', t, c))

    nodes = list(nodes)

    # Arcs
    for t in T:
        for c in C:
            l, k = c
            matching_m = traditional_m_dict.get(k)

            for m in M:
                regular_arcs.append(('source', f'{m}_in', t, c))

                # Travel
                for m2 in M:
                    if m != m2:
                        regular_arcs.append((f'{m}_in', f'{m2}_in', t, c))

                # Enter queues (always)
                regular_arcs.append((f'{m}_in', f'{m}_q_l1', t, c))
                regular_arcs.append((f'{m}_in', f'{m}_q_l2', t, c))

                # Service (normal repair)
                regular_arcs.append((f'{m}_q_l1', 'ss', t, c))
                regular_arcs.append((f'{m}_q_l2', 'ss', t, c))

                # Last period dummy/write-off arcs to ss (high cost)
                if t == max_t:
                    regular_arcs.append((f'{m}_in', 'ss', t, c))
                    regular_arcs.append((f'{m}_q_l1', 'ss', t, c))
                    regular_arcs.append((f'{m}_q_l2', 'ss', t, c))

    # Carry-over
    for i in range(len(T)-1):
        tc = T[i]
        tn = T[i+1]
        for c in C:
            for m in M:
                qq_arcs.append((f'{m}_q_l1', f'{m}_q_l1', tc, c, tn))
                qq_arcs.append((f'{m}_q_l2', f'{m}_q_l2', tc, c, tn))

    if D is None:
        print("[DEBUG] No demand was specified. Using default random values (5-15 per (m,t,c)).")
        D = {(m, t, c): np.random.uniform(5, 15) for m in M for t in T for c in C}

    print(f"[DEBUG] Built network: {len(nodes)} nodes, {len(regular_arcs)} regular arcs, {len(qq_arcs)} qq arcs")
    return {'nodes': nodes, 'regular_arcs': regular_arcs, 'qq_arcs': qq_arcs, 'D': D, 'C': C}
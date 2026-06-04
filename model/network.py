import numpy as np

def build_network(M, traditional_m_dict, L, K, T, D=None, seed=456):
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
            nodes.append(('ss', None, c))
            if t == max_t:
                nodes.append(('dummy', t, c))

            for m in M:
                nodes.append((f'{m}_in', t, c))
                
                # Separate queues - l1 and l2 have separate paths, but the l1 may cross over ot l2 if it is a matching k tuple (e.g. (l1,k1) can be serviced by at the (l2,k1) faciility)
                nodes.append((f'{m}_q_l1', t, c))
                if m in l2_locations and (l == 'l2' or (l == 'l1' and m == traditional_m_dict.get(k))):
                    nodes.append((f'{m}_q_l2', t, c))

    # Arcs
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

                # in -> q_l1 (queue entry cost)
                regular_arcs.append((f'{m}_in', f'{m}_q_l1', t, c))

                # in -> q_l2 (restricted)
                if m == matching_m and f'{m}_q_l2' in [n[0] for n in nodes if n[1]==t and n[2]==c]:
                    regular_arcs.append((f'{m}_in', f'{m}_q_l2', t, c))

                # Service arcs: q -> ss (service cost)
                regular_arcs.append((f'{m}_q_l1', 'ss', t, c))   # l1 queue can always try to service

                if f'{m}_q_l2' in [n[0] for n in nodes if n[1]==t and n[2]==c]:
                    regular_arcs.append((f'{m}_q_l2', 'ss', t, c))

                # Dummy arcs (last period)
                if t == max_t:
                    regular_arcs.append((f'{m}_q_l1', 'dummy', t, c))
                    regular_arcs.append((f'{m}_in', 'dummy', t, c))
                    if f'{m}_q_l2' in [n[0] for n in nodes if n[1]==t and n[2]==c]:
                        regular_arcs.append((f'{m}_q_l2', 'dummy', t, c))

    # Queue carry-over (separate)
    for i in range(len(T)-1):
        tc = T[i]
        tn = T[i+1]
        for c in C:
            for m in M:
                qq_arcs.append((f'{m}_q_l1', f'{m}_q_l1', tc, c, tn))
                if m in l2_locations and (c[0] == 'l2' or (c[0] == 'l1' and m == traditional_m_dict.get(c[1]))):
                    qq_arcs.append((f'{m}_q_l2', f'{m}_q_l2', tc, c, tn))

    # Dummy to ss
    for c in C:
        regular_arcs.append(('dummy', 'ss', max_t, c))

    if D is None:
        # Fallback random demand (for quick testing)
        D = {(m, t, c): np.random.uniform(5, 15) for m in M for t in T for c in C}
    print(f"[DEBUG] Using demand with total volume: {sum(D.values()):.1f}")
    print(f"[DEBUG] Simplified network: {len(set(nodes))} nodes")
    return {
        'nodes': list(set(nodes)),
        'regular_arcs': regular_arcs,
        'qq_arcs': qq_arcs,
        'D': D,
        'C': C
    }
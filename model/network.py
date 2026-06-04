import numpy as np

def build_network(M, traditional_m_dict, L, K, T, seed=456):
    np.random.seed(seed)
    C = [(l, k) for l in L for k in K]
    
    nodes = []
    regular_arcs = []
    qq_arcs = []

    max_t = max(T)
    l2_locations = set(traditional_m_dict.values())

    # Node creation
    for t in T:
        for c in C:
            l, k = c
            nodes.append(('source', t, c))
            nodes.append(('ss', None, c))   # single global super-sink per c
            
            if t == max_t:
                nodes.append(('dummy', t, c))

            for m in M:
                nodes.append((f'{m}_in', t, c))
                nodes.append((f'{m}_q', t, c))   # Simplified single queue per m,c

    # Arcs
    for t in T:
        for c in C:
            l, k = c
            matching_m = traditional_m_dict.get(k)

            for m in M:
                # Source injection
                regular_arcs.append(('source', f'{m}_in', t, c))

                # Travel between entry points (all c)
                for m2 in M:
                    if m != m2:
                        regular_arcs.append((f'{m}_in', f'{m2}_in', t, c))

                # Enter queue (pay queue cost here)
                regular_arcs.append((f'{m}_in', f'{m}_q', t, c))

                # === Service arcs (to super-sink) ===
                # l1 service - enabled by y_m (any l1 demand at any m)
                if l == 'l1':
                    regular_arcs.append((f'{m}_q', 'ss', t, c))

                # l2 native service
                if l == 'l2' and m == matching_m:
                    regular_arcs.append((f'{m}_q', 'ss', t, c))

                # l1 crossover to matching l2 facility
                if l == 'l1' and m == matching_m:
                    regular_arcs.append((f'{m}_q', 'ss', t, c))

                # Dummy in last period
                if t == max_t:
                    regular_arcs.append((f'{m}_q', 'dummy', t, c))
                    regular_arcs.append((f'{m}_in', 'dummy', t, c))

    # Queue carry-over
    for i in range(len(T)-1):
        t_curr = T[i]
        t_next = T[i+1]
        for c in C:
            for m in M:
                qq_arcs.append((f'{m}_q', f'{m}_q', t_curr, c, t_next))

    # Add dummy to ss
    for t in T:
        for c in C:
            if t == max_t:
                regular_arcs.append(('dummy', 'ss', t, c))

    D = {(m, t, c): np.random.uniform(5, 15) for m in M for t in T for c in C}
    
    print(f"[DEBUG] Built simplified network: {len(set(nodes))} nodes, "
        f"{len(regular_arcs)} regular arcs, {len(qq_arcs)} qq arcs")
    
    return {
        'nodes': list(set(nodes)),
        'regular_arcs': regular_arcs,
        'qq_arcs': qq_arcs,
        'D': D,
        'C': C
    }
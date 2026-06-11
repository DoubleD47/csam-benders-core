import numpy as np

def build_network(M, traditional_m_dict, L, K, T, D=None, seed=456):
    np.random.seed(seed)
    C = [(l, k) for l in L for k in K]                     # All commodities: (l1/l2, k1..k5)

    nodes = set()
    regular_arcs = []
    qq_arcs = []

    max_t = max(T)
    l2_locations = set(traditional_m_dict.values())

    # === NODE CREATION (no dummy node) ===
    for t in T:
        for c in C:
            nodes.add(('source', t, c))                     # Source injects demand for (t, c)
            nodes.add(('ss', None, c))                      # Single global super-sink for all met + unmet demand

            for m in M:
                nodes.add((f'{m}_in', t, c))                # Entry point at main node m
                nodes.add((f'{m}_q_l1', t, c))              # l1 queue - always present
                nodes.add((f'{m}_q_l2', t, c))              # l2 queue - always present (capacity controls usage)

    nodes = list(nodes)

    # === REGULAR ARCS ===
    for t in T:
        for c in C:
            l, k = c
            matching_m = traditional_m_dict.get(k)

            for m in M:
                # Source injection
                regular_arcs.append(('source', f'{m}_in', t, c))

                # Demand can travel between any _in nodes in the same time period
                for m2 in M:
                    if m != m2:
                        regular_arcs.append((f'{m}_in', f'{m2}_in', t, c))

                # Enter queues from _in (critical routing to service)
                regular_arcs.append((f'{m}_in', f'{m}_q_l1', t, c))   # Always to l1 queue
                regular_arcs.append((f'{m}_in', f'{m}_q_l2', t, c))   # Always to l2 queue (capacity will gate l1 crossover)

                # Service arcs: queue -> super-sink (normal repair/service cost)
                regular_arcs.append((f'{m}_q_l1', 'ss', t, c))
                regular_arcs.append((f'{m}_q_l2', 'ss', t, c))

                # Last period: direct dummy/write-off arcs to super-sink (high dummy cost)
                if t == max_t:
                    regular_arcs.append((f'{m}_in', 'ss', t, c))       # Direct write-off from entry point
                    regular_arcs.append((f'{m}_q_l1', 'ss', t, c))     # From l1 queue
                    regular_arcs.append((f'{m}_q_l2', 'ss', t, c))     # From l2 queue

    # === QUEUE CARRY-OVER ARCS ===
    for i in range(len(T)-1):
        tc = T[i]
        tn = T[i+1]
        for c in C:
            for m in M:
                qq_arcs.append((f'{m}_q_l1', f'{m}_q_l1', tc, c, tn))   # Carry l1 queue forward
                qq_arcs.append((f'{m}_q_l2', f'{m}_q_l2', tc, c, tn))   # Carry l2 queue forward

    # Default demand with clear debug message
    if D is None:
        print("[DEBUG] No demand was specified. Using default random values (5-15 per (m,t,c)).")
        D = {(m, t, c): np.random.uniform(5, 15) for m in M for t in T for c in C}

    print(f"[DEBUG] Built network: {len(nodes)} nodes, {len(regular_arcs)} regular arcs, {len(qq_arcs)} qq arcs")
    return {'nodes': nodes, 'regular_arcs': regular_arcs, 'qq_arcs': qq_arcs, 'D': D, 'C': C}
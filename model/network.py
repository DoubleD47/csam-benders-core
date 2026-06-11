import numpy as np

def build_network(M, traditional_m_dict, L, K, T, D=None, seed=456):
    """
    Build the time-expanded network for CSAM deployment optimization.
    - All demands can travel between _in nodes.
    - l1 demands can use any l1 facility or crossover to matching l2 facility.
    - l2 demands are restricted to their traditional location.
    - Direct write-off (high dummy cost) from _in or queues to ss in last period.
    """
    np.random.seed(seed)
    C = [(l, k) for l in L for k in K]                     # All commodities: (l1/l2, k1..k5)

    nodes = set()
    regular_arcs = []
    qq_arcs = []

    max_t = max(T)
    l2_locations = set(traditional_m_dict.values())        # m nodes with traditional l2 facilities

    # === NODE CREATION ===
    for t in T:
        for c in C:
            nodes.add(('source', t, c))                     # Source injects demand for this (t, c)
            nodes.add(('ss', None, c))                      # Global super-sink collects ALL met + unmet demand

            for m in M:
                nodes.add((f'{m}_in', t, c))                # Entry point at main node m for this time/commodity
                nodes.add((f'{m}_q_l1', t, c))              # l1 queue - always present
                nodes.add((f'{m}_q_l2', t, c))              # l2 queue - always present (capacity will control usage)

    nodes = list(nodes)

    # === REGULAR ARCS ===
    for t in T:
        for c in C:
            l, k = c
            matching_m = traditional_m_dict.get(k)          # Traditional m for this k (for l2 + crossover)

            for m in M:
                # Source injection at every entry point
                regular_arcs.append(('source', f'{m}_in', t, c))

                # Demand can travel between any _in nodes in the same time period
                for m2 in M:
                    if m != m2:
                        regular_arcs.append((f'{m}_in', f'{m2}_in', t, c))

                # Enter queues from _in (critical for routing to service)
                regular_arcs.append((f'{m}_in', f'{m}_q_l1', t, c))   # Always to l1 queue
                regular_arcs.append((f'{m}_in', f'{m}_q_l2', t, c))   # Always to l2 queue (capacity gates l1 crossover to matching k)

                # Normal service arcs: queue -> super-sink (pay service cost)
                regular_arcs.append((f'{m}_q_l1', 'ss', t, c))         # l1 service (any k)
                regular_arcs.append((f'{m}_q_l2', 'ss', t, c))         # l2 service (native + allowed l1 crossover)

                # Last period: direct write-off arcs to super-sink (high dummy cost)
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
                # Carry l1 queue forward (pay carry-over cost)
                qq_arcs.append((f'{m}_q_l1', f'{m}_q_l1', tc, c, tn))
                # Carry l2 queue forward (pay carry-over cost)
                qq_arcs.append((f'{m}_q_l2', f'{m}_q_l2', tc, c, tn))

    # Default demand with clear message
    if D is None:
        print("[DEBUG] No demand was specified. Using default random values (5-15 per (m,t,c)).")
        D = {(m, t, c): np.random.uniform(5, 15) for m in M for t in T for c in C}

    print(f"[DEBUG] Built network: {len(nodes)} nodes, {len(regular_arcs)} regular arcs, {len(qq_arcs)} qq arcs")
    return {
        'nodes': nodes,
        'regular_arcs': regular_arcs,
        'qq_arcs': qq_arcs,
        'D': D,
        'C': C
    }
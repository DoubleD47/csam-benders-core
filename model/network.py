import numpy as np

# This function builds the network structure for the CSAM deployment problem. It creates nodes and arcs based on the specified logic, including source injection, demand movement between entry points, queueing for service, and direct write-off options in the last period. The function also allows for custom demand input and includes debug print statements to verify the network construction.
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

    nodes = set() # set() will automatically handle duplicates as we add nodes in loops
    regular_arcs = [] # Everything but queue carry-over arcs
    qq_arcs = [] # Queue carry-over arcs (q at t -> q at t+1)

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
            matching_m = traditional_m_dict.get(k)

            for m in M:
                regular_arcs.append(('source', f'{m}_in', t, c))

                # Full connectivity between entry points
                for m2 in M:
                    if m != m2:
                        regular_arcs.append((f'{m}_in', f'{m2}_in', t, c))

                # Always to l1 queue
                regular_arcs.append((f'{m}_in', f'{m}_q_l1', t, c))

                # Restricted l2 queue access
                if l == 2 or matching_m == m:
                    regular_arcs.append((f'{m}_in', f'{m}_q_l2', t, c))

                # Service arcs
                regular_arcs.append((f'{m}_q_l1', 'ss', t, c))
                regular_arcs.append((f'{m}_q_l2', 'ss', t, c))

                # Last period write-offs
                if t == max_t:
                    regular_arcs.append((f'{m}_in', 'ss', t, c))
                    regular_arcs.append((f'{m}_q_l1', 'ss', t, c))
                    regular_arcs.append((f'{m}_q_l2', 'ss', t, c))

# === QUEUE CARRY-OVER ARCS ===
    for i in range(len(T)-1):
        tc = T[i]
        tn = T[i+1]
        for c in C:
            for m in M:
                qq_arcs.append((f'{m}_q_l1', f'{m}_q_l1', tc, c, tn))
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
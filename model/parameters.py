import numpy as np

def get_default_params():
    return {
        'M': ['m1','m2','m3','m4','m5','m6','m7','m8','m9','m10'],
        'traditional_m_dict': {'k1':'m1','k2':'m2','k3':'m3','k4':'m4','k5':'m5'},
        'L': ['l1', 'l2'],
        'K': ['k1','k2','k3','k4','k5'],
        # 12 weekly periods = one quarter; labels 1..12 (no T=0 needed — see README)
        'T': list(range(1, 13)),
        
        'F': {m: 100 for m in ['m1','m2','m3','m4','m5','m6','m7','m8','m9','m10']},  # uniform CSAM opening cost per site
        'C_in_q': 1.0,      # cost to enter queue from _in
        'C_q_q': 0.5,       # queue carry-over cost
        'C_service_l1': 20.0,  # cold spray (CSAM) repair cost (q_l1 -> ss)
        'C_service_l2': 5.0,   # traditional repair cost (q_l2 -> ss)

        # Differentiated dummy / write-off costs
        'C_dummy_in': 1000.0,    # High penalty: demand that never leaves _in (pure abandonment)
        'C_dummy_queue': 500.0,  # Medium penalty: reached a queue but couldn't be serviced by end of horizon

        'C_dummy': 100.0,   # legacy / fallback (can be deprecated later)
        'U_l1': 80,        # capacity of l1 (traditional)
        'U_l2': {'k1':100, 'k2':100, 'k3':100, 'k4':100, 'k5':100}, # capacities of l2 (CSAM) - can be varied by k
        
        # Demand control parameters
        'demand_mean': 10.0,
        'demand_scale': 1.0,      
        'MAX_CSAM_FACILITIES': 3,
        'SEED': 456,
        'EPS': 1e-4,
        'MAX_ITER': 20,
        'EXPERIMENT_NAME': "default_run"
    }


def generate_demand(M, T, C, mean=10.0, scale=1.0, seed=456):
    """
    Generate demand dictionary. 
    Easy to scale for experiments (low/med/high demand).
    """
    np.random.seed(seed)
    return {
        (m, t, c): np.random.uniform(5 * scale, 15 * scale) 
        for m in M 
        for t in T 
        for c in C
    }
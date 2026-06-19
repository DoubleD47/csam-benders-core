import numpy as np

def get_default_params():
    return {
        'M': ['m1','m2','m3','m4','m5','m6','m7','m8','m9','m10'],
        'traditional_m_dict': {'k1':'m1','k2':'m2','k3':'m3','k4':'m4','k5':'m5'},
        'L': ['l1', 'l2'],
        'K': ['k1','k2','k3','k4','k5'],
        # 12 weekly periods = one quarter; labels 1..12 (no T=0 needed — see README)
        'T': list(range(1, 13)),

        'F': {m: 100 for m in ['m1','m2','m3','m4','m5','m6','m7','m8','m9','m10']},
        'C_in_q': 1.0,
        'C_q_q': 0.5,
        'C_service_l1': 20.0,
        'C_service_l2': 5.0,

        'C_dummy_in': 1000.0,
        'C_dummy_queue': 500.0,
        'C_dummy': 100.0,
        'U_l1': 80,
        'U_l2': {'k1':100, 'k2':100, 'k3':100, 'k4':100, 'k5':100},

        # Demand: independent Normal draws per (node m, period t, commodity c)
        'demand_mean': 10.0,
        'demand_variance': 9.0,   # variance of N(mean, variance); std = 3
        'demand_scale': 1.0,      # legacy multiplier on mean (optional)
        'MAX_CSAM_FACILITIES': 3,
        'SEED': 456,
        'EPS': 1e-4,
        'MAX_ITER': 20,
        'EXPERIMENT_NAME': "default_run"
    }


def generate_demand(M, T, C, mean=10.0, variance=9.0, seed=456, scale=1.0, min_demand=0.0):
    """
    Generate demand dictionary with independent Normal samples.

    Each (m, t, c) — every node / time / commodity tuple — draws from the same
    N(mean * scale, variance * scale^2) distribution but receives its own sample.

    Negative draws are clipped to min_demand (default 0).
    """
    np.random.seed(seed)
    effective_mean = mean * scale
    effective_std = np.sqrt(variance) * scale
    return {
        (m, t, c): float(max(min_demand, np.random.normal(effective_mean, effective_std)))
        for m in M
        for t in T
        for c in C
    }
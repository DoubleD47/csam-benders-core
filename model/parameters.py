def get_default_params():
    return {
        'M': ['m1','m2','m3','m4','m5','m6','m7','m8','m9','m10'],
        'traditional_m_dict': {'k1':'m1','k2':'m2','k3':'m3','k4':'m4','k5':'m5'},
        'L': ['l1', 'l2'],
        'K': ['k1','k2','k3','k4','k5'],
        'T': [1, 2],
        
        'F': {m: 1000 for m in ['m1','m2','m3','m4','m5','m6','m7','m8','m9','m10']},
        'C_in_in': 3,
        'C_in_q': 10,
        'C_q_r_l1': 25,
        'C_q_r_l2': 20,
        'C_q_q': 50,
        'C_dummy': 5000,
        'U_l1': 80,
        'U_l2': {'k1':100, 'k2':100, 'k3':100, 'k4':100, 'k5':100},
        
        'MAX_CSAM_FACILITIES': 3,
        'SEED': 456,
        'EPS': 1e-4,
        'MAX_ITER': 50,
        'EXPERIMENT_NAME': "default_run"
    }
from concurrent.futures import ProcessPoolExecutor, as_completed
from model.core import solve_benders
from model.parameters import get_default_params
import itertools
import json

def run_one(args):
    combo, seed = args
    params = get_default_params()
    params.update(combo)
    params['SEED'] = seed
    return solve_benders(params)

if __name__ == "__main__":
    # Define sweep
    param_grid = [
        {'MAX_CSAM_FACILITIES': mc, 'U_l1': ul, 'C_dummy': cd}
        for mc in [2,3,4,5]
        for ul in [50,80,100,120]
        for cd in [2000,5000,10000]
    ]

    seeds = list(range(100, 108))   # 8 seeds

    tasks = list(itertools.product(param_grid, seeds))

    with ProcessPoolExecutor(max_workers=4) as executor:  # adjust to your CPU cores
        futures = [executor.submit(run_one, task) for task in tasks]
        for future in as_completed(futures):
            future.result()  # will raise if any error
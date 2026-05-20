from model.core import solve_benders
from model.parameters import get_default_params
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max_csam", type=int, default=3)
    parser.add_argument("--u_l1", type=int, default=80)
    parser.add_argument("--c_dummy", type=float, default=5000)
    parser.add_argument("--seed", type=int, default=456)
    args = parser.parse_args()

    params = get_default_params()
    params.update({
        'MAX_CSAM_FACILITIES': args.max_csam,
        'U_l1': args.u_l1,
        'C_dummy': args.c_dummy,
        'SEED': args.seed
    })

    solve_benders(params)
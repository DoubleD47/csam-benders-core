# CSAM Experiment Report: 2026-06-18_110719_sweep_csam3_dm10.0_ds1.0_F100_s456

_Generated: 2026-06-18 11:07:40_

## Configuration

- **Scenario:** csam3_dm10.0_ds1.0_F100_s456
- **MAX_CSAM_FACILITIES:** 3
- **Seed:** 456
- **Demand mean / scale:** 10.0 / 1.0
- **CSAM opening cost (F):** 100

## Results

- **Objective (total cost):** 15419.93
- **Subproblem cost:** 15319.93
- **Deployment cost:** 100.00
- **CSAM deployed:** m9 (1 facilities)
- **Total demand:** 4008.9
- **Unmet demand:** 0.0 (0.0%)
- **Benders iterations:** 20
- **Runtime (s):** 20.7

## Output Files

- **regular flows:** `experiments\2026-06-18_110719_sweep_csam3_dm10.0_ds1.0_F100_s456\visualizations\flows_regular.csv`
- **qq flows:** `experiments\2026-06-18_110719_sweep_csam3_dm10.0_ds1.0_F100_s456\visualizations\flows_qq.csv`
- **Full log:** `C:\git\csam-benders-core\experiments\2026-06-18_110719_sweep_csam3_dm10.0_ds1.0_F100_s456\summary.json`

## Full Parameters

```json
{
  "M": [
    "m1",
    "m2",
    "m3",
    "m4",
    "m5",
    "m6",
    "m7",
    "m8",
    "m9",
    "m10"
  ],
  "traditional_m_dict": {
    "k1": "m1",
    "k2": "m2",
    "k3": "m3",
    "k4": "m4",
    "k5": "m5"
  },
  "L": [
    "l1",
    "l2"
  ],
  "K": [
    "k1",
    "k2",
    "k3",
    "k4",
    "k5"
  ],
  "T": [
    1,
    2,
    3,
    4
  ],
  "F": {
    "m1": 100,
    "m2": 100,
    "m3": 100,
    "m4": 100,
    "m5": 100,
    "m6": 100,
    "m7": 100,
    "m8": 100,
    "m9": 100,
    "m10": 100
  },
  "C_in_q": 1.0,
  "C_q_q": 0.5,
  "C_service_l1": 20.0,
  "C_service_l2": 5.0,
  "C_dummy_in": 1000.0,
  "C_dummy_queue": 500.0,
  "C_dummy": 100.0,
  "U_l1": 80,
  "U_l2": {
    "k1": 100,
    "k2": 100,
    "k3": 100,
    "k4": 100,
    "k5": 100
  },
  "demand_mean": 10.0,
  "demand_scale": 1.0,
  "MAX_CSAM_FACILITIES": 3,
  "SEED": 456,
  "EPS": 0.0001,
  "MAX_ITER": 20,
  "EXPERIMENT_NAME": "sweep_csam3_dm10.0_ds1.0_F100_s456",
  "F_cost": 100,
  "scenario_name": "csam3_dm10.0_ds1.0_F100_s456"
}
```

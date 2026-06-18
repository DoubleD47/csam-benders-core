# CSAM Factorial Sweep Report

_Sweep folder: `2026-06-18_f_sensitivity`_
_Generated: 2026-06-18 11:31:49_

## Factor Grid

- **MAX_CSAM_FACILITIES:** [3]
- **demand_mean:** [10.0]
- **demand_scale:** [1.0]
- **F_cost:** [25, 50, 100, 200, 400]
- **SEED:** [456]

- **Scenarios run:** 5
- **Full factorial size:** 5
- **Failed:** 0

## Summary Statistics

- **objective:** mean=55482.33, min=55352.33, max=55727.33
- **deployed_count:** mean=1.00, min=1.00, max=1.00
- **unmet_demand_pct:** mean=0.00, min=0.00, max=0.00
- **runtime_seconds:** mean=135.35, min=101.05, max=153.05

## Deployment Frequency

- **m8:** 5 scenarios (100%)

## Scenario Results

| scenario | MAX_CSAM_FACILITIES | demand_scale | F_cost | SEED | objective | deployed_count | deployed_facilities | unmet_demand_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| csam3_dm10.0_ds1.0_F100_s456 | 3 | 1.00 | 100 | 456 | 55427.33 | 1 | m8 | 0.00 |
| csam3_dm10.0_ds1.0_F200_s456 | 3 | 1.00 | 200 | 456 | 55527.33 | 1 | m8 | 0.00 |
| csam3_dm10.0_ds1.0_F25_s456 | 3 | 1.00 | 25 | 456 | 55352.33 | 1 | m8 | 0.00 |
| csam3_dm10.0_ds1.0_F400_s456 | 3 | 1.00 | 400 | 456 | 55727.33 | 1 | m8 | 0.00 |
| csam3_dm10.0_ds1.0_F50_s456 | 3 | 1.00 | 50 | 456 | 55377.33 | 1 | m8 | 0.00 |


## Figures

![demand_vs_repair_(csam3_dm10.0_ds1.0_F100_s456).png](visualizations/demand_vs_repair_(csam3_dm10.0_ds1.0_F100_s456).png)

![deployment_count_by_scenario.png](visualizations/deployment_count_by_scenario.png)

![deployment_frequency.png](visualizations/deployment_frequency.png)

![movement_heatmap_(all_scenarios).png](visualizations/movement_heatmap_(all_scenarios).png)

![movement_heatmap_(csam3_dm10.0_ds1.0_F100_s456).png](visualizations/movement_heatmap_(csam3_dm10.0_ds1.0_F100_s456).png)

![objective_by_F_cost.png](visualizations/objective_by_F_cost.png)

![objective_by_MAX_CSAM_FACILITIES.png](visualizations/objective_by_MAX_CSAM_FACILITIES.png)

![objective_by_SEED.png](visualizations/objective_by_SEED.png)

![objective_by_demand_scale.png](visualizations/objective_by_demand_scale.png)

![repair_heatmap_(all_scenarios).png](visualizations/repair_heatmap_(all_scenarios).png)

![repair_heatmap_(csam3_dm10.0_ds1.0_F100_s456).png](visualizations/repair_heatmap_(csam3_dm10.0_ds1.0_F100_s456).png)

![unmet_demand_by_scenario.png](visualizations/unmet_demand_by_scenario.png)

# CSAM Factorial Sweep Report

_Sweep folder: `2026-06-18_demand_sensitivity`_
_Generated: 2026-06-18 14:51:42_

## Factor Grid

- **MAX_CSAM_FACILITIES:** [3]
- **demand_mean:** [10.0]
- **demand_scale:** [0.8, 1.0, 1.2]
- **F_cost:** [100]
- **SEED:** [456]

- **Scenarios run:** 3
- **Full factorial size:** 3
- **Failed:** 0

## Summary Statistics

- **objective:** mean=59628.84, min=43636.86, max=79822.32
- **deployed_count:** mean=1.00, min=0.00, max=2.00
- **unmet_demand_pct:** mean=0.00, min=0.00, max=0.00
- **runtime_seconds:** mean=118.05, min=16.86, max=175.99

## Deployment Frequency

- **m7:** 1 scenarios (33%)
- **m2:** 1 scenarios (33%)
- **m10:** 1 scenarios (33%)

## Scenario Results

| scenario | MAX_CSAM_FACILITIES | demand_scale | F_cost | SEED | objective | deployed_count | deployed_facilities | unmet_demand_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| csam3_dm10.0_ds0.8_F100_s456 | 3 | 0.80 | 100 | 456 | 43636.86 | 0 | none | 0.00 |
| csam3_dm10.0_ds1.0_F100_s456 | 3 | 1.00 | 100 | 456 | 55427.33 | 1 | m7 | 0.00 |
| csam3_dm10.0_ds1.2_F100_s456 | 3 | 1.20 | 100 | 456 | 79822.32 | 2 | m2, m10 | 0.00 |


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

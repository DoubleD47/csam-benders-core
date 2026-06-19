# CSAM Factorial Sweep Report

_Sweep folder: `2026-06-18_normal_demand_pilot`_
_Generated: 2026-06-18 21:42:06_

## Factor Grid

- **MAX_CSAM_FACILITIES:** [3]
- **demand_mean:** [8.0, 10.0, 12.0]
- **demand_variance:** [9.0]
- **F_cost:** [100]
- **SEED:** [456]

- **Scenarios run:** 3
- **Full factorial size:** 3
- **Failed:** 0

## Summary Statistics

- **objective:** mean=60373.02, min=43809.12, max=81096.13
- **deployed_count:** mean=1.00, min=0.00, max=2.00
- **unmet_demand_pct:** mean=0.00, min=0.00, max=0.00
- **runtime_seconds:** mean=110.63, min=16.70, max=159.71

## Deployment Frequency

- **m9:** 1 scenarios (33%)
- **m1:** 1 scenarios (33%)
- **m10:** 1 scenarios (33%)

## Scenario Results

| scenario | MAX_CSAM_FACILITIES | demand_mean | demand_variance | F_cost | SEED | objective | deployed_count | deployed_facilities | unmet_demand_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| csam3_dm10.0_dv9.0_F100_s456 | 3 | 10.00 | 9.00 | 100 | 456 | 56213.79 | 1 | m9 | 0.00 |
| csam3_dm12.0_dv9.0_F100_s456 | 3 | 12.00 | 9.00 | 100 | 456 | 81096.13 | 2 | m1, m10 | 0.00 |
| csam3_dm8.0_dv9.0_F100_s456 | 3 | 8.00 | 9.00 | 100 | 456 | 43809.12 | 0 | none | 0.00 |


## Figures

![demand_vs_repair_(csam3_dm10.0_dv9.0_F100_s456).png](visualizations/demand_vs_repair_(csam3_dm10.0_dv9.0_F100_s456).png)

![deployment_count_by_scenario.png](visualizations/deployment_count_by_scenario.png)

![deployment_frequency.png](visualizations/deployment_frequency.png)

![movement_heatmap_(all_scenarios).png](visualizations/movement_heatmap_(all_scenarios).png)

![movement_heatmap_(csam3_dm10.0_dv9.0_F100_s456).png](visualizations/movement_heatmap_(csam3_dm10.0_dv9.0_F100_s456).png)

![objective_by_F_cost.png](visualizations/objective_by_F_cost.png)

![objective_by_MAX_CSAM_FACILITIES.png](visualizations/objective_by_MAX_CSAM_FACILITIES.png)

![objective_by_SEED.png](visualizations/objective_by_SEED.png)

![objective_by_demand_mean.png](visualizations/objective_by_demand_mean.png)

![objective_by_demand_variance.png](visualizations/objective_by_demand_variance.png)

![repair_heatmap_(all_scenarios).png](visualizations/repair_heatmap_(all_scenarios).png)

![repair_heatmap_(csam3_dm10.0_dv9.0_F100_s456).png](visualizations/repair_heatmap_(csam3_dm10.0_dv9.0_F100_s456).png)

![unmet_demand_by_scenario.png](visualizations/unmet_demand_by_scenario.png)

# CSAM Factorial Sweep Report

_Sweep folder: `2026-06-18_quick`_
_Generated: 2026-06-18 11:08:28_

## Factor Grid

- **MAX_CSAM_FACILITIES:** [1, 3]
- **demand_mean:** [10.0]
- **demand_scale:** [1.0]
- **F_cost:** [100]
- **SEED:** [456, 123]

- **Scenarios run:** 4
- **Full factorial size:** 4
- **Failed:** 0

## Summary Statistics

- **objective:** mean=15782.14, min=15419.93, max=16144.34
- **deployed_count:** mean=1.00, min=1.00, max=1.00
- **unmet_demand_pct:** mean=0.00, min=0.00, max=0.00
- **runtime_seconds:** mean=20.85, min=20.74, max=20.96

## Deployment Frequency

- **m9:** 4 scenarios (100%)

## Scenario Results

| scenario | MAX_CSAM_FACILITIES | demand_scale | F_cost | SEED | objective | deployed_count | deployed_facilities | unmet_demand_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| csam1_dm10.0_ds1.0_F100_s123 | 1 | 1.00 | 100 | 123 | 16144.34 | 1 | m9 | 0.00 |
| csam1_dm10.0_ds1.0_F100_s456 | 1 | 1.00 | 100 | 456 | 15419.93 | 1 | m9 | 0.00 |
| csam3_dm10.0_ds1.0_F100_s123 | 3 | 1.00 | 100 | 123 | 16144.34 | 1 | m9 | 0.00 |
| csam3_dm10.0_ds1.0_F100_s456 | 3 | 1.00 | 100 | 456 | 15419.93 | 1 | m9 | 0.00 |


## Figures

![demand_vs_repair_(csam1_dm10.0_ds1.0_F100_s123).png](visualizations/demand_vs_repair_(csam1_dm10.0_ds1.0_F100_s123).png)

![deployment_count_by_scenario.png](visualizations/deployment_count_by_scenario.png)

![deployment_frequency.png](visualizations/deployment_frequency.png)

![movement_heatmap_(all_scenarios).png](visualizations/movement_heatmap_(all_scenarios).png)

![movement_heatmap_(csam1_dm10.0_ds1.0_F100_s123).png](visualizations/movement_heatmap_(csam1_dm10.0_ds1.0_F100_s123).png)

![objective_by_F_cost.png](visualizations/objective_by_F_cost.png)

![objective_by_MAX_CSAM_FACILITIES.png](visualizations/objective_by_MAX_CSAM_FACILITIES.png)

![objective_by_SEED.png](visualizations/objective_by_SEED.png)

![objective_by_demand_scale.png](visualizations/objective_by_demand_scale.png)

![repair_heatmap_(all_scenarios).png](visualizations/repair_heatmap_(all_scenarios).png)

![repair_heatmap_(csam1_dm10.0_ds1.0_F100_s123).png](visualizations/repair_heatmap_(csam1_dm10.0_ds1.0_F100_s123).png)

![unmet_demand_by_scenario.png](visualizations/unmet_demand_by_scenario.png)

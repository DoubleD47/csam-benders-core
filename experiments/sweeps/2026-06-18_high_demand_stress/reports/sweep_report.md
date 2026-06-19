# CSAM Factorial Sweep Report

_Sweep folder: `2026-06-18_high_demand_stress`_
_Generated: 2026-06-18 21:59:53_

## Factor Grid

- **MAX_CSAM_FACILITIES:** [5]
- **demand_mean:** [14.0, 16.0, 18.0]
- **demand_variance:** [16.0]
- **F_cost:** [100]
- **SEED:** [456]

- **Scenarios run:** 3
- **Full factorial size:** 3
- **Failed:** 0

## Summary Statistics

- **objective:** mean=143687.01, min=108154.62, max=187052.08
- **deployed_count:** mean=4.33, min=3.00, max=5.00
- **unmet_demand_pct:** mean=0.04, min=0.00, max=0.11
- **runtime_seconds:** mean=146.04, min=142.53, max=149.89

## Deployment Frequency

- **m1:** 3 scenarios (100%)
- **m2:** 2 scenarios (67%)
- **m10:** 2 scenarios (67%)
- **m5:** 1 scenarios (33%)
- **m6:** 1 scenarios (33%)
- **m8:** 1 scenarios (33%)
- **m9:** 1 scenarios (33%)
- **m3:** 1 scenarios (33%)
- **m4:** 1 scenarios (33%)

## Scenario Results

| scenario | MAX_CSAM_FACILITIES | demand_mean | demand_variance | F_cost | SEED | objective | deployed_count | deployed_facilities | unmet_demand_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| csam5_dm14.0_dv16.0_F100_s456 | 5 | 14.00 | 16.00 | 100 | 456 | 108154.62 | 3 | m1, m2, m10 | 0.00 |
| csam5_dm16.0_dv16.0_F100_s456 | 5 | 16.00 | 16.00 | 100 | 456 | 135854.33 | 5 | m1, m5, m6, m8, m9 | 0.00 |
| csam5_dm18.0_dv16.0_F100_s456 | 5 | 18.00 | 16.00 | 100 | 456 | 187052.08 | 5 | m1, m2, m3, m4, m10 | 0.11 |


## Figures

![demand_vs_repair_(csam5_dm16.0_dv16.0_F100_s456).png](visualizations/demand_vs_repair_(csam5_dm16.0_dv16.0_F100_s456).png)

![deployment_count_by_scenario.png](visualizations/deployment_count_by_scenario.png)

![deployment_frequency.png](visualizations/deployment_frequency.png)

![movement_heatmap_(all_scenarios).png](visualizations/movement_heatmap_(all_scenarios).png)

![movement_heatmap_(csam5_dm16.0_dv16.0_F100_s456).png](visualizations/movement_heatmap_(csam5_dm16.0_dv16.0_F100_s456).png)

![objective_by_F_cost.png](visualizations/objective_by_F_cost.png)

![objective_by_MAX_CSAM_FACILITIES.png](visualizations/objective_by_MAX_CSAM_FACILITIES.png)

![objective_by_SEED.png](visualizations/objective_by_SEED.png)

![objective_by_demand_mean.png](visualizations/objective_by_demand_mean.png)

![objective_by_demand_variance.png](visualizations/objective_by_demand_variance.png)

![repair_heatmap_(all_scenarios).png](visualizations/repair_heatmap_(all_scenarios).png)

![repair_heatmap_(csam5_dm16.0_dv16.0_F100_s456).png](visualizations/repair_heatmap_(csam5_dm16.0_dv16.0_F100_s456).png)

![unmet_demand_by_scenario.png](visualizations/unmet_demand_by_scenario.png)

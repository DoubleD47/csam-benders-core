# Factorial 1 — 270-run full factorial (2026-06-18)

Technical note for us. Formulation below matches `model/parameters.py`, `model/network.py`, and `model/core.py` as implemented for this sweep. Results are from the existing 270 summary JSONs via `summarize_sweep.py`. No new factorial was run.

## 1. Introduction

This sweep is the completed full factorial at `experiments/sweeps/2026-06-18_full_factorial/`: 10 CSAM budgets × 3 demand means × 3 demand variances × 1 opening cost × 3 seeds = **270** Benders runs (`MAX_ITER = 20`).

The model deploys mobile CSAM (`l1`) units on a 10-node network that already has traditional (`l2`) repair at `m1`–`m5`. Demand is a 12-week, commodity-specific min-cost flow. Recourse is solved by Benders: binary deployments in the master, flows in the subproblem.

An earlier draft of this note used a two-period network with `r` / `out` / dummy nodes and stale costs (`U_{l1}=50`, `C_{q\text{-}r}`, etc.). That is not the code that produced these 270 results. Sections 2–3 replace that writeup. Sections 4–6 are the experimental design, CSV results, and limitations. Do not start the next factorial from this note.

## 2. Formulation (as implemented)

### 2.1 Sets

| Set | Code | Meaning |
|-----|------|---------|
| $M=\{m1,\dots,m10\}$ | `M` | candidate CSAM sites |
| $L=\{l1,l2\}$ | `L` | repair types (CSAM-flexible vs traditional-only) |
| $K=\{k1,\dots,k5\}$ | `K` | vehicle / repair classes |
| $C=L\times K$ | `C` | 10 commodities $(l,k)$ |
| $T=\{1,\dots,12\}$ | `T = list(range(1, 13))` | weekly periods (one quarter) |
| $t^{\max}=\max T=12$ | `max_t` | last period |

Traditional `l2` sites: $k1\mapsto m1,\dots,k5\mapsto m5$ (`traditional_m_dict`). There is **no** $T=\{1,2\}$ in this model, and **no** `r` / `out` / dummy nodes.

### 2.2 Parameters (defaults used in the sweep)

From `get_default_params()`, with sweep factors overwriting budget, demand law, seed, and $F$.

| Symbol | Code | Sweep value |
|--------|------|-------------|
| $F_m$ | `F[m]`, `F_cost` | $100$ at every $m$ |
| $U_{l1}$ | `U_l1` | $80$ CSAM jobs / deployed site / week |
| $U_{l2,k}$ | `U_l2[k]` | $100$ traditional jobs / class $k$ / week |
| $c^{\text{in}\to q}$ | `C_in_q` | $1$ |
| $c^{q\to q}$ | `C_q_q` | $0.5$ |
| $c^{\text{svc},l1}$ | `C_service_l1` | $20$ |
| $c^{\text{svc},l2}$ | `C_service_l2` | $5$ |
| $c^{\text{wo,in}}$ | `C_dummy_in` | $1000$ |
| $c^{\text{wo,q}}$ | `C_dummy_queue` | $500$ |
| $\varepsilon$ | `EPS` | $10^{-4}$ |
| $I_{\max}$ | `MAX_ITER` | $20$ |

`C_dummy = 100` is still in `parameters.py` but is **not** used in `core.py`. Same-period `_in → _in` travel has cost **0**.

Demand (independent per $(m,t,c)$):

$$
D_{m,t,c}=\max\bigl(0,\; Z_{m,t,c}\bigr),\qquad Z_{m,t,c}\stackrel{\text{iid}}{\sim}\mathcal N(\mu,\sigma^2)
$$

with $\mu=$ `demand_mean`, $\sigma^2=$ `demand_variance`, `numpy.random.seed(SEED)`. `demand_scale=1` in this sweep, so the coded $N(\mu\cdot\text{scale},\;\sigma^2\cdot\text{scale}^2)$ is just $N(\mu,\sigma^2)$. That is $10\times 12\times 10=1200$ draws per scenario.

### 2.3 Time-expanded network

`build_network` builds one copy of the graph per $(t,c)$. Node types:

- `source` at $(t,c)$ — injects demand
- $m_{\text{in}}$ at $(t,c)$ — entry / transfer at site $m$
- $m_{q_{l1}}$, $m_{q_{l2}}$ at $(t,c)$ — CSAM and traditional queues
- `ss` per commodity (time-less super-sink)

Regular arcs $A^{\text{reg}}$ (all same $t$ except `ss`):

1. `source` $\to m_{\text{in}}$ for every $m$ (demand injection).
2. $m_{\text{in}}\to m'_{\text{in}}$ for $m\neq m'$ (same-period travel, cost 0).
3. $m_{\text{in}}\to m_{q_{l1}}$ always.
4. $m_{\text{in}}\to m_{q_{l2}}$ only if $l=l2$ **or** $m$ is the matching traditional site for $k$ (`l1` crossover).
5. $m_{q_{l1}}\to\texttt{ss}$ and $m_{q_{l2}}\to\texttt{ss}$ every week (service).
6. At $t=t^{\max}$ only: $m_{\text{in}}\to\texttt{ss}$ (unconstrained `_in` write-off).

Queue carry-over $A^{\text{qq}}$: $m_{q_{lp},t}\to m_{q_{lp},t+1}$ for $t=1,\dots,11$ and $lp\in\{l1,l2\}$. Twelve weeks imply **11** carry-over intervals.

**Last-period write-off (important).** `network.py` also appends $q\to\texttt{ss}$ at $t=t^{\max}$, but that tuple is the **same key** as the service arc. PuLP therefore has one variable. In the objective, that variable is charged $c^{\text{wo,q}}=500$ rather than the service cost; in the capacity constraints it still counts as service flow. So **queued last-period write-off is capacity-constrained**. Only `_in\to ss` at $t=12$ is a free (high-penalty) dump.

There is **no** `_in` carry-over across weeks. Demand at $t<12$ must leave $m_{\text{in}}$ the same week (travel to another `_in`, or enter a queue).

### 2.4 Master problem

Binary $y_m$ = deploy CSAM at $m$. $\theta\ge 0$ approximates recourse.

$$
\begin{align}
\min_{y,\theta}\quad
& \sum_{m\in M} F_m y_m + \theta \\
\text{s.t.}\quad
& \sum_{m\in M} y_m \le \texttt{MAX\_CSAM\_FACILITIES} \\
& y_m\in\{0,1\},\quad \theta\ge 0 \\
& \text{optimality cuts and feasibility cuts from the loop.}
\end{align}
$$

Stop when $UB-LB\le\varepsilon$ or after $I_{\max}=20$ iterations (`while ub - lb > EPS and iter_count < MAX_ITER`).

### 2.5 Primal subproblem (fixed $\bar y$)

Flows $x_a\ge 0$ on $A^{\text{reg}}$, $x^{qq}_a\ge 0$ on $A^{\text{qq}}$. Objective as coded in `core.py`:

$$
\begin{align}
Q(\bar y)=\min\quad
& c^{\text{in}\to q}\sum_{\text{in}\to q}x_a
+ c^{q\to q}\sum_{A^{\text{qq}}}x^{qq}_a \\
& + c^{\text{svc},l1}\sum_{\substack{q_{l1}\to\texttt{ss}\\ t\neq t^{\max}}}x_a
+ c^{\text{svc},l2}\sum_{\substack{q_{l2}\to\texttt{ss}\\ t\neq t^{\max}}}x_a \\
& + c^{\text{wo,in}}\sum_{\substack{\text{in}\to\texttt{ss}\\ t=t^{\max}}}x_a
+ c^{\text{wo,q}}\sum_{\substack{q\to\texttt{ss}\\ t=t^{\max}}}x_a.
\end{align}
$$

Constraints:

- Injection: $x_{\texttt{source}\to m_{\text{in}},t,c}=D_{m,t,c}$.
- Flow balance at every node except `source` and last-period `_in` (write-off arcs exist). Super-sink: inflow $= \sum_{m,t}D_{m,t,c}$ per commodity.
- CSAM capacity (named `cap_l1_{m}_{t}`, **all** $t$ including $t^{\max}$):

$$
\sum_{c:\,l(c)=l1} x_{m_{q_{l1}}\to\texttt{ss},\,t,c}
\le U_{l1}\,\bar y_m
\qquad\forall m\in M,\; t\in T.
$$

- Traditional capacity at the matching site $m(k)$ only:

$$
\sum_{c:\,k(c)=k} x_{m(k)_{q_{l2}}\to\texttt{ss},\,t,c}
\le U_{l2,k}
\qquad\forall k\in K,\; t\in T.
$$

If this LP is optimal, $UB\leftarrow\min(UB,\;\sum_m F_m\bar y_m+Q(\bar y))$ and an optimality cut is added. If it is infeasible, no incumbent is stored and a feasibility cut is added.

### 2.6 Dual of the subproblem and optimality cut

Let $\pi_{m,t}$ be the PuLP dual of the $\le$ CSAM capacity constraint (`cap_constraints[(m,t)].pi`). In a minimization LP these duals are typically $\le 0$. Let $\bar Q=Q(\bar y)$. The cut actually inserted is

$$
\theta \ge \bar Q + \sum_{m\in M}\sum_{t\in T}\pi_{m,t}\,U_{l1}\,(y_m-\bar y_m),
$$

i.e.

```text
cut_constant = sub_cost - sum(pi[m,t] * U_l1 * ybar[m])
theta >= cut_constant + sum(pi[m,t] * U_l1 * y[m])
```

Only CSAM duals enter the master. Traditional duals and node potentials are folded into $\bar Q$. Travel / queue / write-off costs never appear as explicit cut coefficients.

### 2.7 Feasibility cut actually used

On subproblem infeasibility, `core.py` prints “strong feasibility cut” but adds

$$
\sum_{m\in M} y_m \ge \min(\texttt{iter\_count},\;\texttt{MAX\_CSAM\_FACILITIES}).
$$

That is a **weak cardinality cut**: it does not forbid the specific infeasible $\bar y$, it only raises a lower bound on the number of open sites as the iteration index grows. Together with the budget upper bound, late iterations are forced toward using the full budget, but the master can still propose site combinations whose subproblem is infeasible.

## 3. Why some cells have infinite $UB$ / no incumbent

`ub` starts at $+\infty$. It is updated **only** when a subproblem is Optimal. If every one of the 20 iterations is infeasible, `best_y` stays `None`, `best_sub_cost` stays $\infty$, and `summary.json` writes `"objective": Infinity` with `subproblem_cost: null`, `deployed_facilities: []`, and `unmet_demand_pct: 0.0`.

That $0\%$ unmet is **not** a real outcome. It is “no incumbent flows.” `analyze_sweep.prepare_results_frame` flags these rows `infeasible_no_incumbent`, blanks `objective` / `unmet_demand_pct` / `deployed_count`, and keeps them out of cost averages. **Do not treat unmet $=0\%$ on those 36 rows as service success.**

Why the subproblem can be infeasible (rather than merely expensive): queued demand at $t=12$ can leave only on $q\to\texttt{ss}$, and that arc is still capped by $U_{l1}\bar y_m$ (and traditional $U_{l2}$). There is no unconstrained queue dump. Combined with no `_in` hold across weeks, demand from $t=1,\dots,11$ must enter queues. If CSAM capacity is too small, leftover queue inventory has no feasible outlet, CBC returns Infeasible, and $UB$ stays $\infty$.

In this factorial that happens only at **tight budget + high demand** (Section 5.1). Variance does not split those cells: when a $(\texttt{MAX\_CSAM},\mu)$ pair fails, all 3 variances $\times$ 3 seeds fail.

## 4. Experimental design

Grid from `experiment_scripts/sweep_utils.py` `DEFAULT_FACTOR_GRID` and `sweep_manifest.json` (`truncated: false`, `failed: []`):

| Factor | Levels | Count |
|--------|--------|------:|
| `MAX_CSAM_FACILITIES` | $1,2,\dots,10$ | 10 |
| `demand_mean` | $12,15,18$ | 3 |
| `demand_variance` | $4,9,16$ (std $2,3,4$) | 3 |
| `F_cost` | $100$ | 1 |
| `SEED` | $42,456,123$ | 3 |
| **product** | | **270** |

Everything else is the Section 2 default vector (`U_l1=80`, 12 weeks, costs above, `MAX_ITER=20`). Each cell is one independent demand realization, not a sample-average recourse.

`experiments/sweep_results.json` is an old 3-scenario pilot — ignore it. This writeup uses only

- `experiments/sweeps/2026-06-18_full_factorial/visualizations/sweep_results_table.csv`
- `experiments/sweeps/2026-06-18_full_factorial/visualizations/site_frequency.csv`

## 5. Results (feasible rows only unless noted)

270 result files. After inf-handling: **234 feasible**, **36 `infeasible_no_incumbent`**. 256 / 270 runs hit the 20-iteration cap (all 36 infeasible; 220 / 234 feasible). Full 270-row table is the CSV, not pasted here.

### 5.1 Feasibility pattern

Each $(\texttt{MAX\_CSAM},\mu)$ cell below is 9 runs (3 variances $\times$ 3 seeds). Entries are feasible / 9.

| MAX_CSAM | $\mu=12$ | $\mu=15$ | $\mu=18$ |
|---------:|:--------:|:--------:|:--------:|
| 1 | 9/9 | **0/9** | **0/9** |
| 2 | 9/9 | 9/9 | **0/9** |
| 3 | 9/9 | 9/9 | **0/9** |
| 4 | 9/9 | 9/9 | 9/9 |
| 5 | 9/9 | 9/9 | 9/9 |
| 6 | 9/9 | 9/9 | 9/9 |
| 7 | 9/9 | 9/9 | 9/9 |
| 8 | 9/9 | 9/9 | 9/9 |
| 9 | 9/9 | 9/9 | 9/9 |
| 10 | 9/9 | 9/9 | 9/9 |

The 36 infeasible runs are exactly:

- `MAX_CSAM=1` and $\mu\in\{15,18\}$ (18 runs)
- `MAX_CSAM=2` and $\mu=18$ (9 runs)
- `MAX_CSAM=3` and $\mu=18$ (9 runs)

No infeasible run at $\mu=12$. None at `MAX_CSAM` $\ge 4$. Raw JSONs for those 36 have `objective: Infinity` and `unmet_demand_pct: 0.0` with empty deployments — ignore the $0\%$.

### 5.2 Objective vs `demand_mean`

Mean $UB$ among **feasible** rows in that cell (9 rows when the cell is fully feasible). Em dash = all 9 infeasible (no incumbent; do not average). Values rounded to 0 decimals from the master CSV.

| MAX_CSAM | $\mu=12$ | $\mu=15$ | $\mu=18$ |
|---------:|---------:|---------:|---------:|
| 1 | 162,765 | — | — |
| 2 | 81,683 | 568,690 | — |
| 3 | 81,683 | 165,938 | — |
| 4 | 81,683 | 123,115 | 557,010 |
| 5 | 81,683 | 123,120 | 186,502 |
| 6 | 81,683 | 123,120 | 164,542 |
| 7 | 81,683 | 123,120 | 164,542 |
| 8 | 81,683 | 123,115 | 164,542 |
| 9 | 81,683 | 123,115 | 164,542 |
| 10 | 81,683 | 123,115 | 164,542 |

Pooled over feasible rows (so $\mu=15,18$ omit the infeasible tight-budget cells, which **raises** those means relative to a complete grid):

| $\mu$ | $n$ feasible | mean $UB$ | min | max |
|------:|-------------:|----------:|----:|----:|
| 12 | 90 | 89,791 | 78,201 | 249,561 |
| 15 | 81 | 177,383 | 119,549 | 662,334 |
| 18 | 63 | 223,746 | 160,966 | 650,654 |

Pattern: once the budget is large enough to cover the preferred deployment size (next subsection), extra `MAX_CSAM` does not change cost. Just below that size, cost jumps because the incumbent still exists but pays write-off / extra queueing (feasible unmet is only in those tight cells: max unmet $3.05\%$ at `MAX_CSAM=2`, $\mu=15$). Variance is second-order next to $\mu$ and budget.

### 5.3 Deployment count vs budget

Among 234 feasible rows, `deployed_count` $\in\{1,\dots,6\}$ — **never 7–10**. Crosstab of feasible runs:

| MAX_CSAM \ deployed | 1 | 2 | 3 | 4 | 5 | 6 |
|--------------------:|--:|--:|--:|--:|--:|--:|
| 1 | 9 |  |  |  |  |  |
| 2 |  | 18 |  |  |  |  |
| 3 |  | 9 | 9 |  |  |  |
| 4 |  | 9 |  | 18 |  |  |
| 5 |  | 9 |  | 9 | 9 |  |
| 6 |  | 9 |  | 9 |  | 9 |
| 7 |  | 9 |  | 9 |  | 9 |
| 8 |  | 9 |  | 9 |  | 9 |
| 9 |  | 9 |  | 9 |  | 9 |
| 10 |  | 9 |  | 9 |  | 9 |

By demand mean, when the budget does not bind:

| $\mu$ | preferred $|y|$ (feasible, non-binding) | sites used |
|------:|--------------------------:|------------|
| 12 | 2 | `{m1,m10}` or `{m1,m2}` (the 9 `MAX_CSAM=1` feasibles are all `{m9}` only) |
| 15 | 4 | `{m1,m2,m3,m10}` |
| 18 | 6 | `{m1,m2,m3,m4,m5,m10}` |

Only **7** distinct support sets appear in 234 feasibles: `{m9}` (9), `{m1,m2}` (18), `{m1,m10}` (72), `{m1,m2,m10}` (9), `{m1,m2,m3,m10}` (72), `{m1,m2,m3,m4,m10}` (9), `{m1,m2,m3,m4,m5,m10}` (45).

Opening cost is $100\times$ deployed count in every feasible row (`F_cost=100`).

### 5.4 Site frequency (feasible $n=234$)

From `site_frequency.csv` (count of feasible scenarios in which the site is open):

| node | feasible_scenarios_deployed | feasible_n | deployment_pct |
|------|----------------------------:|-----------:|---------------:|
| m1 | 225 | 234 | 96.2 |
| m10 | 207 | 234 | 88.5 |
| m2 | 153 | 234 | 65.4 |
| m3 | 126 | 234 | 53.8 |
| m4 | 54 | 234 | 23.1 |
| m5 | 45 | 234 | 19.2 |
| m9 | 9 | 234 | 3.8 |

Preferred sites: **m1, m10, m2, m3**. m4/m5 appear only in the high-demand 5–6 site plans. m9 appears only in the nine `MAX_CSAM=1`, $\mu=12$ runs. **m6, m7, m8 never deploy.**

### 5.5 Slack above 6 units

`budget_slack = MAX_CSAM_FACILITIES - deployed_count` (feasible rows).

| MAX_CSAM | $n$ feasible | slack min | slack max | mean slack | max deployed |
|---------:|-------------:|----------:|----------:|-----------:|-------------:|
| 1 | 9 | 0 | 0 | 0.0 | 1 |
| 2 | 18 | 0 | 0 | 0.0 | 2 |
| 3 | 18 | 0 | 1 | 0.5 | 3 |
| 4 | 27 | 0 | 2 | 0.67 | 4 |
| 5 | 27 | 0 | 3 | 1.33 | 5 |
| 6 | 27 | 0 | 4 | 2.0 | 6 |
| 7 | 27 | 1 | 5 | 3.0 | 6 |
| 8 | 27 | 2 | 6 | 4.0 | 6 |
| 9 | 27 | 3 | 7 | 5.0 | 6 |
| 10 | 27 | 4 | 8 | 6.0 | 6 |

For `MAX_CSAM` $\in\{7,8,9,10\}$ every feasible run has positive slack and deploys 2, 4, or 6 sites according to $\mu\in\{12,15,18\}$ (36 / 36 / 36). Those four budget levels are unused headroom, not extra CSAMs.

## 6. Discussion / limitations

- **Capacitated last-period write-off.** $q\to\texttt{ss}$ at $t=12$ is the service arc with a write-off cost. Tight CSAM budgets therefore go **infeasible**, not just high-cost. An unconstrained queue dump (or a distinct write-off arc outside capacity) would change both the 36 inf cells and the objective cliffs at `MAX_CSAM` just below the preferred $|y|$.
- **Weak feasibility cuts.** $\sum y\ge\min(\text{iter},\texttt{MAX\_CSAM})$ is not a combinatorial no-good cut on $\bar y$. The log line calling it “strong” is misleading. A proper feasibility cut (or an always-feasible dummy with a huge cost) would be the next solver change — not a new factorial.
- **`MAX_ITER=20`.** 256 / 270 runs stop on the iteration cap, not $UB-LB\le\varepsilon$. Plateau objectives at large budgets still line up across seeds, but we should not treat every $UB$ as proven optimal. Summaries do not store the final $LB$, so gaps are not in the CSV.
- **Infeasible rows in raw JSON.** `unmet_demand_pct=0` and `deployed_count=0` there are artifacts. Always filter on finite `objective` / `subproblem_cost`.
- **m6–m8 unused; m9 only at budget 1.** With identical $F_m$ and identical demand law at every node, CBC’s first feasible $y$ and the weak cuts can pick odd singletons. Site ranks m1/m10/m2/m3 are still stable once the budget is non-binding.
- **This note stops here.** Do not launch the next factorial until we decide whether to (i) make last-period queue write-off unconstrained, (ii) replace the weak feasibility cut, and/or (iii) raise `MAX_ITER` / record $LB$.

## 7. Data files

| File | Contents |
|------|----------|
| `experiments/sweeps/2026-06-18_full_factorial/visualizations/sweep_results_table.csv` | 270 rows (master table; `status`, `feasible`, costs, deployments, slack) |
| `experiments/sweeps/2026-06-18_full_factorial/visualizations/site_frequency.csv` | site counts among 234 feasibles |
| `experiments/sweeps/2026-06-18_full_factorial/results/*_summary.json` | per-scenario solver summaries (source of the CSVs) |
| `experiments/sweeps/2026-06-18_full_factorial/sweep_manifest.json` | factor grid, 270 names, `status: completed` |

Regenerate tables (no re-solve):

```text
python -m experiment_scripts.summarize_sweep --sweep-dir experiments/sweeps/2026-06-18_full_factorial
```

Do not pass `--analyze` unless figures are wanted. Ignore `experiments/sweep_results.json`.

# CSAM Deployment Optimization via Benders Decomposition

This project solves a multi-period facility deployment problem for **Cold-Spray Additive Manufacturing (CSAM)** mobile repair units that supplement existing traditional repair infrastructure. The model uses **Benders decomposition** to handle the large-scale mixed-integer linear program (MILP) arising from the time-expanded network flow formulation.

---

## Model Overview

The problem involves routing repair demand of type **(l, k)** across a network of main nodes (traditional repair sites). 

- **l ∈ {l1, l2}**: Repair type  
  - `l1`: Flexible — can be processed at any open CSAM facility or at the matching traditional l2 site.  
  - `l2`: Restricted — must be processed at its specific traditional facility (e.g., (l2, k1) only at m1).

- **k**: Specific repair class (k1, k2, ..., determined by parameters).

- **Mobile CSAM facilities** (`y_m`): Binary decisions indicating whether a mobile l1-capable unit is deployed at main node `m`.

Demand arrives at main nodes, can travel between nodes, enters repair queues, incurs queue carry-over costs between periods, and can be satisfied via traditional or CSAM repair. Unmet demand in the final period exits via dummy arcs at high penalty.

---

## Mathematical Formulation (Simplified)

### Sets
- $M$: Main nodes (traditional repair sites)
- $T$: Time periods
- $C = l \times k$: Commodities (repair types)
- $A$: Arcs
  - $A_r$: Regular arcs, for travel in between main nodes
  - $A_q$: Queuing arcs, entering the queue at a main node
  - $A_{qq}$: Queue carry-over arcs between time periods
  - $A_d$: Dummy arcs, carry unment demand from queue to super sink in the final time period
  - $A_{l1}, A_{l2}$: Repair arcs for cold spray and traditional repair to the super sink, respectively

### Variables
- $x_a^{t,c}$: Flow of commodity $c$ on regular arc $a$ in period $t$
- $x_{qq}^{t,t+1,c}_m$: Flow carried over in queue $m$ from $t$ to $t+1$
- $y_m \in \{0,1\}$: Deploy CSAM l1 facility at node $m$

### Objective
$$
\min \quad \sum_{t,c} \Big( \text{travel cost} + \text{queue cost} \Big) + C_{\text{dummy}} \cdot \text{unmet demand} + \text{fixed CSAM cost} \cdot \sum_m y_m
$$

### Flow Conservation (for most nodes)
For each node $n$, time $t$, commodity $c$:
$$
\sum_{a \in \delta^-(n)} x_a^{t,c} + \sum_{qq \in \delta^-_{qq}(n)} x_{qq} = \sum_{a \in \delta^+(n)} x_a^{t,c} + \sum_{qq \in \delta^+_{qq}(n)} x_{qq}
$$

Special nodes:
- **Source** injects demand $D_{m,t,c}$
- **Sink** (per period) → **Super-Sink** (global)
- **Dummy** (last period only) absorbs unmet demand

### Capacity Constraints (Subproblem)
$$
\sum_{c} x_{\text{repair}, m, c}^{t} \leq U_{l1} \cdot y_m \quad \forall m, t \quad \text{(l1 capacity)}
$$
$$
\sum_{\text{allowed } c} x_{\text{l2 repair}, m, c}^{t} \leq U_{l2,m} \quad \forall m, t
$$

### Benders Decomposition
- **Master Problem**: Optimizes facility locations $y_m$ (with feasibility and optimality cuts).
- **Subproblem**: Network flow LP for fixed $y$ (checks feasibility and provides dual-based cuts).

---

## Project Structure

csam-benders-core/
├── model/                          # Network builder + core Benders logic
├── experiment_scripts/             # Run single & sweep experiments
├── visualization_scripts/          # Network diagrams + result plots
├── config/                         # Default parameters
├── experiments/
│   └── sweeps/                     # Organized multi-scenario results
│       └── YYYY-MM-DD_sweep_vX/
│           ├── configs/
│           ├── results/
│           ├── logs/
│           └── visualizations/
├── README.md
└── requirements.txt


---

## Setup & Running

```bash
git clone https://github.com/DoubleD47/csam-benders-core.git
cd csam-benders-core

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
'''

## Single Run

'''bash
python -m experiment_scripts.run_single --max_csam 5 --u_l1 100 --c_dummy 5000 --seed 456
'''

## Parameter Sweep

'''bash
python -m experiment_scripts.run_sweep
python -m experiment_scripts.analyze_sweep
'''

## Key Features

#Time-expanded multi-commodity network flow
#Flexible l1 vs restricted l2 repair logic
#Queue carry-over penalties
#Dummy arcs for unmet demand in final period
#Benders decomposition with strong feasibility/optimality cuts
#Organized experiment tracking
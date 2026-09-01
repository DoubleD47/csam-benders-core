# Introduction

## Primal Subproblem Formulation (Fixed Deployments $\bar{y}$)

For a fixed deployment vector $\bar{y} \in \{0,1\}^{|M|}$, the
subproblem is the following linear program over the time-expanded,
commodity-specific flow network.

### Sets and Indices (Explicit)

- $M = \{m1,\dots,m10\}$: candidate CSAM locations

- $L = \{l1,l2\}$: repair types

- $K = \{k1,\dots,k5\}$: vehicle types

- $C = L \times K$: commodities

- $T = \{1,2\}$: time periods

- $N$: set of all nodes (source, sink, dummy (at $t=2$), ss
  (super-sink), and for each $m,t,c$: $m_{\text{in}}$, $m_{q_{l1}}$,
  $m_{r_{l1}}$, $m_{\text{out}_{l1}}$, and $m_{q_{l2}}$, $m_{r_{l2}}$,
  $m_{\text{out}_{l2}}$ when applicable)

- $A^{\text{reg}}$: regular arcs (source $\to$ in, in $\to$ in (travel),
  in $\to$ q, q $\to$ r, r $\to$ out, out $\to$ sink, sink $\to$ ss,
  q/in $\to$ dummy at $t=2$)

- $A^{\text{qq}}$: queue carryover arcs
  ($m_{q_{lp},t} \to m_{q_{lp},t+1}$ for $t=1$)

### Parameters

- $D_{m,t,c} \geq 0$: demand for commodity $c$ at location $m$ in period
  $t$

- $U_{l1} = 50$: CSAM repair capacity per deployed facility per period

- $U_{l2,k} = 100$: traditional repair capacity at fixed site for
  vehicle type $k$

- Arc costs $c_a$ (as coded): $C_{\text{in-in}}=1$,
  $C_{\text{in-q}}=10$, $C_{q-r,l1}=100$, $C_{q-r,l2}=200$,
  $C_{q-q}=100$, $C_{\text{dummy}}=1000$, plus small $0.1$ routing costs
  on repair/out/sink arcs.

### Decision Variables

$$\begin{align*}
    x_a &\geq 0 && \forall a \in A^{\text{reg}} \quad \text{(regular arc flows)} \\
    x_a^{\text{qq}} &\geq 0 && \forall a \in A^{\text{qq}} \quad \text{(queue carryover flows)}
\end{align*}$$

### Primal Subproblem (SP)

$$\begin{align}
\min \quad & \sum_{a \in A^{\text{reg}}} c_a \, x_a 
+ \sum_{a \in A^{\text{qq}}} C_{q\text{-}q} \, x_a^{\text{qq}} 
+ C_{\text{dummy}} \sum_{\text{dummy arcs}} x_a \label{eq:sub-obj} \\
\text{s.t.} \quad 
& \sum_{a \in \delta^+(n,t,c)} x_a + \sum_{a \in \delta^+_{\text{qq}}(n,t,c)} x_a^{\text{qq}} 
- \sum_{a \in \delta^-(n,t,c)} x_a - \sum_{a \in \delta^-_{\text{qq}}(n,t,c)} x_a^{\text{qq}} 
= b_{n,t,c} \quad && \forall n \in N, \, t \in T, \, c \in C \label{eq:flow-balance} \\
& \sum_{c : l(c)=l1} x_{(m_{q_{l1}} \to m_{r_{l1}},t,c)} 
\leq U_{l1} \cdot \bar{y}_m \quad && \forall m \in M, \, t \in T \label{eq:csam-cap} \\
& \sum_{c : k(c)=k} x_{(m_k_{q_{l2}} \to m_k_{r_{l2}},t,c)} 
\leq U_{l2,k} \quad && \forall k \in K, \, t \in T \label{eq:trad-cap} \\
& x_a \geq 0, \quad x_a^{\text{qq}} \geq 0.
\end{align}$$

where the right-hand side $b_{n,t,c}$ equals $D_{m,t,c}$ for
source-injection arcs at each $m$ (or aggregated at source), and the
total demand for the super-sink balance.
Equation [\[eq:flow-balance\]](#eq:flow-balance){reference-type="eqref"
reference="eq:flow-balance"} is the general node balance (implemented
via one constraint per node in the code).

## Dual of the Subproblem

The dual provides the shadow prices $\pi_{m,t}$ used in the optimality
cuts. We derive it directly from the primal above.

Let:

- $\alpha_{n,t,c} \in \mathbb{R}$: unrestricted dual variable for each
  flow-balance
  constraint [\[eq:flow-balance\]](#eq:flow-balance){reference-type="eqref"
  reference="eq:flow-balance"} (node potential / reduced cost)

- $\pi_{m,t} \geq 0$: dual for each CSAM capacity
  constraint [\[eq:csam-cap\]](#eq:csam-cap){reference-type="eqref"
  reference="eq:csam-cap"}

- $\mu_{k,t} \geq 0$: dual for each traditional capacity
  constraint [\[eq:trad-cap\]](#eq:trad-cap){reference-type="eqref"
  reference="eq:trad-cap"}

### Dual Subproblem (DSP)

$$\begin{align}
\max \quad & \sum_{n,t,c} b_{n,t,c} \, \alpha_{n,t,c} 
- \sum_{m,t} U_{l1} \bar{y}_m \, \pi_{m,t} 
- \sum_{k,t} U_{l2,k} \, \mu_{k,t} \label{eq:dual-obj} \\
\text{s.t.} \quad 
& \alpha_{j,t,c} - \alpha_{i,t,c} \leq c_a 
&& \forall a = (i \to j) \in A^{\text{reg}} \label{eq:dual-arc-reg} \\
& \alpha_{j,t+1,c} - \alpha_{i,t,c} \leq C_{q\text{-}q} 
&& \forall a \in A^{\text{qq}} \ (i = m_{q_{lp},t}, j = m_{q_{lp},t+1}) \label{eq:dual-arc-qq} \\
& \pi_{m,t} \geq \alpha_{m_{r_{l1}},t,c} - \alpha_{m_{q_{l1}},t,c} 
&& \forall m,t, \, c \text{ with } l(c)=l1 \label{eq:dual-csam-pi} \\
& \mu_{k,t} \geq \alpha_{m_k_{r_{l2}},t,c} - \alpha_{m_k_{q_{l2}},t,c} 
&& \forall k,t, \, c \text{ with } k(c)=k \label{eq:dual-trad-mu} \\
& \pi_{m,t} \geq 0, \quad \mu_{k,t} \geq 0, \quad \alpha \text{ free}.
\end{align}$$

By strong duality (when feasible), the optimal dual objective equals the
primal subproblem cost $\bar{Q} = Q(\bar{y})$.

### Optimality Cut Generation

After solving the subproblem, extract $\pi_{m,t}^* =$ dual value of
constraint [\[eq:csam-cap\]](#eq:csam-cap){reference-type="eqref"
reference="eq:csam-cap"}. The optimality cut added to the master problem
is:
$$\theta \geq \bar{Q} + \sum_{m \in M} \sum_{t \in T} \pi_{m,t}^* \, U_{l1} \, (y_m - \bar{y}_m)$$
This is the subgradient cut of the recourse function $Q(y)$ at the point
$\bar{y}$.

This side-by-side primal--dual presentation ensures full transparency
for the Benders cuts. The only dual variables that enter the master cuts
are the $\pi_{m,t}$ associated with the CSAM capacity constraints (the
linking constraints that depend on $y_m$). All other duals
($\alpha, \mu$) are internalized in the constant term $\bar{Q}$.

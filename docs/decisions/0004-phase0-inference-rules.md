# ADR-0004: Phase 0 Statistical Inference, Horizon Selection, and Overlap Protocol

- **Date:** 2026-08-11
- **Author:** B (Statistics)
- **Status:** proposed (Awaiting Person A joint Phase-0 ratification)
- **Gate:** B (Statistics) | A (Data)

## Context

Phase 0 statistical inference rules for market event studies and local projections must be pre-registered before opening market data. 

The project's effective sample size is bounded by independent physical shock clusters ($G = N_{\text{independent\_driver\_clusters}} \approx 6\text{--}15$), rather than raw weekly observations ($T \approx 780$). Standard asymptotic estimators and unconstrained horizon searches fail under this regime, generating severe false-positive risks ($p < 0.05$ firing up to 32% under the null).

To enforce Lock 1 (Rules before candidates) and Lock 2 (Candidates before outcomes), this decision record establishes the canonical estimation, horizon selection, overlap handling, and few-cluster inference architecture for all downstream market analysis.

## Decision

### 1. Analysis-Grid Mapping and Baseline Definition
- **Grid Alignment:** Date-only public anchors (`public_anchor_precision == "date"`) map to the first analysis anchor strictly after the `public_anchor` calendar date (`first_usable_analysis_anchor` per R-001).
- **Pre-Treatment Baseline ($y_{\text{baseline}}$):** Per R-001, $y_{\text{baseline}}$ is defined as the last analysis anchor strictly prior to `public_anchor`. Defining $t-1$ as the same calendar date as `public_anchor` is strictly prohibited to prevent post-announcement price leakage from entering the pre-treatment baseline.
- **Timestamp Precision:** Same-day mapping is permitted iff `anchor_ts <= analysis_anchor_ts` and `public_anchor_precision == "timestamp"`.

### 2. Primary Horizons and Path Evaluation
- **Primary Point Estimands:** Primary hypothesis testing is restricted to four mechanism horizons corresponding to explicit dynamic cascade stages:
  $$h \in \{1, 4, 12, 26\} \text{ weeks}$$
  - $h=1$: Immediate operational friction / shock onset.
  - $h=4$: Short-term participant adaptation / routing shift.
  - $h=12$: Intermediate inventory and flow redistribution.
  - $h=26$: Seasonal / full crop-year resolution.
- **Descriptive Full Path:** The full response path $h \in [0, 26]$ is reported as a secondary descriptive output, evaluated with 95% Montiel Olea & Plagborg-Møller (2021) / Sup-$t$ **simultaneous confidence bands** to control family-wise error rate across horizons.

### 3. Anchor Uncertainty Robustness (Jitter Envelope)
- Primary point estimands must survive an anchor-jitter robustness envelope where episode anchors are shifted by $j \in \{-1, +1\}$ weekly grid steps.
- A primary finding is robust to anchor uncertainty iff the sign and statistical significance at $h \in \{1, 4, 12, 26\}$ hold across the $j \in \{-1, +1\}$ jitter envelope.

### 4. Overlap Handling and Clean Baseline Eligibility
- **Pre-Event Horizon:** Fixed pre-event window $W_{\text{pre}} = [-12, -1]$ weeks with baseline $h_{\text{ref}} = -1$ (or $y_{\text{baseline}}$).
- **Clean Baseline Eligibility:** An episode $i$ is eligible for primary Sample P estimation iff no prior episode in the same corridor occurred in the window $[T_i - 12\text{ weeks}, T_i - 1\text{ week}]$.
- **Post-Window Contamination:** If a subsequent episode $j$ occurs at $T_j = T_i + \Delta t$ ($\Delta t < 26$ weeks), local projection estimations for episode $i$ at $h \ge \Delta t$ must include a shock indicator $\text{Shock}_j$ as a control covariate, with a secondary robustness check restricting estimation to uncontaminated post-windows.
- **H7 Rule Unchanged:** H7 ($\le 1$ episode per corridor/driver per 60 days) remains strictly an episode deduplication rule and is not modified for estimation convenience.

### 5. Primary Estimator Architecture
- **Stacked Episode Panel LP (Architecture B):** Primary dynamic estimation runs on the stacked episode panel:
  $$Y_{i, T_i + h} - Y_{i, \text{baseline}} = \alpha_h + \beta_h \cdot \text{Shock}_i + \boldsymbol{\gamma}_h' \mathbf{X}_{i} + \varepsilon_{i, h}$$
  weighted by inverse-cluster weights $w_i = 1 / K_c$ per H.2 / R-005 ($K_c = \text{episodes in cluster } c$).
- **Inference Method:** Standard errors MUST be clustered by `cluster_id` (satisfying R-005).

### 6. Few-Cluster Inferential Tier System
Inference is governed strictly by the number of independent physical driver clusters $G = N_{\text{independent\_driver\_clusters}}$ in Sample P:

- **Tier 0 ($G < 4$): PROJECT KILL / DESCRIPTIVE ONLY.** Formal hypothesis testing and $p$-values are suspended. Report individual event trajectories and range envelopes only. Trade thesis pre-registration is prohibited.
- **Tier 1 ($4 \le G \le 5$): PERMUTATION & WILD BOOTSTRAP ONLY.** Inference strictly via Webb (2014) 6-point Wild Cluster Bootstrap and Fisher Randomization Permutation tests. Report $p$-values with explicit small-sample warnings.
- **Tier 2 ($6 \le G \le 14$): PRIMARY INFERENCE TIER.** Primary inference via Webb Wild Cluster Bootstrap (restricted null). Secondary inference via CR2 (Bell & McCaffrey small-sample corrected SEs).
- **Tier 3 ($G \ge 15$): STANDARD CR2 / CRSE.** Standard cluster-robust inference with CR2 adjustment.

### 7. Model Complexity Constraint
Total estimated parameters $K_h$ in local projection regressions (including intercept, treatment, and controls) MUST satisfy:
$$K_h \le \left\lfloor \frac{G}{3} \right\rfloor + 1$$
- $G \in [4, 5] \implies K_h \le 2$ (Intercept + Treatment Indicator only; 0 additional controls).
- $G \in [6, 10] \implies K_h \le 3$ (Intercept + Treatment + $y_{\text{baseline}}$ control).
- $G \in [11, 15] \implies K_h \le 5$ (Intercept + Treatment + $y_{\text{baseline}}$ + max 2 controls).

### 8. Ex-Post Variable Restrictions
`peak_severity_date`, `end_date`, and `duration_days` are strictly prohibited from being used as $t=0$ alignment anchors or conditioning covariates in market LPs. They are declared strictly as ex-post descriptive variables or duration-response targets.

## Consequences

- Preregistering point horizons $h \in \{1, 4, 12, 26\}$ and simultaneous confidence bands closes post-hoc horizon mining.
- Inverse-cluster weighting ($w_i = 1/K_c$) and Wild Cluster Bootstrap prevent few-cluster over-rejection.
- Parameter complexity caps prevent overfitting when $G < 15$.
- If Sample P yields $G < 6$, formal trade thesis pre-registration is suspended. If $G < 4$, the quantitative project converts to a purely descriptive physical case study.

## Evidence

Synthetic validation fixtures under `tests/fixtures/make_synthetic_episode_panel.py` plant known dynamic responses $\beta(h)$ and small-$G$ cluster dependence to verify estimation accuracy.

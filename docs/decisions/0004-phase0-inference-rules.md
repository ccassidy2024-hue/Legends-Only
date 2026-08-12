# ADR-0004: Phase 0 Inference Estimand, Overlap Handling, and Cluster Accounting

- **Date:** 2026-08-11 (revised 2026-08-12)
- **Author:** B (Statistics)
- **Status:** proposed — awaiting joint A + B Phase-0 human ratification
- **Gate:** B (Statistics) | A (Data)
- **Provenance:** this revision was drafted by an AI-assisted Person B session.
  It is a technical proposal only. It is **not** a human Person B ratification,
  it does **not** record joint agreement, and no numeric value in it has been
  jointly ratified. Person A cross-review and human Person B adoption are both
  still required before this ADR may become `accepted`.

## Context

Phase 0 statistical inference rules for market event studies and local
projections must be preregistered before any market data is opened (Lock 2).

The project's effective sample size is bounded by the number of independent
physical driver clusters, not by raw weekly observations. `BLUEPRINT_REVIEW.md`
§1 measured the consequence directly: two independent AR(1) series scanned over
27 lags fire naive `p < 0.05` **32.3%** of the time under the null, with an
honest |t| threshold of 3.28 rather than 1.96. Unconstrained horizon search is
therefore not a stylistic problem in this project; it is the dominant source of
false discovery.

This record establishes the estimand definition, overlap handling, sample-
composition accounting, and few-cluster inference architecture for downstream
market analysis. It deliberately leaves every unresolved Phase-0 *value* to the
joint human ballot in §13.

**No horizon values are selected by this ADR.** Any numeric duration appearing
below is explicitly **proposed and unratified**.

## 0. Scope — what this ADR does NOT decide

This ADR selects **no**:

- D13 analysis-grid frequency, weekday/calendar convention, cutoff time,
  timezone, holiday treatment, or missing-anchor handling;
- calendar target-date → analysis-anchor mapping rule `M` (that mapping is a
  D13 dependency, §3);
- ratified D9 numeric horizon values (§2 proposes a candidate set only);
- balanced-versus-horizon-varying estimation sample policy (§6);
- release clock, release calendar, or any source fact;
- severity cutpoints (D12 remains deliberately unregistered per R-003);
- same-corridor interpretation when `navigation_basin` is a list (§5);
- qualifying-episode scope beyond the ballot in §5 / §13;
- primary competing-shock estimand or sensitivity policy beyond stating the
  selection cost of censoring (§5);
- any dose / intensity treatment variable (§7).

It creates no live preregistration config, no ratification manifest, and no tag.
It runs no event study and no local projection, and it inspects no market
outcome. It does not modify `panel.py` or the frozen ADR-0001 four-column
observation interface. It does not modify ADR-0005.

## 1. Notation — public-anchor origin, R-001 usability, R-004 reference

Define, for each episode *i*:

```text
a_i      = episode i's public_anchor
TGT_i(Δ) = a_i + Δ                    # calendar target date; D13-independent
M(·)     = future jointly ratified D13 target-date → analysis-anchor mapping
τ_i(Δ)   = M(TGT_i(Δ))                # analysis anchor at which the response is read
ρ_i      = R-004 clean pre-treatment reference analysis anchor
```

**`TGT_i(Δ)` is D13-independent.** The unresolved mapping `M` is the **only**
point at which D13 touches the response horizon. Until `M` is jointly ratified
with D13, no calendar duration may be mapped to an analysis-grid observation for
estimation.

Two distinct rulings govern event-time construction and are **not**
interchangeable:

- **Episode usability / t = 0 — R-001 only.** Where
  `public_anchor_precision == "date"`, the episode becomes usable at the first
  analysis anchor whose calendar date is **strictly after** `a_i`
  (`first_usable_analysis_anchor`). The date is never interpreted as midnight,
  BOD, noon, or EOD. Where `public_anchor_precision == "timestamp"`,
  same-calendar-day use is permitted only when `anchor_ts <= analysis_anchor_ts`
  and the timestamp is source-supported. **t = 0 is retained solely for this
  R-001 usability rule.** Economic response durations Δ are **not** measured
  from t = 0.
- **Clean pre-treatment reference — R-004.** `ρ_i` is the **last analysis
  anchor with calendar date strictly before `a_i`**. `ρ_i` is used only as the
  outcome-differencing reference. It is **not** the clean-window boundary (§5).

**The distinction that must not collapse.** After R-001 remapping, the
observation at relative step `-1` is *not* generally `ρ_i`. If `a_i` falls on
Oct 19 and the first eligible analysis anchor is Oct 26 (t = 0 under R-001),
then relative step `-1` is Oct 19 — the same calendar date as the public anchor
— which may already contain information that became public during that day.
R-004 requires Oct 12. Using observed step `-1` as the reference is therefore
prohibited: it is the exact contamination R-004 was written to prevent, and it
biases the estimated response toward zero by absorbing part of the event into
the baseline.

Throughout this ADR, `ρ_i` always denotes the R-004 clean reference, never
relative step `-1`, and never a mechanical t−1 relative to t = 0.

## 2. Primary estimand in calendar time (D9 — PROPOSED, NOT RATIFIED)

**Structural rule (methodological, proposed).** The primary estimand is defined
at **calendar-time economic durations** Δ measured in days from each episode's
own public anchor `a_i`:

```text
TGT_i(Δ) = a_i + Δ
```

not as a count of analysis-grid steps, and **not** as an offset from R-001
t = 0.

Rationale, and it is not cosmetic:

1. The analysis grid is D13 and **unresolved**. A horizon expressed in grid
   steps (or from remapped t = 0) makes the estimand a function of an
   unregistered decision — choosing the grid later would silently change what
   hypothesis is being tested. Calendar targets from `a_i` are invariant to the
   D13 choice until `M` is applied.
2. The mechanisms the project cares about run on calendar time. A storage
   decision, a routing shift, or a crop-year rollover does not rescale itself
   when the panel frequency changes.

**Proposed candidate duration set — NOT ratified:**

```text
Δ ∈ {7, 30, 90, 180} calendar days
```

with the mechanism reading: 7 d immediate operational friction; 30 d participant
adaptation / routing shift; 90 d inventory and flow redistribution; 180 d
seasonal / crop-year resolution.

**Honest provenance of these numbers.** This set is approximately a
re-expression of the `{1, 4, 12, 26}` week set in a superseded draft of this
ADR, not an independent re-derivation:

| Proposed Δ | Superseded draft | Approx. equivalence |
|---|---|---|
| 7 days | 1 week | 1.00 weeks |
| 30 days | 4 weeks | ≈ 4.3 weeks |
| 90 days | 12 weeks | ≈ 12.9 weeks |
| 180 days | 26 weeks | ≈ 25.7 weeks |

It is stated this way so that no reader mistakes a change of units for new
evidence. Per R-007, the numeric values of the pre-event, post-event, and
reference/baseline horizons are a **joint A + B human Phase-0 decision**. They
are not adopted by appearing in this ADR, in any draft, or in any review
comment. Until they are recorded in a ratified ADR and the corresponding
preregistration record, estimation that depends on them is blocked.

## 3. D9-to-D13 mapping firewall

This ADR does **not** select any analysis-grid parameter. It also does not
license inheriting one by default from current code.

Before any market-response estimation, D13 must separately preregister the grid
frequency, weekday/calendar convention, cutoff time, timezone, holiday
treatment, and missing-anchor handling, together with a **deterministic mapping
`M` from a calendar target date to an analysis anchor**. Admissible mapping
families include at least:

1. **first eligible anchor on or after** the target date;
2. **ceiling** to the next grid point;
3. **floor** to the previous grid point;
4. **nearest** grid point.

These alternatives **differ** when anchors or outcomes are missing, when the
target date falls between grid points, or when the panel has gaps. This ADR
**selects none**. It does **not** inherit a choice from current `panel.py`
defaults.

**Implementation hazard to be closed explicitly, not silently.** The repository
already contains grid-shaped defaults that no ADR has ratified (for example
`panel.weekly_anchors` Friday / 23:59 conventions and related helpers). Those
are code defaults, not preregistered decisions. D13 must either ratify them
against Person A's verified release-calendar evidence or override them. Any
change to `panel.py` is leakage-sensitive and requires the separate
dual-reviewed lane (`WORKFLOW.md` §2); it must not be attempted on a discovery
or ADR branch.

## 4. Anchor-precision firewall (does not interact with sensitivity checks)

Where `anchor_precision_days > 0`, market-response event-window and local-
projection **alignment is blocked** until A + B separately preregister how
nonzero anchor uncertainty affects R-001 usability, `ρ_i` construction, and
response-horizon mapping. Ledger admission and descriptive use may proceed if
the episode is otherwise admissible.

This firewall is recorded in ADR-0005 P1 with lookup entry R-009 (operative on
`main` after PR #7 merge as of this revision's drafting context; the normative
home remains ADR-0005 regardless of which commit a reviewer checks out).

**A jitter or anchor-sensitivity check does not lift this firewall.** Shifting
anchors by ±1 grid step as a robustness envelope measures sensitivity to anchor
placement; it does not supply the missing preregistered rule for where
usability, `ρ_i`, and `τ_i(Δ)` belong when the anchor day itself is uncertain. A
sensitivity envelope may be reported as a diagnostic once alignment is
unblocked. It is not a substitute for the A + B preregistration, and it may not
be used to justify estimating on episodes the firewall excludes.

## 5. Overlap handling — eligibility, later-shock censoring, right-edge truncation

### 5.1 Clean pre-event window (proposed Δ_pre unratified)

Define the proposed clean pre-event window in **calendar time from the public
anchor**:

```text
W_pre(i) = [a_i − Δ_pre, a_i)
```

**Proposed, not ratified:** `Δ_pre = 90` calendar days. The value is part of the
§13 ballot.

**`ρ_i` is not the clean-window boundary.** `ρ_i` is only the R-004
outcome-differencing reference (§1). Do not end `W_pre(i)` at `ρ_i` or at
`y_ref`.

### 5.2 Qualifying prior / later episodes — UNRESOLVED BALLOT ITEMS

**Proposed qualification criteria (not yet jointly ratified):** a prior or later
episode *j* qualifies for eligibility / censoring calculations only if:

1. `status == accepted`;
2. it is evaluated within the **same reported sample** as episode *i*
   (Sample P eligibility and Sample X eligibility are evaluated **separately**
   and **never pooled**); and
3. it is dated **only** by its `public_anchor` (never by ex-post dates listed in
   §5.3).

These accepted-only / per-sample qualification rules remain on the unresolved
A + B ballot (§13). They are **not** presented as already ratified.

**“Same corridor” is unresolved** because `navigation_basin` is a list.
Admissible interpretations — **none selected here** — include at least:

- any shared basin;
- identical basin sets; or
- a separately registered basin-to-corridor mapping.

The clean-window / competing-shock rules **cannot be operationalized** until D2
and the chosen corridor interpretation are jointly ratified.

### 5.3 Later-shock censoring boundary

If a later qualifying episode *j* exists for episode *i*, define:

```text
Δ_next(i) = a_j − a_i
```

using the later episode's **`public_anchor` only**. Episode *i* contributes
**no observation** at horizons `Δ ≥ Δ_next(i)`.

**Explicitly prohibited** as inputs to the censoring boundary:

- `physical_onset`
- `peak_severity_date`
- `end_date`
- `duration_days`
- `relief_confirmed_date`
- any other ex-post date

Subsequent shock indicators must **not** be added as regression controls
(post-treatment / collider bias). That is the same principle R-006 applies to
ex-post episode fields.

### 5.4 Censoring’s selection cost (does not eliminate bias)

Later-shock censoring avoids including a post-treatment control, but it still
**conditions sample membership on a post-treatment event**. It can:

- change sample composition by horizon;
- disproportionately remove busy-corridor episodes;
- change the estimand's population across Δ; and
- potentially bias causal interpretation.

**Censoring does not claim to eliminate bias.** The primary competing-shock
estimand and any sensitivity policy remain an **unresolved joint A + B
decision** (§13).

### 5.5 Right-edge truncation (separate from competing-shock censoring)

An episode contributes at duration Δ only when `τ_i(Δ)` is within the registered
sample period **and** the outcome is observed there.

ADR-0003 D1(8) forbids moving `sample_end` earlier merely to guarantee a full
post-event path. Do **not** move `sample_end` earlier to force complete
coverage.

**Separate reporting is required** for:

1. competing-shock censoring;
2. right-edge truncation; and
3. missing outcomes.

Do **not** pool these reasons into a single “censored” bucket. Right-edge
truncation is a **registered-calendar boundary** issue. This ADR does **not**
claim that all missing-outcome mechanisms are outcome-independent.

### 5.6 H7 unchanged

H7 (≤ 1 episode per corridor/driver per 60 days) remains an episode
deduplication rule in `EPISODE_PROTOCOL.md` §H. It is not modified, relaxed, or
reinterpreted for estimation convenience.

## 6. Sample-specific cluster counts — `G_LP^P(Δ)` and `G_LP^X(Δ)`

Define separately:

```text
G_LP^P(Δ) = number of independent driver clusters (cluster_id) contributing at
            least one LP-eligible, uncensored, non-truncated, observed Sample P
            episode observation at duration Δ

G_LP^X(Δ) = analogous count for Sample X
```

Each count is computed **after every applicable** eligibility, precision,
censoring, truncation, and missing-outcome rule for that sample. Sample P and
Sample X are never pooled to inflate a tier.

The inference tier and complexity cap at a reported horizon **must** use the
count for the sample being reported (`G_LP^P(Δ)` or `G_LP^X(Δ)`). Pooling P and
X to reach a more favorable tier is prohibited.

**Monotonicity is not unconditional.** Claiming that a cluster count is weakly
decreasing in Δ requires nested eligibility and outcome availability, a fixed
sample definition, a fixed monotone D13 mapping `M`, and consistently nested
censoring. Those conditions are not guaranteed under the unresolved ballot;
therefore this ADR **does not** assert unconditional monotonicity of
`G_LP^P(Δ)` or `G_LP^X(Δ)`.

**`G_LP^S(Δ)` MUST be reported at every horizon** for the sample `S ∈ {P, X}`
being presented, alongside the number of contributing episodes. Reporting a
path without it invites the reader to assume a constant sample that does not
exist.

**Unresolved joint decision — balanced versus horizon-varying sample.** Two
admissible policies exist and this ADR selects neither:

- **Balanced:** restrict every horizon to episodes with complete coverage to
  max(Δ). One population throughout; smaller `G_LP^S`, potentially below the
  usable range at long horizons.
- **Horizon-varying:** use all eligible observations at each Δ. Larger
  `G_LP^S(Δ)` at short horizons; the estimand's population changes with Δ and
  the path is not directly comparable across Δ.

Whichever is chosen must be preregistered **before** estimation. The choice
belongs on the §13 ballot.

## 7. Identified estimator architecture

### 7.1 Why a binary `Shock_i` treatment coefficient is not identified

In a stacked episode panel where every row is a treated episode at one horizon,
a binary indicator `Shock_i ≡ 1` for every row is **collinear with the
intercept**. Therefore no separate treatment coefficient is identified. Any
earlier draft equation containing `β(Δ)·Shock_i` is withdrawn for that reason
(not merely because of post-treatment control concerns about later shocks).

### 7.2 Estimand and regression

Define the episode-horizon response:

```text
D_i(Δ) = Y[i, τ_i(Δ)] − Y[i, ρ_i]
```

and the primary regression on the estimation set `S(Δ)` of LP-eligible episodes
contributing at Δ:

```text
D_i(Δ) = μ(Δ) + γ(Δ)'(X_i − X̄_w(Δ)) + ε_i(Δ),   i ∈ S(Δ)
```

**Symbol definitions:**

| Symbol | Meaning |
|---|---|
| `Y[i, ·]` | Outcome series value for episode *i* at the named analysis anchor |
| `τ_i(Δ)` | Mapped analysis anchor `M(a_i + Δ)` (§1, §3) |
| `ρ_i` | R-004 clean pre-treatment reference anchor (§1) |
| `D_i(Δ)` | Episode *i* response at calendar duration Δ |
| `μ(Δ)` | Weighted average episode response at average covariates |
| `X_i` | Preregistered pre-treatment covariate vector for episode *i* |
| `X̄_w(Δ)` | Weighted covariate mean over `S(Δ)` under the estimation weights |
| `γ(Δ)` | Coefficient vector on demeaned covariates |
| `ε_i(Δ)` | Residual |
| `S(Δ)` | Estimation set at Δ after all eligibility / precision / censoring / truncation / missing-outcome rules for the reported sample |

**Clear statements:**

1. One row represents **one treated episode at one horizon**.
2. A binary `Shock_i` equals one for every such row.
3. It is collinear with the intercept.
4. Therefore **no separate treatment coefficient is identified**.
5. `μ(Δ)` is the weighted average episode response at average covariates.
6. A future varying dose / intensity measure would require its own
   preregistered construction, timing rule, admissible inputs, and identifying
   variation. **This ADR does not invent a dose variable.**

### 7.3 Weighting and clustering (R-005)

Per `EPISODE_PROTOCOL.md` §H.2 and R-005, downstream market event studies,
impulse-response plots, and local projections MUST either (A) collapse/average
accepted episode observations to `cluster_id` level, or (B) apply inverse-cluster
weights `w_i = 1/K_c` (`K_c` = accepted episodes in cluster *c*) **and** use
cluster-robust standard errors clustered by `cluster_id`. This ADR adopts
option (B) as its primary specification; option (A) remains available and
equally compliant.

## 8. Few-cluster inference tiers — PROJECT HEURISTIC

The tiering below is a **project heuristic proposed by Person B**, not an
established statistical standard and not a jointly ratified rule. The cutpoints
are judgment calls about where each inference method stops being trustworthy at
this project's cluster counts. They are evaluated on the sample-specific count
`G_LP^S(Δ)` for the sample being reported (§6).

| Tier | `G_LP^S(Δ)` | Proposed inference treatment |
|---|---|---|
| T0 | < 4 | Descriptive only. No p-values. Report individual trajectories and range envelopes. |
| T1 | 4–5 | **Descriptive only.** See §8.1. |
| T2 | 6–14 | Primary: restricted-null wild cluster bootstrap. Secondary: CR2 (Bell–McCaffrey) corrected standard errors. |
| T3 | ≥ 15 | Cluster-robust inference with CR2 adjustment. |

These tiers govern **which inference method is admissible at a horizon**. They
are not a kill condition and do not redefine one — see §10. Adoption or
replacement of the entire heuristic remains on the §13 ballot.

### 8.1 Tier T1 (G = 4–5) — descriptive only

At T1 this ADR authorizes **descriptive summaries only**.

It does **not** authorize randomization or permutation inference unless a valid
assignment / exchangeability design, an outcome-blind placebo pool, and a sharp
null are **separately preregistered and jointly ratified**.

At T1, **prohibit**:

- inferential p-values;
- coverage claims;
- the word “significant” (or equivalent confirmatory language); and
- causal or trade-thesis conclusions.

## 9. Model complexity accounting — PROJECT HEURISTIC

Also a proposed project heuristic, not a ratified rule. Let:

```text
K           = actual total number of estimated parameters
p           = number of controls
K = 1 + p   # with Shock_i removed; intercept + controls
K_max(Δ)    = floor( G_LP^S(Δ) / 3 ) + 1   # proposed ceiling for sample S
```

**Corrected accounting (resolves the earlier packet contradiction):**

- `K` is the **actual** number of estimated parameters.
- With `Shock_i` removed, `K = 1 + p`.
- `K_max(Δ)` is a **proposed ceiling**, not necessarily the number of parameters
  actually used.
- An **intercept-only** model has **`K = 1`, never `K = 2`**.
- At `G_LP^S(Δ) ∈ {4, 5}`, T1’s descriptive-only rule (§8.1) may restrict the
  primary summary to the intercept-only response even though the formula’s
  numerical ceiling is 2.
- If the cap is fully used outside that restriction, maximum controls equal
  `K_max(Δ) − 1`.
- Do **not** silently preserve a fictitious “treatment slot.”

Worked ceilings under the formula (ceilings, not mandatory model sizes):

| `G_LP^S(Δ)` | `K_max = floor(G/3)+1` | If fully used: max controls `p = K_max − 1` |
|---|---|---|
| 4–5 | 2 | 1 (but T1 primary may still be intercept-only, `K = 1`) |
| 6–8 | 3 | 2 |
| 9–11 | 4 | 3 |
| 12–14 | 5 | 4 |
| 15 | 6 | 5 |

Adoption or replacement of the entire heuristic remains on the joint A + B
ballot (§13).

## 10. Kill condition — committed rule is NOT overridden here

The project's kill condition is already committed and this ADR does not
redefine, relax, or replace it:

> `episode_schema.yaml`: `kill_condition_primary_sample_min: 6`, on **accepted
> Sample P episodes**; `WORKFLOW.md` names "fewer than 6 usable episodes" as the
> point at which the question is unanswerable with this data.

Two distinct quantities must not be conflated:

- **`N_episodes` in Sample P** — accepted episode rows. This is what the
  committed kill condition is measured on.
- **`G_LP^P(Δ)` / `G_LP^X(Δ)`** — statistical dependence groupings after
  analysis-layer exclusions (§6). This is what inference tiers and complexity
  caps are measured on.

The §8 tiers constrain *method*; the committed Sample-P episode-count kill
condition continues to govern whether the project proceeds at all, and any
proposal to change it is a separate joint human decision, not an
inference-layer detail.

## 11. Ex-post variable restrictions (R-006)

`peak_severity_date`, `end_date`, and `duration_days` MUST NOT be used as the
R-001 t = 0 alignment anchor, as the censoring boundary (§5.3), or as
conditioning covariates in market-response event studies or local projections.
They may remain ex-post descriptive variables and/or preregistered
duration-response targets. §5's censoring rule is the same principle applied to
later shocks.

## 12. Multiplicity treatment — REQUIRED CHOICE, STILL OPEN

Registering horizon values without registering how the horizon path is tested
would re-import exactly the false-discovery problem quantified in §Context.
Exactly one of the following must be jointly chosen and preregistered before
estimation:

- **(a) Single primary horizon.** One Δ is designated the primary test; all
  other durations are secondary/descriptive and are reported without
  confirmatory claims.
- **(b) Multiplicity-controlled simultaneous bands.** All Δ in the primary set
  are tested jointly under simultaneous (sup-t style) confidence bands or an
  equivalent family-wise correction, so that "the best horizon" cannot be
  reported as if it were the only one examined.

This ADR does not choose between (a) and (b). Reporting the most favourable
horizon from an uncorrected set is prohibited under either choice
(`CLAUDE.md` hard rule 4).

## 13. Human joint ballot still required

None of the following are decided by this ADR. Each requires the joint A + B
human Phase-0 decision:

1. **D9 numeric durations** — the §2 set `{7, 30, 90, 180}` days is a proposal
   only (R-007).
2. **Clean-window duration** `Δ_pre` (§5.1; proposed 90 days).
3. **Balanced versus horizon-varying estimation sample** (§6).
4. **Multiplicity treatment** — option (a) or option (b) (§12).
5. **Mapping `M` jointly with D13** (§3), including which admissible family
   (on-or-after / ceiling / floor / nearest) is chosen.
6. **Nonzero-`anchor_precision_days` alignment rule**, which is the separate
   A + B preregistration that lifts the §4 firewall.
7. **Adoption of the §8 tiers and §9 complexity-cap heuristic**, or their
   replacement.
8. **Same-corridor definition** given list-valued `navigation_basin` (§5.2).
9. **Qualifying-episode scope** (accepted-only / per-sample / public_anchor-only
   dating) (§5.2).
10. **Competing-shock estimand and sensitivity policy** (§5.4).
11. **ADR-0004 pre-tag binding** — whether / how this ADR is added to the
    load-bearing ratification set after it merges and before `prereg-rules-v1`
    (§13 governance note).
12. **Whether any dose / intensity variable is introduced** (§7.2).

### Governance and pre-tag digest implications (revision-specific)

ADR-0003 N3 binds a `LOAD_BEARING_RELATIVE_PATHS` set into the ratification
manifest so that post-tag drift of an interpretation file fails closed. As of
this revision, ADR-0004 is **not** in that set (ADR-0005 is, after PR #7). That
is expected while this ADR remains `proposed`: binding an unratified inference
ADR would bind a placeholder.

**Required future step (ballot item 11):** after this ADR merges as `accepted`
and **before** creating `prereg-rules-v1`, A + B must add ADR-0004 to the
load-bearing ratification set so analysis-layer inference rules cannot drift
silently after the freeze. This ADR does **not** modify `governance.py` in this
PR.

## Consequences

- Defining `TGT_i(Δ) = a_i + Δ` decouples the economic hypothesis from both the
  unresolved D13 grid and R-001 remapping; `M` is the only D13 contact point.
- Removing the unidentified `Shock_i` coefficient prevents a collinear treatment
  term from being reported as identified causal effect.
- Censoring at later `public_anchor` boundaries avoids post-treatment controls
  while honestly stating the selection cost; it does not claim bias elimination.
- Sample-specific `G_LP^P(Δ)` / `G_LP^X(Δ)` accounting prevents P/X pooling into
  a more favorable tier and drops unconditional monotonicity claims.
- T1 descriptive-only and corrected `K = 1` intercept-only accounting close the
  earlier heuristic contradictions.
- Because the §4 firewall, §12 multiplicity choice, corridor definition, and
  other §13 ballot items remain open, no market-response estimate may be
  produced under this ADR as it stands. That is the intended state: it is a
  preregistration document awaiting ratification, not an authorization to
  estimate.

## Evidence

**Committed evidence: none for this ADR's estimation rules.** No estimator in
this document has been implemented or validated in this repository, and no
synthetic fixture for episode-panel local projections exists.

**Planned evidence (not yet written, not part of this PR).** Once the D9 values
and the §6 and §12 choices are ratified, Person B should add synthetic
ground-truth fixtures under `tests/fixtures/` that plant a known response path
`μ(Δ)` together with known small-`G` cluster dependence, and assert that the
implemented estimator recovers the planted path, that inverse-cluster weighting
and cluster-robust inference behave correctly at small `G_LP^S`, and that the
§5 censoring / truncation rules reproduce the expected sample-composition
schedule. Those fixtures are the evidence that would justify moving this ADR
beyond `proposed`; they do not exist today and this ADR makes no claim that
they do.

# ADR-0004: Phase 0 Inference Estimand, Overlap Handling, and Cluster Accounting

- **Date:** 2026-08-11 (revised 2026-08-12; Route-A jointly aligned revision 2026-08-17)
- **Author:** B (Statistics)
- **Status:** proposed — awaiting exact-head review, then joint A + B Phase-0 human ratification
- **Gate:** B (Statistics) | A (Data)
- **Provenance:** this revision was drafted by an AI-assisted Person B session
  after an explicit Person A + Person B methodology adjudication (Route A).
  The methodology below is jointly aligned as a technical proposal. It is
  **not** a human Person B ratification of this exact edited text, it does
  **not** record that ADR-0004 has been accepted, and no numeric value in it
  has been jointly ratified. Exact-head review, Person A cross-review, and
  human Person B adoption are all still required before this ADR may become
  `accepted`.

## Context

Phase 0 statistical rules for the Route-A market-response artifact must be
preregistered before any market data is opened (Lock 2).

**Route A is not a local projection.** Every row of the stacked episode panel
is a treated episode. There is no untreated comparison variation. A binary
`Shock_i ≡ 1` is collinear with the intercept. The object specified here is
therefore a **stacked episode-level mean-change (event-study-style)
descriptive artifact**. Its primary estimand is descriptive. It identifies no
counterfactual treatment effect.

This artifact licenses **no** causal language, predictive language,
“significant” language, impulse-response language, local-projection language,
or trade-thesis language. It is not “not a local projection yet.” It is not a
local projection **by design**, because it has no identifying comparison
variation. Only a later, separately ratified design with actual identifying
variation may use that term (see §7.9).

The project's effective sample size is bounded by the number of independent
physical driver clusters, not by raw weekly observations. `BLUEPRINT_REVIEW.md`
§1 measured the consequence directly: two independent AR(1) series scanned over
27 lags fire naive `p < 0.05` **32.3%** of the time under the null, with an
honest |t| threshold of 3.28 rather than 1.96. Unconstrained horizon search is
therefore not a stylistic problem in this project; it is the dominant source of
false discovery.

This record establishes the Route-A descriptive estimand, overlap handling,
sample-composition accounting, claim-language firewall, and the blocked path
to any later Milestone-4 identified design. It deliberately leaves every
unresolved Phase-0 *value* to the joint human ballot in §13.

**No horizon values are selected by this ADR.** Any numeric duration appearing
below is explicitly **proposed and unratified**.

## 0. Scope — what this ADR does NOT decide

This ADR selects **no**:

- D13 analysis-grid frequency, weekday/calendar convention, cutoff time,
  timezone, holiday treatment, or missing-anchor handling;
- calendar target-date → analysis-anchor mapping rule `M` (that mapping is one
  D13 dependency among several, §1.1 / §3);
- ratified D9 numeric horizon values (§2 proposes a candidate set only);
- `Δ_pre` numeric value (§5.1 proposes a candidate only; it is **not**
  operative);
- balanced-versus-horizon-varying estimation sample policy (§6);
- release clock, release calendar, or any source fact;
- severity cutpoints (D12 remains deliberately unregistered per R-003);
- same-corridor interpretation when `navigation_basin` is a list (a D2 /
  ledger / H7 matter, not a prerequisite for the Route-A collision rule in
  §5.2);
- any dose / intensity treatment variable (§7.2);
- covariate universe `X_i` (§7.6);
- summary dispersion statistic for cluster means (§7.5);
- machine-readable exclusion-reason taxonomy (§7.10);
- inference-tier or complexity-cap heuristic as an operative rule for this
  artifact (§8 / §9 remain deferred);
- any frequency, weekday, cutoff, timezone, holiday, or missing-anchor value.

It creates no live preregistration config, no ratification manifest, and no tag.
It runs no event study, no descriptive estimation, and no local projection, and
it inspects no market outcome. It does not modify `panel.py` or the frozen
ADR-0001 four-column observation interface. It does not modify ADR-0005. It
does not amend R-001, R-004, R-005, R-006, R-007, or R-009–R-014. It does not
modify `LOAD_BEARING_RELATIVE_PATHS`.

## 1. Notation — public-anchor origin, R-001 usability, three-case reference

Define, for each episode *i*:

```text
a_i      = episode i's public_anchor
TGT_i(Δ) = a_i + Δ                    # calendar target date
M(·)     = future jointly ratified D13 target-date → analysis-anchor mapping
τ_i(Δ)   = M(TGT_i(Δ))                # analysis anchor at which the response is read
ρ_i      = clean pre-treatment reference analysis anchor (cases below)
```

### 1.1 D13 contact points — `M` is not the only one

`TGT_i(Δ) = a_i + Δ` **may be grid-independent as a calendar target**. The
realized differenced response

```text
D_i(Δ) = Y[i, τ_i(Δ)] − Y[i, ρ_i]
```

is **not** D13-independent. D13 affects at least:

1. `τ_i(Δ)` through target-date mapping `M`;
2. `ρ_i`, because the reference is an analysis-grid anchor;
3. R-001 usability / t = 0 mapping;
4. right-edge truncation / missing-anchor behavior through grid and calendar
   rules.

Therefore `M` is **not** the only D13 contact point. This ADR selects **no**
D13 value.

Until `M` and the remaining D13 conventions are jointly ratified, no calendar
duration may be mapped to an analysis-grid observation for estimation.

### 1.2 Episode usability / t = 0 — R-001 unchanged

Two distinct rulings govern event-time construction and are **not**
interchangeable. This ADR does **not** amend R-001.

- **Episode usability / t = 0 — R-001 only.** Where
  `public_anchor_precision == "date"`, the episode becomes usable at the first
  analysis anchor whose calendar date is **strictly after** `a_i`
  (`first_usable_analysis_anchor`). The date is never interpreted as midnight,
  BOD, noon, or EOD. Where `public_anchor_precision == "timestamp"`,
  same-calendar-day use is permitted only when `anchor_ts <= analysis_anchor_ts`
  and the timestamp is source-supported. **t = 0 is retained solely for this
  R-001 usability rule.** Economic response durations Δ are **not** measured
  from t = 0.

R-004 does **not** govern timestamp anchors. The clean pre-treatment reference
`ρ_i` is constructed under the three cases in §1.3. R-004 remains unchanged
for its committed date-only scope (Case 1).

### 1.3 Clean pre-treatment reference — three cases, plus the P1 firewall

**Case 1 — date-only.** When `public_anchor_precision == "date"`, R-004 remains
unchanged:

```text
ρ_i = last analysis anchor whose CALENDAR DATE is strictly before public_anchor
```

`ρ_i` is used only as the outcome-differencing reference. It is **not** the
clean-window boundary (§5).

**The distinction that must not collapse (Case 1).** After R-001 remapping, the
observation at relative step `-1` is *not* generally `ρ_i`. If `a_i` falls on
Oct 19 and the first eligible analysis anchor is Oct 26 (t = 0 under R-001),
then relative step `-1` is Oct 19 — the same calendar date as the public anchor
— which may already contain information that became public during that day.
R-004 requires Oct 12 in that illustration. Using observed step `-1` as the
reference is therefore prohibited: it is the exact contamination R-004 was
written to prevent, and it biases the estimated response toward zero by
absorbing part of the event into the baseline. Grid dates in this paragraph are
illustrative of the R-001 / R-004 distinction; they do not ratify a D13
weekday or frequency.

**Case 2 — exact source-supported timestamp.** When
`public_anchor_precision == "timestamp"` **and** `anchor_ts` is affirmatively
source-attested:

```text
ρ_i = last analysis anchor whose analysis-anchor timestamp is strictly earlier
      than anchor_ts
```

Equality is excluded. This is the pre-treatment complement of R-001's
at-or-after timestamp usability rule: the same anchor cannot simultaneously be
the pre-treatment reference and t = 0.

**Source-attested** means genuine timestamp evidence from the source. A
defaulted, synthesised, placeholder, inferred, or fill-derived clock value does
**not** qualify.

**Case 3 — unresolvable timestamp comparison.** FAIL CLOSED. If the source
timestamp provenance is inadequate **or** analysis-anchor and event timestamps
cannot be safely compared under the eventual D13 convention:

- the episode is ineligible for this artifact at **all** horizons;
- the exclusion is counted (§7.10);
- do **not** fall back to date-only;
- do **not** invent timezone or clock-conversion behavior.

**Case 4 — nonzero anchor uncertainty.** `anchor_precision_days > 0` remains
blocked under ADR-0005 P1 / R-009 (§4). This ADR does not weaken that
firewall. No frequency, weekday, cutoff, timezone, holiday, or missing-anchor
value is selected here.

Throughout this ADR, `ρ_i` always denotes the Case-1 / Case-2 clean reference
constructed above, never relative step `-1`, and never a mechanical t−1
relative to t = 0. Case-3 and Case-4 episodes have no admissible `ρ_i` for this
artifact.

## 2. Calendar-time durations (D9 — PROPOSED, NOT RATIFIED)

**Structural rule (methodological, proposed).** Reported durations are
**calendar-time economic durations** Δ measured in days from each episode's
own public anchor `a_i`:

```text
TGT_i(Δ) = a_i + Δ
```

not as a count of analysis-grid steps, and **not** as an offset from R-001
t = 0.

Rationale, and it is not cosmetic:

1. The analysis grid is D13 and **unresolved**. A horizon expressed in grid
   steps (or from remapped t = 0) makes the *target* a function of an
   unregistered decision. The calendar target `TGT_i(Δ)` is invariant to the
   D13 choice. The realized `D_i(Δ)` is not: it still depends on D13 through
   `M`, `ρ_i`, R-001 usability, and truncation / missing-anchor rules (§1.1).
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

Where `anchor_precision_days > 0`, alignment of the Route-A descriptive
artifact — and of any future local-projection design — is **blocked** until
A + B separately preregister how nonzero anchor uncertainty affects R-001
usability, `ρ_i` construction, and response-horizon mapping. Ledger admission
and descriptive use of the episode record itself may proceed if the episode is
otherwise admissible.

This firewall is recorded in ADR-0005 P1 with lookup entry R-009 (operative on
`main` after PR #7 merge as of this revision's drafting context; the normative
home remains ADR-0005 regardless of which commit a reviewer checks out). This
ADR does not weaken it.

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

**Proposed, not ratified, not operative:** `Δ_pre = 90` calendar days. The
value is part of the §13 ballot. It MUST NOT be used to compute eligibility,
cluster counts, Option-A aggregation, or exclusion tallies.

**`ρ_i` is not the clean-window boundary.** `ρ_i` is only the
outcome-differencing reference (§1). Do not end `W_pre(i)` at `ρ_i` or at
`y_ref`.

### 5.2 Qualifying collision universe (Route-A estimator rule)

For the Route-A descriptive artifact, a prior or later episode *j* qualifies
for collision / censoring calculations if and only if:

1. it is a **frozen ACCEPTED** episode;
2. it is drawn from the pooled ledger **Sample P ∪ Sample X**; and
3. it is dated **only** by its `public_anchor` (never by ex-post dates listed in
   §5.3).

**Collision detection is pooled across Sample P and Sample X.** Reporting of
`μ^S(Δ)`, contributing counts, cluster means, and exclusion tallies remains
**per sample** `S ∈ {P, X}`.

**Same corridor is not required** for this estimator's collision rule. Any
list-valued-`navigation_basin` interpretation needed for ledger H7 remains a
separate D2 / ledger matter and is not selected here.

Ex-post dates remain prohibited as dating inputs.

### 5.3 Later-shock censoring boundary (post-side, per horizon)

If a later qualifying episode *j* exists for episode *i* with `a_j > a_i`,
define:

```text
Δ_next(i) = a_j − a_i
```

using the later episode's **`public_anchor` only**. Episode *i* contributes
**no observation** at horizons `Δ ≥ Δ_next(i)`.

This post-side rule is **per-horizon** because `τ_i(Δ)` varies by horizon:
post-side contamination can be censored horizon-by-horizon without discarding
every shorter horizon at which the later shock has not yet occurred.

**Explicitly prohibited** as inputs to the censoring boundary:

- `physical_onset`
- `peak_severity_date`
- `end_date`
- `duration_days`
- `relief_confirmed_date`
- any other ex-post date

Subsequent shock indicators must **not** be added as regression controls
(post-treatment / collider bias). That is the same principle R-006 applies to
ex-post episode fields. This ADR does not amend R-006.

### 5.4 Pre-side collision — all horizons

If another qualifying episode `j ≠ i` satisfies

```text
a_i − Δ_pre  ≤  a_j  ≤  a_i
```

then episode *i* is **ineligible at all horizons**.

The left boundary is **closed**. Same-day distinct accepted episodes therefore
**mutually collide**.

This is different from post-side censoring because `ρ_i` is **shared across
every horizon**. Contamination of the baseline contaminates every `D_i(Δ)`.

This can remove an entire contributing cluster when same-day colliding
episodes share a `cluster_id`.

### 5.5 Reference containment — separate condition

Independently of another-episode collision: if `ρ_i` lies outside

```text
[a_i − Δ_pre, a_i)
```

the episode **fails closed** at all horizons. Count this exclusion separately
from baseline collision (§7.10).

The deliberate boundary asymmetry must remain visible:

| Test | Interval | Right boundary |
|---|---|---|
| Another-event collision | `[a_i − Δ_pre, a_i]` | **closed** |
| Admissible reference window | `[a_i − Δ_pre, a_i)` | **open** |

Same-day distinct accepted episodes therefore mutually collide under the
collision test, while a reference falling on `a_i` itself is not an admissible
`ρ_i`.

### 5.6 Censoring’s selection cost (does not eliminate bias)

Later-shock censoring avoids including a post-treatment control, but it still
**conditions sample membership on a post-treatment event**. It can:

- change sample composition by horizon;
- disproportionately remove busy-corridor episodes;
- change the estimand's population across Δ; and
- potentially bias any causal reading that this ADR does **not** adopt.

**Censoring does not claim to eliminate bias.** The Route-A artifact remains
descriptive (§7.3).

### 5.7 Right-edge truncation (separate from competing-shock censoring)

An episode contributes at duration Δ only when `τ_i(Δ)` is within the registered
sample period **and** the outcome is observed there.

ADR-0003 D1(8) forbids moving `sample_end` earlier merely to guarantee a full
post-event path. Do **not** move `sample_end` earlier to force complete
coverage.

**Separate reporting is required** for conceptually distinct reasons (§7.10),
including at least:

1. competing-shock / later-shock censoring;
2. right-edge truncation; and
3. missing outcomes.

Do **not** pool these reasons into a single “censored” bucket. Right-edge
truncation is a **registered-calendar boundary** issue. This ADR does **not**
claim that all missing-outcome mechanisms are outcome-independent.

### 5.8 Coverage limitation (anti-conservative for contamination)

Collision detection is only as complete as the **frozen episode ledger**.
Coverage gaps and unswept exposure can leave true neighbouring shocks unminted
and therefore undetected.

The resulting direction is **anti-conservative** for contamination handling: a
contaminated baseline may be **retained** because the competing episode was
never observed. Missing coverage must **not** be converted into an
untreated-zero claim, and it does not create identifying variation.

### 5.9 Δ_pre gate

Eligibility, cluster counts, Option-A aggregation, and exclusion tallies that
depend on the clean-window rule are **not computable** until `Δ_pre` is
ratified. Do **not** run them using the proposed 90-day value.

### 5.10 H7 unchanged, with a deferred Δ_pre interaction note

H7 (≤ 1 episode per (corridor, driver) per 60 days, without a written
`RULINGS.md` exception) remains an episode **ledger dedup / admission** rule in
`EPISODE_PROTOCOL.md` §H. It is **not** the estimator collision rule. This ADR
does not modify, relax, or reinterpret H7.

**Nonblocking deferred-decision note.** The fixed H7 60-day dedup horizon
creates an important interaction with the future choice of `Δ_pre`. Choosing a
clean window materially beyond roughly that boundary can render some otherwise
H7-compliant same-corridor/driver later episodes ineligible via the
clean-window collision rule. Crossing the H7 horizon therefore changes the
**behavior** of the estimator eligibility rule, not merely its strictness.
This interaction MUST be visible when A + B later ratify `Δ_pre`. This note
does **not** infer or select a `Δ_pre` value from the currently proposed 90
days, and it does not rewrite H7.

## 6. Sample-specific cluster counts — `G^P(Δ)` and `G^X(Δ)`

Define separately, for reported sample `S ∈ {P, X}` and horizon Δ:

```text
E^S(Δ)   = eligible contributing episodes in sample S at Δ
C^S(Δ)   = set of distinct contributing cluster_id values among E^S(Δ)
G^S(Δ)   = |C^S(Δ)|
n_c^S(Δ) = number of contributing episodes from cluster c at Δ
```

Each count is computed **after every applicable** eligibility, precision,
timestamp-provenance, collision, reference-containment, censoring, truncation,
and missing-outcome rule for that sample. Sample P and Sample X are never
pooled to inflate a reported cluster count or to present a combined
`μ^{P∪X}(Δ)`.

**`G^S(Δ)` MUST be reported at every horizon** for the sample being presented,
alongside the number of contributing episodes, every contributing cluster mean,
and each corresponding `n_c^S(Δ)` (§7.5). Reporting a path without these
quantities invites the reader to assume a constant sample that does not exist.

**Monotonicity is not unconditional.** Claiming that a cluster count is weakly
decreasing in Δ requires nested eligibility and outcome availability, a fixed
sample definition, a fixed monotone D13 mapping `M`, and consistently nested
censoring. Those conditions are not guaranteed under the unresolved ballot;
therefore this ADR **does not** assert unconditional monotonicity of
`G^P(Δ)` or `G^X(Δ)`.

**Unresolved joint decision — balanced versus horizon-varying sample.** Two
admissible policies exist and this ADR selects neither:

- **Balanced:** restrict every horizon to episodes with complete coverage to
  max(Δ). One population throughout; smaller `G^S`, potentially below the
  usable range at long horizons.
- **Horizon-varying:** use all eligible observations at each Δ. Larger
  `G^S(Δ)` at short horizons; the estimand's population changes with Δ and
  the path is not directly comparable across Δ.

Whichever is chosen must be preregistered **before** estimation. The choice
belongs on the §13 ballot.

**Cross-horizon comparability firewall.** Until that choice is ratified,
changes in `μ^S(Δ)` across horizons may reflect changes in sample / cluster
composition as well as horizon. The sequence of point estimates MUST NOT be
interpreted as the shape of a single fixed-population trajectory. Per-horizon
episode and cluster counts are required partly for this reason.

## 7. Route-A descriptive artifact — not an identified local projection

The current design is **not** a local projection. Every observation is a
treated episode. There is no untreated comparison variation. `Shock_i ≡ 1` is
collinear with the intercept. The object is a **stacked episode-level
mean-change (event-study-style) descriptive artifact**.

Do not describe it as “not a local projection yet.” It is not a local
projection by design.

### 7.1 Episode-horizon response

Define the episode-horizon response:

```text
D_i(Δ) = Y[i, τ_i(Δ)] − Y[i, ρ_i]
```

| Symbol | Meaning |
|---|---|
| `Y[i, ·]` | Outcome series value for episode *i* at the named analysis anchor |
| `τ_i(Δ)` | Mapped analysis anchor `M(a_i + Δ)` (§1, §3) |
| `ρ_i` | Clean pre-treatment reference anchor (§1.3) |
| `D_i(Δ)` | Episode *i* mean-change at calendar duration Δ |

One row represents **one treated episode at one horizon**.

### 7.2 Primary estimand — R-005 Option A cluster mean-of-means

Replace any episode-weighted regression intercept as the primary estimator.
When clusters contribute unequal numbers of episodes, that intercept is **not**
the same estimand as jointly selected R-005 Option A.

For reported sample `S ∈ {P, X}` and horizon Δ, define the cluster-level
response mean over the **identical contributing set** used by `n_c^S(Δ)`:

```text
D̄_c^S(Δ) = (1 / n_c^S(Δ))
           Σ_{i ∈ E^S(Δ) : cluster_id(i) = c} D_i(Δ)

μ^S(Δ)    = (1 / G^S(Δ))
           Σ_{c ∈ C^S(Δ)} D̄_c^S(Δ)
```

Numerator and denominator of `D̄_c^S(Δ)` are both restricted to contributing
episodes of cluster `c` in `E^S(Δ)`. Each contributing cluster receives weight
**exactly 1**.

**Zero-contributing-cluster fail-closed guard.** `μ^S(Δ)` is defined and
reportable only if `G^S(Δ) ≥ 1`. If `G^S(Δ) == 0`:

- do **not** compute or emit `μ^S(Δ)`;
- mark that sample / horizon **unavailable**;
- report `G^S(Δ) = 0` and the applicable exclusion / truncation / missingness
  tallies;
- never substitute zero, NaN-as-estimate, carry-forward, or silent omission.

This is a mathematical / domain guard, not a new scientific ballot choice. It
does **not** invent a minimum `G > 1`, and it does **not** turn the §8 future
inference tiers into a Route-A eligibility rule.

The primary Route-A artifact is **unadjusted**. The covariate-adjusted
regression previously written as

```text
D_i(Δ) = μ(Δ) + γ(Δ)'(X_i − X̄_w(Δ)) + ε_i(Δ)
```

is **not** the operative primary estimator. `X_i` is explicitly **UNRESOLVED**
(§7.6).

### 7.3 Identification note

Immediately following the definition of `μ^S(Δ)`:

- Every observation is a treated episode.
- The design has **no untreated comparison units**.
- That is why a binary `Shock_i` indicator is collinear with the intercept:
  in a stacked episode panel where every row is treated at the reported
  horizon, `Shock_i ≡ 1` for every row, so no separate treatment coefficient
  is identified. Any earlier draft equation containing `β(Δ)·Shock_i` is
  withdrawn for that mathematical reason (not merely because of
  post-treatment control concerns about later shocks). This is why
  local-projection terminology is removed from Route A: a local projection
  requires identifying comparison variation that this design does not have.
- The mean change `D_i(Δ)` absorbs seasonal, trend, market-wide, and other
  common movements occurring between `ρ_i` and `τ_i(Δ)`.
- `μ^S(Δ)` is identified as a **descriptive mean change** only.
- A causal reading would require additional counterfactual assumptions not
  testable within this design.
- **This ADR does not adopt those assumptions.**

The primary estimand identifies **no** counterfactual treatment effect.

### 7.4 Weighting — R-005 Option A only; R-005 itself unchanged

This ADR does **not** amend R-005.

The committed R-005 / `EPISODE_PROTOCOL.md` §H.2 rule requires that downstream
market event studies, impulse-response plots, and local projections MUST
either (A) collapse / average accepted episode observations to `cluster_id`
level, or (B) apply inverse-cluster weights `w_i = 1/K_c` (`K_c` = accepted
episodes in cluster *c*) **and** use cluster-robust standard errors clustered
by `cluster_id`. Those named objects are the committed ruling's scope. This
Route-A artifact is **not** one of them.

**Route A uses committed R-005 Option A only** as the aggregation rule for
this descriptive artifact: cluster mean-of-means with weight 1 per
contributing cluster (§7.2).

This ADR does **not**:

- redefine Option B;
- introduce `K_c(Δ)` as a replacement for committed R-005 / H.2's `K_c`;
- claim Option B is a robustness estimator for this artifact;
- report standard errors, p-values, or coverage / significance claims for
  `μ^S(Δ)`.

Option B remains a committed R-005 alternative that may be considered in a
**future separately ratified identified design** under the then-operative
R-005 rule.

### 7.5 Required per-horizon reporting

At every reported Δ, require reporting of:

- `μ^S(Δ)` **if** `G^S(Δ) ≥ 1`; otherwise the sample / horizon unavailable
  mark required by the §7.2 zero-cluster guard, never a substituted estimate;
- contributing episode count `|E^S(Δ)|`;
- `G^S(Δ)` contributing cluster count, including `G^S(Δ) = 0` when no
  cluster contributes;
- every contributing cluster mean `D̄_c^S(Δ)` when `G^S(Δ) ≥ 1`;
- each corresponding `n_c^S(Δ)` when `G^S(Δ) ≥ 1`;
- exclusion / censoring tallies by conceptually distinct reason (§7.10).

Do **not** select a summary dispersion statistic now. SD / IQR / range / any
other summary dispersion statistic remains explicitly **DEFERRED**. Showing the
actual cluster means and their contributing episode counts is the required
descriptive transparency.

### 7.6 Covariate universe `X_i` — deferred

`X_i` is added to the explicit deferred-item register (§13). No current
Route-A primary estimate uses `X_i`.

Any future covariate-adjusted secondary specification:

- requires separate preregistration;
- may use only information knowable no later than the pre-treatment reference
  `ρ_i`;
- must be outcome-blind;
- is non-implementable until that covariate set is jointly resolved.

This ADR does **not** invent a covariate list.

### 7.7 Seasonal-mixture caveat

Episodes can cluster in calendar time. Therefore common seasonal movement and
the episode response are **not separable** inside this Route-A `μ^S(Δ)`.

The descriptive artifact performs **no** causal seasonal adjustment.
Seasonality handling belongs to the later identified design (§7.9).

### 7.8 Permitted and prohibited claim language

The Route-A artifact licenses **no**:

- causal language;
- predictive language;
- “significant” language (or equivalent confirmatory language);
- impulse-response language;
- local-projection language;
- trade-thesis language.

Permitted language is descriptive: mean change, contributing counts, cluster
means, exclusion tallies, and the descriptive mean-change path with the
§6 cross-horizon firewall attached.

### 7.9 Milestone-4 local-projection firewall

Route A does **not** abolish future local projections. Nothing about Route A
automatically matures into a local projection through time, implementation
polish, or additional plotting. Route B remains reachable later.

Before any Milestone-4 estimator may be called a “local projection” or receive
causal interpretation, A + B must separately preregister and ratify an
identified design that specifies at minimum:

1. actual source of identifying variation;
2. outcome-blind construction of the comparison / variation source;
3. seasonality treatment consistent with project hard rules;
4. lagged-outcome / dynamics treatment;
5. ratified R-007 horizon values;
6. multiplicity treatment;
7. R-005 treatment appropriate to that identified design;
8. anchor-precision treatment;
9. synthetic ground-truth validation demonstrating recovery under planted
   response paths and dependence.

Until that separate ratification exists, local-projection terminology and
causal interpretation remain **blocked**.

### 7.10 Exclusion-reason reporting — concept now, machine taxonomy later

Require conceptually separate counts / tallies for at least:

- timestamp comparison / provenance unresolvable (Case 3), transparent by
  source family where appropriate so source-specific timestamp quality is not
  hidden;
- baseline collision with another qualifying episode (§5.4);
- no admissible `ρ_i` within `Δ_pre` (§5.5);
- later-shock censoring (§5.3);
- right-edge truncation (§5.7);
- missing outcome (§5.7).

**Do not invent machine-readable status strings in this ADR.** The machine
exclusion taxonomy is explicitly **DEFERRED** to a later dual-reviewed
code-interface decision. Formal count / tally implementation may not invent
ad-hoc reason strings.

### 7.11 MUST-report implementation gate

This ADR may declare report obligations, but formal estimation / reporting is
**blocked** until committed implementation exists.

Before any formal Milestone-4 estimation / reporting:

- per-horizon contributing episode counts exist in committed code;
- per-horizon contributing cluster counts exist;
- required cluster means / `n_c` are emitted;
- required exclusion / censoring tallies are emitted;
- the machine taxonomy has been preregistered / dual-reviewed;
- synthetic ground-truth fixtures verify exact known ledger geometry,
  per-horizon counts, and per-reason tallies;
- generation is reproducible through the repo's normal reproducible-build
  pathway;
- estimator / reporting code fails closed rather than emit a formal artifact
  missing mandatory accounting.

This ADR does **not** implement that machinery.

### 7.12 Placebo — mandatory diagnostic, not identification

The placebo is **diagnostic only**.

It provides no untreated comparison group. It provides no identifying
variation. It does **not** convert this artifact into a causal event study or
a local projection.

Once the needed D9 / D13 choices are ratified, construct the placebo
symmetrically on the pre-anchor grid using the same grid-step span as the
corresponding post / reference interval. This ADR does **not** invent grid
values now.

Every reported `μ^S(Δ)` must be accompanied by either:

- its corresponding preregistered placebo value; **or**
- an explicit placebo-unavailable status / reason.

Do **not** selectively omit unfavorable placebo values. A nonzero placebo is
evidence **against** causal interpretation, not evidence for identification.

Insufficient placebo pre-history does **not** automatically make an otherwise
eligible primary observation ineligible unless a later ballot explicitly says
so.

## 8. Few-cluster inference tiers — PROJECT HEURISTIC, NOT USED BY ROUTE A

The Route-A primary artifact reports **no** standard errors, p-values, or
coverage / significance claims at any cluster count (§7.4). The tiering below
therefore does **not** authorize inference on `μ^S(Δ)`.

The tiering is a **project heuristic proposed by Person B** for a **future
identified design**, not an established statistical standard and not a jointly
ratified rule. The cutpoints are judgment calls about where each inference
method stops being trustworthy at this project's cluster counts. They would be
evaluated on the sample-specific count `G^S(Δ)` for the sample being reported
(§6) **only after** an identified design is separately ratified (§7.9).

| Tier | `G^S(Δ)` | Proposed inference treatment (future identified design only) |
|---|---|---|
| T0 | < 4 | Descriptive only. No p-values. Report individual trajectories and range envelopes. |
| T1 | 4–5 | **Descriptive only.** See §8.1. |
| T2 | 6–14 | Primary: restricted-null wild cluster bootstrap. Secondary: CR2 (Bell–McCaffrey) corrected standard errors. |
| T3 | ≥ 15 | Cluster-robust inference with CR2 adjustment. |

These tiers govern **which inference method would be admissible at a horizon
in a future identified design**. They are not a kill condition and do not
redefine one — see §10. Adoption or replacement of the entire heuristic
remains on the §13 ballot.

### 8.1 Tier T1 (G = 4–5) — descriptive only

At T1 this heuristic authorizes **descriptive summaries only**.

It does **not** authorize randomization or permutation inference unless a valid
assignment / exchangeability design, an outcome-blind placebo pool, and a sharp
null are **separately preregistered and jointly ratified**.

At T1, **prohibit**:

- inferential p-values;
- coverage claims;
- the word “significant” (or equivalent confirmatory language); and
- causal or trade-thesis conclusions.

Route A already imposes those prohibitions at **every** `G^S(Δ)` (§7.8).

## 9. Model complexity accounting — PROJECT HEURISTIC, NOT USED BY ROUTE A

Also a proposed project heuristic for a **future identified / covariate-adjusted
design**, not a ratified rule, and not applicable to the unadjusted Route-A
primary artifact (`X_i` is unresolved; §7.6). Let:

```text
K           = actual total number of estimated parameters
p           = number of controls
K = 1 + p   # intercept + controls; no separate Shock_i coefficient
K_max(Δ)    = floor( G^S(Δ) / 3 ) + 1   # proposed ceiling for sample S
```

**Corrected accounting (resolves the earlier packet contradiction):**

- `K` is the **actual** number of estimated parameters.
- With `Shock_i` removed, `K = 1 + p`.
- `K_max(Δ)` is a **proposed ceiling**, not necessarily the number of parameters
  actually used.
- An **intercept-only** model has **`K = 1`, never `K = 2`**.
- At `G^S(Δ) ∈ {4, 5}`, T1’s descriptive-only rule (§8.1) may restrict the
  primary summary to the intercept-only response even though the formula’s
  numerical ceiling is 2.
- If the cap is fully used outside that restriction, maximum controls equal
  `K_max(Δ) − 1`.
- Do **not** silently preserve a fictitious “treatment slot.”

Worked ceilings under the formula (ceilings, not mandatory model sizes):

| `G^S(Δ)` | `K_max = floor(G/3)+1` | If fully used: max controls `p = K_max − 1` |
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
- **`G^P(Δ)` / `G^X(Δ)`** — statistical dependence groupings after
  analysis-layer exclusions (§6). This is what any future inference tiers and
  complexity caps would be measured on.

The §8 tiers constrain *method for a future identified design*; the committed
Sample-P episode-count kill condition continues to govern whether the project
proceeds at all, and any proposal to change it is a separate joint human
decision, not an inference-layer detail.

## 11. Ex-post variable restrictions (R-006)

`peak_severity_date`, `end_date`, and `duration_days` MUST NOT be used as the
R-001 t = 0 alignment anchor, as the censoring boundary (§5.3), or as
conditioning covariates in the Route-A descriptive artifact or in any future
market-response local projection. They may remain ex-post descriptive variables
and/or preregistered duration-response targets. §5's censoring rule is the same
principle applied to later shocks. This ADR does not amend R-006.

## 12. Multiplicity treatment — REQUIRED CHOICE, STILL OPEN

Registering horizon values without registering how the horizon path is tested
would re-import exactly the false-discovery problem quantified in §Context.
Exactly one of the following must be jointly chosen and preregistered before
any confirmatory use of a horizon path (including in a future identified
design):

- **(a) Single primary horizon.** One Δ is designated the primary test; all
  other durations are secondary/descriptive and are reported without
  confirmatory claims.
- **(b) Multiplicity-controlled simultaneous bands.** All Δ in the primary set
  are tested jointly under simultaneous (sup-t style) confidence bands or an
  equivalent family-wise correction, so that "the best horizon" cannot be
  reported as if it were the only one examined.

This ADR does not choose between (a) and (b). Reporting the most favourable
horizon from an uncorrected set is prohibited under either choice
(`CLAUDE.md` hard rule 4). Route A's descriptive `μ^S(Δ)` path is additionally
constrained by the §6 cross-horizon comparability firewall and by §7.8. The
choice itself remains on the §13 ballot.

## 13. Human joint ballot still required

ADR-0004 remains **`proposed`**. The body above reflects the jointly aligned
Route-A methodology; this exact edited text still requires exact-head review
before the ADR may become `accepted`. No item below is decided merely by
appearing in this file.

### 13.1 Proposed for exact-head ratification (aligned in this text)

These items are specified in the proposed Route-A text and must be visible on
the ballot so a choice is not embedded in prose while absent from the ballot:

1. **Route-A estimator identity / name** — stacked episode-level mean-change
   (event-study-style) descriptive artifact; not a local projection (§7).
2. **Descriptive estimand** — unadjusted R-005 Option A cluster mean-of-means
   `μ^S(Δ)` (§7.2 / §7.4).
3. **Permitted / prohibited claim language** (§7.8).
4. **Timestamp-reference cases** including fail-closed unresolvable timestamp
   comparison (§1.3).
5. **Clean-window collision / reference-containment / pooled accepted P∪X
   detection** rules (§5), with `Δ_pre` itself still unratified.

### 13.2 Explicitly deferred

None of the following are decided by this ADR. Each requires a later joint
A + B human Phase-0 decision:

1. **D9 numeric durations** — the §2 set `{7, 30, 90, 180}` days is a proposal
   only (R-007).
2. **Clean-window duration** `Δ_pre` (§5.1; proposed 90 days; **not
   operative**). The §5.10 H7 interaction must be visible at that ratification.
3. **Balanced versus horizon-varying estimation sample** (§6).
4. **Multiplicity treatment** — option (a) or option (b) (§12).
5. **Mapping `M` jointly with D13** (§3), including which admissible family
   (on-or-after / ceiling / floor / nearest) is chosen, **and all other D13
   values**. D12 remains unregistered.
6. **Nonzero-`anchor_precision_days` alignment rule**, which is the separate
   A + B preregistration that lifts the §4 / R-009 firewall.
7. **Adoption of the §8 tiers and §9 complexity-cap heuristic**, or their
   replacement. They do not apply to the Route-A primary artifact.
8. **Covariate universe `X_i`** (§7.6).
9. **Whether any dose / intensity variable is introduced** (§7.2).
10. **ADR-0004 pre-tag binding** — whether / how this ADR is added to the
    load-bearing ratification set after it merges and before `prereg-rules-v1`
    (§13.3).
11. **Summary dispersion statistic** for cluster means (§7.5).
12. **Machine-readable exclusion-reason taxonomy** (§7.10).

H7 itself is not being altered. Any list-valued-corridor interpretation needed
for ledger H7 remains a separate D2 / ledger matter.

### 13.3 Governance and pre-tag digest implications (revision-specific)

ADR-0003 N3 binds a `LOAD_BEARING_RELATIVE_PATHS` set into the ratification
manifest so that post-tag drift of an interpretation file fails closed. As of
this revision, ADR-0004 is **not** in that set (ADR-0005 is, after PR #7). That
is expected while this ADR remains `proposed`: binding an unratified inference
ADR would bind a placeholder. This edit does **not** add ADR-0004 to
`LOAD_BEARING_RELATIVE_PATHS`.

**Required future step (deferred item 10):** after this ADR merges as
`accepted` and **before** creating `prereg-rules-v1`, A + B must add ADR-0004
to the load-bearing ratification set so analysis-layer inference rules cannot
drift silently after the freeze. This ADR does **not** modify `governance.py`
in this change.

## Consequences

- `TGT_i(Δ) = a_i + Δ` is a grid-independent calendar target; the realized
  differenced response is not D13-independent. `M` is one D13 contact point
  among several (§1.1).
- The Route-A object is specified as a stacked episode-level mean-change
  descriptive artifact. Removing unidentified `Shock_i` / local-projection
  language prevents a collinear treatment term from being reported as an
  identified causal effect.
- Primary aggregation is R-005 Option A (weight 1 per contributing cluster),
  unadjusted, with no standard errors or p-values.
- Censoring at later `public_anchor` boundaries avoids post-treatment controls
  while honestly stating the selection cost; it does not claim bias elimination.
- Pooled accepted P∪X collision detection with per-sample reporting, closed
  same-day collision, and a separate `ρ_i`-outside-window condition make the
  clean-window rule operationalizable in concept once `Δ_pre` is ratified —
  and not before.
- Sample-specific `G^P(Δ)` / `G^X(Δ)` accounting prevents P/X pooling into a
  combined estimand and drops unconditional monotonicity claims. Until the
  balanced vs horizon-varying choice is ratified, the `μ^S(Δ)` sequence is not
  a fixed-population trajectory.
- The Milestone-4 firewall keeps local-projection terminology blocked until a
  separately ratified identified design exists.
- Because D9, `Δ_pre`, D13 / `M`, multiplicity, `X_i`, and other §13.2 items
  remain open, and because the §7.11 implementation gate is unmet, no
  market-response estimate may be produced under this ADR as it stands. That
  is the intended state: it is a preregistration document awaiting
  exact-head review and ratification, not an authorization to estimate.

## Evidence

**Committed evidence: none for this ADR's estimation rules.** No estimator in
this document has been implemented or validated in this repository, and no
synthetic fixture for the Route-A descriptive mean-change artifact exists.

**Planned evidence (not yet written, not part of this change).** Mechanical
Route-A synthetic fixtures test descriptive mean-of-means, counts, cluster
geometry, and exclusion / tally mechanics. They wait for the relevant ratified
interfaces, including at minimum:

- D9 durations;
- `Δ_pre`;
- D13 / mapping `M` and required analysis-grid conventions;
- §6 balanced-versus-horizon-varying sample policy;
- machine-readable exclusion-reason taxonomy.

The §12 multiplicity choice is **not** a prerequisite for writing or testing
those descriptive Route-A mechanics. §12 remains an unresolved choice required
for confirmatory use of a horizon path and for a future identified design, as
already stated in §12 and §13.2.

Once those Route-A interfaces are ratified, Person B should add synthetic
ground-truth fixtures under `tests/fixtures/` that:

1. encode exact known ledger geometry and assert that per-horizon contributing
   episode counts, cluster counts, cluster means / `n_c`, and per-reason
   tallies match the known schedule (§7.11), including the `G^S(Δ) == 0`
   fail-closed path;
2. plant a known descriptive mean-change path `μ^S(Δ)` together with known
   small-`G` cluster dependence and assert that Option-A aggregation recovers
   the planted cluster mean-of-means over contributing episodes only.

A later identified design, if separately ratified under §7.9, would additionally
require synthetic recovery under planted response paths and dependence before
any estimator may be called a local projection, and would require the then-
operative multiplicity treatment. Those fixtures do not exist today and this
ADR makes no claim that they do.

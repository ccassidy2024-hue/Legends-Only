# ADR-0004: Phase 0 Statistical Inference, Horizon Selection, and Overlap Protocol

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

## 0. Scope — what this ADR does NOT decide

This ADR selects **no**:

- D13 analysis-grid frequency, weekday/calendar convention, cutoff time,
  timezone, holiday treatment, or missing-anchor handling;
- calendar-duration → analysis-anchor mapping rule (that mapping is a D13
  dependency, §3);
- ratified D9 numeric horizon values (§2 proposes a candidate set only);
- balanced-versus-horizon-varying estimation sample policy (§6);
- release clock, release calendar, or any source fact;
- severity cutpoints (D12 remains deliberately unregistered per R-003).

It creates no live preregistration config, no ratification manifest, and no tag.
It runs no event study and no local projection, and it inspects no market
outcome. It does not modify `panel.py` or the frozen ADR-0001 four-column
observation interface.

## 1. Event-time mapping and the clean pre-event reference

Two distinct rulings govern here and are **not** interchangeable.

- **t = 0 mapping — R-001.** Where `public_anchor_precision == "date"`, the
  event becomes usable at the first analysis anchor whose calendar date is
  **strictly after** `public_anchor` (`first_usable_analysis_anchor`). The date
  is never interpreted as midnight, BOD, noon, or EOD. Where
  `public_anchor_precision == "timestamp"`, same-calendar-day use is permitted
  only when `anchor_ts <= analysis_anchor_ts` and the timestamp is
  source-supported.
- **Clean pre-event reference — R-004.** The pre-treatment reference
  `y_ref` is the **last analysis anchor strictly before `public_anchor`**.

**The distinction that must not collapse.** After R-001 remapping, the observation
at relative step `-1` is *not* generally `y_ref`. If `public_anchor` falls on
Oct 19 and the first eligible anchor is Oct 26 (t = 0), then relative step `-1`
is Oct 19 — the same calendar date as the anchor — which may already contain
information that became public during that day. R-004 requires Oct 12. Using
observed step `-1` as the reference is therefore prohibited: it is the exact
contamination R-004 was written to prevent, and it biases the estimated response
toward zero by absorbing part of the event into the baseline.

Throughout this ADR, `y_ref` always denotes the R-004 clean reference, never
relative step `-1`.

## 2. Primary estimand in calendar time (D9 — PROPOSED, NOT RATIFIED)

**Structural rule (methodological, proposed).** The primary estimand is defined
at **calendar-time economic durations** Δ measured in days from t = 0, not as a
count of analysis-grid steps.

Rationale, and it is not cosmetic:

1. The analysis grid is D13 and **unresolved**. A horizon expressed in grid
   steps makes the estimand a function of an unregistered decision — choosing
   the grid later would silently change what hypothesis is being tested.
   Calendar durations are invariant to the D13 choice.
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
re-expression of the `{1, 4, 12, 26}` week set in the superseded draft of this
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

## 3. D13 firewall

This ADR does **not** select any analysis-grid parameter. It also does not
license inheriting one by default.

Before any market-response estimation, D13 must separately preregister the grid
frequency, weekday/calendar convention, cutoff time, timezone, holiday
treatment, and missing-anchor handling, together with a **deterministic mapping
from a calendar duration Δ to an analysis anchor**. That mapping is itself a
preregistered choice (for example: first anchor on or after `t0 + Δ`, versus
nearest anchor to `t0 + Δ`); this ADR names the requirement and selects none of
the options.

**Implementation hazard to be closed explicitly, not silently.** The repository
already contains grid-shaped defaults that no ADR has ratified:
`panel.weekly_anchors` defaults to a Friday convention stamped at 23:59, and
`panel.synthesise_release_ts` defaults `release_hour=12`. Those are code
defaults, not preregistered decisions, and D13 must either ratify them against
Person A's verified release-calendar evidence or override them. Any change to
`panel.py` is leakage-sensitive and requires the separate dual-reviewed lane
(`WORKFLOW.md` §2); it must not be attempted on a discovery or ADR branch.

## 4. Anchor-precision firewall (does not interact with sensitivity checks)

Where `anchor_precision_days > 0`, market-response event-window and local-
projection **alignment is blocked** until A + B separately preregister how
nonzero anchor uncertainty affects t = 0 and pre-treatment baseline
construction. Ledger admission and descriptive use may proceed if the episode is
otherwise admissible.

This firewall is recorded in ADR-0005 P1 with lookup entry R-009. At the time
this revision was written those records live on the source-handling branch
(PR #7) and are **not yet present on `main`**; this section states the
constraint prospectively and does not assert that the record already exists on
this branch.

**A jitter or anchor-sensitivity check does not lift this firewall.** The
superseded draft of this ADR proposed shifting anchors by ±1 grid step as a
robustness envelope. Re-estimating under perturbed anchors measures how sensitive
a result is to anchor placement; it does not supply the missing preregistered
rule for *where t = 0 and `y_ref` belong* when the anchor day itself is
uncertain. A sensitivity envelope may be reported as a diagnostic once alignment
is unblocked. It is not a substitute for the A + B preregistration, and it may
not be used to justify estimating on episodes the firewall excludes.

## 5. Overlap handling — eligibility, then censoring (not future-shock controls)

- **Clean pre-event eligibility.** Episode *i* is eligible for primary
  estimation only if no prior qualifying episode in the same corridor falls
  within a preregistered pre-event clean window ending at `y_ref`. **Proposed,
  not ratified:** a 90-calendar-day pre-window (a re-expression of the
  superseded draft's 12 weeks). The value is part of the §13 ballot.
- **Post-t = 0 contamination is handled by censoring, never by controlling.**
  If a subsequent qualifying shock onsets at `T_i + Δ_next`, the response path
  for episode *i* is **censored/truncated at `Δ_next`**: horizons `Δ ≥ Δ_next`
  contribute no observation for that episode.

  The superseded draft instead added a `Shock_j` indicator as a control
  covariate at contaminated horizons. That is rejected. A shock occurring after
  t = 0 is a **post-treatment** variable: conditioning on it induces
  post-treatment/collider bias, and where the second shock is itself partly a
  consequence of the first (a plausible mechanism in a congested corridor) the
  control absorbs part of the very response being estimated. This is the same
  principle R-006 applies to `peak_severity_date`, `end_date`, and
  `duration_days` — quantities knowable only after the episode unfolds may not
  condition the estimator.

- **Consequence, stated rather than hidden: the estimation sample is
  horizon-dependent.** Censoring removes long-horizon observations
  non-randomly — episodes in busy corridors and episodes near the right edge of
  the sample lose their long horizons first. Therefore `β(Δ)` at Δ = 180 d is
  **not** estimated on the same population as `β(Δ)` at Δ = 7 d, and the
  reported sequence is not one population's response path unless a balanced
  sample is imposed (§6).
- **Right-edge censoring.** ADR-0003 D1(8) forbids moving `sample_end` earlier
  merely to guarantee a full post-event horizon. Right-edge truncation is
  therefore an analysis-layer censoring/eligibility problem, handled here and in
  §6, and never by shortening the sample period.
- **H7 unchanged.** H7 (≤ 1 episode per corridor/driver per 60 days) remains an
  episode deduplication rule in `EPISODE_PROTOCOL.md` §H. It is not modified,
  relaxed, or reinterpreted for estimation convenience.

## 6. `G_LP(Δ)` — cluster accounting after every exclusion

Define:

```text
G_LP(Δ) = number of independent driver clusters (cluster_id) contributing at
          least one LP-eligible, uncensored episode observation at duration Δ
```

`G_LP(Δ)` is computed **after** all of: Sample P / Sample X membership
(`EPISODE_PROTOCOL.md` §E.4), clean pre-event eligibility (§5), later-shock
censoring (§5), right-edge censoring (§5), and the anchor-precision firewall
(§4). It is weakly decreasing in Δ.

**`G_LP(Δ)` MUST be reported at every horizon**, alongside the number of
contributing episodes, whenever any response path is presented. Reporting a
path without it invites the reader to assume a constant sample that does not
exist.

**Unresolved joint decision — balanced versus horizon-varying sample.** Two
admissible policies exist and this ADR selects neither:

- **Balanced:** restrict every horizon to episodes with complete coverage to
  max(Δ). One population throughout; smaller `G_LP`, potentially below the
  usable range at long horizons.
- **Horizon-varying:** use all eligible observations at each Δ. Larger
  `G_LP(Δ)` at short horizons; the estimand's population changes with Δ and the
  path is not directly comparable across Δ.

Whichever is chosen must be preregistered **before** estimation, because
choosing it afterward is a specification search over sample composition. The
choice belongs on the §13 ballot.

## 7. Primary estimator architecture

Stacked episode-panel local projection on the clean reference:

```text
Y[i, T_i + Δ] - Y[i, y_ref] = α(Δ) + β(Δ)·Shock_i + γ(Δ)'X_i + ε[i, Δ]
```

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
this project's cluster counts. They are stated so they can be argued with, and
they are evaluated on `G_LP(Δ)` — which varies by horizon (§6), so the
applicable tier may differ across Δ.

| Tier | `G_LP(Δ)` | Proposed inference treatment |
|---|---|---|
| T0 | < 4 | Descriptive only. No p-values. Report individual trajectories and range envelopes. |
| T1 | 4–5 | Randomization/permutation inference and Webb (2014) 6-point wild cluster bootstrap only, with explicit small-sample warnings. |
| T2 | 6–14 | Primary: restricted-null wild cluster bootstrap. Secondary: CR2 (Bell–McCaffrey) corrected standard errors. |
| T3 | ≥ 15 | Cluster-robust inference with CR2 adjustment. |

These tiers govern **which inference method is admissible at a horizon**. They
are not a kill condition and do not redefine one — see §10.

## 9. Model complexity cap — PROJECT HEURISTIC

Also a proposed project heuristic, not a ratified rule. Total estimated
parameters `K` at a given horizon (intercept + treatment + controls) is capped
relative to the cluster count actually available at that horizon:

```text
K(Δ) ≤ floor( G_LP(Δ) / 3 ) + 1
```

Worked values, arithmetically consistent with that formula:

| `G_LP(Δ)` | `floor(G/3) + 1` | Practical content |
|---|---|---|
| 4–5 | 2 | intercept + treatment only |
| 6–8 | 3 | + one control (e.g. `y_ref`) |
| 9–11 | 4 | + two controls |
| 12–14 | 5 | + three controls |
| 15 | 6 | + four controls |

The superseded draft's worked examples did not follow its own formula (it
asserted `K ≤ 3` at G = 10 and `K ≤ 5` at G = 15, where the formula gives 4 and
6). The table above is corrected. Because the cap binds on `G_LP(Δ)`, the
admissible control set may legitimately shrink at longer horizons.

## 10. Kill condition — committed rule is NOT overridden here

The project's kill condition is already committed and this ADR does not
redefine, relax, or replace it:

> `episode_schema.yaml`: `kill_condition_primary_sample_min: 6`, on **accepted
> Sample P episodes**; `WORKFLOW.md` names "fewer than 6 usable episodes" as the
> point at which the question is unanswerable with this data.

Two distinct quantities must not be conflated:

- **`N_episodes` in Sample P** — accepted episode rows. This is what the
  committed kill condition is measured on.
- **`N_independent_driver_clusters` / `G_LP(Δ)`** — statistical dependence
  groupings, per R-002 and §6. This is what inference tiers and complexity caps
  are measured on.

The superseded draft introduced a second, weaker kill threshold at `G < 4` and
demoted 6 to "suspend trade thesis preregistration". That is withdrawn. The §8
tiers constrain *method*; the committed Sample-P episode-count kill condition
continues to govern whether the project proceeds at all, and any proposal to
change it is a separate joint human decision, not an inference-layer detail.

## 11. Ex-post variable restrictions (R-006)

`peak_severity_date`, `end_date`, and `duration_days` MUST NOT be used as the
t = 0 alignment anchor or as conditioning covariates in market-response event
studies or local projections. They may remain ex-post descriptive variables
and/or preregistered duration-response targets. §5's censoring rule is the same
principle applied to post-t = 0 shocks.

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

1. **D9 numeric values** — pre-event, post-event, and reference/baseline
   horizons. The §2 set `{7, 30, 90, 180}` days is a proposal only (R-007).
2. **Pre-event clean-window duration** (§5; proposed 90 days).
3. **Balanced versus horizon-varying estimation sample** (§6).
4. **Multiplicity treatment** — option (a) or option (b) (§12).
5. **Calendar-duration → analysis-anchor mapping rule**, jointly with D13 (§3).
6. **Nonzero-`anchor_precision_days` alignment rule**, which is the separate
   A + B preregistration that lifts the §4 firewall.
7. **Adoption of the §8 tiers and §9 complexity cap** as project heuristics, or
   their replacement.

### Governance and pre-tag digest implications

ADR-0003 N3 binds a `LOAD_BEARING_RELATIVE_PATHS` set into the ratification
manifest so that post-tag drift of an interpretation file fails closed. That set
governs **sweep authorization** and does not currently include this ADR, which
is correct: ADR-0004 governs analysis-layer estimation, not candidate discovery,
and binding it to `prereg-rules-v1` would force digest churn for a document the
sweep does not consult.

That leaves a gap the humans should close deliberately rather than by default:
**analysis-layer preregistration is currently digest-bound by nothing.** Before
the freeze tag (`preregistration-v1`), A + B should decide whether this ADR and
its ratified numeric values are bound into a manifest at that tag, so the
inference rules cannot drift silently after the ledger is frozen. This ADR does
**not** modify `governance.py` and does not bind itself; doing so while its
values remain proposed would bind a placeholder.

## Consequences

- Defining the estimand in calendar durations decouples the hypothesis from the
  unresolved D13 grid, so the grid decision can no longer silently change what
  is being tested.
- Censoring at later-shock onset removes a post-treatment control that would
  have biased `β(Δ)` and, in a congested corridor, could have absorbed part of
  the response itself — at the cost of a horizon-dependent sample that must be
  reported via `G_LP(Δ)`.
- Requiring `G_LP(Δ)` at every horizon makes the shrinking long-horizon sample
  visible instead of implicit, and makes it possible to see when a long-horizon
  estimate rests on too few clusters to interpret.
- Separating episode count from cluster count keeps the committed Sample-P kill
  condition intact while still constraining inference method by cluster count.
- Because the §4 firewall and the §12 multiplicity choice both remain open, no
  market-response estimate may be produced under this ADR as it stands. That is
  the intended state: it is a preregistration document awaiting ratification,
  not an authorization to estimate.

## Evidence

**Committed evidence: none for this ADR's estimation rules.** No estimator in
this document has been implemented or validated in this repository, and no
synthetic fixture for episode-panel local projections exists.

**Planned evidence (not yet written, not part of this PR).** Once the D9 values
and the §6 and §12 choices are ratified, Person B should add synthetic
ground-truth fixtures under `tests/fixtures/` that plant a known response path
`β(Δ)` together with known small-`G` cluster dependence, and assert that the
implemented estimator recovers the planted path, that inverse-cluster weighting
and cluster-robust inference behave correctly at small `G_LP`, and that the §5
censoring rule reproduces the expected `G_LP(Δ)` schedule. Those fixtures are
the evidence that would justify moving this ADR beyond `proposed`; they do not
exist today and this ADR makes no claim that they do.

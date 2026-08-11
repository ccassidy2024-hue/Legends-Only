# ADR-0002: Episode Ledger pre-registration protocol

- **Date:** 2026-08-10
- **Author:** A | B
- **Status:** proposed
- **Gate:** A(data) | B(statistics)

## Context

Milestone 1 is the Episode Ledger, not the screener (`BLUEPRINT_REVIEW.md` §1).
The ledger *is* the sample: with 15–25 episodes, each entry carries roughly 4–6%
of the project's total evidence, and the dominant failure mode is not too few
episodes but **false independence** — several manifestations of one shock
counted as several episodes, which understates standard errors by roughly √k.

Two failure modes are invisible after the fact and therefore have to be
prevented structurally rather than reviewed for:

1. **Outcome-selected candidates.** Human and LLM recall of grain-logistics
   events is filtered through market salience. A candidate list built from
   memory has already conditioned on the outcome.
2. **Event-level look-ahead.** `build_asof_panel` guards series vintages
   (ADR-0001) but cannot see event dates. Anchoring an episode on its physical
   onset rather than on when it became public inserts the "delay" that the
   project's hypothesis is supposed to test.

## Decision

Adopt `research/episodes/EPISODE_PROTOCOL.md`, with
`research/episodes/episode_schema.yaml` as the machine-readable single source of
truth. Load-bearing choices:

1. **Two locks.** Rules are committed and tagged before candidates exist;
   candidates are complete and frozen before any market data is opened. The
   second lock binds the researchers' information set, not just the files —
   accidental exposure is logged in `outcome_exposure_log`, not hidden.
2. **`public_anchor` is t = 0.** The episode-level analogue of `release_ts`.
   `physical_onset` and `official_announcement` may be recorded separately and
   used as pre-registered robustness anchors where the protocol allows.
   `peak_severity_date` is ex-post: it must never be used as t=0 alignment for
   market-response event studies / LPs, and must never be a conditioning
   covariate in those estimators. It may remain descriptive and/or an
   explicitly preregistered duration-response target, consistent with
   `EPISODE_PROTOCOL.md` §B.5 / R-006.
3. **Candidates come from mechanical source sweeps (S1–S8), never from recall.**
   LLM-suggested candidates require independent sweep confirmation or are
   rejected `R2`.
4. **Severity is derived by code** from physical metrics, using percentile
   cutpoints of each class's own physical history. Humans never type a severity
   class. Prices — including barge freight rates — may never enter severity.
5. **Contamination stratifies, it does not filter.** Sample P (classes A/B) is
   the headline sample; Sample X adds class C; class D is excluded. The split is
   pre-registered so it cannot be tuned later.
6. **Navigation basin and growing region are separate required fields**, because
   the exclusion restriction for the precipitation instrument depends on that
   distinction (`BLUEPRINT_REVIEW.md` §5).
7. **Dedup rules H1–H9 plus a mandatory independence audit at freeze.** Primary
   reporting is `N_episodes` and `N_independent_driver_clusters`.
   `N_underlying_drivers` is descriptive only. Default
   `cluster_id = underlying_driver_id` unless a documented ruling says
   otherwise. No privileged episodes-per-driver ratio. Preserve physically
   distinct rows. Downstream market event studies / IRFs / LPs **must** either
   collapse to `cluster_id` or use inverse-cluster weights with cluster-robust
   SEs (`EPISODE_PROTOCOL.md` §H.2).
8. **Date-only public anchors use the conservative mapping:** first analysis
   anchor strictly after the public_anchor calendar date
   (`first_usable_analysis_anchor`). Pre-treatment baseline is the last analysis
   anchor strictly before `public_anchor` (not t=−1 after remapping). Timestamp
   precision allows same-day use only when `anchor_ts <= analysis_anchor_ts`.
9. **Ex-post fields** (`peak_severity_date`, `end_date`, `duration_days`) are
   not t=0 anchors and not conditioning covariates in market-response event
   studies / LPs (`EPISODE_PROTOCOL.md` §B.5).
10. **Rejected candidates are retained** with reason codes, so a reviewer can
   audit the rejection pattern.
11. **Enforcement in code.** `python -m grainsys.episodes` runs in `make all`; a
   `market_outcomes_reviewed: true` entry fails the build.

## Open items — must be closed in Phase 0 before any candidate is recorded

- Sample period, corridor list, and per-class physical thresholds
- Severity calibration ADR: metrics by class, reference period, as-of vs
  ex-post, cutpoints, combination rule, missing-data treatment; only then set
  `cutpoints_registered: true`
- Market-response horizons to preregister **before corresponding estimation**
  (numerical values are an A+B decision; not invented here):
  - pre-event horizon
  - post-event horizon
  - reference / baseline horizon
- The three-candidate calibration set for inter-rater alignment

Until cutpoints are registered, the validator deliberately leaves
`severity_class` null rather than guessing. Raw physical metrics may still be
collected.

**Note:** ADR-0002 remains **proposed**. Person B CHANGES_REQUESTED items on
PR #1 are encoded in the protocol / `RULINGS.md` (R-004–R-007) and await
re-audit; this ADR is not falsely marked accepted.

## Consequences

- Milestone 1 costs 50–70 person-hours. That is the real price of a sample that
  survives adversarial review.
- Sample P may well be 6–10 episodes. `WORKFLOW.md` already names "fewer than 6
  usable episodes" as a kill condition; learning this at pre-registration is the
  cheapest possible time to learn it.
- Anchor and dedup decisions get the same mandatory dual review as `panel.py`
  and the leakage tests — they are the episode-layer equivalent of leakage.
- Post-freeze episode changes require a further ADR and are analysed as a
  separate, labelled sample.

## Evidence

`tests/test_episodes.py` plants malformed, outcome-contaminated and
severity-hand-assigned entries and asserts the validator rejects each one.

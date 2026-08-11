# Episode Methodology

**The operative document is `research/episodes/EPISODE_PROTOCOL.md`.** This page
is the short summary; on any conflict, the protocol and
`research/episodes/episode_schema.yaml` win.

## Purpose

The Episode Ledger is the pre-registration unit for mechanism research. Weekly
series are highly autocorrelated; independent physical stress episodes are much
closer to the effective sample for cascade questions
(`BLUEPRINT_REVIEW.md` §1).

## Order of work

1. Pre-register the rules — thresholds, severity cutpoints, event windows — and
   tag them, before writing down a single candidate.
2. Generate candidates by mechanically sweeping primary sources. Never from
   memory: recall of grain events is filtered through market salience, which is
   outcome selection with extra steps.
3. Verify physical evidence, fix the anchor, score severity from physical
   metrics, assess contamination and substitution.
4. Second-researcher review, then freeze.
5. Only after the freeze tag may market outcomes be examined, in an explicitly
   labelled pass.

## What counts as an episode

A dated interval when a documented physical or operational constraint
materially degraded a U.S. grain logistics corridor's capability to move, load,
transfer or hold grain, with an anchor date that was publicly observable at the
time.

A gauge reading or storm track is a **driver**, not an episode. It becomes an
episode only when a primary source documents an operational consequence.

## Identification discipline

- `public_anchor` (first publicly observable date) is t = 0; physical onset,
  official announcement and peak severity are recorded separately.
- `public_anchor_precision` records whether the source supports a **date** or an
  exact **timestamp**. Date-only evidence must not invent a clock time. Primary
  mapping: first analysis anchor **strictly after** the public_anchor date
  (`first_usable_analysis_anchor`).
- Severity metrics are **raw physical evidence**; `severity_class` is **derived**
  and stays null until Phase 0 cutpoints are registered. Ex-post descriptive
  classes must not masquerade as contemporaneous.
- Primary reporting: `N_episodes` and `N_independent_driver_clusters`.
  `N_underlying_drivers` is descriptive. Default
  `cluster_id = underlying_driver_id`. Preserve physically distinct rows.
- Severity from physical metrics only — never prices, and never barge freight
  rates, which are a price.
- Navigation-basin geography is recorded separately from growing-region
  geography; that distinction is what makes the precipitation instrument
  defensible (`BLUEPRINT_REVIEW.md` §5).
- Contamination classes stratify the sample rather than filtering it after the
  fact.
- Substitution channels record ex-ante availability; usage only where
  documented.
- Export Sales ≠ Export Inspections; Grain Stocks are slow and revised.

## Enforcement

`python -m grainsys.episodes` (in `make all`) validates every entry against the
schema, refuses to let a human hand-assign severity, regenerates the ledger
summary, and fails the build if any entry has `market_outcomes_reviewed: true`
before the freeze.

## Relationship to screening and modelling

- Pairwise screening around episodes is exploratory / hypothesis-generating.
- Serious dynamics use direct shock-response methods (Jordà local projections)
  off an identified shock, not chained pairwise correlations.
- Accounting identities are not discoveries; prefer residuals, duration and
  deviations.

## Statement separation

Always separate: what the data show | why we think it happens | what we expect
next | how it could be traded. A written negative result is a valid outcome.

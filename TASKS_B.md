# TASKS_B.md — Person B: statistics / models

## Ownership

Ownership means **default work assignment**. It never exempts a change from
REVIEW-ROUTING-v1 (ADR-0014 / `WORKFLOW.md`) Tier A/B/C requirements.

- Synthetic validation and ground-truth fixtures (`tests/fixtures/`)
- `src/grainsys/screening/` (exploratory only; honest multiple-testing treatment)
- Robustness checks
- Event-study machinery around the Episode Ledger
- `src/grainsys/modeling/` (local projections and later dynamics — when authorized)
- Mechanism memos' statistical sections (`research/memos/`)

## Frozen interface from Person A

```python
columns = ["series_id", "period_end", "release_ts", "value"]
Panel = build_asof_panel(obs, anchors)  # .values, .age_days
```

Build against synthetic fixtures before real USDA/market panels exist.

## Inferential discipline

- Naive best-of-many-lags p-values are exploratory, not ordinary significance
- Prefer max-t / permutation-style correction for lag mining
- Accounting identities are not discoveries
- Separate: what data show | why | expect next | how traded
- Negative results are valid

## Current milestone focus

Validate plumbing on synthetic data (done in foundation tests).
Milestone 1 closed as a negative result (0 admissible episodes; Sample P = 0).
Support Milestone 2–5 without fabricating observations or opening market data.
An empty upstream sample may make M3–M4 not-estimable; write that down.

## Review sensitivity

Follow REVIEW-ROUTING-v1. Screening lag / panel / leakage / inference /
freeze-gate work is typically Tier B (exact-head counterpart review before
merge). New scientific choices escalate to Tier A. Do not weaken those tests.

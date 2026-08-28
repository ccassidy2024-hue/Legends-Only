# TASKS_A.md — Person A: data / plumbing

## Ownership

Ownership means **default work assignment**. It never exempts a change from
REVIEW-ROUTING-v1 (ADR-0014 / `WORKFLOW.md`) Tier A/B/C requirements.

- Source verification and documentation (`docs/sources/`)
- `catalog/series/*.yaml` (one file per series; no invented IDs/delays)
- `src/grainsys/ingest/`
- Release timing / vintage assumptions (recorded in YAML, never guessed in notebooks)
- `src/grainsys/panel.py` and as-of panel construction
- Episode physical-data research (`research/episodes/`)

## Frozen interface to Person B

```python
# long-format observations
columns = ["series_id", "period_end", "release_ts", "value"]

# panel builder
Panel = build_asof_panel(obs, anchors)  # .values, .age_days
```

Ship synthetic fixtures first so B is never blocked on real data.

## Current milestone focus

**Milestone 1 — Episode Ledger / pre-registration:** closed as an
empty-ledger negative result (4234 no-episode dispositions, 0 survivors,
0 admissible rows). Market outcomes remain unopened.

**Milestones 2–8:** M2 is `M2_NEGATIVE_RESULT_EMPTY_SAMPLE` (0 catalogued
real series; do not fabricate `release_ts` or resurrect dropped D5
candidates). M3/M4 are written not-estimable (zero ledger windows / zero
identified shocks). M3 family size = 0 tests performed. M5 Gate C FAIL memo
`research/memos/M5_NEGATIVE_RESULT_MECHANISM.md` awaits A/B human signatures.
M6/M7 skipped
under the <6 kill. M8 is `M8_WRITTEN_NEGATIVE_RESULT_UNANSWERABLE`.
Synthetic `panel.py` plumbing stays; do not edit it for this closeout.

## Review sensitivity

Follow REVIEW-ROUTING-v1. Panel / leakage / lineage / capture / freeze-gate
work is typically Tier B (exact-head counterpart review before merge). New
scientific choices escalate to Tier A. Do not weaken leakage tests.

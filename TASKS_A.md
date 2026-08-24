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

**Milestone 1 — Episode Ledger / pre-registration**

- Populate episodes from documented physical/logistics evidence only
- Leave market outcomes blank
- Record contemporaneous knowability and sources

Then **Milestone 2 — As-of panel + leakage protection** on real series once catalogued.

## Review sensitivity

Follow REVIEW-ROUTING-v1. Panel / leakage / lineage / capture / freeze-gate
work is typically Tier B (exact-head counterpart review before merge). New
scientific choices escalate to Tier A. Do not weaken leakage tests.

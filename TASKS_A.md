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

**Milestone 1 — Episode Ledger / pre-registration — CLOSED (negative result)**

- Frozen D5 = 4234 candidates; Phase-2 I1/I2/I3 triage: 4234 no-episode
  dispositions, 0 survivors, 0 admissible episode rows
- Do not invent episode YAML or reopen discovery to manufacture survivors
- UNKNOWN is not zero; S4 proximity is driver-only absent I2

**Milestone 2 — As-of panel + leakage protection**

- Synthetic `panel.py` + leakage tests already exist
- Real as-of panel requires catalogued series with genuine `release_ts`
- Do not invent source IDs, release delays, or observations
- Do not resurrect dropped M1 candidates as panel rows

## Review sensitivity

Follow REVIEW-ROUTING-v1. Panel / leakage / lineage / capture / freeze-gate
work is typically Tier B (exact-head counterpart review before merge). New
scientific choices escalate to Tier A. Do not weaken leakage tests.

# ADR-0001: Canonical observation schema and lag convention

- **Date:** 2026-08-10
- **Author:** A | B
- **Status:** accepted
- **Gate:** A(data) | B(statistics)

## Context

As-of panel construction and lag screening both require a single observation
schema and a single lag-direction convention. Without them, look-ahead leakage
and reversed "lead/lag" claims are inevitable.

## Decision

### Observation schema (frozen interface)

Long-format observations must carry:

```text
series_id, period_end, release_ts, value
```

- `period_end` — the period the observation is about
- `release_ts` — when the information became available (mandatory for
  time-dependent real observations)
- Panel construction: `Panel = build_asof_panel(obs, anchors)` exposing at
  least `.values` and `.age_days`
- No observation may enter an anchor if `release_ts > anchor`

### Lag convention (defined once)

```text
lag = +k  means  X known at t is evaluated as a predictor of Y at t+k
```

Positive lag therefore means **X leads Y**.

### Statement separation

Always separate: what the data show | why we think it happens | what we expect
next | how it could be traded.

## Consequences

- Indexing panels on `period_end` alone is forbidden for research claims.
- Screener output uses this lag sign convention only.
- Changes to `panel.py`, screening lag logic, or leakage tests require careful
  dual review (see `WORKFLOW.md` / `TASKS_*.md`).

## Evidence

Synthetic fixtures and tests under `tests/` plant known lags and release delays
and must continue to pass.

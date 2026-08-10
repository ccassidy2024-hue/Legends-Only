# CLAUDE.md — Legends-Only / grainsys

Persistent instructions for AI assistants in this repository.

## Canonical path

`C:\dev\Legends-Only` is the only development root. Do not create a second project root.

## Document hierarchy

1. `PROJECT_BLUEPRINT.md` — original vision
2. `BLUEPRINT_REVIEW.md` — methodological amendments (**wins** on methodology / milestone order)
3. `WORKFLOW.md` — operating agreement
4. This file + `.cursor/rules/project.mdc` — concise implementation rules

## Objective

Mechanism-aware discovery for U.S. grain logistics — not generic ML prediction.
Negative results are valid.

Chain: physical/logistics shock → operational response → participant adaptation →
inventory/flow → market → possible delayed underreaction → falsifiable trade thesis.

Separate always: what data show | why we think it | what we expect next | how traded.

## Milestone order

0 setup → 1 Episode Ledger → 2 as-of panel → 3 exploratory screener → 4 local projections →
5 mechanism + lit review → 6 stronger ID → 7 historical replay → 8 thesis or negative result.

No early NetworkX cascade graph. No ABM / SD / optimizer / trading UI / DL scope creep.

## Hard rules

1. No look-ahead. Schema: `series_id, period_end, release_ts, value`. `release_ts` mandatory for real timed obs.
2. `build_asof_panel(obs, anchors)` → `.values`, `.age_days`. Reject `release_ts > anchor`.
3. `lag=+k` means X_t predicts Y_(t+k) (X leads Y). Defined once; enforce with synthetic tests.
4. Screener is exploratory. Naive min p across lags ≠ ordinary significance. Prefer max-t / permutation correction.
5. Episodes are the important research unit; identify from physical evidence before market outcomes when practical.
6. Accounting / near-accounting identities are not discoveries; prefer residuals, duration, deviations.
7. Seasonality is a major confounder; OOS transforms must not use future info.
8. When testing X→Y, account for Y's own history where appropriate.
9. Never silently interpolate across large missing periods.
10. Transforms reproducible and documented.
11. Export Sales ≠ Export Inspections; Grain Stocks ≠ fresh weekly info.
12. Navigation-basin weather ≠ crop-growing-region weather.
13. Substitution channels: Gulf vs PNW, barge vs rail, U.S. vs Brazil/other origins.
14. No invented source IDs or release delays.
15. No memo number unless regenerable from committed code (`make all`).
16. Do not weaken panel/timing/lag tests — fix the implementation.

## Code layout

`src/grainsys/`: `panel.py`, `catalog.py`, `ingest/`, `transforms/`, `screening/`, `modeling/`, `utils/`

One YAML per series under `catalog/series/`. Raw data immutable. Notebooks gitignored.

## Frozen A/B interface

Observations columns above + `build_asof_panel`. See `TASKS_A.md` / `TASKS_B.md`.

Changes to `panel.py`, screening lag logic, or core leakage tests need careful dual review.

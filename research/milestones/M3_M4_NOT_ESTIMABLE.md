# M3 / M4 — not estimable

Both follow from the closed M1 empty ledger and the M2 empty real sample.
No new scientific values. No universe screen. No residual-threshold shock.

## M3 — exploratory screener

**Result: `NOT_ESTIMABLE`.** Reason: `zero_ledger_windows`.

- `N_episodes = 0`, `N_independent_driver_clusters = 0` (ledger generated
  summary).
- Authorized event-study screening runs **inside and around Episode Ledger
  windows** (`BLUEPRINT_REVIEW.md` §1 and revised milestone 3). There are no
  windows.
- `src/grainsys/screening/lagscan.py` is exploratory plumbing (`min_obs=104`,
  HAC, max-t). It is not a license to universe-screen real series, and there
  are no catalogued real series to screen.
- Multiplicity for an empty episode set is already `N_episodes=0`. Naive
  best-lag p-values remain non-evidence.

## M4 — local projections

**Result: `NOT_ESTIMABLE`.** Reason: `zero_identified_shocks`.

- Jordà local projections need **one identified shock**
  (`BLUEPRINT_REVIEW.md` §4). The ledger has 0 accepted episodes.
- `src/grainsys/modeling/` remains a stub. Do not invent a residual-threshold
  or statistical shock; that would be a **new Tier A** scientific choice.
- Do not reintroduce an early NetworkX cascade graph.

## Kill condition

`WORKFLOW.md`: fewer than 6 usable episodes → the question is unanswerable
with this data; say so and stop. Sample P = 0.

Honesty: UNKNOWN is not zero. Missing I2 is not proof of no physical
disruption. S4 proximity is driver identity only absent I2.

Machine-readable twin: `empty_sample_closeout.yaml`.

# M2 — `M2_NEGATIVE_RESULT_EMPTY_SAMPLE`

Milestone 2 as-of panel plumbing is already on `main` (`src/grainsys/panel.py`,
synthetic leakage tests). This file records the **research-sample** result, not
a rewrite of that plumbing.

## Result

`M2_NEGATIVE_RESULT_EMPTY_SAMPLE`

- Catalogued real series: **0** (`catalog/series/` has `_template.yaml` and
  `README.md` only).
- Real as-of panel rows: **0**. No committed observations under `data/`.
- Fabricated observations: **false**.
- `panel.py` / leakage tests: **unchanged** by this closeout.

## Why empty is the correct result

`build_asof_panel` is **series-keyed**, not episode-keyed (ADR-0001). M1
`N_episodes = 0` does not by itself forbid series-based rows. This repository
still has **zero catalogued real series** and forbids invented `source_id` /
`release_ts` / release delays. A non-empty **real** panel would be fabrication.

Synthetic panel construction and leakage tests stay as the M2 plumbing proof.
Do not redo them. Do not resurrect dropped D5 candidates as series or
observations. Market data stays closed.

The episode-anchored event-study sample is empty because the Episode Ledger
*is* that sample (`BLUEPRINT_REVIEW.md` §1) and M1 closed with 0 admissible
rows.

Honesty: UNKNOWN is not zero. Missing I2 is not proof of no physical
disruption. S4 proximity is driver identity only absent I2.

## Review

Empty deterministic closeout is **not B-RED**. B-RED only if `panel.py`, as-of
joins, `release_ts` alignment, or core leakage tests change.

Machine-readable twin: `empty_sample_closeout.yaml`.

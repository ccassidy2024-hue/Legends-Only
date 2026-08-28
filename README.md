# Legends-Only

Mechanism-aware quantitative discovery for the **U.S. grain logistics system**.

Goal: identify delayed physical and behavioral cascades, validate whether the
strongest mechanisms are real, and determine whether any produce a falsifiable
trade thesis. A **written negative result is a valid final outcome**.

This is **not** a generic machine-learning prediction project.

```text
physical/logistics shock
→ operational response
→ participant adaptation
→ downstream inventory/flow effect
→ market effect
→ possible delayed market underreaction
→ falsifiable trade thesis
```

Always separate: **what the data show** | **why we think it happens** |
**what we expect next** | **how it could potentially be traded**.

## Document hierarchy (source of truth)

| Priority | Document | Governs |
|----------|----------|---------|
| 1 | `PROJECT_BLUEPRINT.md` | Original vision and research objective |
| 2 | `BLUEPRINT_REVIEW.md` | Methodological amendments; **takes precedence** on methodology and milestone order where it conflicts with the original blueprint |
| 3 | `WORKFLOW.md` | Operating agreement, repo conventions, collaboration, AI usage |
| 4 | `CLAUDE.md` + `.cursor/rules/project.mdc` | Concise persistent implementation rules derived from the above |

Intellectual history is preserved: the blueprint is not rewritten to pretend
the later critique never existed.

## Research milestone order

0. Repository / research setup ← **current foundation complete after reconciliation**
1. Episode Ledger / pre-registration
2. As-of panel + leakage protection (real series)
3. Exploratory screener with honest multiple-testing treatment
4. Direct shock-response modeling / local projections
5. Mechanism research + literature review
6. Stronger causal/dynamic identification where justified
7. Historical replay
8. Trade thesis **or** written negative result

Do **not** reintroduce a NetworkX cascade graph as an early milestone.
Do **not** build ABM / system-dynamics / optimizer / trading UI / deep learning
merely because they sound sophisticated.

## Canonical interfaces

```python
# observations
["series_id", "period_end", "release_ts", "value"]

# panel
from grainsys.panel import build_asof_panel
panel = build_asof_panel(obs, anchors)  # .values, .age_days
```

Lag convention (defined once): **`lag = +k` means X at t predicts Y at t+k**
(X leads Y).

## Setup

Python 3.11+. Canonical clone path: `C:\dev\Legends-Only` (not OneDrive).

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
make test          # or: pytest -q
make all           # lint + tests (no proprietary data required)
```

## Ownership

- Person A (data/plumbing): `TASKS_A.md`
- Person B (statistics/models): `TASKS_B.md`

## Critical rules (short)

- No look-ahead: `release_ts` gates as-of membership
- Screener is exploratory; naive best-lag p-values are not ordinary significance
- Episode identification before market-outcome mining whenever practical
- Accounting identities are not discoveries
- Do not invent source IDs or release delays
- No memo number unless regenerable via `make all` from a clean clone
- Synthetic tests protect panel/timing/lag logic — never weaken them

## Status

Research foundation is tested (synthetic panel, leakage, lag recovery).
**Milestone 1 closed as a negative result:** 4234 frozen D5 candidates
mechanically triaged, 4234 no-episode dispositions, 0 I1/I2/I3 survivors,
0 admissible Episode Ledger rows. Fictional example `EP-0000-000` remains
excluded. UNKNOWN is not zero. S4 proximity is driver-only absent I2.
No freeze tag; market data remains closed.
**Next:** Milestone 2 as-of panel — real-series panel is not-estimable
without catalogued series and genuine `release_ts` (do not invent observations).

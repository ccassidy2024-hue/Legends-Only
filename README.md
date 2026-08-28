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

0. Repository / research setup ← foundation complete
1. Episode Ledger / pre-registration ← **closed: empty-ledger negative result (0 admissible episodes)**
2. As-of panel + leakage protection ← **closed: `M2_NEGATIVE_RESULT_EMPTY_SAMPLE` (0 real series)**
3. Exploratory screener with honest multiple-testing treatment ← **not estimable (0 ledger windows)**
4. Direct shock-response modeling / local projections ← **not estimable (0 identified shocks)**
5. Mechanism research + literature review ← **empty-sample four-statement memo**
6. Stronger causal/dynamic identification where justified ← **skipped under <6 kill**
7. Historical replay ← **skipped under <6 kill**
8. Trade thesis **or** written negative result ← **closed: unanswerable (Sample P = 0)**

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
**Milestone 1 closed** as a legitimate empty-ledger negative result: frozen
D5=4234 candidates were mechanically triaged (S1=37 R12, S4=4197 R3);
survivors=0; admissible episode rows=0. UNKNOWN is not zero; missing I2 is
not proof of no physical disruption; S4 proximity is driver-only absent I2.
Market outcomes remain unopened. See `research/episodes/EPISODE_LEDGER.md`.
**M2–M5:** `M2_NEGATIVE_RESULT_EMPTY_SAMPLE` (0 catalogued real series; do not
fabricate rows). M3/M4 not-estimable. M3 multiplicity: planned family size = 0
tests performed (never-run, not ran-and-null). M5 memo:
`research/memos/M5_EMPTY_SAMPLE_FOUR_STATEMENTS.md`. Synthetic panel plumbing
is unchanged. **M6/M7 skipped** under the `WORKFLOW.md` <6 kill.
**M8 closed:** written negative result — the question is unanswerable with
this data; Gate F #5 no mispricing. See
`research/milestones/M8_WRITTEN_NEGATIVE_RESULT.md`.

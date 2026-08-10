# Legends-Only

Mechanism-aware quantitative discovery for the **U.S. grain logistics system**.

The goal is to identify delayed physical and behavioral cascades, validate whether the strongest mechanisms are real, and determine whether any produce a falsifiable trade thesis. A **negative result is a valid outcome**.

This is **not** a generic machine-learning prediction project.

## Research chain

```
physical shock
→ operational response
→ participant adaptation
→ downstream inventory / flow effect
→ market effect
→ possible market underreaction
→ trade thesis
```

## Current phase

**Repository scaffold only.**

No real screener, dataset acquisition, fabricated series, agent-based models, system-dynamics models, optimization engines, trading execution systems, fancy UI, or deep-learning models yet.

Next research artifact (when authorized): an **Episode Ledger** of independently identified physical/logistics stress episodes, identified without looking at subsequent market outcomes whenever practical.

## Repository layout

| Path | Role |
|------|------|
| `catalog/series/` | One YAML metadata file per series |
| `config/` | Project settings |
| `data/raw/` | Immutable raw archives (never overwrite) |
| `data/interim/` | Intermediate transforms |
| `data/processed/` | Analysis-ready panels |
| `research/episodes/` | Episode Ledger and related notes |
| `src/grainsys/` | Python package (ingest, transforms, screening, modeling, utils) |
| `tests/fixtures/` | Synthetic fixtures with known ground truth |
| `outputs/` | Generated tables, charts, reports (gitignored contents) |
| `docs/` | Project documentation |

## Python environment

- Python **3.11+**
- src-layout package `grainsys`
- pytest

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Unix:
# source .venv/bin/activate

pip install -e ".[dev]"
pytest
```

## Critical research rules (summary)

1. Naive pairwise lag scans are **not** statistical evidence (autocorrelation + multiple testing → false discovery).
2. Episode identification should be **blind to market outcomes** when practical.
3. Pairwise screening is **exploratory / hypothesis-generating only**.
4. Explicitly flag **accounting / near-accounting** relationships; they are not independent discoveries.
5. Prefer **residuals, persistence/duration, and deviations** from expected relationships when justified.
6. Include **substitution channels** (Gulf vs PNW/rail; U.S. vs Brazil origin) in the system view.
7. Prefer **Jordà local projections** (or similar direct shock-response methods) for serious dynamics.
8. Every time-dependent series must record **publication / information availability** timing — no look-ahead.
9. Panel construction, as-of joins, lag direction, and release timing require **synthetic tests with known ground truth**.
10. Always separate: **what data show** / **why we think it happens** / **what we expect next** / **how it could be traded**.

See `PROJECT_BLUEPRINT.md`, `CLAUDE.md`, and `.cursor/rules/project.mdc` for the full persistent rules.

## Status

Scaffold created. Do not proceed beyond setup until explicitly authorized.

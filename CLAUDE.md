# CLAUDE.md — Legends-Only / grainsys

Persistent instructions for AI assistants working in this repository.

## Project

**Legends-Only**: mechanism-aware quantitative discovery for U.S. grain logistics. Goal: identify delayed physical/behavioral cascades, validate real mechanisms, and assess falsifiable trade theses. Negative results are valid.

**Not** a generic ML prediction project.

Research chain:

`physical shock → operational response → participant adaptation → inventory/flow → market effect → possible underreaction → trade thesis`

## Current phase

Repository scaffold only. Do **not** build the real screener, hunt datasets, fabricate data, ABMs, system-dynamics models, optimizers, trading systems, fancy UI, or deep learning unless the user explicitly authorizes that phase.

## Hard research rules

1. **Pairwise lag scans ≠ evidence.** Autocorrelated weekly series + many lags = severe false discovery.
2. **Episode Ledger first.** Identify physical/logistics stress episodes without looking at subsequent market outcomes whenever practical.
3. **Screening is exploratory only** (hypothesis-generating).
4. **Flag accounting / near-accounting identities**; do not treat them as discoveries (e.g., basis ≈ transport cost).
5. Prefer **residuals, persistence/duration, deviations** from expected relationships when justified.
6. Include **substitution channels**: Gulf vs PNW/rail; U.S. vs Brazil origin.
7. For dynamics, prefer **Jordà local projections** (direct shock-response), not chained pairwise correlations.
8. Record **publication / information availability** for every time-dependent series. **No look-ahead.** Do not invent source IDs or release delays.
9. Panel construction, as-of joins, lag direction, release timing → **synthetic tests with known ground truth**.
10. Always separate: **what data show** | **why we think it happens** | **what we expect next** | **how it could be traded**.

## Data rules

- `data/raw/` is **immutable** — never overwrite raw files.
- One YAML per series under `catalog/series/`.
- Large/raw data, outputs, notebooks, secrets, and env files are gitignored.
- Do not invent metadata values.

## Code layout

- Package: `src/grainsys/` (`ingest`, `transforms`, `screening`, `modeling`, `utils`)
- Tests: `tests/` with fixtures in `tests/fixtures/`
- Config: `config/settings.yaml`
- Episodes: `research/episodes/EPISODE_LEDGER.md`
- Blueprint: `PROJECT_BLUEPRINT.md`

## Python

- Python ≥ 3.11, src layout, pytest
- Keep dependencies minimal (pandas, numpy, scipy, statsmodels, pyyaml, matplotlib, pytest)

## Statement discipline

Never conflate empirical description, causal interpretation, forward expectation, and tradeability in the same claim without labeling which is which.

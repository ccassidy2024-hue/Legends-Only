# Legends-Only — Project Blueprint

## Objective

Build a mechanism-aware quantitative discovery engine for the U.S. grain logistics system. Identify delayed physical and behavioral cascades, validate whether the strongest mechanisms are real, and determine whether any produce a falsifiable trade thesis.

A negative result is a valid scientific outcome.

## What this project is not (yet)

Do **not** build until explicitly authorized:

- Agent-based models
- System dynamics models
- Optimization systems
- Trading / execution systems
- Fancy UI
- Deep-learning models
- A production pairwise “screener” treated as evidence
- Fabricated or speculative real datasets

## Causal research chain

```
physical shock
→ operational response
→ participant adaptation
→ downstream inventory / flow effect
→ market effect
→ possible market underreaction
→ trade thesis
```

## Research principles (mandatory)

### 1. Pairwise lag scans are not evidence

Highly autocorrelated weekly series combined with searching many lags produce severe false-discovery problems. Do not treat naive pairwise lag scans as statistical evidence.

### 2. Episode Ledger first

The first research artifact is an **Episode Ledger** of independently identified physical/logistics stress episodes. Episodes must be identified **without looking at the subsequent market outcome** whenever practical. Market outcomes remain blank during initial identification.

### 3. Screening is exploratory only

Pairwise screening is hypothesis-generating only. It does not validate mechanisms or trade theses.

### 4. Accounting identities

Explicitly identify accounting or near-accounting relationships. Do **not** treat identities such as geographic cash-price differences mechanically reflecting transportation costs as independent discoveries.

### 5. Prefer economically justified transforms

Prefer residuals, persistence/duration, and deviations from expected relationships when economically justified.

### 6. Substitution channels

The system view must eventually include substitution channels such as:

- Gulf vs PNW / rail routing
- U.S. vs Brazil origin substitution

### 7. Direct shock-response methods

For serious dynamic analysis, prefer methods such as **Jordà local projections** over chaining multiple pairwise correlations.

### 8. Information availability / no look-ahead

Every time-dependent dataset must record publication timing / information availability. No look-ahead leakage is permitted. Do **not** invent source IDs or publication delays.

### 9. Synthetic ground-truth tests

Anything involving panel construction, as-of joins, lag direction, or release timing must have explicit synthetic tests with known ground truth.

### 10. Four-statement separation

Always keep these statements separate:

1. **What the data show**
2. **Why we think it happens**
3. **What we expect next**
4. **How it could be traded**

## Data architecture

### Layers

| Layer | Path | Rule |
|-------|------|------|
| Raw | `data/raw/` | Never overwrite. Append or version new pulls. |
| Interim | `data/interim/` | Cleaning / joins in progress |
| Processed | `data/processed/` | Analysis-ready artifacts |

### Series catalog

Each real series gets its **own YAML** under `catalog/series/` (not one giant catalog file).

Designed fields (populate only when known; do not invent):

- `series_id`
- `name`
- `description`
- `source`
- `source_url` or source identifier
- `frequency`
- `units`
- `geography`
- `transformation`
- `release` / publication timing
- `release_delay_days` (only when actually known)
- `economic_role`
- `notes`
- `verification_status`

### Example skeleton (do not fill with invented values)

```yaml
series_id: null  # assign when series is real
name: null
description: null
source: null
source_url: null
frequency: null
units: null
geography: null
transformation: null
release:
  schedule: null
  information_available_as_of: null
release_delay_days: null  # only if known
economic_role: null
notes: null
verification_status: unverified
```

## Package architecture

```
src/grainsys/
  ingest/       # load raw sources; respect immutability
  transforms/   # residuals, persistence, deviations
  screening/    # exploratory hypothesis generation only
  modeling/     # local projections and related dynamics
  utils/        # paths, as-of helpers, catalog I/O
```

## Test philosophy

Synthetic fixtures under `tests/fixtures/` plant relationships where the correct lag and direction are known.

Eventually protect:

- Lag direction
- No future leakage
- As-of availability
- Transformation reproducibility
- Missing-data handling
- Accounting-identity handling

## Phase gate

**Current phase: repository scaffold.**

Do not proceed beyond setup until the project owner explicitly authorizes the next phase.

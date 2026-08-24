# ADR-0013: D6-CONCRETE-VALUES-v1

- **Date:** 2026-08-23
- **Author:** A | B
- **Status:** accepted / jointly ratified / CLOSED
- **Decision scope:** D6 concrete operational values only
  (`capture.sweeps_subdir`, `capture.rehome_policy`)
- **D6-CONCRETE-VALUES:** CLOSED
- **D6 architecture:** remains governed by ADR-0010 (not reopened)
- **D6 mechanical implementation:** OPEN
- **Gate:** A(data) | B(statistics) — Person B must exact-head review
  persistence fidelity of this ADR
- **Ratification:** Contract **D6-CONCRETE-VALUES-v1** was jointly ratified by
  Human Person A and Human Person B by direct phone agreement on 2026-08-23.
  Human Person A: **AGREE**. Human Person B: **AGREE**. Joint scientific
  closure: **2026-08-23**. No AI review substitutes for either vote. This ADR
  is the operative canonical home of those concrete D6 values.

This ADR is documentation-only persistence of an already jointly ratified
human decision. It does not create the decision. It does **not** reopen
ADR-0010.

It does **not**:

- implement D6 capture/rehome mechanics
- modify `config/` or create `prereg_rules.yaml`
- modify `capture.py`, `candidate_universe.py`, or other runtime code
- choose a content-hash storage surface
- choose a provenance-manifest layout
- authorize an episode-side derived view or materialized copy
- authorize any alternative `rehome_policy` token
- choose a source archive
- choose a source coverage scope
- create a candidate
- create an episode
- choose severity
- choose an H7 survivor
- choose D2 membership
- inspect or choose a market outcome
- create `prereg-rules-v1` or a prereg tag
- bind this ADR into N3 / `LOAD_BEARING_RELATIVE_PATHS`
- authorize discovery or a source sweep

D12 remains deliberately unregistered. This ADR does not claim Lock-1 is
complete. Market data may not be opened on the basis of this persistence.

## Context

ADR-0010 closed **D6-CAPTURE-LIFECYCLE-v1** as architecture and left the
concrete `capture.sweeps_subdir` value and concrete `rehome_policy` token
OPEN. Person A and Person B jointly approved the two concrete values below by
direct phone agreement on 2026-08-23. This ADR persists those values only.

## Decision

Governing contract: **D6-CONCRETE-VALUES-v1**.

### 1. Frozen `capture.sweeps_subdir`

```text
capture.sweeps_subdir = "sweeps"
```

Canonical raw capture path is based on:

```text
$GRAIN_DATA_ROOT/sweeps/<sweep_id>/<candidate_id>/
```

The literal `"sweeps"` is an operational storage value. It is not an episode
rule and not a source-selection rule.

### 2. Frozen `capture.rehome_policy`

```text
capture.rehome_policy = "candidate_keyed_no_move"
```

Meaning for the **first** D6 implementation:

- canonical raw evidence remains candidate-keyed;
- canonical evidence is never physically moved because an episode is formed;
- evidence may support zero, one, or multiple episodes;
- multiple candidate evidence objects may support one or multiple episodes;
- candidates producing no episode retain canonical evidence;
- no episode-side materialized copy is authorized in the first implementation;
- no episode-side reference view is required in the first implementation;
- `$GRAIN_DATA_ROOT/episodes/<episode_id>/` is **not** an authoritative
  raw-evidence location;
- no alternative `rehome_policy` token is authorized by this decision.

### 3. Future derived episode-organized representations

A future reference-only view or hash-verified derived copy may be considered
later. Introducing another `rehome_policy` value requires a later explicit
A+B decision. This ADR does **not** approve any such derived view or alternate
policy.

### 4. Non-decisions retained as open or elsewhere

This decision does **not** choose:

- exact content-hash storage surface
- exact provenance-manifest layout
- episode derived-view implementation
- future alternate rehome policies
- new candidate CSV columns
- timestamps
- reviewer fields
- source-specific values

Those remain implementation questions or later decisions where applicable.

## Human ratification

| Researcher | Vote | Date |
|---|---|---|
| Human Person A | AGREE | 2026-08-23 (direct phone agreement) |
| Human Person B | AGREE | 2026-08-23 (direct phone agreement) |

Joint scientific closure: 2026-08-23.

No AI review substitutes for either vote.

## Immediate consequence

**D6-CONCRETE-VALUES-v1 is scientifically CLOSED.**

D6 architecture remains governed by ADR-0010.

D6 mechanical implementation remains OPEN.

This ADR does **not**:

- authorize discovery
- authorize a source sweep
- create candidates or episodes
- inspect market outcomes
- implement capture/rehome code
- claim Lock-1 is complete

Scientific closure of these two concrete values is not runtime execution.

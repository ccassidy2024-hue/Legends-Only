# ADR-0008: D5 deterministic candidate identity

- **Date:** 2026-08-21
- **Author:** A | B
- **Status:** accepted / jointly ratified
- **Decision scope:** D5-CANDIDATE-IDENTITY-v1 minting/order contract only
- **D5-CANDIDATE-IDENTITY:** CLOSED
- **Live candidate table / minting / sweep:** NOT authorized by this ADR
- **Gate:** A(data) | B(statistics) — Person B must exact-head review
  persistence fidelity of this ADR
- **Ratification:** Contract **D5-CANDIDATE-IDENTITY-v1** was jointly ratified
  by Human Person A and Human Person B. Human Person A recorded **AGREE**
  before Person B's final vote. Human Person B recorded **AGREE** on
  2026-08-21. Joint scientific closure: **2026-08-21**. No AI review
  substitutes for either vote. This ADR is the operative canonical home of
  that identity contract.

This ADR is documentation-only persistence of an already jointly ratified
scientific contract. It specifies the D5 contract; this PR does **not**
create the live candidate table, mint IDs, run a source sweep, generate a
candidate universe, or author episodes.

D5 by itself does **not** activate R-015/H7 candidate-ID tie resolution.
Candidate-to-episode lineage is a separately governed dependency
(ADR-0009).

D12 remains deliberately unregistered. This ADR does not create
`prereg-rules-v1` or claim Lock-1 is complete. Market data may not be opened
on the basis of this persistence.

## Context

Phase 1 requires every hit to receive a `candidate_id` before human
adjudication and before Person A/B parity assignment. Without a frozen
identity rule, enumeration order or later results could determine IDs and
the workload split.

This ADR records the jointly ratified **D5-CANDIDATE-IDENTITY-v1** contract.

## Decision

Governing contract: **D5-CANDIDATE-IDENTITY-v1**.

### 1. Canonical candidate table

Canonical candidate table:

`research/episodes/discovery/candidates/candidates.csv`

This decision specifies the contract; this PR does **not** create that live
table.

### 2. ID prefix

Candidate ID prefix: `CAND`

### 3. Ordering keys

Candidate identity ordering is deterministic using:

`[sweep_id, source_reference]`

### 4. stable_id_key

`stable_id_key` is null for the registered D5 contract unless separately
governed later.

### 5. source_reference

`source_reference` is a deterministic hit-level locator.

It does not have to be a URL, but it must identify the source hit
deterministically within the registered sweep/source contract.

### 6. Identity collisions fail closed

If two different candidate records collide on the same registered identity
tuple, fail closed.

There is no positional tie-break and no discovery-order fallback.

### 7. Mint timing

Candidate IDs are minted once from the COMPLETE FROZEN Phase-1 hit set for
that candidate-universe version.

Minting occurs before:

- candidate-level human adjudication
- reviewer parity assignment
- episode authoring
- H7 candidate-ID tie resolution

### 8. Enumeration-order invariance

An identical frozen hit set must produce identical IDs independent of
enumeration order.

### 9. Changed universe is a new version

A changed candidate universe is a new/versioned candidate universe and is
deterministically reminted.

Do not patch or manually preserve old candidate numbering inside a changed
universe merely for convenience.

### 10. Reviewer parity

Reviewer assignment derives mechanically from final deterministic candidate
sequence:

- odd sequence number → Person A
- even sequence number → Person B

Reviewer balance may never alter candidate ordering or candidate IDs.

### 11. Prohibited selectors

Candidate IDs may not be ordered, selected, or renumbered using:

- severity
- perceived importance
- remembered events
- market outcomes
- statistical results
- power
- H7 survival
- episode desirability
- researcher convenience

### 12. R-015 / H7 not activated by D5 alone

D5 by itself does NOT activate R-015/H7 candidate tie resolution because
candidate-to-episode lineage is a separately governed dependency.

## Human ratification

| Researcher | Vote | Date |
|---|---|---|
| Human Person A | AGREE | recorded before Person B's final vote |
| Human Person B | AGREE | 2026-08-21 |

Joint scientific closure: 2026-08-21.

No AI review substitutes for either vote.

## Immediate consequence

**D5-CANDIDATE-IDENTITY-v1 is scientifically CLOSED.**

This ADR does **not**:

- create a live candidate table
- mint candidate IDs
- run a source sweep
- generate a candidate universe
- author episodes
- activate R-015/H7 candidate-ID tie resolution
- claim Lock-1 is complete
- authorize opening market data

Scientific closure is not runtime execution. Live minting remains unauthorized
until remaining Phase-0 / N3 prerequisites close under separately governed
review.

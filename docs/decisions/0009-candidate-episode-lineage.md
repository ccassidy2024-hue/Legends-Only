# ADR-0009: Candidate-to-episode lineage

- **Date:** 2026-08-21
- **Author:** A | B
- **Status:** accepted / jointly ratified
- **Decision scope:** CANDIDATE-EPISODE-LINEAGE-v1 scientific join only
- **CANDIDATE-EPISODE-LINEAGE:** CLOSED
- **Schema / validator / disposition ledger implementation:** NOT performed
  by this ADR
- **Gate:** A(data) | B(statistics) — Person B must exact-head review
  persistence fidelity of this ADR
- **Ratification:** Contract **CANDIDATE-EPISODE-LINEAGE-v1** was jointly
  ratified by Human Person A and Human Person B. Human Person A recorded
  **AGREE** before Person B's final vote. Human Person B recorded **AGREE**
  on 2026-08-21. Joint scientific closure: **2026-08-21**. No AI review
  substitutes for either vote. This ADR is the operative canonical home of
  that lineage contract.

This ADR is documentation-only persistence of an already jointly ratified
scientific contract. It does not create candidate rows, episode YAML, or a
disposition ledger, and it does not modify schema or validator code.

D12 remains deliberately unregistered. This ADR does not create
`prereg-rules-v1` or claim Lock-1 is complete. Market data may not be opened
on the basis of this persistence. Implementation does not already enforce
lineage.

## Context

R-015 allows exact-`public_anchor` H7 ties to use `candidate_id` only after
deterministic D5 minting **and** deterministic candidate-to-episode lineage.
Candidates and episodes are distinct objects. The protocol's H-rules can
combine many hits into one episode, and can produce multiple episode rows
from shared ancestry. A singular exclusive `candidate_id` would lose
history.

This ADR records the jointly ratified **CANDIDATE-EPISODE-LINEAGE-v1**
contract. D5 identity is ADR-0008. D6 capture lifecycle is ADR-0010.

## Decision

Governing contract: **CANDIDATE-EPISODE-LINEAGE-v1**.

### 1. Distinct objects

Candidate records and episode records are distinct scientific objects.

### 2. Hits remain candidates

Raw discovery hits remain candidate records.

### 3. One YAML per episode

Episode authoring uses one YAML record per episode.

### 4. Nonempty ancestry

Every authored episode must carry a nonempty `candidate_ids` ancestry
collection.

### 5. Unique, D5-ordered storage

`candidate_ids` must be unique and stored in frozen D5 candidate order.

### 6. Non-exclusive ancestry

Candidate ancestry is non-exclusive.

Allowed mappings include:

- many candidates → one episode
- one candidate → multiple episodes
- many candidates → multiple episodes

No one-to-one ownership assumption is permitted.

### 7. H1/H2/H3/H8 union

When H1/H2/H3/H8 causes records/hits to be combined into one episode, the
resulting episode ancestry is the union of every contributing candidate ID,
normalized in frozen D5 order.

### 8. H4/H5 shared ancestry

H4/H5 may legitimately produce multiple episode records sharing candidate
ancestry when the episode rules independently justify those records.

### 9. No-episode disposition

A candidate that produces no episode must not silently disappear.

It must receive a candidate-keyed no-episode disposition in the separately
implemented disposition ledger.

### 10. Reverse mapping is derived

Reverse candidate→episode mapping is DERIVED from episode ancestry /
dispositions.

The frozen candidate table is not mutated to add a single `episode_id`
ownership field.

### 11. R-015 tie key

For R-015 exact-public-anchor tie resolution, the episode's deterministic
candidate tie key is:

`min(candidate_ids)`

under the frozen D5 candidate order.

### 12. Shared-minimum fail closed

If exact-anchor H7 competitors share the same derived minimum candidate ID,
fail closed pending a separately ratified deterministic rule.

Do not invent a fallback.

### 13. Rejected / non-primary retention

Rejected, subsumed, or otherwise non-primary episode YAML retains its actual
candidate ancestry rather than losing provenance.

### 14. Universe version

Lineage is scoped to the applicable frozen candidate-universe version.

### 15. D6 compatibility

D6 and all capture mechanics must preserve this many-to-many model and may
not assume that one candidate capture has exactly one episode destination.

## Human ratification

| Researcher | Vote | Date |
|---|---|---|
| Human Person A | AGREE | recorded before Person B's final vote |
| Human Person B | AGREE | 2026-08-21 |

Joint scientific closure: 2026-08-21.

No AI review substitutes for either vote.

## Immediate consequence

**CANDIDATE-EPISODE-LINEAGE-v1 is scientifically CLOSED.**

This ADR does **not**:

- create candidate rows
- create episode YAML
- populate a disposition ledger
- modify schema or validator code
- claim implementation already enforces lineage
- claim Lock-1 is complete
- authorize opening market data
- authorize a source sweep

Scientific closure is not runtime execution. Mechanical `candidate_ids`
fields, disposition-ledger files, and validator checks remain later,
separately governed implementation.

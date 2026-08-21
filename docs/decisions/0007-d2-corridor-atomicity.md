# ADR-0007: D2 corridor atomicity

- **Date:** 2026-08-21
- **Author:** A | B
- **Status:** accepted / jointly ratified
- **Decision scope:** D2-ATOMICITY-v1 common atomicity rule only
- **D2-ATOMICITY:** CLOSED
- **Mode-specific topology profiles:** OPEN unless separately ratified
- **D2-MEMBERSHIP:** OPEN
- **Gate:** A(data) | B(statistics) — Person B must exact-head review
  persistence fidelity of this ADR
- **Ratification:** Contract **D2-ATOMICITY-v1** was jointly ratified by
  Human Person A and Human Person B. Human Person A recorded **AGREE** before
  Person B's final vote. Human Person B recorded **AGREE** on 2026-08-21.
  Joint scientific closure: **2026-08-21**. No AI review substitutes for
  either vote. This ADR is the operative canonical home of that atomicity
  contract.

This ADR is documentation-only persistence of an already jointly ratified
scientific contract. It does not create the decision, execute D2 membership,
populate a registry or crosswalk, freeze a mode topology profile, choose
reference interval R, or authorize candidate discovery.

It does not amend ADR-0006. It complements ADR-0006's requirement that the
atomicity principle be frozen before registry population.

D12 remains deliberately unregistered. This ADR does not create
`prereg-rules-v1`, a live prereg file, or Lock-1 completion.

## Context

ADR-0006 closed the D2 *construction* rule and left the atomicity principle
to be written and frozen before registry population. Without a common
atomicity rule, later topology profiles and registry rows could split or
merge corridors after seeing membership, events, or results.

This ADR records the jointly ratified **D2-ATOMICITY-v1** common rule. Mode-
specific topology profiles remain separately governed and are not frozen
here.

## Decision

Governing contract: **D2-ATOMICITY-v1**.

### 1. Common graph-topological identity

Atomic corridor identity uses a common graph-topological rule.

### 2. Mode activation

The rule is INACTIVE for a transportation mode until A+B have jointly frozen
that mode's topology profile.

### 3. Structural graph only

The graph is constructed only from pre-membership structural transport
capability. It may not be constructed or adjusted based on event occurrence,
candidate counts, episode counts, H7 behavior, statistical power, market
outcomes, or later results.

### 4. Linear-network atom

For a linear network, one atomic corridor is the maximal connected edge-chain
whose internal vertices all have graph degree exactly 2 under the frozen
topology profile.

### 5. Degree-1 endpoint

A degree-1 vertex is an endpoint boundary.

### 6. Degree ≥3 junction

A degree >=3 vertex is a junction boundary.

### 7. Pure degree-2 cycle

A connected pure degree-2 cycle is one atomic corridor under the common rule.

### 8. No post-hoc merge-back

No post-hoc merge-back is allowed.

### 9. No materiality or yield splits

No length, tonnage, materiality, event-frequency, expected-yield,
statistical-power, or subjective-importance threshold may split or merge
corridors.

### 10. Mode transition

A mode transition is a corridor boundary.

### 11. Direction

Direction alone is not a corridor boundary.

### 12. Terminals

A terminal alone is not automatically a corridor boundary.

### 13. Source-native geographies

Source-native waterways, ports, districts, locks, reporting regions, and
other source geographies may map onto project corridors but may never
themselves define, split, or merge project corridors merely because the
source reports that way.

### 14. Unfrozen mode profile

An unfrozen mode topology profile is:

INACTIVE / NOT YET EXECUTABLE.

It is not D2 UNKNOWN.

### 15. Unresolved identity after freeze

Once a mode topology profile is frozen, an unresolved load-bearing fact
needed to establish corridor identity is:

ATOMICITY_UNRESOLVED.

That state blocks final registry/crosswalk freeze and D2 membership for that
mode.

### 16. D2 UNKNOWN timing

D2 UNKNOWN is only meaningful after stable corridor identity exists.

### 17. No residual discretionary grounds

Unenumerated discretionary grounds for splitting or merging corridors are
inadmissible.

### 18. Mode-specific remainder

Every mode-specific graph abstraction rule beyond the common atomicity rule
must live in the separately frozen topology profile for that mode.

## Human ratification

| Researcher | Vote | Date |
|---|---|---|
| Human Person A | AGREE | recorded before Person B's final vote |
| Human Person B | AGREE | 2026-08-21 |

Joint scientific closure: 2026-08-21.

No AI review substitutes for either vote.

## Immediate consequence

**D2-ATOMICITY is scientifically CLOSED.**

Mode-specific topology profiles remain **OPEN** unless separately ratified.

This ADR does **not**:

- create corridor registry rows
- create crosswalk rows
- execute D2 membership
- choose reference interval R
- freeze any mode topology profile
- authorize a source sweep
- claim D2-MEMBERSHIP is closed
- claim Lock-1 is complete

Scientific closure is not runtime execution. Registry population, constructor
execution, and membership remain unauthorized until their separately governed
prerequisites close.

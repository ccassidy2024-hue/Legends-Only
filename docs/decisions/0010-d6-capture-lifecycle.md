# ADR-0010: D6 candidate capture lifecycle

- **Date:** 2026-08-21
- **Author:** A | B
- **Status:** accepted / jointly ratified
- **Decision scope:** D6-CAPTURE-LIFECYCLE-v1 architecture only
- **D6-CAPTURE-LIFECYCLE:** CLOSED as architecture
- **Concrete `capture.sweeps_subdir` / `rehome_policy` token / derived
  materialization mechanism:** OPEN
- **Gate:** A(data) | B(statistics) — Person B must exact-head review
  persistence fidelity of this ADR
- **Ratification:** Contract **D6-CAPTURE-LIFECYCLE-v1** was jointly ratified
  by Human Person A and Human Person B on 2026-08-21. Human Person A:
  **AGREE**. Human Person B: **AGREE**. Joint scientific closure:
  **2026-08-21**. No AI review substitutes for either vote. This ADR is the
  operative canonical home of that capture-lifecycle contract.

This ADR is documentation-only persistence of an already jointly ratified
scientific contract. It does not run a sweep, create a candidate or episode,
populate D2, inspect market outcomes, choose remaining D6 path/token values,
or implement capture/rehome mechanics.

A prior D6 read-only audit found **no implemented runtime physical rehome**.
The architecture defect was singular/exclusive **move wording**, not an
already-active move feature. This PR does not turn that finding into new
implementation.

D12 remains deliberately unregistered. This ADR does not create
`prereg-rules-v1` or claim Lock-1 is complete. Market data may not be opened
on the basis of this persistence.

## Context

Phase 1 hits need a capture home before any `episode_id` exists. Prior D6
placeholder wording described physically moving a hit under one episode
directory. That exclusive-ownership model is incompatible with
CANDIDATE-EPISODE-LINEAGE-v1 (ADR-0009): one candidate may map to zero, one,
or many episodes, and many candidates may map to one episode.

This ADR records the jointly ratified **D6-CAPTURE-LIFECYCLE-v1** contract.
It retains the existing conceptual candidate-keyed capture architecture and
forbids physical MOVE of canonical evidence as the D6 lifecycle.

## Decision

Governing contract: **D6-CAPTURE-LIFECYCLE-v1**.

### 1. Canonical raw home

Phase-1 raw evidence is canonically associated with the applicable frozen
candidate-universe version, `sweep_id`, and `candidate_id`.

The existing conceptual candidate-keyed capture architecture is retained.

This decision does NOT choose the concrete `capture.sweeps_subdir` value.

### 2. Immutability

Once a captured evidence object has been recorded with provenance and
content hash, its bytes may not be silently overwritten, replaced, deleted,
or rewritten in place.

A correction/replacement creates separately identifiable/versioned evidence
with preserved provenance.

### 3. Rehome is logical, not physical MOVE

D6 does not physically MOVE canonical candidate evidence out of its
candidate-keyed home when an episode is authored.

Prior wording that implies a hit must physically move under one episode ID
is superseded for D6 lifecycle purposes.

### 4. No exclusive episode ownership

A candidate capture may support:

- zero episodes
- one episode
- multiple episodes

Multiple candidates may support one episode.

Many-to-many relationships are permitted.

Evidence storage may not impose one-candidate → one-episode ownership.

### 5. Episode records reference canonical evidence

Episode-side evidence fields must deterministically identify the canonical
captured evidence and its content/provenance identity.

Scientific ancestry follows the separately ratified
CANDIDATE-EPISODE-LINEAGE-v1 contract.

D6 itself does not invent scientific lineage.

### 6. Derived materialization is non-authoritative

An implementation may optionally create an episode-organized copy/view only
if:

- it is explicitly derivative
- it is not an independently mutable second raw truth
- its content identity is verified against canonical candidate evidence

This ballot does not choose hardlink/copy/manifest/path-string
implementation.

### 7. No-episode retention

If a candidate generates no episode, its canonical evidence remains retained
and auditable.

No episode directory is required merely to preserve evidence.

### 8. Hash and provenance are load-bearing

Canonical captured evidence must carry sufficient typed provenance and
content-hash identity to establish which exact retrieved evidence later
episode records refer to.

Existing protocol/schema/runtime requirements must be made mechanically
consistent with this rule before live discovery.

This persistence PR does not perform that implementation.

### 9. Episode-directory wording

Any existing:

`$GRAIN_DATA_ROOT/episodes/<episode_id>/`

concept may at most be a derived episode-organized representation under this
lifecycle.

It is not the unique authoritative raw home and may not require
destruction/removal of candidate-keyed canonical evidence.

### 10. Candidate-universe version discipline

Capture identity is interpreted relative to the candidate-universe version
that minted the candidate ID.

Reminting/correction under a new governed candidate universe does not
silently rename or retarget historical captured evidence.

### 11. Post-freeze corrections

After candidate/ledger freeze, capture, lineage, hash, or provenance
corrections follow governed versioning.

They may not silently rewrite the frozen historical analysis artifact.

### 12. Prohibited selectors

Capture location, retention, referencing, materialization, or rehome
treatment may not depend on:

- market outcomes
- statistical results
- severity
- H7 desirability
- candidate counts
- episode counts
- document counts
- sample-size/power needs
- remembered-event importance
- implementation convenience

### 13. Activation dependencies

This lifecycle architecture may exist before implementation, but mechanics
that depend on deterministic candidate IDs or plural lineage remain
operationally dependent on the separately ratified D5 and lineage contracts.

### 14. Remaining D6 values still open

This decision does NOT choose:

- concrete `capture.sweeps_subdir` string
- serialized `rehome_policy` token/value
- optional derived-materialization mechanism

Those remaining concrete values/mechanics must later conform to this
contract and be frozen under normal preregistration/review governance before
discovery.

### 15. No discovery authorization

This contract does not:

- run a sweep
- create a candidate
- create an episode
- inspect a real event for selection
- populate D2
- inspect market outcomes
- choose other open D1–D11/D13 values
- register D12

## Human ratification

| Researcher | Vote | Date |
|---|---|---|
| Human Person A | AGREE | 2026-08-21 |
| Human Person B | AGREE | 2026-08-21 |

Joint scientific closure: 2026-08-21.

No AI review substitutes for either vote.

## Immediate consequence

**D6-CAPTURE-LIFECYCLE-v1 is scientifically CLOSED as architecture.**

Concrete `capture.sweeps_subdir`, serialized `rehome_policy` token, and
optional derived-materialization mechanism remain **OPEN**.

This ADR does **not**:

- implement capture or rehome
- choose D6 path/token values
- run a source sweep
- create candidates or episodes
- populate D2
- claim implementation already enforces lineage or capture
- claim Lock-1 is complete
- authorize opening market data

Scientific closure is not runtime execution. Live discovery remains
unauthorized.

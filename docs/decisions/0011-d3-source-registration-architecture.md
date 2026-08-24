# ADR-0011: D3 source-registration architecture

- **Date:** 2026-08-23
- **Author:** A | B
- **Status:** accepted / jointly ratified
- **Decision scope:** D3 architecture only
- **D3-ARCHITECTURE:** CLOSED
- **D3 source/archive values:** OPEN
- **Gate:** A(data) | B(statistics) — Person B must exact-head review
  persistence fidelity of this ADR
- **Ratification:** Contract **D3-ARCHITECTURE-v1** was jointly ratified by
  Human Person A and Human Person B by direct phone agreement on 2026-08-23.
  Human Person A: **AGREE**. Human Person B: **AGREE**. Joint scientific
  closure: **2026-08-23**. No AI review substitutes for either vote. This ADR
  is the operative canonical home of that source-registration architecture
  contract.

This ADR is documentation-only persistence of an already jointly ratified
human decision. It does not create the decision.

It does **not**:

- register an endpoint
- register a district
- register an archive URL
- promote any family
- choose D1 dates
- choose D4 keywords
- run a sweep
- create candidates
- create episodes
- inspect market outcomes
- create `prereg-rules-v1`
- create a live `prereg_rules.yaml`
- amend ADR-0005 / R-014 LNM classification
- bind this ADR into N3 / `LOAD_BEARING_RELATIVE_PATHS` (later pre-tag pass)

D12 remains deliberately unregistered. This ADR does not claim Lock-1 is
complete. Market data may not be opened on the basis of this persistence.

## Context

Phase 0 still requires a frozen rule for *how* candidate-generating discovery
archives are registered before any live `source_archives` rows are populated
or any Phase-1 sweep runs. Without that rule, later registration could expand
the search universe after seeing hits, or treat supplementary vehicles as
candidate- or absence-generating families without explicit promotion.

This ADR records the jointly ratified **D3-ARCHITECTURE-v1** contract. It
closes **D3-ARCHITECTURE** only. **Actual source/archive values remain OPEN.**

## Decision

Governing contract: **D3-ARCHITECTURE-v1**.

### 1. Explicit preregistration identity

Every candidate-generating discovery archive must be explicitly
preregistered before sweep execution with sufficient identity to distinguish
its sweep family, publishing authority/scope, publication vehicle, and
endpoint/archive surface.

### 2. Duplicate identities fail closed

Duplicate registered archive identities are forbidden and fail closed.

### 3. Multi-vehicle inclusion frozen before sweep

Where one authority/scope publishes relevant records through multiple
provenance-distinct vehicles, inclusion/exclusion of those vehicles must be
explicitly frozen before any sweep; implementation may not choose among them
after seeing hits.

### 4. Publication levels enter only by explicit registration

Division-, national-, district-, local-, or other publication levels enter
a sweep family only through explicit preregistration; source discovery
during execution may not silently expand the registered universe.

### 5. Supplementary sources

Supplementary sources do not independently mint candidates or generate
absence exposure unless a future A+B preregistration explicitly promotes
them and defines the required scope/endpoints.

### 6. No outcome- or yield-selected registration

Archive registration and promotion decisions may not use candidate counts,
event frequency, remembered disruptions, downstream statistical results,
sample-size/power needs, market outcomes, or expected trading usefulness.

### 7. No values chosen here

This contract chooses no actual district, endpoint, URL, archive date,
keyword, matcher, source clock, or absence-generating family.

### 8. Unresolved completeness stays at evidentiary level

Source families whose historical completeness/retention/revision evidence
is unresolved remain usable only at the evidentiary level their verified
evidence supports; uncertainty may not be converted into swept-zero
exposure.

## Current source status (non-normative preservation; not changed by this ADR)

These ADRs do **not** strengthen current source evidence beyond what is already
established:

- **SWL / MKARNS** retrospective archive: positive-evidence-only under current
  evidence
- **National NTNI** retrospective use: positive-evidence-only until exhaustive
  historical coverage is established
- **USCG LNM:** supplementary only under ADR-0005 / R-014
- **No current family** is absence-generating-ready solely because of this ADR

No source endpoint or coverage interval is invented here.

## Immediate consequence

**D3 architecture is CLOSED.**

Actual `source_archives` rows remain **OPEN** and must later be populated only
from verified evidence before live discovery.

## Human ratification

| Researcher | Vote | Date |
|---|---|---|
| Human Person A | AGREE | 2026-08-23 |
| Human Person B | AGREE | 2026-08-23 |

Joint scientific closure: 2026-08-23.

No AI review substitutes for either vote.

## What this ADR does NOT decide

This ADR chooses **no**:

- D1 dates
- D2 membership
- D3 districts / endpoints / URLs / archive dates
- D4 keywords / matchers
- D5 / D6 / D8–D11 / D13 values
- `absence_generating_families`
- `source_identity_keys`
- release clocks
- promotion of SWL, NTNI, LNM, or any other family into absence-generating
  status

It does not create `prereg-rules-v1`, authorize a sweep, or bind ADR-0011 into
N3 interpretation digests. That binding is a later, separately governed
pre-tag step.

## Consequences

- The D3 registration architecture is now the canonical lookup for how later
  `source_archives` population must be governed. It is not itself that
  population.
- Live Phase-1 sweeps remain unauthorized. Candidate discovery remains
  unauthorized.
- Supplementary / positive-evidence-only classifications for LNM, SWL/MKARNS,
  and national NTNI retrospective use are unchanged by this persistence.

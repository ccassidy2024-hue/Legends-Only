# ADR-0012: D7 coverage architecture

- **Date:** 2026-08-23
- **Author:** A | B
- **Status:** accepted / jointly ratified
- **Decision scope:** D7 architecture only
- **D7-ARCHITECTURE:** CLOSED
- **D7 coverage/source-specific values:** OPEN
- **Gate:** A(data) | B(statistics) — Person B must exact-head review
  persistence fidelity of this ADR
- **Ratification:** Contract **D7-ARCHITECTURE-v1** was jointly ratified by
  Human Person A and Human Person B by direct phone agreement on 2026-08-23.
  Human Person A: **AGREE**. Human Person B: **AGREE**. Joint scientific
  closure: **2026-08-23**. No AI review substitutes for either vote. This ADR
  is the operative canonical home of that coverage architecture contract.

This ADR is documentation-only persistence of an already jointly ratified
human decision. It does not create the decision.

**ADR-0005 P5 / R-013 remains controlling** for coverage zero-semantics.
This ADR does not reopen, weaken, or replace that package.

It does **not**:

- choose `source_identity_keys` values
- choose `absence_generating_families` values
- invent archive-specific scope intervals
- invent explicit gap intervals
- invent endpoint-specific coverage facts
- promote any current source family
- register an endpoint or district
- choose D1 dates
- choose D4 keywords
- run a sweep
- create candidates
- create episodes
- inspect market outcomes
- create `prereg-rules-v1`
- create a live `prereg_rules.yaml`
- bind this ADR into N3 / `LOAD_BEARING_RELATIVE_PATHS` (later pre-tag pass)

D12 remains deliberately unregistered. This ADR does not claim Lock-1 is
complete. Market data may not be opened on the basis of this persistence.

## Context

ADR-0005 P5 / R-013 froze the general meaning of covered exposure and
`records_matched: 0` for absence-generating / exhaustive sweep families.
Phase 0 still requires a frozen D7 *architecture* for how that semantics is
applied at preregistration — without choosing the live identity keys, family
promotions, or archive-specific intervals.

Without that architecture, later coverage classification could invent
swept-zero exposure from incomplete archives, treat archive-history bounds as
sweep scope, or promote families after seeing yield.

This ADR records the jointly ratified **D7-ARCHITECTURE-v1** contract. It
closes **D7-ARCHITECTURE** only. **Coverage/source-specific values remain
OPEN.**

## Decision

Governing contract: **D7-ARCHITECTURE-v1**.

### 1. Covered exposure

For absence-generating/exhaustive sweep families, covered exposure is the
union of actually enumerated scopes minus affirmatively known gap intervals.

### 2. Known gaps are explicit interval rows

Known gaps must be represented as explicit interval-scoped absent or unknown
coverage rows with both `scope_start` and `scope_end`; prose-only gap disclosure
is insufficient.

### 3. Archive-history bounds ≠ sweep scope

`earliest_available` and `latest_available` describe archive-history
availability only and may not be substituted for actual sweep scope.

### 4. Zero-match admissibility

`records_matched: 0` is admissible only over accessible records actually
enumerated within registered net covered scope and only for a family
separately preregistered as absence-generating/exhaustive. It never proves
no real-world physical event occurred.

### 5. Identity keys jointly frozen later

The exact `source_identity_keys` must be jointly frozen before live coverage
execution. This contract does **NOT** choose their values.

### 6. Absence-generating families jointly frozen later

The exact `absence_generating_families` set must be jointly frozen from
source-specific completeness/retention/migration/revision evidence before
live discovery. This contract does **NOT** promote any current family.

### 7. Completeness is not inferred from weak signals

Archive reachability, oldest-visible record, issue-number continuity,
generic page counts, or agency nonresponse cannot by themselves establish
historical completeness.

### 8. Supplementary / positive-evidence-only families

Supplementary/positive-evidence-only families generate no swept-zero
exposure unless separately promoted through the governed D3/D7 process.

### 9. No yield- or outcome-selected coverage classification

Coverage classification may not be selected or tuned using event yield,
candidate counts, episode counts, statistical power, market outcomes,
remembered disruptions, or expected trading usefulness.

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

**D7 architecture is CLOSED.**

The following remain **OPEN**:

- `source_identity_keys` values
- `absence_generating_families` values
- archive-specific scope intervals
- explicit gap intervals
- endpoint-specific coverage facts

No current source family is promoted by this ADR.

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
- D3 districts / endpoints / URLs
- D4 keywords
- D5 / D6 / D8–D11 / D13 values
- live `source_identity_keys`
- live `absence_generating_families`
- archive-specific scope or gap intervals
- release clocks

It does not reopen ADR-0005 P5 / R-013, create `prereg-rules-v1`, authorize a
sweep, or bind ADR-0012 into N3 interpretation digests. That binding is a
later, separately governed pre-tag step.

## Consequences

- The D7 coverage architecture is now the canonical lookup for how later
  coverage census / exposure classification must be governed. It is not itself
  that census or those live values.
- ADR-0005 P5 / R-013 remains the controlling zero-semantics record.
- Live Phase-1 sweeps remain unauthorized. Candidate discovery remains
  unauthorized.
- Supplementary / positive-evidence-only classifications for LNM, SWL/MKARNS,
  and national NTNI retrospective use are unchanged by this persistence.

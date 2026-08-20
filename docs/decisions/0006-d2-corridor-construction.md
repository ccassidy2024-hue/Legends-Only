# ADR-0006: D2 corridor construction

- **Date:** 2026-08-17
- **Author:** A | B
- **Status:** accepted / jointly ratified construction rule
- **Decision scope:** D2 construction rule only
- **D2-CONSTRUCTION:** CLOSED
- **D2-MEMBERSHIP:** OPEN
- **Gate:** A(data) | B(statistics) — Person B must exact-head review
  persistence fidelity of this ADR
- **Ratification:** Contract **D2-CONSTRUCTION-v2** was jointly ratified by
  Human Person A and Human Person B on 2026-08-17. Human Person A: **AGREE**.
  Human Person B: **AGREE**. No AI review substitutes for either vote. This
  ADR is the operative canonical home of that construction contract.

Acceptance of this ADR does **not** choose reference interval R, D1 dates,
registry contents, corridor IDs, crosswalk contents, final membership, D3/D7
coverage, source sweeps, candidates, episodes, or market outcomes.

This ADR is documentation-only persistence of the construction rule. It does
not execute the constructor, populate a registry or crosswalk, or authorize
candidate discovery.

## Context

Phase 0 still requires a frozen rule for *how* the D2 eligible-corridor
universe is constructed before any membership list is generated. Without that
rule, later registry population, source→corridor mapping, and constructor
execution would be free to redefine the population after seeing outputs.

This ADR records the jointly ratified **D2-CONSTRUCTION-v2** contract. It
closes **D2-CONSTRUCTION** only. **D2-MEMBERSHIP remains OPEN.**

## Decision

Governing contract: **D2-CONSTRUCTION-v2**.

### Interpretive population label

For the current waterborne construction, the resulting eligible population is
“attributably-active waterborne corridors during R.”

This is not a claim to all grain corridors, all U.S. grain infrastructure, or
all possible transportation corridors. The architecture remains open to
analogous non-waterborne construction under clause 11.

### 1. Atomic project corridor

The project corridor unit is one atomic, stable `corridor_id` in a canonical
registry. Source waterways, ports, districts, locks, and other source-native
geographies are inputs; they are not themselves project corridors.

### 2. Registry governance

Before registry population, A+B must write and freeze the principle that
defines an atomic corridor.

The registry and source→corridor crosswalk are load-bearing, A+B-reviewed,
versioned, and hash-bound.

After freeze, no corridor may be silently split, merged, renamed in identity,
or remapped.

Any such change requires a new registry/crosswalk version, a new constructor
execution, and a new review.

### 3. Source→corridor mapping and ambiguous aggregates

Every source geography is mapped through the frozen crosswalk as:

- contained
- spans_multiple
- out_of_scope
- unresolved

Only a source unit unambiguously contained in exactly one atomic corridor may
qualify that corridor.

A multi-corridor or otherwise ambiguous aggregate cannot qualify any individual
corridor and cannot complete the enumeration needed to call any individual
corridor ineligible.

If it is the only evidence bearing on a corridor, that corridor is UNKNOWN.

### 4. Reference interval R

This decision does not select R.

R may be frozen only after the relevant D1 sample boundary is sufficiently
fixed to prove that R is strictly prior to and non-overlapping with the
analysis sample.

A+B must jointly freeze R before candidate discovery and before
`prereg-rules-v1`.

R may be selected using:

- source/artifact availability
- completeness
- a written a-priori representativeness rationale

R may NOT be selected using:

- generated membership count
- identities of included or excluded corridors
- candidate or episode counts
- event frequency
- remembered disruptions
- market outcomes
- statistical results
- statistical power
- expected event yield

After execution, a small or unfavorable universe is a result or feasibility
fact, not grounds to widen R or relax the construction rule.

### 5. Complete required-input contract

Before execution, enumerate and freeze the complete required-input set,
including:

- every required annual artifact
- dictionary and commodity mapping
- geography/topology evidence
- corridor registry and crosswalk
- units
- traffic/direction treatment
- row key
- duplicate and total/subtotal handling
- status-assignment rule

Bind source identifiers, versions, retrieval evidence, and content hashes.

An input may not be declared non-required during execution to turn UNKNOWN
into INELIGIBLE.

### 6. Waterborne physical evidence and commodity vintage gate

Waterborne eligibility uses immutable WCUS annual Cargo artifacts over R.

The registered commodity concept is WCSC master codes:

- 4100
- 4200
- 4300
- 4400
- 4510
- 4520
- 4530
- 22220

These are translated to the representation actually present in each required
Cargo artifact only through source-attested mapping evidence.

Before execution, the mapping evidence for every required year in R must be
verified and hash-bound.

If the relevant mapping is verified invariant over R, bind that verified
mapping/version.

If a historical mapping change or unresolved vintage is found, execution is
BLOCKED until A+B separately ratify one exact vintage-consistent
commodity-mapping rule.

Implementation may not choose among possible vintage algorithms.

### 7. Qualifying physical row

Include all source-defined physical Cargo traffic/direction classes without
favorable directional selection.

Exclude duplicate totals/subtotals under the frozen row-key rule.

A qualifying row must:

- come from a required frozen artifact in R
- use a registered commodity representation
- map unambiguously to one corridor
- be nonduplicate
- contain an observed numeric `ShortTons` value > 0

No positive-activity cutoff beyond >0 is used.

The following may NOT affect membership:

- volume rank
- percentile
- top-N
- materiality
- subjective importance
- familiarity
- expected event yield
- source coverage
- candidate count
- episode count
- market outcome
- statistical result
- statistical convenience

### 8. Existential eligibility / universal ineligibility

ELIGIBLE is existential:
one valid qualifying positive row is sufficient.

Once eligibility is established, a separate missing required artifact does not
retract that positive physical fact.

INELIGIBLE is universal:
every required frozen input bearing on the corridor must be present, readable,
correctly mapped, and completely and unambiguously enumerated, and that complete
enumeration must contain no qualifying positive row.

If eligibility has not been established and any required evidence is:

- missing
- unreadable
- suppressed
- withheld
- redacted
- nonnumeric
- ambiguously mapped
- otherwise unobserved

status is UNKNOWN, never INELIGIBLE.

Such a value is neither a qualifying positive nor proof of zero.

### 9. First-class terminal statuses

The deterministic constructor emits exactly:

- ELIGIBLE
- INELIGIBLE
- UNKNOWN

for every considered registry corridor.

UNKNOWN is a first-class terminal construction output and may never silently
coerce to INELIGIBLE.

This contract does not choose later analysis or reporting treatment for
UNKNOWN corridors.

### 10. D3/D7 coverage separation

D3/D7 source coverage never determines physical membership.

It determines corridor×source×time exposure where search and later zero
interpretation are permitted.

A physically eligible but uncovered corridor remains physically eligible with
uncovered or unknown source exposure.

Coverage is never reduced to a crude corridor-level boolean.

### 11. Non-waterborne corridors

A non-waterborne corridor must pass the same architecture using a separately
registered official mode-specific physical grain-movement source and atomic
geography.

WCUS/WCSC Cargo does not qualify `rail_network` or another non-waterborne mode.

Without the required official source, mapping, and complete-input rule, the
corridor remains UNKNOWN.

### 12. Multi-geography canonicalization

Any later record involving multiple project corridors stores a canonical,
unique, registry-sorted set of atomic `corridor_id`s.

Source-native geography labels do not replace those IDs.

This clause fixes identity/canonicalization only; it does not decide an H7
survivor rule or written-exception standard.

### 13. Post-freeze source revision

A source correction, replacement, dictionary change, boundary change, or
mapping discrepancy discovered after the D2 universe is frozen is logged with
its provenance.

It does not silently rewrite the universe attached to the original
preregistered analysis.

Any re-execution using revised material is a new versioned construction with
new hashes, new review, and a separately governed/preregistered analysis.

Later values never inherit earlier release identity by coincidence.

### 14. Output and bounded final review

Execution produces a deterministic, registry-ordered, versioned, hash-bound
manifest containing:

- ELIGIBLE / INELIGIBLE / UNKNOWN status
- status reason
- frozen input identities
- registry version
- crosswalk version
- commodity mapping version
- row-rule version
- reproducibility evidence

The generated membership list is exactly the registry-ordered set of ELIGIBLE
`corridor_id`s.

Final review may verify only:

- execution correctness
- frozen-input completeness
- provenance/hash identity
- registry correctness
- crosswalk correctness
- commodity mapping correctness
- row-key mapping correctness
- status assignment
- deterministic reproduction

Its only outputs are:

- PASS

or

- FAIL WITH A CITED DEFECT

A failure is corrected by repairing the cited defect under the frozen contract
and re-executing.

Review may NOT manually add, remove, or reclassify a corridor and may NOT use:

- importance
- familiarity
- event yield
- source coverage
- candidate/episode counts
- market outcomes
- statistical convenience

A review that can amend the output is not an execution review.

## Human ratification

| Researcher | Vote | Date |
|---|---|---|
| Human Person A | AGREE | 2026-08-17 |
| Human Person B | AGREE | 2026-08-17 |

No AI review substitutes for either vote.

## Source-fact caveats (non-normative evidence / status)

These uncertainties are execution guards, not reasons to change the ratified
constructor:

- Relevant publication code/name pairs were consistent across audited official
  2000–2022 Cargo artifacts.
- Full historical master→publication crosswalk invariance was **not** proved.
- Confidentiality obligations exist.
- Audited public Cargo fields showed no observed suppression token, but that
  does not prove universal historical absence.
- Final annual revision/correction behavior remains unknown.

## Immediate consequence

**DO NOT execute D2 membership yet.**

Execution still requires separately freezing:

- D1 boundary sufficient to prove R is strictly pre-sample
- R
- atomicity principle
- registry contents
- source→corridor crosswalk
- complete required-artifact set
- R-specific commodity mapping/vintage evidence
- row-key / duplicate handling
- other separately governed prerequisites

**D2-CONSTRUCTION is CLOSED.**
**D2-MEMBERSHIP remains OPEN.**

## Consequences

- The construction rule is now the canonical lookup for how a later D2
  membership execution must be built. It is not itself that execution.
- This ADR chooses no analysis sample, no R, no registry or crosswalk rows, no
  corridor IDs, and no membership statuses.
- D3/D7 coverage remains a separate exposure layer and never determines
  physical membership.
- Clause 12 canonicalizes multi-geography identity only; it does not amend H7.
- This file is not added to `LOAD_BEARING_RELATIVE_PATHS` by this persistence
  PR. Binding the construction rule into preregistration/manifest machinery is
  a later, separately governed step.
- Live Phase-1 sweeps remain unauthorized. Candidate discovery remains
  unauthorized.

# D2 Construction Evidence Pack

**Date:** 2026-08-24
**Status:** Implementation-ready evidence pack
**Prepared by:** Cursor Agent (post-PR#20-merge)

## Current State

| Contract | Status | ADR |
|----------|--------|-----|
| D2-CONSTRUCTION | CLOSED | ADR-0006 |
| D2-ATOMICITY | CLOSED | ADR-0007 |
| D2-MEMBERSHIP | OPEN | - |

## Mechanically Derivable from Closed Contracts

Once the Tier-A scientific values below are fixed, these are mechanically derivable:

1. **Registry structure** - Follows from topology profile + atomicity rule (ADR-0007)
2. **Crosswalk structure** - Follows from registry structure (ADR-0006 clause 3)
3. **Constructor implementation** - Deterministic per D2-CONSTRUCTION-v2 contract:
   - Status assignment: ELIGIBLE / INELIGIBLE / UNKNOWN (clause 9)
   - Existential eligibility (clause 8): one valid qualifying positive row sufficient
   - Universal ineligibility (clause 8): requires complete enumeration with no qualifying row
   - UNKNOWN is first-class terminal (clause 9): never coerce to INELIGIBLE

4. **Commodity mapping verification workflow** - From ADR-0006 clause 6:
   - WCSC master codes: 4100, 4200, 4300, 4400, 4510, 4520, 4530, 22220
   - Mapping evidence must be verified and hash-bound before execution
   - Vintage changes block execution until A+B ratify exact vintage-consistent rule

## Tier-A Scientific Values Still OPEN

These require explicit A+B joint decision before D2 membership execution:

### BALLOT ITEM 1: Reference Interval R Dates
**ADR-0006 clause 4** requires A+B to jointly freeze R before candidate discovery.

R may be selected using:
- Source/artifact availability
- Completeness
- Written a-priori representativeness rationale

R may NOT be selected using:
- Generated membership count, identities, candidate/episode counts
- Event frequency, remembered disruptions
- Market outcomes, statistical results/power/convenience
- Expected event yield

**One-line ballot:** `R_START=____-__-__ R_END=____-__-__`

### BALLOT ITEM 2: D1 Sample Boundary Dates
**ADR-0006 clause 4** requires D1 boundary to prove R is strictly prior to and non-overlapping with analysis sample.

**One-line ballot:** `D1_SAMPLE_START=____-__-__ D1_SAMPLE_END=____-__-__`

### BALLOT ITEM 3: Waterborne Mode Topology Profile Activation
**ADR-0007 clause 2** requires A+B frozen mode-specific topology profile before mode activation.

Common atomicity rule (CLOSED):
- Linear-network atom: maximal connected edge-chain with internal vertices degree=2
- Degree-1 vertex = endpoint boundary
- Degree ≥3 vertex = junction boundary
- Pure degree-2 cycle = one atomic corridor

Mode-specific profile elements requiring A+B freeze:
- Graph abstraction rules beyond common atomicity
- Source-native geography → project corridor mapping rules

**One-line ballot:** `WATERBORNE_TOPOLOGY_PROFILE=[attach reference or state "requires separate ADR"]`

## Execution Prerequisites Checklist

Per ADR-0006 "Immediate consequence":

- [ ] D1 boundary sufficient to prove R is strictly pre-sample
- [ ] Reference interval R frozen (BALLOT ITEM 1+2)
- [ ] Atomicity principle frozen (DONE: ADR-0007)
- [ ] Registry contents frozen
- [ ] Source→corridor crosswalk frozen
- [ ] Complete required-artifact set enumerated
- [ ] R-specific commodity mapping/vintage evidence verified
- [ ] Row-key / duplicate handling rule frozen

## Files This Evidence Pack Does NOT Touch

Per instruction:
- `panel.py` / lag/alignment code
- Screener/modeling modules
- Parked PRs #4/#5/#6
- Real candidates, episodes, or outcomes
- Tests (no weakening)

## Next Actions

1. **If all Tier-A values are fixed by 11:28 ratification:** Proceed to bounded D2 implementation
2. **If any Tier-A value remains open:** Return one-line ballot items for A+B decision

---

**D2_CONSTRUCTION_READY** marker will be set when:
- All three ballot items have explicit A+B recorded values
- Execution prerequisites checklist is complete

# S2-S8 Final Minimal A+B Ballot

**Status:** READY FOR DECISION
**Date:** 2026-08-26
**Context:** M1 execution resumed from `S2_S8_FINAL_MINIMAL_BALLOT_READY`

## Summary

This ballot contains **only genuine science decisions** requiring A+B agreement.
All mechanical implementation is complete or blocked only on these decisions.

---

## BALLOT ITEMS

### Item 1: S2-THRESHOLD-POLICY

**Family:** S2 (USGS/AHPS Navigation Gauges)
**Classification:** Tier A (scientific decision)

**Decision Required:**

Given D8 `binding_operational_restriction_only` mode (no invented thresholds)
and S2 protocol requirement for "programmatic threshold breach detection",
which resolution should be adopted?

| Option | Description | Impact |
|--------|-------------|--------|
| **A** | Use USACE low water reference planes as official benchmarks | Enables programmatic detection with official thresholds |
| **B** | S2 triggers only on documented operational restrictions | S2 becomes corroborating source (not independent trigger) |
| **C** | Reopen D8 via ADR for gauge-specific thresholds | Requires new ADR with preregistered values |

**Implementation ready:** 10 navigation gauges documented with USGS station IDs
(see `S2_NAVIGATION_GAUGES.md`)

**Blocked pending:** This decision

---

### Item 2: S4-PROXIMITY-RADIUS

**Family:** S4 (NHC Storm Archive)
**Classification:** Tier A (scientific decision)

**Decision Required:**

Given the proposed 12-node export universe (TEMCO Kalama removed per
corporate-only evidence audit), which proximity radius should be adopted
for hurricane landfall candidate generation?

| Option | Description | Impact |
|--------|-------------|--------|
| **50nm** | Conservative - direct landfalls only | Fewer candidates |
| **100nm** | Standard - includes near-miss disruptions | More candidates |

**Implementation ready:** 12 export nodes documented with FGIS/official sources
(see `S4_EXPORT_NODES.md`)

**Blocked pending:** This decision

---

## NON-BALLOT ITEMS (Implementation Ready)

The following families have complete source registration and adapters.
They are executable once the S2/S4 ballot items are decided:

| Family | Status | Adapter | Tests |
|--------|--------|---------|-------|
| **S3** USCG MSIB | ✓ REGISTERED | `uscg_msib.py` | 9 pass |
| **S5** AMS GTR | ✓ REGISTERED | `ams_gtr.py` | 7 pass |
| **S6** USACE LPMS | ✓ REGISTERED | `usace_lpms.py` | 8 pass |
| **S7** STB Dockets | ✓ REGISTERED | `stb_dockets.py` | 10 pass |
| **S8** Port Advisory | ✓ REGISTERED | `port_advisory.py` | 9 pass |

**Total tests:** 46 pass (all S3-S8 adapters)

---

## Protocol vs D8 Conflict Proof

**Conflict location:** S2 sweep protocol vs D8 physical threshold mode

**S2 Protocol (EPISODE_PROTOCOL.md §J):**
```
S2 | USGS/AHPS gauges | Programmatic threshold breach detection
```

**D8 Configuration (prereg_rules.yaml):**
```yaml
physical_thresholds:
  mode: binding_operational_restriction_only
  class_thresholds: []
```

**Nature of conflict:**
- S2 requires thresholds for programmatic detection
- D8 prohibits invented thresholds (empty class_thresholds)
- Resolution options documented in S2-THRESHOLD-POLICY ballot item

---

## Evidence Audit Summary

### TEMCO Kalama (REMOVED)

- **Previous status:** Proposed S4 export node
- **Evidence type:** Corporate website only
- **Decision:** REMOVED from S4 node set
- **Rationale:** Corporate-only evidence does not meet Tier 1 requirements
- **Alternative:** Hurricane proximity captured via Port of Longview node

### S4 Radius Choice (PRESERVED)

- **Current human choice:** 100nm vs 50nm
- **Status:** Preserved as the only two options
- **Requires:** A+B ballot decision (Item 2)

---

## Current State

```
CURRENT_MAIN       | 3647265 (feat(governance): persist S2-S8 A+B ratification record)
OPEN_PR            | None yet (branch: cursor/s3-s8-independent-lanes-f4b1)
SCIENCE_GATES      | S2-THRESHOLD-POLICY, S4-PROXIMITY-RADIUS
REVIEW_GATES       | None (all Tier B implementation ready)
NEXT_ACTION        | A+B decide on S2 and S4 ballot items
```

```
D5_COMPLETE_UNIVERSE_READY = FALSE
```

Rationale: S2 and S4 adapters cannot execute until ballot items decided.
S1 complete (37 hits); S3/S5/S6/S7/S8 adapters ready but universe
incomplete without S2/S4.

---

## Markers

```
M1_EXECUTION_RESUMED
S2_S8_FINAL_MINIMAL_BALLOT_READY
S2_PROTOCOL_D8_CONFLICT_DOCUMENTED
S4_TEMCO_KALAMA_REMOVED
S3_S5_S6_S7_S8_ADAPTERS_IMPLEMENTED
ALL_TESTS_PASS
```

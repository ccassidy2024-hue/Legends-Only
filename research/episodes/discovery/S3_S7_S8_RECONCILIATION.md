# S3/S7/S8 Status Reconciliation

**Date:** 2026-08-26  
**Context:** Reconcile claimed "independent lanes complete" status with actual artifacts

## Status Summary

| Family | PR | Branch | Adapter | Tests | Coverage Status |
|--------|-----|--------|---------|-------|-----------------|
| S3 (USCG MSIB) | #35 | cursor/s3-s8-independent-lanes-f4b1 | uscg_msib.py | 9 pass | IMPLEMENTED |
| S5 (AMS GTR) | #36 | cursor/s5-ams-gtr-adapter-7cf5 | ams_gtr.py | 27 pass | IMPLEMENTED |
| S6 (USACE LPMS) | #37 | cursor/s6-usace-lpms-adapter-7cf5 | usace_lpms.py | 35 pass | IMPLEMENTED |
| S7 (STB dockets) | #35 | cursor/s3-s8-independent-lanes-f4b1 | stb_dockets.py | 10 pass | IMPLEMENTED |
| S8 (Port advisory) | #35 | cursor/s3-s8-independent-lanes-f4b1 | port_advisory.py | 9 pass | BLOCKED on S4 |

## S3: USCG MSIB

**Official Source Surface:**
- Authority: U.S. Coast Guard
- Vehicle: Marine Safety Information Bulletins (MSIB)
- Endpoint: USCG NAVCEN archive by district

**Adapter Status:** `src/grainsys/ingest/uscg_msib.py`
- District coverage: Lower Mississippi, Ohio, Columbia-Snake basins
- Sample period: 2010-2024
- Enumeration: By district and year

**Test Status:** 9 tests pass in test_s3_s8_adapters.py
- District coverage verification
- MSIB number parsing
- Basin mapping

**Coverage Limitations:**
- Archive completeness varies by district
- Positive-evidence-only (no absence generation)
- Some districts may have incomplete historical archives

**No PR required:** Adapter is in PR #35

---

## S7: STB Service Dockets

**Official Source Surface:**
- Authority: Surface Transportation Board
- Vehicle: Service docket search + railroad performance filings
- Endpoint: STB docket system

**Adapter Status:** `src/grainsys/ingest/stb_dockets.py`
- Railroad coverage: Class I grain railroads (BNSF, UP, NS, CSX, CN, CP)
- Docket prefixes: Service orders, embargoes, performance
- Sample period: 2010-2024

**Test Status:** 10 tests pass in test_s3_s8_adapters.py
- Railroad registration
- Docket number parsing
- Grain-relevance filtering

**Coverage Limitations:**
- Document formats vary significantly
- Not all dockets are grain-relevant
- Requires case-by-case classification

**No PR required:** Adapter is in PR #35

---

## S8: Port Authority/Terminal Operator Notices

**Official Source Surface:**
- Authority: Various port authorities and terminal operators
- Vehicle: Published advisories where archives exist
- Endpoint: Per-port/terminal official sources

**Adapter Status:** `src/grainsys/ingest/port_advisory.py`
- Port coverage: Must align with S4 node set
- Archive identification: Per-source verification required

**Test Status:** 9 tests pass in test_s3_s8_adapters.py
- Port registration
- S4 node coverage validation
- Archive availability checking

**BLOCKED:** S8 cannot execute until S4 node set is ratified because:
1. `validate_s4_node_coverage()` function requires ratified S4 nodes
2. Archive verification limited to proposed S4 nodes only
3. Per instruction: "S8 then use only the proposed officially supported S4 nodes"

**Coverage Limitations:**
- Most heterogeneous source family
- Archive availability varies by operator
- Positive-evidence-only semantics
- Some ports/terminals have no public archive

**Execution dependency:** S4 ratification → S8 archive verification → S8 execution

---

## PR #35 Status

**Branch:** cursor/s3-s8-independent-lanes-f4b1  
**Head commit:** eba45083ebb1e1f73ce1a06ea76e87d8c21502a3  
**Files changed:** 12  
**Test count:** 46 tests (in test_s3_s8_adapters.py)

**Changed files:**
- config/discovery/prereg_rules.yaml (54 additions)
- research/episodes/discovery/S2_NAVIGATION_GAUGES.md (new)
- research/episodes/discovery/S2_S8_ADAPTER_INVENTORY.md (modified)
- research/episodes/discovery/S2_S8_FINAL_BALLOT.md (new)
- research/episodes/discovery/S4_EXPORT_NODES.md (new)
- src/grainsys/ingest/__init__.py (modified)
- src/grainsys/ingest/ams_gtr.py (new)
- src/grainsys/ingest/port_advisory.py (new)
- src/grainsys/ingest/stb_dockets.py (new)
- src/grainsys/ingest/usace_lpms.py (new)
- src/grainsys/ingest/uscg_msib.py (new)
- tests/test_s3_s8_adapters.py (new)

**CI Status:** Needs verification after config schema fixes in PR #36/#37

---

## Reconciliation

The claim "independent lanes complete" is **partially accurate**:

| Family | Implementation | Execution | Notes |
|--------|---------------|-----------|-------|
| S3 | ✓ COMPLETE | ○ PENDING | Adapter ready, needs D3 registration ratification |
| S5 | ✓ COMPLETE | ○ PENDING | PR #36 - config fix pushed |
| S6 | ✓ COMPLETE | ○ PENDING | PR #37 - config fix pushed |
| S7 | ✓ COMPLETE | ○ PENDING | Adapter ready, docket classification TBD |
| S8 | ✗ BLOCKED | ✗ BLOCKED | Depends on S4 ratification |

**What "complete" means:**
- Adapter code written and tested
- Source registration documented

**What is NOT complete:**
- A+B ratification of scientific parameters
- D3 endpoint registration in prereg_rules.yaml
- Actual sweep execution

## Marker

`S3_S7_S8_RECONCILIATION_COMPLETE`
`S8_BLOCKED_ON_S4_RATIFICATION`

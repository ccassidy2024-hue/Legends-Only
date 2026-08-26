# S2-S8 Source Adapter Inventory

**Status:** PENDING governance classification
**Date:** 2026-08-25
**Context:** Lock-1 post S1 sweep execution

## Overview

This document inventories the canonical adapters and source contracts required for
sweep families S2-S8 per §J Phase 1 table in EPISODE_PROTOCOL.md. Each family
requires a dedicated adapter/parser before sweep execution can proceed.

## S1 Status (Reference)

| Item | Status |
|------|--------|
| Family | S1 - USACE NTNI |
| Adapter | `src/grainsys/ingest/ntni.py` |
| ADR | ADR-0015 (D3/D4 positive-evidence-only S1) |
| Sweep status | EXECUTED - 37 keyword hits, 3 source failures |
| Parser ratified | Yes - N3 manifest includes ntni.py digest |

## S2: USGS/AHPS Gauges

| Item | Value |
|------|-------|
| Authority | U.S. Geological Survey / NOAA NWS |
| Data source | USGS Water Services API, AHPS data |
| Vehicle | Programmatic threshold breach detection over full sample period |
| Adapter needed | Yes - gauge data parser with threshold policy |
| Contract dependencies | D3 endpoint registration, D4 threshold policy |
| Implementation complexity | Moderate - requires defining navigation gauges and thresholds |

### Required components

1. **Endpoint registration**: List of USGS station IDs at navigation-relevant locations
2. **Threshold policy**: Physical thresholds triggering "breach" events
3. **Sample period coverage**: Must cover 2010-01-01 to 2024-12-31
4. **Parser**: API response handling and threshold breach detection

### Governance notes

- Requires A+B decision on which gauges are "navigation gauges"
- Threshold values are scientific decisions (Tier A)
- Parser implementation is Tier B

---

## S3: USCG MSIBs and Closure Notices

| Item | Value |
|------|-------|
| Authority | U.S. Coast Guard |
| Data source | Marine Safety Information Bulletins |
| Vehicle | Enumerate by district and year |
| Adapter needed | Yes - MSIB archive parser |
| Contract dependencies | D3 district/endpoint registration |
| Implementation complexity | Moderate - varies by district archive format |

### Required components

1. **District endpoints**: CG district archive URLs
2. **Date range enumeration**: Year-by-year archive structure
3. **Parser**: MSIB document extraction and normalization
4. **Keyword policy**: Reuse D4 terms or define S3-specific terms

### Governance notes

- Must verify archive completeness vs positive-evidence-only semantics
- No absence evidence generation per current D7 coverage policy

---

## S4: NHC Storm Archive

| Item | Value |
|------|-------|
| Authority | NOAA National Hurricane Center |
| Data source | NHC historical storm database / HURDAT2 |
| Vehicle | Landfalls within pre-registered radius of grain export/transfer nodes |
| Adapter needed | Yes - storm track parser with spatial filtering |
| Contract dependencies | Node list, radius threshold |
| Implementation complexity | Low-moderate - well-documented data format |

### Required components

1. **Node registration**: Grain export/transfer facilities with coordinates
2. **Radius threshold**: Distance defining "proximity" (scientific decision)
3. **Parser**: HURDAT2 or similar storm track data
4. **Landfall detection**: Track interpolation to coast

### Governance notes

- Spatial proximity is a scientific decision (Tier A)
- Node list requires A+B agreement

---

## S5: AMS Grain Transportation Report

| Item | Value |
|------|-------|
| Authority | USDA Agricultural Marketing Service |
| Data source | Weekly Grain Transportation Report archive |
| Vehicle | Weekly issues; keyword scan of transportation-conditions sections |
| Adapter needed | Yes - PDF/document parser for GTR |
| Contract dependencies | Archive URL, section identification |
| Implementation complexity | Moderate-high - PDF extraction complexity |

### Required components

1. **Archive endpoint**: USDA GTR archive location
2. **Section identification**: Which sections contain transportation conditions
3. **Parser**: PDF text extraction (may require OCR for older issues)
4. **Keyword policy**: Apply D4 terms or define S5-specific terms

### Governance notes

- PDF extraction may require specialized libraries
- Historical format changes may complicate parsing

---

## S6: USACE LPMS (Lock Performance Monitoring System)

| Item | Value |
|------|-------|
| Authority | U.S. Army Corps of Engineers |
| Data source | LPMS database / NDC portal |
| Vehicle | Outage/queue records exceeding pre-registered thresholds |
| Adapter needed | Yes - LPMS data parser with threshold policy |
| Contract dependencies | Lock list, threshold policy |
| Implementation complexity | Moderate - depends on data access format |

### Required components

1. **Lock registration**: Which locks are in scope
2. **Threshold policy**: Queue/outage duration thresholds
3. **Data access**: API or bulk download mechanism
4. **Parser**: LPMS record normalization

### Governance notes

- Data access may require authentication
- Threshold values are scientific decisions (Tier A)

---

## S7: STB Service Dockets and Rail Performance

| Item | Value |
|------|-------|
| Authority | Surface Transportation Board |
| Data source | STB docket system, railroad performance filings |
| Vehicle | Enumerate service orders and reported service events |
| Adapter needed | Yes - STB docket/filing parser |
| Contract dependencies | Docket type classification |
| Implementation complexity | High - varied document formats |

### Required components

1. **Docket type registration**: Which docket types are relevant
2. **Railroad coverage**: Which railroads serve grain corridors
3. **Parser**: Docket/filing extraction and classification
4. **Event detection**: Identify service disruption records

### Governance notes

- Document formats vary significantly
- May require case-by-case classification

---

## S8: Port Authority / Terminal Operator Notices

| Item | Value |
|------|-------|
| Authority | Various port authorities and terminal operators |
| Data source | Published advisories where archives exist |
| Vehicle | Enumerate published advisories |
| Adapter needed | Yes - per-port/terminal parsers |
| Contract dependencies | Port/terminal list, archive identification |
| Implementation complexity | High - heterogeneous sources |

### Required components

1. **Source registration**: Which ports/terminals have usable archives
2. **Archive identification**: Verified archive URLs/access methods
3. **Parser(s)**: Per-source adapters (may need multiple)
4. **Normalization**: Common output format across sources

### Governance notes

- Most heterogeneous family - may require multiple adapters
- Archive availability varies by operator
- Positive-evidence-only semantics apply

---

## Implementation Priority

Based on data accessibility and mechanical complexity:

| Priority | Family | Rationale |
|----------|--------|-----------|
| 1 | S4 (NHC) | Well-documented public archive, simple format |
| 2 | S5 (AMS GTR) | Consistent weekly publication, known archive |
| 3 | S2 (USGS) | Public API, requires threshold policy |
| 4 | S6 (LPMS) | Requires data access verification |
| 5 | S3 (USCG) | District-by-district archive structure |
| 6 | S7 (STB) | Complex document parsing |
| 7 | S8 (Ports) | Heterogeneous, requires source identification |

## Execution Status (2026-08-26)

**M1 execution resumed.** Adapter implementation and source registration complete
for S3/S5/S6/S7/S8. S2 and S4 blocked on Tier-A scientific decisions only.

| Family | Status | Adapter | Tests | Blocking Item(s) |
|--------|--------|---------|-------|------------------|
| S2 (USGS) | **BLOCKED** | - | - | Threshold policy decision (Tier A) |
| S3 (USCG) | ✓ **READY** | `uscg_msib.py` | 9 pass | - |
| S4 (NHC) | **BLOCKED** | - | - | Radius threshold decision (Tier A) |
| S5 (AMS GTR) | ✓ **READY** | `ams_gtr.py` | 7 pass | - |
| S6 (LPMS) | ✓ **READY** | `usace_lpms.py` | 8 pass | - |
| S7 (STB) | ✓ **READY** | `stb_dockets.py` | 10 pass | - |
| S8 (Ports) | ✓ **READY** | `port_advisory.py` | 9 pass | - |

**Total adapter tests:** 46 pass (see `tests/test_s3_s8_adapters.py`)

### Remaining Tier-A Decisions (A+B ballot)

1. **S2-THRESHOLD-POLICY:** Protocol-vs-D8 conflict resolution
2. **S4-PROXIMITY-RADIUS:** 50nm vs 100nm hurricane proximity

See `S2_S8_FINAL_BALLOT.md` for complete ballot.

## Implemented Adapters

| Adapter | Source | Key Functions |
|---------|--------|---------------|
| `uscg_msib.py` | USCG NAVCEN | `national_msib_endpoint()`, `parse_navcen_msib_listing()` |
| `ams_gtr.py` | USDA AMS | `gtr_archive_endpoint()`, `parse_gtr_archive_listing()` |
| `usace_lpms.py` | USACE NDC | `lock_queue_endpoint()`, `parse_lock_queue_xml()` |
| `stb_dockets.py` | STB | `docket_search_url()`, `enumerate_service_orders()` |
| `port_advisory.py` | Various | `get_official_archive_ports()`, `validate_s4_node_coverage()` |

## Blocked Items (Tier A only)

S2 and S4 require A+B scientific decisions:

1. **S2-THRESHOLD-POLICY**: Resolve protocol-vs-D8 conflict
2. **S4-PROXIMITY-RADIUS**: Select 50nm or 100nm

All D3 endpoint registration and Tier B implementation is complete for S3/S5/S6/S7/S8.

## Next Steps

1. A+B decide on S2-THRESHOLD-POLICY ballot item
2. A+B decide on S4-PROXIMITY-RADIUS ballot item
3. Upon decision: implement S2 and S4 adapters
4. Execute full S2-S8 sweep universe
5. Update N3 manifest with new parser digests

## Marker

`S2_S8_ADAPTER_INVENTORY_DOCUMENTED`
`S2_S8_FINAL_MINIMAL_BALLOT_READY`
`M1_EXECUTION_RESUMED`
`S3_S5_S6_S7_S8_ADAPTERS_IMPLEMENTED`

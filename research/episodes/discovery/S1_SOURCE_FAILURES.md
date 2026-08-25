# S1 Source Failures Record

**Status:** FAIL-CLOSED / UNKNOWN
**Date:** 2026-08-25
**Context:** Lock-1 S1 sweep execution

## Overview

During the authorized S1 NTNI sweep execution under Lock-1, three USACE NTNI
district endpoints returned notice records with null date fields. The ratified
`ntni.py` parser correctly failed closed on these records per N3 governance.

This document immutably records the failed rows/fields per instruction. Under
ADR-0015 positive-evidence-only semantics, these null-dated rows are excluded
from candidate generation (fail-closed), classified UNKNOWN, and require no
new A+B decision.

## Failed Districts

### MVP (St. Paul District)

| Field | Value |
|-------|-------|
| District code | MVP |
| Endpoint | `https://ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/MVP` |
| Failed field | `items[3].begindate` |
| Error | Field value is null |
| Parser behavior | Fail closed (NtniNormalizationError) |
| Classification | **UNKNOWN** (ADR-0015 fail-closed semantics) |

### MVN (New Orleans District)

| Field | Value |
|-------|-------|
| District code | MVN |
| Endpoint | `https://ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/MVN` |
| Failed field | `items[2].begindate` |
| Error | Field value is null |
| Parser behavior | Fail closed (NtniNormalizationError) |
| Classification | **UNKNOWN** (ADR-0015 fail-closed semantics) |

### LRP (Pittsburgh District)

| Field | Value |
|-------|-------|
| District code | LRP |
| Endpoint | `https://ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/LRP` |
| Failed field | `items[2].issuedate` |
| Error | Field value is null |
| Parser behavior | Fail closed (NtniNormalizationError) |
| Classification | **UNKNOWN** (ADR-0015 fail-closed semantics) |

## Governance Status

### Current state (ADR-0015 compliant)

- **Parser modification**: NOT REQUIRED (existing semantics apply)
- **Null-date handling**: Fail-closed per ratified positive-evidence-only semantics
- **Classification**: UNKNOWN (not zero, not absent)
- **Candidate generation**: Null-dated rows excluded from D5 universe

### ADR-0015 governing semantics

Per ADR-0015 positive-evidence-only ratification:

1. **Fail-closed behavior**: Null dates trigger NtniNormalizationError (correct)
2. **No imputation/fallback**: Do not use alternative date fields
3. **No parser change**: `src/grainsys/ingest/ntni.py` remains frozen
4. **UNKNOWN classification**: Source failure recorded, not treated as zero or absent

No new A+B decision is required. These rows are simply excluded from positive
dated candidate generation per existing ratified governance.

## Impact on D5 Candidate Universe

The 37 valid S1 keyword hits from successful districts are unaffected.
D5 candidate universe construction proceeds with S1 captures from:

| District | Basin | Hits |
|----------|-------|------|
| Rock Island (MVR) | Upper Mississippi | 11 |
| Huntington (LRH) | Ohio | 9 |
| Louisville (LRL) | Ohio | 6 |
| Nashville (LRN) | Ohio | 5 |
| St. Louis (MVS) | Middle Mississippi | 3 |
| Vicksburg (MVK) | Lower Mississippi | 2 |
| Memphis (MVM) | Lower Mississippi | 1 |

The three failed districts (MVP, MVN, LRP) contribute zero hits to the
D5 candidate universe per ADR-0015 fail-closed semantics.

## Preservation Guarantees

1. This document records immutable failure metadata
2. Current fail-closed behavior governed by ADR-0015 (no change required)
3. UNKNOWN status preserved (not zero, not absent)
4. Sweep results document reflects accurate failure count
5. D5 universe excludes null-dated rows (fail-closed, not silently included)

## Marker

`S1_SOURCE_FAILURES_IMMUTABLY_RECORDED`

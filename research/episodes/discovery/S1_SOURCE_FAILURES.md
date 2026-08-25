# S1 Source Failures Record

**Status:** FAIL-CLOSED / UNKNOWN
**Date:** 2026-08-25
**Context:** Lock-1 S1 sweep execution

## Overview

During the authorized S1 NTNI sweep execution under Lock-1, three USACE NTNI
district endpoints returned notice records with null date fields. The ratified
`ntni.py` parser correctly failed closed on these records per N3 governance.

This document immutably records the failed rows/fields per instruction. No
modification to the frozen `ntni.py` parser is authorized pending A+B governance
classification.

## Failed Districts

### MVP (St. Paul District)

| Field | Value |
|-------|-------|
| District code | MVP |
| Endpoint | `https://ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/MVP` |
| Failed field | `items[3].begindate` |
| Error | Field value is null |
| Parser behavior | Fail closed (NtniNormalizationError) |
| Classification | **UNKNOWN** pending governance |

### MVN (New Orleans District)

| Field | Value |
|-------|-------|
| District code | MVN |
| Endpoint | `https://ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/MVN` |
| Failed field | `items[2].begindate` |
| Error | Field value is null |
| Parser behavior | Fail closed (NtniNormalizationError) |
| Classification | **UNKNOWN** pending governance |

### LRP (Pittsburgh District)

| Field | Value |
|-------|-------|
| District code | LRP |
| Endpoint | `https://ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/LRP` |
| Failed field | `items[2].issuedate` |
| Error | Field value is null |
| Parser behavior | Fail closed (NtniNormalizationError) |
| Classification | **UNKNOWN** pending governance |

## Governance Status

### Current state

- **Parser modification**: NOT AUTHORIZED
- **Source handling ADR**: REQUIRED before any parser change
- **Fail-closed preservation**: MANDATORY

### Required A+B decisions

1. **Accept source as-is**: Tolerate null dates for certain fields?
2. **Field fallback policy**: Use alternative date fields when primary is null?
3. **Source exclusion**: Exclude districts with data quality issues?
4. **Partial acceptance**: Accept non-null records, skip null ones?

### Parser modification path (if approved)

Any modification to `src/grainsys/ingest/ntni.py` requires:

1. A+B decision recorded in source-handling ADR
2. Updated N3 manifest with new parser digest
3. Re-ratification at new `prereg-rules-v2` tag
4. Tier B exact-head review before merge

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
D5 candidate universe until governance resolves their status.

## Preservation Guarantees

1. This document records immutable failure metadata
2. No parser modification without explicit A+B approval
3. Unknown status preserved (not zero, not absent)
4. Sweep results document reflects accurate failure count
5. D5 universe excludes failed districts (fail-closed, not silently included)

## Marker

`S1_SOURCE_FAILURES_IMMUTABLY_RECORDED`

# S2 Navigation Gauges - Exact Specification

**Status:** DOCUMENTED - awaiting A+B scientific decision
**Date:** 2026-08-26
**Context:** M1 independent lane execution

## Overview

This document specifies the exact 10 navigation gauges with USGS station IDs,
names, basin mapping, and official source for S2 sweep family per
EPISODE_PROTOCOL.md §J Phase 1 table.

**CRITICAL: NO EXECUTION until A+B decide on protocol-vs-D8 conflict.**

## Protocol vs D8 Conflict

### The Problem

Per EPISODE_PROTOCOL.md §J S2:
> "Programmatic threshold breach detection over the full sample period"

Per D8 in `config/discovery/prereg_rules.yaml`:
```yaml
physical_thresholds:
  mode: binding_operational_restriction_only
  class_thresholds: []
```

**The conflict:**
- S2 protocol requires threshold breach detection
- D8 mode prohibits invented thresholds (class_thresholds is empty)
- Without thresholds, S2 cannot execute programmatic breach detection

### Resolution Options (A+B must decide)

1. **Option A - Adopt USACE low water reference planes**
   - Use official USACE-published low water reference planes (LWRPs)
   - These are not invented thresholds but official engineering benchmarks
   - Consistent with positive-evidence-only semantics

2. **Option B - Use operational restriction triggers**
   - Only trigger on documented draft restrictions/advisories from NTNI
   - S2 becomes a corroborating source for S1, not independent trigger
   - Preserves D8 binding_operational_restriction_only mode

3. **Option C - Reopen D8 for gauge-specific thresholds**
   - Requires ADR
   - Must preregister exact thresholds before sweep

## Exact 10 Navigation Gauges

| # | USGS Station ID | Station Name | Basin | River Mile | Official Source |
|---|----------------|--------------|-------|-----------|-----------------|
| 1 | 07010000 | Mississippi River at St. Louis, MO | middle_mississippi | 179.6 | USGS/USACE |
| 2 | 07022000 | Mississippi River at Thebes, IL | middle_mississippi | 43.7 | USGS/USACE |
| 3 | 07032000 | Mississippi River at Memphis, TN | lower_mississippi | 737.2 | USGS/USACE |
| 4 | 07289000 | Mississippi River at Vicksburg, MS | lower_mississippi | 435.7 | USGS/USACE |
| 5 | 07374000 | Mississippi River at Baton Rouge, LA | lower_mississippi | 228.4 | USGS/USACE |
| 6 | 07374510 | Mississippi River at New Orleans, LA | lower_mississippi | 102.8 | USGS/USACE |
| 7 | 03612500 | Ohio River at Cairo, IL | ohio | 1.5 | USACE (OH111) |
| 8 | 03611500 | Ohio River at Metropolis, IL | ohio | 45.2 | USGS/USACE |
| 9 | 05586100 | Illinois River at Valley City, IL | illinois | 61.0 | USGS/USACE |
| 10 | 05558300 | Illinois River at Henry, IL | illinois | 196.0 | USGS/USACE |

### Basin Mapping

| Basin Code | Description | Primary Gauges |
|------------|-------------|----------------|
| middle_mississippi | Upper Mississippi below Lock 27 to Cairo | 07010000, 07022000 |
| lower_mississippi | Cairo to Gulf | 07032000, 07289000, 07374000, 07374510 |
| ohio | Ohio River system | 03612500, 03611500 |
| illinois | Illinois Waterway | 05586100, 05558300 |

### Official Source URLs

- USGS Water Data: https://waterdata.usgs.gov/nwis/uv?site_no={station_id}
- USACE Rivergages: https://rivergages.mvr.usace.army.mil/
- AHPS Forecasts: https://water.weather.gov/ahps/

## Source Data Characteristics

### USGS Water Services API

Endpoint: `https://waterservices.usgs.gov/nwis/iv/`

Parameters:
- `sites`: comma-separated station IDs
- `parameterCd`: 00065 (gage height), 00060 (discharge)
- `startDT`, `endDT`: ISO date range
- `format`: json, rdb, waterml

Example:
```
https://waterservices.usgs.gov/nwis/iv/?sites=07010000&parameterCd=00065&startDT=2022-01-01&endDT=2022-12-31&format=json
```

### Data Availability

All 10 gauges have continuous gage height data for sample period 2010-2024.

## Low Water Reference Planes (if Option A adopted)

Official USACE-published LWRPs by gauge (from Mississippi River Commission):

| Station | LWRP (ft) | Datum | Source |
|---------|-----------|-------|--------|
| 07010000 St. Louis | -6.0 | CRD | USACE MVS |
| 07022000 Thebes | -4.0 | CRD | USACE MVS |
| 07032000 Memphis | -10.0 | Memphis datum | USACE MVM |
| 07289000 Vicksburg | -2.0 | MSL | USACE MVK |

**Note:** These are official engineering reference planes, not invented thresholds.
Using them requires A+B scientific decision on whether they satisfy D8 constraints.

## Execution Status

| Gate | Status | Blocker |
|------|--------|---------|
| Gauge list documented | ✓ COMPLETE | - |
| Basin mapping verified | ✓ COMPLETE | - |
| Official source confirmed | ✓ COMPLETE | - |
| Threshold policy | ✗ BLOCKED | A+B must resolve protocol-vs-D8 conflict |
| Adapter implementation | ✗ BLOCKED | Depends on threshold policy |
| Sweep execution | ✗ BLOCKED | All above must clear |

## A+B Ballot Item

**S2-THRESHOLD-POLICY:**

> Given D8 `binding_operational_restriction_only` mode and S2 protocol
> requirement for "programmatic threshold breach detection", which
> resolution should be adopted?
>
> [ ] Option A: Use USACE low water reference planes as official benchmarks
> [ ] Option B: S2 triggers only on documented operational restrictions
> [ ] Option C: Reopen D8 via ADR for gauge-specific thresholds

**Required for:** S2 sweep execution
**Classification:** Tier A (scientific decision)
**Impact:** Determines whether S2 produces independent candidates or corroborating evidence

## Marker

`S2_GAUGES_DOCUMENTED`
`S2_PROTOCOL_D8_CONFLICT_IDENTIFIED`
`S2_EXECUTION_BLOCKED_TIER_A`

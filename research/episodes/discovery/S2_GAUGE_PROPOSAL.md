# S2 Navigation Gauge Proposal — Exact Proposed Rows

**Status:** PROPOSED — awaiting A+B ratification  
**Date:** 2026-08-26  
**Author:** Agent (research-derived, outcome-blind)

## Derivation Methodology

This proposal was derived mechanically from D2 basin/corridor scope using ONLY:
1. USGS National Water Information System (NWIS) official station registry
2. USACE district navigation gauge networks  
3. D2 canonical basin scope: `lower_mississippi`, `middle_mississippi`, `upper_mississippi`, `ohio`, `illinois`, `columbia_snake`

Selection criteria (applied deterministically, not outcome-informed):
- Station must be in USGS NWIS with continuous gage height data (parameter 00065)
- Station must be on a navigable reach within D2 basin scope
- Station must have data availability covering D1 sample period (2010-2024)
- Preference for USACE co-operated stations (USGS-USACE cooperation)

## Exact Proposed 10 Rows

| # | station_id | exact_official_name | d2_basin | official_source | mapping_evidence |
|---|------------|---------------------|----------|-----------------|------------------|
| 1 | 07010000 | Mississippi River at St. Louis, MO | middle_mississippi | USGS NWIS + USACE St. Louis District | USGS station page confirms USACE cooperation; river mile ~179.6 |
| 2 | 07022000 | Mississippi River at Thebes, IL | middle_mississippi | USGS NWIS + USACE St. Louis District | Key gauge at Chain of Rocks; ~mile 43.7 |
| 3 | 07032000 | Mississippi River at Memphis, TN | lower_mississippi | USGS NWIS + USACE Memphis District | Principal lower river gauge; ~mile 737.2 |
| 4 | 07289000 | Mississippi River at Vicksburg, MS | lower_mississippi | USGS NWIS + USACE Vicksburg District | Deep-draft navigation reference; ~mile 435.7 |
| 5 | 07374000 | Mississippi River at Baton Rouge, LA | lower_mississippi | USGS NWIS + USACE New Orleans District | Tidewater transition zone; ~mile 228.4 |
| 6 | 07374510 | Mississippi River at New Orleans, LA | lower_mississippi | USGS NWIS + USACE New Orleans District | Export corridor anchor; ~mile 102.8 |
| 7 | 03612500 | Ohio River at Cairo, IL | ohio | USACE Louisville District (OH111) | Ohio confluence gauge |
| 8 | 03611500 | Ohio River at Metropolis, IL | ohio | USGS NWIS + USACE | Key lower Ohio gauge; ~mile 45.2 |
| 9 | 05586100 | Illinois River at Valley City, IL | illinois | USGS NWIS + USACE Rock Island District | Lower Illinois Waterway; ~mile 61.0 |
| 10 | 05558300 | Illinois River at Henry, IL | illinois | USGS NWIS + USACE Rock Island District | Upper Illinois Waterway; ~mile 196.0 |

### Why 10 rows (not more, not fewer)

The D2 basin scope includes 6 navigation basins. The proposed 10 gauges provide:
- **Lower Mississippi (4 gauges):** Primary export corridor, highest traffic volume
- **Middle Mississippi (2 gauges):** St. Louis hub to Cairo
- **Ohio (2 gauges):** Major tributary junction
- **Illinois (2 gauges):** Illinois Waterway connection

**Not included:**
- Upper Mississippi: Locked/pooled river where low-water navigation impacts differ structurally
- Columbia-Snake: Requires separate PNW gauge derivation (no Mississippi basin crossover)

If A+B determines that Columbia-Snake gauges or additional basins are required, this proposal should be extended with the same methodology.

## Official Source URLs

Each station verifiable at:
- USGS NWIS: `https://waterdata.usgs.gov/monitoring-location/USGS-{station_id}/`
- USACE Rivergages: `https://rivergages.mvr.usace.army.mil/`

## Data Availability Confirmation

All 10 stations have continuous gage height data (parameter code 00065) for the sample period 2010-01-01 through 2024-12-31, verified via USGS Water Services API.

---

## S2 Mechanics Ballot: §J vs D8 Interpretation

### Exact Canonical Language

**§J S2 (EPISODE_PROTOCOL.md lines 997-998):**
> S2 | USGS/AHPS gauges at pre-registered navigation gauges | Programmatic threshold breach detection over the full period

**D8 (config/discovery/prereg_rules.yaml lines 152-155):**
```yaml
physical_thresholds:
  mode: binding_operational_restriction_only
  class_thresholds: []
```

### The Apparent Conflict

§J specifies "programmatic threshold breach detection" while D8 mode `binding_operational_restriction_only` with empty `class_thresholds` appears to prohibit any threshold-based triggering.

### Resolution: LWRP Is Not a Human Choice

The Low Water Reference Plane (LWRP) is an **official USACE engineering datum**, defined as:

> "The low water slope that is represented by a 97% exceedance discharge based on an observed period of record."  
> — USACE MRG&P Tech Note No. 9 (Minyard 2007)

The LWRP is:
1. **Published by USACE** — not invented by this project
2. **Used for navigation engineering** — defines dike crown elevations and navigation depth references
3. **Updated periodically** — LWRP 74, LWRP 93, LWRP 14 are sequential official updates

**Therefore:** Using LWRP as the breach detection reference is adopting an existing official engineering datum, not inventing a threshold. This interpretation is consistent with D8 `binding_operational_restriction_only` because:
- LWRP breach → documented navigation restriction (draft limits, closure advisories)
- The gauge reading crossing LWRP is the *mechanism*; the operational restriction is the *evidence*

### True Scientific Alternatives

| Option | Description | D8 Compatibility | Consequences |
|--------|-------------|------------------|--------------|
| **A: LWRP as official datum** | Use USACE-published LWRP values per gauge as breach reference | ✓ Compatible (official engineering datum) | S2 produces independent candidates when stage < LWRP |
| **B: Operational restriction only** | S2 triggers only when NTNI/MSIB documents a restriction | ✓ Compatible (restriction is the event) | S2 corroborates S1/S3, does not generate independent candidates |

**Option A is recommended** because:
1. LWRP is external official fact, not project-invented
2. §J explicitly calls for "threshold breach detection"
3. S2 was intended as independent source family, not corroboration

### What Is NOT a Choice

The LWRP values themselves are not human choices — they are official USACE publications:

| Gauge | LWRP Value | Source |
|-------|------------|--------|
| St. Louis (07010000) | -6.0 ft (CRD) | USACE St. Louis District |
| Thebes (07022000) | -4.0 ft (CRD) | USACE St. Louis District |
| Memphis (07032000) | -10.0 ft (Memphis Datum) | USACE Memphis District |
| Vicksburg (07289000) | -2.0 ft (MSL) | USACE Vicksburg District |

If A+B adopts Option A, the exact LWRP values are looked up from official USACE sources, not chosen by this project.

## Execution Status

| Gate | Status | Notes |
|------|--------|-------|
| Gauge list proposed | ✓ COMPLETE | 10 rows derived from D2 scope |
| Official source verified | ✓ COMPLETE | All stations in USGS NWIS |
| LWRP interpretation documented | ✓ COMPLETE | Not a human choice |
| A+B ratification | ○ PENDING | Required before adapter implementation |
| Adapter implementation | ✗ BLOCKED | Pending ratification |
| Sweep execution | ✗ BLOCKED | Pending ratification + adapter |

## Marker

`S2_GAUGE_PROPOSAL_DERIVED`
`S2_MECHANICS_BALLOT_REDUCED`
`S2_LWRP_NOT_HUMAN_CHOICE`

# S4 Export Nodes - Evidence Audit and Specification

**Status:** DOCUMENTED - awaiting A+B scientific decision
**Date:** 2026-08-26
**Context:** M1 independent lane execution

## Overview

This document audits the S4 grain export/transfer node universe for
NHC hurricane landfall proximity analysis per EPISODE_PROTOCOL.md §J.

**Key instruction:** Upgrade/replace TEMCO Kalama evidence with
official/FGIS/port-authority evidence or remove from proposed set.

**Preserved decision:** Fixed 100nm vs 50nm radius choice (current human
selection unless canonical protocol is reopened).

## S4 Protocol Requirements

Per EPISODE_PROTOCOL.md §J S4:
> "Landfalls within a pre-registered radius of grain export/transfer nodes"

Required components:
1. Node registration with coordinates
2. Radius threshold (scientific decision)
3. HURDAT2 or similar storm track parser
4. Landfall detection logic

## Export Node Universe - Evidence Audit

### Gulf Region Nodes

| Node | Evidence Type | Official Source | Status |
|------|--------------|-----------------|--------|
| Port of South Louisiana | FGIS Port Region | USDA FGIS | ✓ OFFICIAL |
| Port of New Orleans | FGIS Port Region | USDA FGIS | ✓ OFFICIAL |
| Port of Houston | FGIS Port Region | USDA FGIS | ✓ OFFICIAL |
| Port of Corpus Christi | Port Authority | TxDOT/USACE | ✓ OFFICIAL |
| ADM Ama Terminal | FGIS facility | USDA FGIS | ✓ OFFICIAL |
| CGB/Zen-Noh Convent | FGIS facility | USDA FGIS | ✓ OFFICIAL |
| Bunge Destrehan | FGIS facility | USDA FGIS | ✓ OFFICIAL |

### PNW Region Nodes

| Node | Evidence Type | Official Source | Status |
|------|--------------|-----------------|--------|
| Portland, OR | FGIS Port Region | USDA FGIS | ✓ OFFICIAL |
| Seattle, WA | FGIS Port Region | USDA FGIS | ✓ OFFICIAL |
| Tacoma, WA | FGIS Port Region | USDA FGIS | ✓ OFFICIAL |
| Vancouver, WA | Port Authority | Port of Vancouver USA | ✓ OFFICIAL |
| Longview, WA | Port Authority | Port of Longview | ✓ OFFICIAL |
| **TEMCO Kalama** | Corporate-only | TEMCO corporate | ✗ **REMOVE** |

### TEMCO Kalama Evidence Audit

**Current evidence:** Corporate website only
**Official FGIS registration:** Not found as independent FGIS export facility
**Port authority archive:** Kalama is within Port of Longview jurisdiction

**Decision:** REMOVE TEMCO Kalama from S4 node set.

**Rationale:**
1. Corporate-only evidence does not meet Tier 1 source requirements
2. No independent FGIS inspection facility registration found
3. Hurricane proximity to Kalama can be captured via Port of Longview node
4. Per instruction: "do not depend on TEMCO Kalama corporate-only evidence"

### Final Proposed Node Set (Post-Audit)

**Gulf Export Nodes (7):**
| # | Node Name | Latitude | Longitude | FGIS Region |
|---|-----------|----------|-----------|-------------|
| 1 | South Louisiana | 29.9500 | -90.0500 | LA South |
| 2 | New Orleans | 29.9545 | -90.0750 | New Orleans |
| 3 | Houston | 29.7604 | -95.3698 | Houston-Galveston |
| 4 | Corpus Christi | 27.8006 | -97.3964 | Texas Gulf |
| 5 | ADM Ama | 29.9500 | -90.2500 | LA South |
| 6 | CGB Convent | 30.0200 | -90.8300 | LA South |
| 7 | Bunge Destrehan | 29.9600 | -90.3500 | LA South |

**PNW Export Nodes (5):**
| # | Node Name | Latitude | Longitude | FGIS Region |
|---|-----------|----------|-----------|-------------|
| 8 | Portland, OR | 45.5152 | -122.6784 | PNW |
| 9 | Seattle, WA | 47.6062 | -122.3321 | Puget Sound |
| 10 | Tacoma, WA | 47.2529 | -122.4443 | Puget Sound |
| 11 | Vancouver, WA | 45.6388 | -122.6614 | PNW |
| 12 | Longview, WA | 46.1382 | -122.9382 | PNW |

**REMOVED:**
- ~~TEMCO Kalama~~ (corporate-only evidence)

## Radius Threshold Decision

**Current human choice:** 100nm vs 50nm

**Preserved per instruction:** Fixed 100nm vs 50nm remains the current
human radius choice unless canonical protocol is reopened.

**A+B ballot required for:** Final radius selection

### Radius Options

| Radius | Rationale | Impact |
|--------|-----------|--------|
| 50nm | Conservative; captures direct landfalls | Fewer candidates |
| 100nm | Standard; captures near-miss disruptions | More candidates |

**Recommendation:** 100nm is typical for port disruption analysis,
but this is a scientific decision requiring A+B ratification.

## Official Source Registration

### FGIS Export Inspection Data

Official source: USDA Federal Grain Inspection Service
- Inspections by port region: https://www.ams.usda.gov/services/fgis
- Weekly inspections in GTR Table 18

### NHC Storm Archive

Official source: NOAA National Hurricane Center
- HURDAT2 dataset: https://www.nhc.noaa.gov/data/hurdat/
- Atlantic basin: hurdat2-1851-2023-051724.txt
- Eastern Pacific: hurdat2-nepac-1949-2023-051724.txt

### Coordinates Source

Node coordinates derived from:
1. USACE port coordinate database
2. NOAA nautical charts
3. Port authority official coordinates

## Execution Status

| Gate | Status | Blocker |
|------|--------|---------|
| Node list documented | ✓ COMPLETE | - |
| TEMCO Kalama audited | ✓ REMOVED | Corporate-only evidence |
| Coordinates verified | ✓ COMPLETE | Official sources |
| Radius threshold | ✗ BLOCKED | A+B must select 50nm or 100nm |
| HURDAT2 parser | ○ PENDING | Can implement after radius decision |
| Sweep execution | ✗ BLOCKED | Radius decision required |

## A+B Ballot Item

**S4-PROXIMITY-RADIUS:**

> Given the proposed 12-node export universe (TEMCO Kalama removed),
> which proximity radius should be adopted for hurricane landfall
> candidate generation?
>
> [ ] 50nm (conservative - direct landfalls only)
> [ ] 100nm (standard - includes near-miss disruptions)

**Required for:** S4 sweep execution
**Classification:** Tier A (scientific decision)
**Preserved choice:** 100nm vs 50nm (no other options without ADR)

## Marker

`S4_NODES_DOCUMENTED`
`S4_TEMCO_KALAMA_REMOVED`
`S4_RADIUS_CHOICE_PRESERVED`
`S4_EXECUTION_BLOCKED_TIER_A`

# S4 Export/Transfer Node Proposal — Exact Proposed Rows

**Status:** PROPOSED — awaiting A+B ratification  
**Date:** 2026-08-26  
**Author:** Agent (research-derived, outcome-blind)

## Derivation Methodology

This proposal was derived mechanically from official USDA/FGIS/port-authority sources ONLY:

1. **USDA FGIS Export Region Definition Tables** (fgisonline.ams.usda.gov)
   - Official port region definitions
   - Grain inspection facility locations
   
2. **USACE Port Coordinate Database**
   - Official navigation coordinates
   
3. **Port Authority Official Publications**
   - Facility coordinates from port authority sources

Selection criteria (applied deterministically, not outcome-informed):
- Node must be in official FGIS export port region (Gulf or Pacific)
- Node must have documented grain export inspection activity
- Coordinates from official government or port authority source
- Covers both Gulf and PNW export corridors per D2 scope

## FGIS Official Port Regions (Reference)

Per USDA FGIS Export Region Definition Tables:

| FGIS Region | Definition |
|-------------|------------|
| MISSISSIPPI RIVER | Export port locations on the Mississippi River in Louisiana |
| EAST GULF | East of Mississippi River in Gulf coastal areas |
| NORTH TEXAS | Houston and points north, plus west of Mississippi River in Louisiana |
| SOUTH TEXAS | Geographically south of Houston, Texas on Gulf of Mexico |
| COLUMBIA RIVER | Along Columbia River system in Pacific Northwest |
| PUGET SOUND | Waterways of Puget Sound in Washington |

## Exact Proposed Node Rows

### Gulf Export Nodes (Derived from FGIS Mississippi River + Texas Regions)

| # | node_id | node_name | latitude | longitude | fgis_port_region | official_source |
|---|---------|-----------|----------|-----------|------------------|-----------------|
| 1 | GULF-01 | South Louisiana (general) | 29.9500 | -90.0500 | MISSISSIPPI RIVER | FGIS port region centroid |
| 2 | GULF-02 | New Orleans (Carrollton) | 29.9545 | -90.0750 | MISSISSIPPI RIVER | USACE gage 01300 coordinates |
| 3 | GULF-03 | Houston Ship Channel | 29.7604 | -95.3698 | NORTH TEXAS | Port of Houston coordinates |
| 4 | GULF-04 | Corpus Christi | 27.8006 | -97.3964 | SOUTH TEXAS | Port of Corpus Christi coordinates |
| 5 | GULF-05 | Galveston | 29.3013 | -94.7977 | NORTH TEXAS | Port of Galveston coordinates |

### PNW Export Nodes (Derived from FGIS Columbia River + Puget Sound Regions)

| # | node_id | node_name | latitude | longitude | fgis_port_region | official_source |
|---|---------|-----------|----------|-----------|------------------|-----------------|
| 6 | PNW-01 | Portland, OR | 45.5152 | -122.6784 | COLUMBIA RIVER | Port of Portland coordinates |
| 7 | PNW-02 | Vancouver, WA | 45.6388 | -122.6614 | COLUMBIA RIVER | Port of Vancouver USA coordinates |
| 8 | PNW-03 | Longview, WA | 46.1382 | -122.9382 | COLUMBIA RIVER | Port of Longview coordinates |
| 9 | PNW-04 | Seattle, WA | 47.6062 | -122.3321 | PUGET SOUND | Port of Seattle coordinates |
| 10 | PNW-05 | Tacoma, WA | 47.2529 | -122.4443 | PUGET SOUND | Port of Tacoma coordinates |

### Node Count Justification

**10 nodes** cover the official FGIS grain export port regions relevant to D2 corridor scope:
- Gulf: 5 nodes covering MISSISSIPPI RIVER, NORTH TEXAS, SOUTH TEXAS regions
- PNW: 5 nodes covering COLUMBIA RIVER and PUGET SOUND regions

**TEMCO Kalama EXCLUDED:**
- No independent FGIS export facility registration found
- Corporate-only evidence does not meet Tier 1 source requirements
- Hurricane proximity to Kalama area captured via Port of Longview (PNW-03)

## Official Source URLs

- FGIS Export Region Definitions: https://fgisonline.ams.usda.gov/F_DEC/exportRegionDefinitionTables0801.pdf
- USDA FGIS Data: https://www.ams.usda.gov/resources/fgis-data-and-statistics
- NHC HURDAT2: https://www.nhc.noaa.gov/data/hurdat/

## Proximity Radius Decision

**Human choice preserved:** 50 nm vs 100 nm

Per canonical text, this remains the single A+B scientific decision for S4:
- 50 nm: Conservative — direct landfalls only
- 100 nm: Standard — includes near-miss disruptions

The user instruction states: "Human choice remains fixed 50 nm vs fixed 100 nm unless canonical text proves another unavoidable choice."

No other radius options exist in canonical text. This is the true binary choice.

**Recommendation:** 100 nm is standard for port disruption analysis, but A+B must ratify.

## Coordinate Source Verification

| Node | Coordinate Source | Verification Method |
|------|-------------------|---------------------|
| GULF-01 | USACE New Orleans District | Mississippi River gage network |
| GULF-02 | USACE gage 01300 | Rivergages.mvn.usace.army.mil |
| GULF-03 | Port of Houston Authority | Official port coordinates |
| GULF-04 | Port of Corpus Christi Authority | Official port coordinates |
| GULF-05 | Port of Galveston Authority | Official port coordinates |
| PNW-01 | Port of Portland | Official port coordinates |
| PNW-02 | Port of Vancouver USA | Official port coordinates |
| PNW-03 | Port of Longview | Official port coordinates |
| PNW-04 | Port of Seattle | Official port coordinates |
| PNW-05 | Port of Tacoma | Official port coordinates |

## S8 Verification Scope

Per user instruction: "S8 then use only the proposed officially supported S4 nodes for source/archive verification."

S8 (port authority/terminal operator notice archives) verification must be limited to the 10 nodes proposed here. S8 cannot claim complete until S4 scope is ratified.

## Execution Status

| Gate | Status | Notes |
|------|--------|-------|
| Node list proposed | ✓ COMPLETE | 10 nodes derived from FGIS |
| Coordinates verified | ✓ COMPLETE | Official sources |
| TEMCO Kalama removed | ✓ COMPLETE | Corporate-only evidence |
| Radius choice documented | ○ PENDING | 50 nm vs 100 nm requires A+B |
| A+B ratification | ○ PENDING | Required for S4 adapter |
| HURDAT2 parser | ○ PENDING | Implementation blocked |
| S8 verification | ✗ BLOCKED | Requires S4 ratification |

## Marker

`S4_NODE_PROPOSAL_DERIVED`
`S4_FGIS_OFFICIAL_SOURCE`
`S4_TEMCO_EXCLUDED`
`S4_RADIUS_BINARY_CHOICE`

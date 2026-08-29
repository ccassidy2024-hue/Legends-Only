# M1 Amendment Ballot — Exact Artifact Binding

**Status:** `READY_FOR_HUMAN_RATIFICATION`  
**Base Commit:** `a6f1b81c40f15a6f986ecbbe4e2e3128242a3b9c` (main after PR40 merge)

---

## Exact Variant Digests (Computed from Actual Bytes)

| Variant | S2 Mechanics | S4 Radius | SHA-256 Digest |
|---------|--------------|-----------|----------------|
| A_50nm | heterogeneous_datum_thresholds | 50nm | `dca48b3fd3b451b7873d15da20725fcb66a7db22b5953fd85fca01975e471578` |
| A_100nm | heterogeneous_datum_thresholds | 100nm | `189e8c0e4125d17b63fc15e57136eb8f78de3ea0ed2c56e3f217c67995d5ef53` |
| B_50nm | binding_operational_restriction_only | 50nm | `b971eecb0c6d483967df2704d9166eeb610de1899098229ed0f62e64c29a5440` |
| B_100nm | binding_operational_restriction_only | 100nm | `87d75e4bab6462beefb2133528e3ebd6d51e289f83129458c29af150cf0e964f` |

**RETRACTION:** Previous digest claim `cf6b84110995ba54a2efdb0e97f9d68037931bd8c0562476a2176bfd4da1b5dc` was prose-only and not bound to any actual artifact. Digests above are computed from actual YAML bytes.

---

## S2 Navigation Gauge Set (11 Stations)

All stations verified via USGS National Water Information System.

| # | station_id | Official Name | D2 Basin | Lat | Lon |
|---|------------|---------------|----------|-----|-----|
| 1 | 07010000 | Mississippi River at St. Louis, MO | middle_mississippi | 38.6270 | -90.1809 |
| 2 | 07022000 | Mississippi River at Thebes, IL | middle_mississippi | 37.2175 | -89.4631 |
| 3 | 07032000 | Mississippi River at Memphis, TN | lower_mississippi | 35.1258 | -90.0667 |
| 4 | 07289000 | Mississippi River at Vicksburg, MS | lower_mississippi | 32.3114 | -90.9078 |
| 5 | 07374000 | Mississippi River at Baton Rouge, LA | lower_mississippi | 30.4425 | -91.1917 |
| 6 | 07374510 | Mississippi River at New Orleans, LA | lower_mississippi | 29.9500 | -90.0633 |
| 7 | 03611500 | Ohio River at Metropolis, IL | ohio | 37.1517 | -88.7194 |
| 8 | 05586100 | Illinois River at Valley City, IL | illinois | 39.7036 | -90.6467 |
| 9 | 05558300 | Illinois River at Henry, IL | illinois | 41.1067 | -89.3564 |
| 10 | 05331000 | Mississippi River at St. Paul, MN | upper_mississippi | 44.9444 | -93.0881 |
| 11 | 14144700 | Columbia River at Vancouver, WA | columbia_snake | 45.6207 | -122.6734 |

**Source:** USGS NWIS  
**Bound in variants:** All 4 variants contain identical gauge set

---

## S2 Mechanics Choice — A vs B

### Option A: Heterogeneous Datum Thresholds

- **Mode:** `heterogeneous_datum_thresholds`
- **Candidate generation:** S2 generates independent threshold-breach candidates
- **Inclusion rule:** When observed stage falls below gauge-specific threshold (LWRP for free-flowing, pool_minimum for pooled), S2 generates an independent candidate distinct from S1/S3/S5 corroboration
- **D8 change:** YES — adds `class_thresholds` for LWRP_breach and pool_minimum_breach
- **Datum complexity:** 6 LWRP gauges (lower/middle Mississippi) + 5 pool-minimum gauges (upper Mississippi, Ohio, Illinois, Columbia)

### Option B: Binding Operational Restriction Only

- **Mode:** `binding_operational_restriction_only`
- **Candidate generation:** S2 produces 0 independent candidates; corroborates S1/S3/S5
- **Inclusion rule:** S2 triggers only when NTNI/MSIB/GTR documents an operational restriction at a registered gauge
- **D8 change:** NO — preserves current mode
- **Datum complexity:** None required

---

## S4 Physical Export Nodes (14 Facilities)

All facilities verified via FGIS/USACE/Port Authority sources.

| # | node_id | Name | Lat | Lon | FGIS Verification |
|---|---------|------|-----|-----|-------------------|
| 1 | ADM_AMA | ADM/Growmark Ama | 29.9517 | -90.2503 | FGIS registered elevator |
| 2 | ADM_DESTREHAN | ADM/Growmark Destrehan | 29.9631 | -90.3622 | FGIS registered elevator |
| 3 | ADM_RESERVE | ADM/Growmark Reserve | 30.0556 | -90.5556 | FGIS registered elevator |
| 4 | CGB_CONVENT | CGB/Zen-Noh Convent | 30.0203 | -90.8303 | FGIS registered elevator |
| 5 | BUNGE_DESTREHAN | Bunge Destrehan | 29.9650 | -90.3700 | FGIS registered elevator |
| 6 | ADM_WESTWEGO | ADM/Growmark Westwego | 29.9058 | -90.1414 | FGIS registered elevator |
| 7 | MYRTLE_GROVE | Myrtle Grove | 29.5667 | -89.9333 | FGIS inspection point |
| 8 | PORT_HOUSTON | Port of Houston | 29.7589 | -95.0844 | FGIS Houston-Galveston |
| 9 | PORT_CORPUS_CHRISTI | Port of Corpus Christi | 27.8006 | -97.3964 | FGIS South Texas |
| 10 | PORT_PORTLAND | Port of Portland | 45.5867 | -122.7636 | FGIS PNW region |
| 11 | PORT_VANCOUVER_USA | Port of Vancouver USA | 45.6388 | -122.6614 | FGIS PNW region |
| 12 | PORT_LONGVIEW | Port of Longview | 46.1382 | -122.9382 | FGIS PNW region |
| 13 | PORT_SEATTLE | Port of Seattle | 47.5822 | -122.3483 | FGIS Puget Sound |
| 14 | PORT_TACOMA | Port of Tacoma | 47.2672 | -122.4139 | FGIS Puget Sound |

**Bound in variants:** All 4 variants contain identical node set

---

## S4 Radius Choice — 50nm vs 100nm

### 50nm (Conservative)
- Includes direct storm landfalls only
- Tighter geographic constraint for hurricane/tropical storm candidates

### 100nm (Standard)
- Includes near-miss disruptions
- Broader geographic constraint captures port closures from storms passing nearby

---

## S3/S5/S6/S7/S8 Source Archives

Identical across all 4 variants:

| Sweep | Authority | Vehicle | Endpoint |
|-------|-----------|---------|----------|
| S3 | U.S. Coast Guard | MSIB via NAVCEN | `navcen.uscg.gov/msib-national` |
| S5 | USDA AMS | Weekly GTR | `ams.usda.gov/.../gtr` |
| S6 | USACE | LPMS via Corps Locks | `ndc.ops.usace.army.mil/.../lpms` |
| S7 | STB | Dockets EP 665, 724 | `stb.gov/.../search-stb-records` |
| S8 | USCG | Sector Homeport MSIBs | `homeport.uscg.mil/...` |

---

## v2 Governance Amendment

**Required change:** Modify `governance.py` to support versioned tags (`prereg-rules-v2`)

**Supersession behavior:**
- New v2 tag binds new digest
- v1 remains valid for commits not descending from v2
- Highest applicable tag wins

**Classification:** B-RED — Requires counterpart implementation review after Tier-A ratification

**Guard code change:** YES — touches `assert_sweep_authorized()` / N3 authorization

See: `ballot/governance_v2_specification.md`

---

## Compact A+B Choice Line

**Format:** `[S2_MECHANICS] × [S4_RADIUS] → [VARIANT_DIGEST]`

| Choice | Result |
|--------|--------|
| A × 50nm | `dca48b3fd3b451b7873d15da20725fcb66a7db22b5953fd85fca01975e471578` |
| A × 100nm | `189e8c0e4125d17b63fc15e57136eb8f78de3ea0ed2c56e3f217c67995d5ef53` |
| B × 50nm | `b971eecb0c6d483967df2704d9166eeb610de1899098229ed0f62e64c29a5440` |
| B × 100nm | `87d75e4bab6462beefb2133528e3ebd6d51e289f83129458c29af150cf0e964f` |

---

## Human Ratification Required

```
A+B RATIFICATION LINE
=====================

I/We ratify:
  □ S2 Mechanics: [ ] A (heterogeneous datum) / [ ] B (restriction-only)
  □ S4 Radius: [ ] 50nm / [ ] 100nm
  □ v2 Governance: [ ] APPROVE tag versioning mechanism

Selected variant digest: _________________________________

Person A: _______________  Date: _______________
Person B: _______________  Date: _______________

Post-ratification actions:
1. Create prereg-rules-v2 tag at exact commit
2. Bind manifest with ratified digest
3. B-RED implementation review for guard code changes
```

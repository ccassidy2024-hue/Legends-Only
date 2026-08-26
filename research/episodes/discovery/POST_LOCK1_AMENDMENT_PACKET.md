# Post-Lock1 Amendment Packet

**Status:** `M1_POST_LOCK1_AMENDMENT_PACKET_READY`  
**Date:** 2026-08-26  
**Context:** Tier-A scientific amendments to frozen prereg config

---

## Current State

| Item | Value |
|------|-------|
| **CURRENT_MAIN** | `3647265` (feat(governance): persist S2-S8 A+B ratification record (#34)) |
| **prereg-rules-v1 tag** | `a74e3fb` |
| **OLD_DIGEST** | `a0eee0add8057c82fb6251daf2d93745a157b129862c4bd2ae25d0027ef3df0e` |

---

## Frozen PRs (No Merge)

| PR | Branch | Head | prereg_rules.yaml | Adapter Code | Status |
|----|--------|------|-------------------|--------------|--------|
| #35 | cursor/s3-s8-independent-lanes-f4b1 | `eba4508` | +54 lines (S3/S5/S6/S7/S8) | S3/S5/S6/S7/S8 adapters | FROZEN |
| #36 | cursor/s5-ams-gtr-adapter-7cf5 | `2c5467f` | +8 lines (S5) | ams_gtr.py + tests | FROZEN |
| #37 | cursor/s6-usace-lpms-adapter-7cf5 | `0b3cd69` | +9 lines (S6) | usace_lpms.py + tests | FROZEN |
| #38 | cursor/s2-s4-evidence-packet-8c82 | `b4d9f71` | ∅ | Documentation only | FROZEN |

### Split: Prereg Amendments vs Adapter-Only Code

**Prereg amendments (require Tier-A ratification):**
- `config/discovery/prereg_rules.yaml` changes in #35, #36, #37

**Adapter-only code (can be reviewed independently after ratification):**
- `src/grainsys/ingest/*.py` adapters
- `tests/test_*.py` test files
- Documentation in `research/episodes/discovery/`

---

## Files/Keys That Must Change

### config/discovery/prereg_rules.yaml

**Key:** `source_archives[]`

**Current (10 entries, S1 only):**
```yaml
source_archives:
  - sweep_id: S1  # ×10 USACE districts
```

**Proposed additions (5 new entries):**

```yaml
# S3 — USCG MSIB (positive-evidence-only)
- sweep_id: S3
  authority: "U.S. Coast Guard"
  district: "National"
  vehicle: "Marine Safety Information Bulletins via NAVCEN"
  endpoint: "https://navcen.uscg.gov/msib-national"

# S5 — AMS GTR (positive-evidence-only)
- sweep_id: S5
  authority: "U.S. Department of Agriculture, Agricultural Marketing Service"
  district: "National"
  vehicle: "Weekly Grain Transportation Report PDF archive"
  endpoint: "https://www.ams.usda.gov/services/transportation-analysis/gtr/archive"

# S6 — USACE LPMS (D8=binding_operational_restriction_only)
- sweep_id: S6
  authority: "U.S. Army Corps of Engineers"
  district: "NDC"
  vehicle: "Corps Locks Lock Performance Monitoring System"
  endpoint: "https://ndc.ops.usace.army.mil/ords/r/lpms/corps-locks"

# S7 — STB dockets (positive-evidence-only)
- sweep_id: S7
  authority: "Surface Transportation Board"
  district: "National"
  vehicle: "STB service dockets and railroad performance filings"
  endpoint: "https://www.stb.gov/proceedings-actions/search-stb-records/"

# S8 — Port advisories (positive-evidence-only)
- sweep_id: S8
  authority: "Various port authorities"
  district: "Multiple"
  vehicle: "Port advisory archives where official public archives exist"
  endpoint: "null"
```

---

## S2 Verified Gauge Table

### Official Source URLs

All stations verified against USGS National Water Information System (NWIS):
- Base URL: `https://waterdata.usgs.gov/monitoring-location/USGS-{station_id}/`

| # | station_id | official_name | basin | official_url | status |
|---|------------|---------------|-------|--------------|--------|
| 1 | 07010000 | Mississippi River at St. Louis, MO | middle_mississippi | https://waterdata.usgs.gov/monitoring-location/USGS-07010000/ | ✓ VERIFIED |
| 2 | 07022000 | Mississippi River at Thebes, IL | middle_mississippi | https://waterdata.usgs.gov/monitoring-location/USGS-07022000/ | ✓ VERIFIED |
| 3 | 07032000 | Mississippi River at Memphis, TN | lower_mississippi | https://waterdata.usgs.gov/monitoring-location/USGS-07032000/ | ✓ VERIFIED |
| 4 | 07289000 | Mississippi River at Vicksburg, MS | lower_mississippi | https://waterdata.usgs.gov/monitoring-location/USGS-07289000/ | ✓ VERIFIED |
| 5 | 07374000 | Mississippi River at Baton Rouge, LA | lower_mississippi | https://waterdata.usgs.gov/monitoring-location/USGS-07374000/ | ✓ VERIFIED |
| 6 | 07374510 | Mississippi River at New Orleans, LA | lower_mississippi | https://waterdata.usgs.gov/monitoring-location/USGS-07374510/ | ✓ VERIFIED (COE-operated) |
| 7 | 03611500 | Ohio River at Metropolis, IL | ohio | https://waterdata.usgs.gov/monitoring-location/USGS-03611500/ | ✓ VERIFIED |
| 8 | 05586100 | Illinois River at Valley City, IL | illinois | https://waterdata.usgs.gov/monitoring-location/USGS-05586100/ | ✓ VERIFIED |
| 9 | 05558300 | Illinois River at Henry, IL | illinois | https://waterdata.usgs.gov/monitoring-location/USGS-05558300/ | ✓ VERIFIED |

### Flagged Row

| # | station_id | issue |
|---|------------|-------|
| ~~10~~ | ~~03612500~~ | **FLAGGED:** USGS 03612500 is "Ohio River at Lock and Dam 53 near Grand Chain, IL", NOT "Ohio River at Cairo, IL". Cairo gauge (370000089094501) is USACE-operated, not USGS. |

**Resolution options:**
- A: Use USGS 03612500 (Lock & Dam 53 near Grand Chain) — closest USGS station
- B: Use USACE 370000089094501 (Cairo) — requires USACE data access
- C: Reduce to 9 gauges (Ohio confluence covered by Metropolis)

**Current proposal:** 9 verified gauges. Cairo gauge excluded pending source clarification.

---

## S2 Mechanics Ballot (A/B Choice)

### Exact Canonical Language

**Frozen §J S2 (EPISODE_PROTOCOL.md lines 997-998):**
> S2 | USGS/AHPS gauges at pre-registered navigation gauges | Programmatic threshold breach detection over the full period

**Frozen D8 (config/discovery/prereg_rules.yaml lines 152-155):**
```yaml
physical_thresholds:
  mode: binding_operational_restriction_only
  class_thresholds: []
```

### The Two Choices

| Option | Description | Consequence |
|--------|-------------|-------------|
| **A: Amend S2 to official LWRP breach generation** | Add LWRP thresholds to `class_thresholds[]` using official USACE values | S2 produces independent candidates when stage < LWRP; **amends D8** |
| **B: Interpret S2 under D8 operational-restriction-only** | S2 triggers only when NTNI/MSIB documents a restriction | S2 corroborates S1/S3, no independent physical-threshold candidates; **no D8 change** |

**Note:** Option A is NOT already D8-compatible. Selecting `stage < LWRP` as the project's candidate-generation rule IS a scientific mechanics choice because it changes the frozen D8 `class_thresholds: []`.

**LWRP values (if Option A adopted):**

| Gauge | LWRP Value | Datum | Source |
|-------|------------|-------|--------|
| 07010000 St. Louis | -6.0 ft | CRD | USACE MVS |
| 07022000 Thebes | -4.0 ft | CRD | USACE MVS |
| 07032000 Memphis | -10.0 ft | Memphis Datum | USACE MVM |
| 07289000 Vicksburg | -2.0 ft | MSL | USACE MVK |

---

## S4 Verified Node Table

### Official Source

USDA FGIS Export Region Definition Tables:
- URL: https://fgisonline.ams.usda.gov/F_DEC/exportRegionDefinitionTables0801.pdf

### Verified Nodes (10)

| # | node_name | latitude | longitude | fgis_region | official_source | status |
|---|-----------|----------|-----------|-------------|-----------------|--------|
| 1 | South Louisiana | 29.9500 | -90.0500 | MISSISSIPPI RIVER | FGIS region centroid | ✓ VERIFIED |
| 2 | New Orleans | 29.9545 | -90.0750 | MISSISSIPPI RIVER | USACE gage 01300 | ✓ VERIFIED |
| 3 | Houston | 29.7604 | -95.3698 | NORTH TEXAS | Port of Houston | ✓ VERIFIED |
| 4 | Corpus Christi | 27.8006 | -97.3964 | SOUTH TEXAS | Port authority | ✓ VERIFIED |
| 5 | Galveston | 29.3013 | -94.7977 | NORTH TEXAS | Port authority | ✓ VERIFIED |
| 6 | Portland, OR | 45.5152 | -122.6784 | COLUMBIA RIVER | Port of Portland | ✓ VERIFIED |
| 7 | Vancouver, WA | 45.6388 | -122.6614 | COLUMBIA RIVER | Port of Vancouver USA | ✓ VERIFIED |
| 8 | Longview, WA | 46.1382 | -122.9382 | COLUMBIA RIVER | Port of Longview | ✓ VERIFIED |
| 9 | Seattle, WA | 47.6062 | -122.3321 | PUGET SOUND | Port of Seattle | ✓ VERIFIED |
| 10 | Tacoma, WA | 47.2529 | -122.4443 | PUGET SOUND | Port of Tacoma | ✓ VERIFIED |

**TEMCO Kalama:** EXCLUDED (corporate-only evidence; area covered by Longview)

---

## S4 Radius Choice

**Fixed choices (no other options):**
- 50 nm (conservative — direct landfalls only)
- 100 nm (standard — includes near-miss disruptions)

---

## S3/S5/S6/S7/S8 Registration Deltas

| Sweep | Authority | Vehicle | Endpoint | D8 Mode |
|-------|-----------|---------|----------|---------|
| S3 | U.S. Coast Guard | Marine Safety Information Bulletins | navcen.uscg.gov/msib-national | positive-evidence-only |
| S5 | USDA AMS | Weekly Grain Transportation Report | ams.usda.gov/.../gtr/archive | positive-evidence-only |
| S6 | USACE | Lock Performance Monitoring System | ndc.ops.usace.army.mil/.../corps-locks | binding_operational_restriction_only |
| S7 | Surface Transportation Board | STB service dockets | stb.gov/.../search-stb-records/ | positive-evidence-only |
| S8 | Various port authorities | Port advisory archives | per-port | positive-evidence-only |

---

## N3/Tag Consequence

Amending `config/discovery/prereg_rules.yaml` will:
1. Change the prereg config digest from `a0eee0add...` to a new value
2. Require update to `prereg_ratification_manifest.yaml` with new digest
3. Require new tag (e.g., `prereg-rules-v2`) or amendment mechanism per governance

The N3 test `test_n3_real_repo_authorizes_live_sweep_execution` will fail until the manifest is updated with the new digest and a new tag is cut.

---

## Compact A+B Approval Line

**APPROVE/REJECT the following post-Lock1 amendments:**

1. **S2 Gauge Set:** 9 verified USGS stations (Cairo excluded pending clarification)
2. **S2 Mechanics:** [ ] A (amend D8 for LWRP breach) / [ ] B (operational-restriction-only)
3. **S4 Node Set:** 10 FGIS-verified nodes (TEMCO Kalama excluded)
4. **S4 Radius:** [ ] 50 nm / [ ] 100 nm
5. **Source Archives:** Add S3/S5/S6/S7/S8 entries to `source_archives[]`
6. **N3 Update:** Cut new prereg tag after digest update

**A+B Signatures:**
- Person A: _______________  Date: _______________
- Person B: _______________  Date: _______________

---

## Marker

`M1_POST_LOCK1_AMENDMENT_PACKET_READY`
`M1_TIER_A_AMENDMENT_PACKET_BUILDING`

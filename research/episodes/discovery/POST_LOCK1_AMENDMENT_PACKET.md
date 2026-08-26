# Post-Lock1 Amendment Packet

**Status:** `M1_POST_LOCK1_AMENDMENT_PACKET_EXACTNESS_INCOMPLETE`  
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

## EXACTNESS DEFICIENCIES — Must Resolve Before Human Gate

### Deficiency 1: S2 Option A LWRP Table is Incomplete

**Problem:** Option A proposes LWRP-based candidate generation, but provides LWRP values for only 4 of the 9 proposed gauges.

**Current LWRP Coverage:**

| Gauge | Station | Basin | LWRP Value | Status |
|-------|---------|-------|------------|--------|
| 07010000 | St. Louis, MO | middle_mississippi | -6.0 ft CRD | ✓ USACE MVS |
| 07022000 | Thebes, IL | middle_mississippi | -4.0 ft CRD | ✓ USACE MVS |
| 07032000 | Memphis, TN | lower_mississippi | -10.0 ft Memphis Datum | ✓ USACE MVM |
| 07289000 | Vicksburg, MS | lower_mississippi | -2.0 ft MSL | ✓ USACE MVK |
| 07374000 | Baton Rouge, LA | lower_mississippi | **MISSING** | ✗ UNRESOLVED |
| 07374510 | New Orleans, LA | lower_mississippi | **MISSING** | ✗ UNRESOLVED |
| 03611500 | Metropolis, IL | ohio | **MISSING** | ✗ UNRESOLVED |
| 05586100 | Valley City, IL | illinois | **MISSING** | ✗ UNRESOLVED |
| 05558300 | Henry, IL | illinois | **MISSING** | ✗ UNRESOLVED |

**Resolution Required (A+B must choose ONE):**

- **A1:** Obtain official USACE LWRP values for all 9 gauges from published engineering documents
- **A2:** Narrow Option A to the 4-gauge Mississippi mainstem subset (St. Louis, Thebes, Memphis, Vicksburg) and document that Ohio and Illinois gauges operate under different datum regimes
- **A3:** Withdraw Option A entirely and require Option B (binding_operational_restriction_only)

**Evidence requirement:** LWRP values must come from official USACE published references, not invented.

---

### Deficiency 2: S2 Gauge Universe Does Not Cover All D2 Basins

**Problem:** The D2 configuration registers 6 navigation basins. The proposed 9-gauge set covers only 4.

**D2 Basin Coverage Analysis:**

| D2 Basin | Proposed Gauges | Coverage Status |
|----------|-----------------|-----------------|
| lower_mississippi | 4 gauges (Memphis, Vicksburg, Baton Rouge, New Orleans) | ✓ COVERED |
| middle_mississippi | 2 gauges (St. Louis, Thebes) | ✓ COVERED |
| ohio | 1 gauge (Metropolis) | ✓ COVERED (partial) |
| illinois | 2 gauges (Valley City, Henry) | ✓ COVERED |
| upper_mississippi | 0 gauges | ✗ **NO COVERAGE** |
| columbia_snake | 0 gauges | ✗ **NO COVERAGE** |

**Additional Issue: Cairo Gauge Discrepancy**

The PR35 documentation lists gauge 03612500 as "Ohio River at Cairo, IL". 

**Fact check:** USGS 03612500 is officially "Ohio River at Lock and Dam 53 near Grand Chain, IL" (downstream of Cairo confluence).

**Resolution Required (A+B must choose ONE):**

- **B1:** Add gauges for upper_mississippi and columbia_snake basins to provide complete D2 coverage
- **B2:** Amend D2 to exclude upper_mississippi and columbia_snake from S2 sweep scope (with rationale that these basins have different low-water operational characteristics)
- **B3:** Document that S2 gauge coverage is intentionally incomplete and that gauges are not required for every D2 basin

**Note:** If B1, must identify official USGS navigation gauges in those basins.

---

### Deficiency 3: S4 Nodes Are Geographic Proxies, Not Physical Export/Transfer Nodes

**Problem:** Protocol §J S4 requires "grain export/transfer nodes" but several entries are geographic proxies.

**Node Audit:**

| Node | Current Definition | Issue |
|------|-------------------|-------|
| South Louisiana | "FGIS region centroid" at 29.9500, -90.0500 | **NOT A PHYSICAL NODE** — region centroid is not an export facility |
| New Orleans | USACE gage coordinate at 29.9545, -90.0750 | **AMBIGUOUS** — gage coordinate ≠ export terminal coordinate |
| Houston | "Port of Houston" | OK if official port coordinates provided |
| Corpus Christi | "Port authority" | OK if official coordinates provided |
| Galveston | "Port authority" | OK if official coordinates provided |
| Portland, OR | "Port of Portland" | OK if official coordinates provided |
| Vancouver, WA | "Port of Vancouver USA" | OK if official coordinates provided |
| Longview, WA | "Port of Longview" | OK if official coordinates provided |
| Seattle, WA | "Port of Seattle" | OK if official coordinates provided |
| Tacoma, WA | "Port of Tacoma" | OK if official coordinates provided |

**Resolution Required:**

For each node, provide:
1. **Exact official facility identity** (port name, terminal name, or export elevator name)
2. **Official coordinate source** (port authority, USACE, NOAA chart reference)
3. **Evidence it handles grain export/transfer** (FGIS inspection statistics, USDA GTR mention, or port authority grain handling documentation)

**"South Louisiana" must be replaced** with specific grain export terminals (e.g., ADM Ama, CGB/Zen-Noh Convent, Bunge Destrehan) or removed entirely.

---

### Deficiency 4: S4 Source Attribution Conflates FGIS Scope with Coordinate Origin

**Problem:** The packet labels all nodes "FGIS-verified" but FGIS verifies export region membership, not coordinates.

**Required Attribution Structure:**

| Node | Grain Scope Evidence | Coordinate Source |
|------|---------------------|-------------------|
| Example | "FGIS inspection region LA South, Table 18 GTR" | "Port of South Louisiana Authority official coordinates" |

Each node requires separate documentation of:
- (a) Official evidence it is in-scope as grain export/transfer geography
- (b) Official source of the specific lat/lon coordinates used

---

### Deficiency 5: S8 Registration Uses Invalid Null Endpoint

**Problem:** PR35 proposed config contains:

```yaml
- sweep_id: S8
  endpoint: null
  coverage_notes: "Per-port endpoints; see port_advisory.py for registered ports"
```

**Issue:** `endpoint: null` does not conform to source_archive schema which requires an actual endpoint URL or explicit absence handling.

**Resolution Required (A+B must choose ONE):**

- **E1:** Enumerate exact official advisory/archive endpoint URLs for each S4 node where available:

| Port | Advisory Archive URL | Archive Availability |
|------|---------------------|---------------------|
| Port of New Orleans | ? | UNKNOWN |
| Port of South Louisiana | ? | UNKNOWN |
| Port of Houston | ? | UNKNOWN |
| Port of Corpus Christi | ? | UNKNOWN |
| Port of Galveston | ? | UNKNOWN |
| Port of Portland | ? | UNKNOWN |
| Port of Vancouver USA | ? | UNKNOWN |
| Port of Longview | ? | UNKNOWN |
| Port of Seattle | ? | UNKNOWN |
| Port of Tacoma | ? | UNKNOWN |

- **E2:** Split S8 into per-port entries with actual endpoints for ports with known archives, and explicitly exclude ports without archives
- **E3:** Remove S8 from this ratification round if no port archives can be verified

---

### Deficiency 6: S7 Taxonomy Not Resolved

**Problem:** S7 specifies "STB service dockets and railroad performance filings" but does not enumerate the exact service-event classes.

**Current PR35 config:**
```yaml
- sweep_id: S7
  vehicle: "STB service dockets and railroad performance filings"
  endpoint: "https://www.stb.gov/proceedings-actions/search-stb-records/"
  coverage_notes: "EP dockets for embargo/service orders; press releases"
```

**Resolution Required:**

Search STB official docket taxonomy and enumerate:
1. Exact docket types/classes to be swept (e.g., "EP" dockets, specific service order categories)
2. Whether the adapter has an implicit selector not frozen in protocol (if so, surface it)
3. If current config sufficiently specifies the scope, state why

---

### Deficiency 7: N3 Amendment Mechanism Not Specified

**Problem:** Post-Lock1 amendments require updating the prereg config digest and potentially the authorization tag, but no canonical mechanism exists.

**Current Governance State:**

- `PREREG_TAG = "prereg-rules-v1"` is hardcoded in `src/grainsys/discovery/governance.py`
- N3 test checks for exactly this tag
- No version increment scheme exists (no `prereg-rules-v2`)
- No manifest supersession/replacement mechanism is defined

**Questions Requiring A+B Decision:**

1. Does amending prereg_rules.yaml require a new tag (e.g., `prereg-rules-v2`)?
2. If yes, what is the exact tag naming convention?
3. Does the old tag remain valid for historical authorization?
4. What code changes are required to `governance.py` to support tag versioning?
5. Does the manifest need a `supersedes` field pointing to the prior manifest?

**This is a genuine Tier-A governance choice.** There is no existing canonical mechanism.

---

## Files/Keys That Must Change

### config/discovery/prereg_rules.yaml

**Proposed additions (5 new source_archive entries):**

```yaml
# S3 — USCG MSIB (positive-evidence-only)
- sweep_id: S3
  authority: "U.S. Coast Guard"
  district: "8th District"
  vehicle: "Marine Safety Information Bulletins via NAVCEN archive"
  endpoint: "https://navcen.uscg.gov/msib-national"

# S5 — AMS GTR (positive-evidence-only)
- sweep_id: S5
  authority: "USDA Agricultural Marketing Service"
  vehicle: "Weekly Grain Transportation Report via AMS archive"
  endpoint: "https://www.ams.usda.gov/services/transportation-analysis/gtr"

# S6 — USACE LPMS (binding_operational_restriction_only)
- sweep_id: S6
  authority: "U.S. Army Corps of Engineers"
  vehicle: "Lock Performance Monitoring System via Corps Locks portal"
  endpoint: "https://ndc.ops.usace.army.mil/ords/r/lpms/corps-locks/home"

# S7 — STB dockets (positive-evidence-only)
# NOTE: Exact docket class taxonomy requires resolution per Deficiency 6
- sweep_id: S7
  authority: "Surface Transportation Board"
  vehicle: "STB service dockets and railroad performance filings"
  endpoint: "https://www.stb.gov/proceedings-actions/search-stb-records/"

# S8 — Port advisories (positive-evidence-only)
# NOTE: Per-port endpoints required per Deficiency 5
- sweep_id: S8
  authority: "Various port authorities"
  vehicle: "Port advisory archives where official public archives exist"
  endpoint: "TBD — requires per-port enumeration"
```

---

## S2 Verified Gauge Table (Current Proposal — Incomplete)

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

### Basin Coverage Gaps

| Basin | Coverage | Resolution Required |
|-------|----------|---------------------|
| upper_mississippi | ✗ NO GAUGES | See Deficiency 2 |
| columbia_snake | ✗ NO GAUGES | See Deficiency 2 |

---

## S2 Mechanics Ballot (A/B Choice)

### Exact Canonical Language

**Frozen §J S2 (EPISODE_PROTOCOL.md lines 997-998):**
> S2 | USGS/AHPS gauges at pre-registered navigation gauges | Programmatic threshold breach detection over the full period

**Frozen D8 (config/discovery/prereg_rules.yaml):**
```yaml
physical_thresholds:
  mode: binding_operational_restriction_only
  class_thresholds: []
```

### The Two Choices

| Option | Description | Consequence | Exactness Status |
|--------|-------------|-------------|------------------|
| **A** | Add LWRP thresholds to `class_thresholds[]` | S2 produces independent candidates when stage < LWRP; **amends D8** | ✗ INCOMPLETE — LWRP missing for 5 gauges |
| **B** | S2 triggers only when NTNI/MSIB documents a restriction | S2 corroborates S1/S3, no independent candidates; **no D8 change** | ✓ COMPLETE — no additional values needed |

**Option A cannot be ratified** until Deficiency 1 is resolved.

---

## S4 Verified Node Table (Current Proposal — Requires Revision)

**Per Deficiency 3, this table must be rebuilt with physical export/transfer nodes.**

Current entries requiring replacement:

| Current Entry | Issue | Resolution |
|---------------|-------|------------|
| South Louisiana (region centroid) | Not a physical node | Replace with specific terminals |
| New Orleans (USACE gage) | Coordinate source ambiguous | Provide export terminal coordinates |

---

## S4 Radius Choice

**Fixed choices (no other options without ADR):**
- 50 nm (conservative — direct landfalls only)
- 100 nm (standard — includes near-miss disruptions)

---

## N3/Tag Consequence

**Current mechanism:** Hardcoded `prereg-rules-v1` tag

**Required for amendment:**
1. Update `config/discovery/prereg_rules.yaml`
2. Update `config/discovery/prereg_ratification_manifest.yaml` with new digest
3. **UNRESOLVED:** Tag versioning mechanism (see Deficiency 7)

---

## Digest Computation (Cannot Complete Until Deficiencies Resolved)

The exact proposed digest cannot be computed until:
- Deficiency 5 (S8 endpoint) is resolved
- The final prereg_rules.yaml content is determined

---

## Current Blockers Summary

| Deficiency | Item | Status | Blocks |
|------------|------|--------|--------|
| 1 | S2 LWRP completeness | UNRESOLVED | Option A ratification |
| 2 | S2 basin coverage | UNRESOLVED | S2 gauge universe ratification |
| 3 | S4 physical nodes | UNRESOLVED | S4 node table ratification |
| 4 | S4 source attribution | UNRESOLVED | S4 evidence fidelity |
| 5 | S8 null endpoint | UNRESOLVED | S8 source registration |
| 6 | S7 taxonomy | UNRESOLVED | S7 exact scope |
| 7 | N3 amendment mechanism | UNRESOLVED | Tag versioning governance |

---

## State

```
CURRENT_MAIN = 3647265
PR39_HEAD = 648f6f2be49be4ed852e1e8e87970a7c7d2fc9e0
ADAPTER_ONLY_PRS = #35(frozen), #36(frozen), #37(frozen)
SCIENCE_GATES = S2_LWRP(INCOMPLETE), S2_BASIN(INCOMPLETE), S4_NODES(INCOMPLETE)
GOVERNANCE_GATE = N3_AMENDMENT_MECHANISM(UNDEFINED)
REVIEW_GATES = HUMAN_RATIFICATION(NOT_MATURE)
NEXT_ACTION = Resolve Deficiencies 1-7 before requesting human ratification
```

`D5_COMPLETE_UNIVERSE_READY = FALSE`

---

## Marker

`M1_POST_LOCK1_AMENDMENT_PACKET_EXACTNESS_INCOMPLETE`
`HUMAN_GATE_NOT_MATURE`

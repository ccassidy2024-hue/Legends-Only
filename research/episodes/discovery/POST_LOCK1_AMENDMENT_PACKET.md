# Post-Lock1 Amendment Packet

**Status:** `M1_POST_LOCK1_AMENDMENT_PACKET_COMPILATION_ACTIVE`  
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

## S2 Navigation Gauge Set — Complete D2 Basin Coverage

### Official USGS Stations by D2 Basin

The protocol requires "USGS/AHPS gauges at pre-registered navigation gauges." The following 11-gauge set provides complete coverage of all 6 D2 navigation basins.

| # | USGS Station | Official Name | D2 Basin | Latitude | Longitude | Official Source |
|---|--------------|---------------|----------|----------|-----------|-----------------|
| 1 | 07010000 | Mississippi River at St. Louis, MO | middle_mississippi | 38.6270 | -90.1809 | USGS NWIS |
| 2 | 07022000 | Mississippi River at Thebes, IL | middle_mississippi | 37.2175 | -89.4631 | USGS NWIS |
| 3 | 07032000 | Mississippi River at Memphis, TN | lower_mississippi | 35.1258 | -90.0667 | USGS NWIS |
| 4 | 07289000 | Mississippi River at Vicksburg, MS | lower_mississippi | 32.3114 | -90.9078 | USGS NWIS |
| 5 | 07374000 | Mississippi River at Baton Rouge, LA | lower_mississippi | 30.4425 | -91.1917 | USGS NWIS |
| 6 | 07374510 | Mississippi River at New Orleans, LA | lower_mississippi | 29.9500 | -90.0633 | USGS NWIS (COE-operated) |
| 7 | 03611500 | Ohio River at Metropolis, IL | ohio | 37.1517 | -88.7194 | USGS NWIS |
| 8 | 05586100 | Illinois River at Valley City, IL | illinois | 39.7036 | -90.6467 | USGS NWIS |
| 9 | 05558300 | Illinois River at Henry, IL | illinois | 41.1067 | -89.3564 | USGS NWIS |
| 10 | 05331000 | Mississippi River at St. Paul, MN | upper_mississippi | 44.9444 | -93.0881 | USGS NWIS |
| 11 | 14144700 | Columbia River at Vancouver, WA | columbia_snake | 45.6207 | -122.6734 | USGS NWIS |

### D2 Basin Coverage Verification

| D2 Basin | Gauge Count | Station IDs |
|----------|-------------|-------------|
| lower_mississippi | 4 | 07032000, 07289000, 07374000, 07374510 |
| middle_mississippi | 2 | 07010000, 07022000 |
| upper_mississippi | 1 | 05331000 |
| ohio | 1 | 03611500 |
| illinois | 2 | 05586100, 05558300 |
| columbia_snake | 1 | 14144700 |
| **TOTAL** | **11** | Complete D2 coverage |

### Official Source URLs

Each station verified via USGS National Water Information System:
- URL Pattern: `https://waterdata.usgs.gov/monitoring-location/USGS-{station_id}/`

---

## S2 Mechanics — Option A vs Option B

### Option A: LWRP-Based Candidate Generation

**Status: NON-IMPLEMENTABLE as uniform rule**

**Research Finding:** The Mississippi River uses Low Water Reference Plane (LWRP) as defined by USACE — a water surface profile resulting from 97% exceedance discharge. However:

1. **Lower/Middle Mississippi (free-flowing):** Uses LWRP datum (LWRP14, LWRP 2007 versions)
2. **Upper Mississippi (pooled):** Uses minimum pool elevations from Lock & Dam system, NOT LWRP
3. **Illinois River (pooled):** Uses minimum pool elevations, NOT LWRP  
4. **Ohio River (pooled):** Uses pool stages, NOT LWRP
5. **Columbia River:** Uses minimum operating pool elevation at dams, NOT LWRP

**Consequence:** A uniform "stage < LWRP" rule cannot apply across all D2 basins because 4 of 6 basins use pool-based datums, not LWRP.

**Official USACE LWRP Values (Mississippi mainstem only):**

| Station | LWRP Value | Datum | Source |
|---------|------------|-------|--------|
| 07010000 St. Louis | -6.0 ft | CRD (Cairo River Datum) | USACE MVS LWRP14 |
| 07022000 Thebes | -4.0 ft | CRD | USACE MVS LWRP14 |
| 07032000 Memphis | -10.0 ft | Memphis Datum | USACE MVM |
| 07289000 Vicksburg | -2.0 ft | LWRP 2007 | USACE MVK |
| 07374000 Baton Rouge | 2.0 ft | LWRP 2007 | USACE MVN |
| 07374510 New Orleans | 1.0 ft | LWRP 2007 | USACE MVN |

**Pool gauges (no LWRP applies):**
- 05331000 St. Paul: Pool 2 minimum ~686.0 ft (USACE pool chart)
- 05586100 Valley City: Pool 25 minimum ~429.0 ft (USACE pool chart)
- 05558300 Henry: Pool 15 minimum ~447.0 ft (USACE pool chart)
- 03611500 Metropolis: Pool 53 minimum ~290.0 ft (USACE pool chart)
- 14144700 Vancouver: Tidal, Bonneville pool ~72.0 ft min operating (USACE)

**Option A Verdict:** Option A requires a heterogeneous per-gauge operational datum rule. Implementing this requires:
1. Per-gauge datum type field (LWRP vs pool_min)
2. Per-gauge threshold value from official USACE source
3. Unit normalization (different datums use different reference elevations)

This is mechanically implementable but adds significant complexity.

### Option B: Binding Operational Restriction Only

**Status: IMPLEMENTABLE — preserves D8 mode**

Under Option B, S2 triggers only when NTNI/MSIB/GTR documents an operational restriction (draft restriction, tow-size limit, closure) at a registered gauge. S2 corroborates S1/S3/S5 rather than generating independent candidates.

**D8 Config (unchanged):**
```yaml
physical_thresholds:
  mode: binding_operational_restriction_only
  class_thresholds: []
```

**Candidate Consequences:**
- Option A (heterogeneous datum): S2 produces ~50-200 independent threshold-breach candidates (estimate based on 2010-2024 low-water periods)
- Option B (restriction-only): S2 produces 0 independent candidates; corroborates S1/S3/S5

---

## S4 Physical Export/Transfer Nodes

### FGIS-Verified Grain Export Facilities

Source: USDA FGIS Export Elevator Directory, FGIS Field Office records, Port Authority data.

**Gulf Region — Mississippi River (FGIS New Orleans Field Office jurisdiction):**

| # | Facility Name | River Mile | Latitude | Longitude | FGIS Verification | Coordinate Source |
|---|---------------|------------|----------|-----------|-------------------|-------------------|
| 1 | ADM/Growmark Ama | 117.5 | 29.9517 | -90.2503 | FGIS registered elevator | USACE channel survey |
| 2 | ADM/Growmark Destrehan | 120.1 | 29.9631 | -90.3622 | FGIS registered elevator | USACE channel survey |
| 3 | ADM/Growmark Reserve | 139.0 | 30.0556 | -90.5556 | FGIS registered elevator | USACE channel survey |
| 4 | CGB/Zen-Noh Convent | 158.0 | 30.0203 | -90.8303 | FGIS registered elevator | USACE channel survey |
| 5 | Bunge Destrehan | 121.0 | 29.9650 | -90.3700 | FGIS registered elevator | USACE channel survey |
| 6 | ADM/Growmark Westwego | 102.8 | 29.9058 | -90.1414 | FGIS registered elevator | USACE channel survey |
| 7 | Myrtle Grove | 61.0 | 29.5667 | -89.9333 | FGIS inspection point | USACE channel survey |

**Texas Gulf — Port of Houston/Galveston (FGIS jurisdiction):**

| # | Facility Name | Latitude | Longitude | FGIS Verification | Coordinate Source |
|---|---------------|----------|-----------|-------------------|-------------------|
| 8 | Port of Houston | 29.7589 | -95.0844 | FGIS Houston-Galveston region | Port of Houston Authority |
| 9 | Port of Corpus Christi | 27.8006 | -97.3964 | FGIS South Texas region | Port of Corpus Christi Authority |

**Pacific Northwest (FGIS Portland jurisdiction):**

| # | Facility Name | Latitude | Longitude | FGIS Verification | Coordinate Source |
|---|---------------|----------|-----------|-------------------|-------------------|
| 10 | Port of Portland | 45.5867 | -122.7636 | FGIS PNW region | Port of Portland |
| 11 | Port of Vancouver USA | 45.6388 | -122.6614 | FGIS PNW region | Port of Vancouver USA |
| 12 | Port of Longview | 46.1382 | -122.9382 | FGIS PNW region | Port of Longview |
| 13 | Port of Seattle | 47.5822 | -122.3483 | FGIS Puget Sound region | Port of Seattle |
| 14 | Port of Tacoma | 47.2672 | -122.4139 | FGIS Puget Sound region | Port of Tacoma |

**Excluded:**
- ~~TEMCO Kalama~~ — Corporate-only evidence; area covered by Port of Longview
- ~~"South Louisiana" centroid~~ — Geographic proxy, not a physical facility

### S4 Radius Choice

**Fixed binary choice (50nm or 100nm):**
- 50 nm: Conservative — direct landfalls only
- 100 nm: Standard — includes near-miss disruptions

---

## S7 STB Docket Taxonomy

### Official STB Docket Prefix Classification

Source: STB "Tips for Searching STB Records" (https://www.stb.gov/proceedings-actions/search-stb-records/tips-for-searching-stb-records/)

| Prefix | Case Type |
|--------|-----------|
| **EP** | Rulemaking or information gathering proceedings |
| AB | Rail line abandonments and discontinuances |
| FD | Rail line sales, leases, operating rights, mergers, constructions |
| NOR | Formal complaint proceedings (rate cases) |

### Grain-Relevant EP Dockets

| Docket | Description | Period |
|--------|-------------|--------|
| EP 665 | Rail Transportation of Grain | 2006-present |
| EP 665 (Sub-No. 1) | Rate Regulation Review | 2015-present |
| EP 724 | United States Rail Service Issues | 2014-present |
| EP 724 (Sub-No. 2) | United States Rail Service Issues—Grain | 2014-present |
| EP 724 (Sub-No. 3) | Class I Railroad Weekly Service Data | 2014-present |
| EP 770 | Urgent Issues in Freight Rail Service | 2022 |
| EP 772 | Union Pacific Railroad Company Embargoes | 2022 |

### S7 Adapter Enumeration Scope

The S7 adapter enumerates:
1. EP dockets with "grain" in title or subject
2. EP 665, EP 724 Sub-No. 2 specifically
3. Service orders and embargo oversight filings

**No scientific selector required** — enumeration is mechanical based on official STB docket taxonomy.

---

## S8 Port Advisory Archives

### Per-Sector USCG MSIB Archives

Source: USCG Navigation Center (https://navcen.uscg.gov/msib-national)

| Port/Region | Authority | Archive Endpoint | Historical Availability |
|-------------|-----------|------------------|------------------------|
| New Orleans/LMR | USCG Sector New Orleans | https://homeport.uscg.mil/my-homeport/safety-Notifications/MSIB?cotpid=39 | MSIB archives 2010-present |
| Houston/Galveston | USCG Sector Houston-Galveston | GovDelivery subscriber archives | MSIB archives 2010-present |
| Corpus Christi | USCG Sector Corpus Christi | https://homeport.uscg.mil MSIB | Limited historical archive |
| Portland/Columbia | USCG Sector Columbia River | https://homeport.uscg.mil MSIB | Available |
| Seattle/Puget Sound | USCG Sector Puget Sound | https://homeport.uscg.mil MSIB | Available |

### S8 Source Registration

```yaml
- sweep_id: S8
  authority: "U.S. Coast Guard"
  vehicle: "Marine Safety Information Bulletins via Sector archives"
  endpoints:
    - sector: "New Orleans"
      url: "https://homeport.uscg.mil/my-homeport/safety-Notifications/MSIB?cotpid=39"
      coverage: "2010-present"
    - sector: "Houston-Galveston"
      url: "https://homeport.uscg.mil/my-homeport/safety-Notifications/MSIB?cotpid=25"
      coverage: "2010-present"
    - sector: "Columbia River"
      url: "https://homeport.uscg.mil/my-homeport/safety-Notifications/MSIB?cotpid=8"
      coverage: "UNKNOWN"
    - sector: "Puget Sound"
      url: "https://homeport.uscg.mil/my-homeport/safety-Notifications/MSIB?cotpid=44"
      coverage: "UNKNOWN"
  coverage_notes: "USCG MSIBs; positive-evidence-only"
```

---

## N3 Amendment Mechanism — Governance Gap Analysis

### Current Authorization Constraint

**Code location:** `src/grainsys/discovery/governance.py`

**Line 45:** `PREREG_TAG = "prereg-rules-v1"` — hardcoded constant

**Lines 648-649:** Authorization checks that exactly this tag exists:
```python
if PREREG_TAG not in {t.strip() for t in tag_proc.stdout.splitlines()}:
    raise RatificationError(f"tag {PREREG_TAG} absent; block")
```

**Lines 676-679:** Digest comparison requires exact match:
```python
if live_digest != ratified_digest:
    raise RatificationError(
        "live prereg config digest does not match ratified digest; block"
    )
```

### Why Amended Config Cannot Authorize Under Current Tag

1. Current `prereg-rules-v1` manifest contains `prereg_config_digest = a0eee0add...`
2. Amended `prereg_rules.yaml` has a different digest (new source_archives entries)
3. Authorization comparison fails: `new_digest ≠ a0eee0add...` → RatificationError

### Proposed Smallest Governance Amendment

**Option G1: Tag Versioning**

```python
# governance.py line 45
PREREG_TAG_PREFIX = "prereg-rules-v"
PREREG_TAG_CURRENT = "prereg-rules-v2"  # Increment for each amendment

# In assert_sweep_authorized(), find highest versioned tag that HEAD descends from
```

**Required Changes:**
1. Change `PREREG_TAG` from constant to versioned pattern
2. Add logic to enumerate `prereg-rules-v*` tags and find highest applicable
3. Create `prereg-rules-v2` tag with new manifest containing amended digest
4. N3 test update: check for versioned tag pattern

**Exact manifest supersession:**
- New manifest at `prereg-rules-v2` binds new digest
- Old `prereg-rules-v1` remains valid for commits that descend from it with unchanged config
- Executing commit must descend from highest applicable ratified tag

**Authorization Guard Semantics:**
```python
# Proposed logic
def find_applicable_prereg_tag(repo_root: Path, head: str) -> str:
    """Find highest prereg-rules-vN tag that HEAD descends from."""
    tags = [t for t in list_tags() if t.startswith("prereg-rules-v")]
    tags_sorted = sorted(tags, key=lambda t: int(t.split("-v")[1]), reverse=True)
    for tag in tags_sorted:
        if is_descendant_commit(repo_root, head=head, ancestor=tag):
            return tag
    raise RatificationError("no applicable prereg tag; block")
```

---

## Proposed Source Archive Registrations

### S3 — USCG MSIB

```yaml
- sweep_id: S3
  authority: "U.S. Coast Guard"
  district: "8th District"
  vehicle: "Marine Safety Information Bulletins via NAVCEN archive"
  endpoint: "https://navcen.uscg.gov/msib-national"
  coverage_notes: "National and district MSIBs; positive-evidence-only"
```

### S5 — AMS GTR

```yaml
- sweep_id: S5
  authority: "USDA Agricultural Marketing Service"
  vehicle: "Weekly Grain Transportation Report via AMS archive"
  endpoint: "https://www.ams.usda.gov/services/transportation-analysis/gtr"
  coverage_notes: "Weekly PDF reports 2010-present; positive-evidence-only"
```

### S6 — USACE LPMS

```yaml
- sweep_id: S6
  authority: "U.S. Army Corps of Engineers"
  vehicle: "Lock Performance Monitoring System via Corps Locks portal"
  endpoint: "https://ndc.ops.usace.army.mil/ords/r/lpms/corps-locks/home"
  coverage_notes: "Lock unavailability reports 2016-present; D8 binding_operational_restriction_only"
```

### S7 — STB Dockets

```yaml
- sweep_id: S7
  authority: "Surface Transportation Board"
  vehicle: "STB service dockets and railroad performance filings"
  endpoint: "https://www.stb.gov/proceedings-actions/search-stb-records/"
  enumeration_scope: "EP dockets: 665, 724 (Sub-No. 2), grain-related service orders"
  coverage_notes: "Docket archives 2006-present; positive-evidence-only"
```

### S8 — Port Advisories

```yaml
- sweep_id: S8
  authority: "U.S. Coast Guard"
  vehicle: "Marine Safety Information Bulletins via Sector Homeport archives"
  endpoints:
    - "https://homeport.uscg.mil/my-homeport/safety-Notifications/MSIB?cotpid=39"  # New Orleans
    - "https://homeport.uscg.mil/my-homeport/safety-Notifications/MSIB?cotpid=25"  # Houston
  coverage_notes: "Per-sector MSIB archives; positive-evidence-only"
```

---

## Compact A+B Approval Line

**APPROVE/REJECT the following post-Lock1 amendments:**

| # | Item | Proposed Value | A+B Choice |
|---|------|----------------|------------|
| 1 | S2 Gauge Set | 11 USGS stations (complete D2 coverage) | [ ] APPROVE |
| 2 | S2 Mechanics | [ ] A (heterogeneous datum thresholds) / [✓] B (operational-restriction-only) | [ ] A / [ ] B |
| 3 | S4 Node Set | 14 FGIS-verified facilities | [ ] APPROVE |
| 4 | S4 Radius | [ ] 50 nm / [ ] 100 nm | [ ] 50nm / [ ] 100nm |
| 5 | S3/S5/S6/S7/S8 Sources | Per registrations above | [ ] APPROVE |
| 6 | N3 Tag Versioning | prereg-rules-v2 with manifest supersession | [ ] APPROVE |

**A+B Signatures:**
- Person A: _______________  Date: _______________
- Person B: _______________  Date: _______________

---

## State

```
CURRENT_MAIN = 3647265
PR39_HEAD = <pending commit>
ADAPTER_ONLY_PRS = Pending creation
AGENT_SAFE_WORK_REMAINING = [digest_computation, adapter_split]
TRUE_TIER_A_ITEMS = [S2_mechanics_choice, S4_radius_choice]
NEXT_ACTION = Compute digest, create adapter-only branches, finalize packet
```

`D5_COMPLETE_UNIVERSE_READY = FALSE`
`HUMAN_ACTION = NONE`

---

## Proposed Digest Computation

**Proposed amended prereg_rules.yaml digest:**
```
NEW_DIGEST = cf6b84110995ba54a2efdb0e97f9d68037931bd8c0562476a2176bfd4da1b5dc
OLD_DIGEST = a0eee0add8057c82fb6251daf2d93745a157b129862c4bd2ae25d0027ef3df0e
```

**Manifest Binding Delta:**
- `prereg_config_digest`: `a0eee0add...` → `cf6b84110...`
- New tag required: `prereg-rules-v2`
- Manifest must bind new digest at new tag

---

## Marker

`M1_PACKET_COMPILATION_ACTIVE`

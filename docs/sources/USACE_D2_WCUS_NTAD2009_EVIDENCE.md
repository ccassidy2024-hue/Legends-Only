# D2 official-source evidence: WCUS Cargo and NTAD2009

- **Checked:** 2026-08-24
- **Purpose:** evidence for the still-governed D2 execution inputs
- **Decision status:** factual census only; this record does not choose `R`,
  freeze a topology profile, create registry/crosswalk rows, or execute D2
  membership

## Authorities and source surfaces

The U.S. Army Corps of Engineers Waterborne Commerce Statistics Center
(WCSC) states that it collects vessel, tonnage, commodity, origin, and
destination information. Its official Cargo collection describes the annual
Manuscript Cargo files as yearly waterway/commodity/traffic publications.

- WCSC: <https://www.iwr.usace.army.mil/About/Technical-Centers/WCSC-Waterborne-Commerce-Statistics-Center/>
- Cargo collection parent: <https://usace.contentdm.oclc.org/digital/collection/p16021coll2/id/1814/>
- Cargo description: <https://usace.contentdm.oclc.org/digital/api/collection/p16021coll2/id/1671/download>

The official 2009 National Transportation Atlas Database (NTAD2009) is a
Bureau of Transportation Statistics archive. Its Navigable Waterway Network
is the USACE network and includes a link shapefile plus its nodal shapefile.

- NTAD2009 record: <https://rosap.ntl.bts.gov/view/dot/7541>
- Frozen download: <https://rosap.ntl.bts.gov/view/dot/7541/dot_7541_DS1.zip>
- USACE NWN description: <https://usace.contentdm.oclc.org/digital/api/collection/p16021coll2/id/1450/download>

## Pre-sample annual Cargo artifacts

The ten annual all-regions files below are separately downloadable official
artifacts. Each contains exactly one `CompletedYear`, the seven publication
grain codes listed below, and no negative or nonnumeric observed `ShortTons`
rows. Counts exclude the header. Hashes are SHA-256 over the downloaded bytes.

| Year | CONTENTdm ID | Rows | Bytes | SHA-256 |
|---:|---:|---:|---:|---|
| 2000 | 1797 | 61,389 | 4,233,249 | `67f0c4ae7bd386199b8147c02c9dba2d0ee73b06a304bf7f2ef4bedb9bad84ba` |
| 2001 | 1798 | 58,126 | 4,012,844 | `98c82e1c420c09c0a0c2ca2bfdee21e853701f15a960061fd853e6eb153960bc` |
| 2002 | 1799 | 57,905 | 3,991,004 | `ef9f50bc4585661e13451a862d0239b61d262e379399e04a578620f69266a7ab` |
| 2003 | 1800 | 57,761 | 3,980,666 | `cc61163f90fc814913fc3d91ee4cbf4ebc44a1b839dbd22633d0d7dee637e1b6` |
| 2004 | 1801 | 58,837 | 4,054,146 | `61afa4dcab2240ad1461a76f8c33e574b6b51f9a94dc17294d4ba537ab77b382` |
| 2005 | 1802 | 58,273 | 4,013,274 | `ed288a7e7b8712fb27319aba87e4c981794d1bdf5a6de0926db862f196723a80` |
| 2006 | 1803 | 56,217 | 3,874,659 | `7b18471a8e20492d10ff8d9d38843e19bb40da5450fe416ece0dc462f1a99bca` |
| 2007 | 1804 | 56,018 | 3,860,284 | `df7214b495ea092fe8791665e8752e194bedc8774606951ed51078dd431336b9` |
| 2008 | 1805 | 46,885 | 3,272,729 | `96d6d07d4ce5326e3a1b73de94f30ccaee1d28b9e8a3bbcf0d12dab3a248e64d` |
| 2009 | 1806 | 45,019 | 3,142,761 | `801fb1ee8cecaafc427f1919bcb666653d4021952674a9580918029c51f0d5fa` |

The deterministic annual schema is:

`RegionCode, RegionName, WaterwayCode, WaterwayName, TrafficCode,
TrafficName, CommodityCode, CommodityName, Allo1Code, In/Out/Thru,
Allo2Code, Up/Down, ShortTons, TonMiles, CompletedYear`.

Observed source-defined traffic classes are Overseas Imports, Overseas
Exports, Canadian Imports, Canadian Exports, Coastwise, Lakewise, Internal,
Intraport, and Intraterritory. The observed allocation/direction classes are
Inbound Receiving, Outbound Shipping, Local, and Thru, paired where applicable
with Port, Upbound/East/North, or Downbound/West/South. ADR-0006 requires all
of these source-defined classes; none may be selected for favorable direction.

### Commodity representation

The official `Select master_commodity` workbook supports this
master-to-publication mapping:

| Ratified master code | Source concept | Cargo publication code | Cargo publication name |
|---:|---|---:|---|
| 4100 | wheat | 6241 | Wheat |
| 4200 | rice | 6442 | Rice |
| 4300 | barley | 6443 | Barley & Rye |
| 4400 | maize/corn | 6344 | Corn |
| 4510 | rye | 6443 | Barley & Rye |
| 4520 | oats | 6445 | Oats |
| 4530 | grain sorghum | 6447 | Sorghum Grains |
| 22220 | soybeans | 6522 | Soybeans |

The official cross-reference workbook is CONTENTdm item 2107, downloaded from
<https://usace.contentdm.oclc.org/digital/api/collection/p16021coll2/id/2107/download>.
It contains one 663-row-by-6-column table (including the header) with schema
`COMMODITY, COMM_NAME, PUB_GROUP, PUB_NAME, PMS_GROUP, PMS_NAME`. Its SHA-256
is `bfd7d01f942abb07bccba1bf86bb6882cea52f31f56a8ae0379c68d74dfa1f43`.
The eight mappings above are the exact rows for master codes 4100, 4200,
4300, 4400, 4510, 4520, 4530, and 22220.

The 2009 WCUS commodity-classification publication independently lists publication codes
6241, 6344, 6442, 6443, 6445, 6447, and 6522 with those names:
<https://usace.contentdm.oclc.org/digital/api/collection/p16021coll2/id/136/download>.

### Aggregate artifact is not an annual-artifact substitute

The official combined 2000–2016 workbook (CONTENTdm ID 1796; SHA-256
`32a61faa23838379266b481c749fb6bd222674ddaadf1a8d9ec97b233ce1dbc5`)
matches the separate annual row counts for 2000–2005 but differs for
2006–2009. The combined counts are respectively 57,357, 57,049, 47,835, and
45,774, versus annual-file counts 56,217, 56,018, 46,885, and 45,019.

That is direct evidence of artifact/version differences. ADR-0006 calls for
the exact annual Cargo artifacts, so an implementation must bind the chosen
annual files individually and must not silently substitute the aggregate
workbook or reconcile the differences by convenience.

## Strictly pre-sample topology artifact

The complete official NTAD2009 archive is 690,531,059 bytes. Its SHA-512 is
`560ef05ff3fdf296d8e22228aeff472d74d145711163d786a2253125a322ddcac5d8f7343d2e05a8432dd6b5510d899cc1c74a4cf04a65f60d808217e2e5328f`,
which exactly matches the checksum published on the BTS record.

The nested `NTAD2009_SHP_Final_Navigable_Waterway_Network_2009.zip` has
SHA-256 `301184844cb8aa065adaacbf8639ce42bf97445991631bbf08acb570c6752f48`.
Its link and node DBF hashes are:

- `waterway_2009/waterway.dbf`:
  `675b0354f292e18163df258a79cfee1e107a3058c27a1765211b9ff3dff2fbf5`
- `waterway_2009/waterwaynd.dbf`:
  `260ff5f309b22cf9f6ed108db8443aef49b5b63b7998c15e52716c6d4a255f82`

Verified structural facts:

- 6,905 unique link `FEATURID` rows and 6,285 unique node `FEATURID` rows;
- every link has `ANODE` and `BNODE`, and every endpoint resolves to a node;
- no self-loop;
- 12 unordered endpoint pairs have parallel links;
- every link carries `VERSION = 09`;
- link sources/types comprise 5,610 `CORPS`, 955 `VANDERBILT`, 43 `ORNL`,
  55 `CWIS`, 240 `LOCK`, and 2 `NONCOMM` rows.

These facts make NTAD2009 a viable strictly pre-2010 topology input. They do
not decide whether the mode profile retains all source link types, restricts
to the `CORPS` subset, how it treats parallel links for degree, or how the
already-approved basin/export-node scope maps onto graph atoms. Those are
explicit profile choices and must be frozen before registry generation.

## Exact remaining D2 decision boundary

The evidence supports, but does not itself ratify, a full pre-sample
reference interval of calendar years 2000–2009 and NTAD2009 as the topology
vintage. The still-required A+B record must state exactly:

1. `R` start and end;
2. retained NTAD2009 link types and domestic/non-U.S. treatment;
3. parallel-link degree semantics;
4. the exact mapping from approved basin/export-node scope to retained graph
   links/nodes;
5. whether all registry atoms or only scope-mapped atoms are considered by
   the membership constructor.

Only after those values are exact may implementation generate and review the
versioned registry, source-geography crosswalk, and deterministic
ELIGIBLE/INELIGIBLE/UNKNOWN membership output.

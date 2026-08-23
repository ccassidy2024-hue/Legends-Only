# PERSON A — D3/D7 LOCK-1 DECISION-READINESS AUDIT

**Report to ChatGPT / Person A**  
**Audit mode:** read-only  
**Date:** 2026-08-23  
**Main SHA audited:** `ee76ca1ac7c32502b87d37d9a2e47f9939f054b6` (matches expected; `origin/main` identical)

---

## 1. Exact main SHA audited

`ee76ca1ac7c32502b87d37d9a2e47f9939f054b6`

---

## 2. Exact source-family inventory

Families the repo presently contemplates (no live `prereg_rules.yaml`; no committed coverage rows; `source_archives: []` in template only).

| Registry ID | Name / vehicle (as contemplated) | Where defined |
|---|---|---|
| **S1** | USACE navigation notices — district/year enumeration; vehicles include Notices to Navigation Interests (NTNI), lock/closure notices, channel/dredging notices, district navigation bulletins | `EPISODE_PROTOCOL.md` §J; `config.py` `PROTOCOL_SWEEP_FAMILIES`; Tier 1 §C.1 |
| **S1 sub-scope (unregistered)** | Per-district endpoints; multi-vehicle rule; division/national USACE vehicles in/out of S1 | `PHASE0_MISSING_DECISIONS.md` D3 |
| **S1 / SWL–MKARNS** (handoff; **not in repo files**) | Southwestern Division / MKARNS navigation-notice vehicle | Person A handoff only |
| **S1 / national NTNI retrospective** (handoff + Tier 1 naming) | Corps NTNI as anchor vehicle | Tier 1 §C.1; handoff |
| **S2** | USGS/AHPS gauges at preregistered navigation gauges | §J Phase 1 |
| **S3** | USCG MSIBs and closure notices (distinct from LNM) | §J Phase 1 |
| **S4** | NHC storm archive (landfalls within preregistered radius) | §J Phase 1 |
| **S5** | AMS Grain Transportation Report (GTR) archive | §J Phase 1; Tier 1 §C.1 |
| **S6** | USACE LPMS outage/queue records | §J Phase 1 |
| **S7** | STB service dockets / rail performance filings | §J Phase 1 |
| **S8** | Port authority / terminal operator notice archives | §J Phase 1 |
| **USCG LNM** | Local Notices to Mariners — supplementary only | ADR-0005 P6; R-014 |
| **Tier-1 corroboration (non-sweep)** | USGS NWIS, NOAA/NWS (non-NHC), USDA FGIS Export Inspections, USDA FAS shipment facts, FRA, state DOT, railroad/port operator notices | §C.1 (evidence/severity, not S1–S8 rows) |

**Not registered anywhere in repo:** live district list, endpoints, coverage census files, `absence_generating_families` values, catalog series YAMLs for GTR/Export Inspections/ESMIS.

---

## 3. D3 classification table

Classifications restricted to the four allowed values. “Zero as swept-zero” = under current evidence, could `records_matched: 0` ever be admissible over net covered scope?

| Family | Current identifier | Authority | Intended role | Candidate discovery? | Absence-generating? | Supplementary only? | Hist. release/vintage req. | Coverage evidence | Completeness evidence | Known gaps | Zero → swept-zero? | Unresolved promotion blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **S1** (USACE nav notices) | `S1` (family only) | USACE | Primary Phase-1 sweep | Yes (when registered) | **Not designated** | No | Anchor: public-on date (P1); sweep scope needs explicit endpoints | **NOT ESTABLISHED in repo** | **NOT ESTABLISHED** | **NOT ESTABLISHED** | **No** | No D3 `source_archives` rows; no census commits; multi-vehicle rule unset |
| **S1 / SWL–MKARNS** | None | USACE SWL (handoff) | S1 sub-vehicle | Via S1 only | No | No | Same as S1 | Handoff: partial page census; **not in repo** | **NOT ESTABLISHED** | 864/902 targets unverified (handoff) | **No** | No authoritative completeness/retention/migration/revision statement; FOIA status unknown in repo |
| **S1 / national NTNI** | None (Tier 1 name only) | USACE | S1 vehicle + Tier-1 anchor | Via S1 | No | No | P1 anchor rules | **NOT ESTABLISHED** | **NOT ESTABLISHED** | **NOT ESTABLISHED** | **No** | Exhaustive historical coverage not proved |
| **S2** | `S2` | USGS/AHPS | Gauge-threshold sweep | Yes | Not designated | No | N/A for discovery; gauge values for anchors need Tier-1 docs | **NOT ESTABLISHED** | **NOT ESTABLISHED** | Gauge list unset (D3-like) | **No** | No preregistered gauge list/endpoints |
| **S3** | `S3` | USCG | MSIB/closure sweep | Yes | Not designated | No | P1 for anchors | **NOT ESTABLISHED** | **NOT ESTABLISHED** | **NOT ESTABLISHED** | **No** | No district/endpoints registered |
| **S4** | `S4` | NHC/NOAA | Storm landfall sweep | Yes | Not designated | No | N/A | **NOT ESTABLISHED** | **NOT ESTABLISHED** | Radius/nodes unset | **No** | No preregistered radius/export nodes |
| **S5 (GTR)** | `S5` | USDA AMS | Weekly GTR keyword sweep | Yes | Not designated | No | **P4/R-012** for leakage-sensitive as-of use of GTR tables | **NOT ESTABLISHED** | **NOT ESTABLISHED** | **NOT ESTABLISHED** | **No** | No archive endpoint; no release/vintage catalog |
| **S6** | `S6` | USACE | LPMS threshold sweep | Yes | Not designated | No | Tier-1 operational records | **NOT ESTABLISHED** | **NOT ESTABLISHED** | D8 thresholds unset | **No** | No LPMS endpoints/thresholds |
| **S7** | `S7` | STB | Rail service sweep | Yes | Not designated | No | Tier-1 dockets | **NOT ESTABLISHED** | **NOT ESTABLISHED** | **NOT ESTABLISHED** | **No** | No endpoints |
| **S8** | `S8` | Port/terminal ops | Terminal notice sweep | Yes | Not designated | No | Tier-1 notices | **NOT ESTABLISHED** | **NOT ESTABLISHED** | **NOT ESTABLISHED** | **No** | No port/terminal archive list |
| **USCG LNM** | None (classified in ADR-0005) | USCG | Corroboration / public-by knowability | **No** (independent) | **No** | **Yes** | P1 (public-by ≠ public-on) | **NOT ESTABLISHED** | Non-exhaustive by contract | N/A | **No** | P6/R-014: promotion requires future D3-compatible ADR |
| **FGIS Export Inspections** | None (Tier 1 only) | USDA FGIS | Severity D4 / corroboration | No | No | De facto yes | **P4/R-012** for historical as-of | No catalog series | **NOT ESTABLISHED** | **NOT ESTABLISHED** | **No** | Not an S-family; no vintage/release catalog in repo |

**Summary:** No family is `ABSENCE_GENERATING_READY`. LNM is `SUPPLEMENTARY_ONLY` (ratified). S1/SWL/NTNI and all S2–S8 are `BLOCKED_UNVERIFIED` or `POSITIVE_EVIDENCE_ONLY` (SWL/NTNI retrospective per handoff; **not contradicted by repo, also not recorded in repo**).

**D3 status:** **PARTIALLY_READY** — architecture and fail-closed loaders exist; **no registrable endpoint inventory**.

---

## 4. D7 readiness table

| Layer | Status | Evidence |
|---|---|---|
| **1. Ratified zero semantics (P5/R-013)** | **DONE** | ADR-0005 accepted; R-013; `coverage.py` docstring + tests |
| **2. Source-family exposure facts** | **MISSING** | No coverage YAML rows; no `earliest_available`/`latest_available` commits; SWL handoff not in repo |
| **3. Live config values** | **UNCHOSEN** | Template nulls: `records_dir`, `gap_policy_notes`, `absence_generating_families: []`, `source_identity_keys: []` |
| **4. Mechanical implementation present** | **PARTIAL** | `CoverageRecord`, N2 state machine, `compute_covered_exposure`, P5 clip/subtract/gap logic, template, config validation |
| **5. Mechanical implementation missing** | **GAPS** | No bulk loader from `records_dir`; no network enumeration in `sweep.py` (by design); per-event-class masks not wired (ADR-0003 future obligation); optional P5 cross-row overlap checks not implemented (ADR-0005 staging note) |

**Per absence-generating family (none designated yet; if S1 were promoted hypothetically):**

| Field | S1 (hypothetical) | All other S2–S8 |
|---|---|---|
| `scope_start` | UNKNOWN | UNKNOWN |
| `scope_end` | UNKNOWN | UNKNOWN |
| `known gap intervals` | NOT ESTABLISHED | NOT ESTABLISHED |
| `authority / vehicle identity` | USACE / notices (generic); SWL vehicle NOT ESTABLISHED | UNKNOWN |
| `endpoint / archive identity` | NOT ESTABLISHED | NOT ESTABLISHED |
| `enumeration exhaustive for net scope?` | **NOT ESTABLISHED** (SWL: 864/902 unverified per handoff) | NOT ESTABLISHED |
| `zero matches admissible?` | **No** under current evidence | **No** |

**D7 status:** **PARTIALLY_READY** — semantics frozen; **exposure facts and config choices absent**.

---

## 5. D1 dependency finding

D1 (`sample_start` / `sample_end`) depends on:

1. **Per-family coverage census** — archive existence, `earliest_available` / `latest_available` (history bounds, not sweep scope), explicit `absent`/`unknown` rows (R-013).
2. **D3 registration** — which archives are in-scope for discovery (not which events occurred).
3. **D7 designation** — which families are absence-generating vs supplementary; `source_identity_keys`; gap intervals.
4. **ADR-0003 D1 architecture** — global period + per-source/class masks; uncovered interval = unknown exposure, not zero; source late-start does not force global start backward; regime denominators use covered exposure.
5. **NOT permitted inputs** — eventful years, candidate yield, market outcomes, statistical power.

**Coexistence rule (already written):** One mandatory global `sample_start`/`sample_end`; masks supplement; eligibility/exposure clipped to intersection of global period and applicable family/class coverage; families starting after global start contribute nothing before their coverage start.

**One weak family and global start:** Global start must **not** be chosen from remembered events or yield. A weak or late-starting family should **narrow eligible exposure** (unknown before its coverage start), not silently define global start unless A+B explicitly preregister that aggregation rule. ADR-0003 item 6 requires explicit covered-exposure or common-mask definition for cross-source comparability.

**Facts frozen before honest `sample_start`/`sample_end` computation:**

- D3 `source_archives` (all endpoints)
- D7 coverage census rows for every registered archive
- `absence_generating_families` and `source_identity_keys`
- Affirmatively known gap intervals
- Rule for aggregating multi-family coverage into global bounds (union vs intersection for start/end — **not yet chosen as a live config rule**)
- Per-class masks (future; not mechanical yet)

---

## 6. D1_RULE_READY / D1_RULE_NOT_READY

**D1_RULE_READY** (architectural rule only)

**Rationale:** ADR-0003 §D1 architecture (items 1–8) and `PHASE0_MISSING_DECISIONS.md` §D1 state the outcome-blind, coverage-based rule without dates. The rule can be frozen as policy now.

**Caveat:** ADR-0003 remains **`proposed`** (not `accepted`). Concrete `sample_start`/`sample_end` values are **not computable honestly** until D3/D7 exposure facts exist. Architecture ≠ dates.

---

## 7–8. D3 / D7 ballot readiness

| Decision | Verdict | Rationale |
|---|---|---|
| **D3 architecture** | **BALLOT_READY** | Registration **contract** can be frozen: required fields per archive, multi-vehicle policy, supplementary vs sweep scope, no endpoint invention. |
| **D3 values** | **NOT_BALLOT_READY** | No verified endpoint/district inventory in repo. |
| **D7 architecture** | **BALLOT_READY** | P5 already ratified; ballot can freeze identity-key choice, gap-row requirements, explicit non-promotion of unverified families. |
| **D7 values** | **NOT_BALLOT_READY** | `absence_generating_families`, `gap_policy_notes`, and per-family scope/gaps cannot be chosen without evidence. |

---

## 9. Draft ballot(s) (architecture-only; no invented values)

### D3 architecture ballot (A+B)

> **We ratify the D3 registration contract for Phase-1 discovery archives:**
> 1. Every in-scope archive is one explicit row in `source_archives` with nonempty `sweep_id`, `authority`, `district`, `vehicle`, `endpoint`.
> 2. Duplicate archive identities are forbidden.
> 3. Where a district publishes through multiple vehicles, we preregister either all in-scope vehicles or an explicit exclusion rule before any sweep.
> 4. Division/national USACE vehicles are in or out of S1 by explicit registration, not ad hoc discovery.
> 5. Supplementary families (including USCG LNM under ADR-0005 P6) do not mint candidates and are not absence-generating unless separately promoted by ADR.
> 6. No district, endpoint, URL, or date is chosen in this ballot; those are evidence commits after coverage census.
> 7. SWL/MKARNS, national NTNI retrospective, and all other S1 sub-vehicles remain **unpromoted** until completeness/retention/revision evidence closes D7 dependencies.

### D7 architecture ballot (A+B)

> **We ratify the D7 coverage contract binding P5/R-013:**
> 1. `coverage.absent_must_be_explicit: true` remains mandatory.
> 2. Known gaps are interval-scoped `absent`/`unknown` rows with both `scope_start` and `scope_end`; never prose-only.
> 3. `records_matched: 0` is admissible only for families listed in `absence_generating_families` after exhaustive enumeration over net covered scope; it never proves real-world absence.
> 4. `earliest_available`/`latest_available` are archive-history bounds only and must not substitute for sweep scope.
> 5. We choose `source_identity_keys` explicitly (proposal: `authority`, `district`, `vehicle`, `endpoint`, `source_family`) before any family promotion.
> 6. No family enters `absence_generating_families` until authority-written completeness/retention/migration/revision evidence exists for that family’s net scope.
> 7. Until such evidence exists, all current families remain positive-evidence or blocked; zero-match interpretation stays inadmissible.

---

## 10. SWL inquiry status

**UNKNOWN_FROM_REPO**

No committed memo, ticket, letter, FOIA reference, or email log concerning an SWL Operations / records / FOIA completeness inquiry. Person A handoff census numbers (91 pages, 902 IDs, etc.) are **not present** in canonical files at this SHA.

**Minimum questions any authoritative response must answer before SWL could be considered for retrospective absence generation:**

1. Inclusion scope — what notices are in the online/archive register?
2. Historical completeness — is the public archive a complete issued-notice register?
3. Pre-2012 / migration behavior — what happened to notices before the oldest visible item?
4. Retention / purge practice — are notices removed, expired, or consolidated?
5. Target retrievability — are all issued notice IDs reachable at stable endpoints?
6. Revision / correction / supersession identity — how are amendments/cancellations represented?
7. Existence of an authoritative issued-notice register distinct from the web archive UI.

Nonresponse is not evidence.

---

## 11. Release / vintage / absence capability matrix

| Source | A: candidate/event fact | B: public_anchor / knowability | C: historical as-of value + release_ts (P4) | D: absence exposure |
|---|---|---|---|---|
| **Export Inspections (FGIS)** | Tier 1 for throughput facts (§D.4) | Tier 1 if contemporaneous publication evidenced | **NOT ESTABLISHED** — no series catalog; P4 normative only; no mechanical enforcement | **No** — not an S-family; not absence-generating |
| **GTR (AMS)** | S5 sweep + Tier 1 severity | Tier 1 tables + press for knowability | **NOT ESTABLISHED** — no catalog/release clock audit in repo; ESMIS analog noted for API timestamps | **No** until S5 registered + exhaustive scope proved |
| **USCG LNM** | **No** independent discovery (P6) | **Yes** — supplementary public-by | **NOT ESTABLISHED** for leakage paths | **No** (P6/R-014) |
| **USACE notices / SWL** | **Yes** when S1 registered + sweep hit | **Yes** — Tier 1 anchor vehicle (P1 applies to republication) | **NOT ESTABLISHED** — revision/supersession identity unknown for SWL | **No** — POSITIVE_EVIDENCE_ONLY / BLOCKED; 864/902 unverified (handoff) |
| **National NTNI** | Via S1 when registered | **Yes** — Tier 1 anchor | **NOT ESTABLISHED** — exhaustive historical coverage unproved | **No** — POSITIVE_EVIDENCE_ONLY unless exhaustive coverage proved |

**Firewall:** Evidence for A does not imply B, C, or D. ADR-0005 P4 is normative; code does not yet enforce release identity.

---

## 12. Top external evidence priorities (max 5)

| Rank | Unresolved fact | Evidence type | Unlocks | Negative answer meaning |
|---|---|---|---|---|
| **1** | SWL/MKARNS archive completeness, retention, migration, revision identity | Written response from USACE SWL Operations / records / FOIA | D3 S1 sub-registration; D7 S1 absence promotion; D1 coverage lower bound for MKARNS vehicle | SWL remains POSITIVE_EVIDENCE_ONLY forever under current contract; zero matches inadmissible |
| **2** | National NTNI — is public archive an exhaustive issued-notice register for retrospective use? | USACE national navigation/publications authority statement | D3 multi-vehicle S1 rule; NTNI retrospective classification | NTNI stays POSITIVE_EVIDENCE_ONLY; cannot support absence denominators |
| **3** | Per-district USACE navigation-notice vehicles and stable archive endpoints | Official district publication index + coverage census (metadata only) | D3 `source_archives` population; D7 census template fills | District excluded or `unknown` coverage; no swept-zero |
| **4** | GTR + Export Inspections release/vintage identity for historical as-of | USDA AMS/FGIS publication documentation + verified release calendar | P4 mechanical ingest; D13 grid; severity D4 vintage safety | Historical as-of use of those series remains blocked/leakage-sensitive |
| **5** | ESMIS / USDA API timestamp semantics | Official USDA documentation on publication instant | P4 enforcement; `panel.synthesise_release_ts` policy (separate PR) | Date-only retention; no fabricated intraday `release_ts` |

---

## 13. Exact remaining blockers

1. **No live `prereg_rules.yaml`** — all D1–D7 values null/empty.
2. **No `prereg-rules-v1` tag** — sweeps blocked by N3 (`test_n3_real_repo_refuses_live_sweep_execution`).
3. **ADR-0003 still `proposed`** — load-bearing for N3 but not accepted.
4. **ADR-0002 still `proposed`** — Phase 0 open-item package unresolved.
5. **D3:** zero committed `source_archives`; multi-vehicle and division/national scope rules unset.
6. **D7:** zero coverage census rows; `absence_generating_families` empty; SWL completeness unproved; no FOIA status in repo.
7. **D1 dates:** cannot be computed without items 5–6.
8. **D4, D5, D6, D8–D11, D13** still open (Lock-1 beyond D3/D7).
9. **P4:** normative only — no ingest enforcement for GTR/Export Inspections/ESMIS.
10. **Person A SWL census (handoff) not persisted** in repo — adjudication relies on out-of-repo knowledge unless committed as coverage metadata.

---

## 14. Whether any repo edit is warranted now

**No edit required to complete this audit.**

*(This memo exists only to share the completed read-only audit report.)*

---

## 15. If an edit is warranted, describe only (DO NOT implement)

1. **Coverage census artifact** (metadata only): commit SWL/MKARNS page-enumeration facts from Person A handoff under `research/episodes/discovery/coverage/` using `_template.yaml` — `present`/`unknown` rows, no notice content, no swept-zero claims.
2. **SWL inquiry log**: one-line `SENT|NOT_SENT|date` record when inquiry is dispatched (no inference from silence).
3. **Accept ADR-0003** when A+B ready — unblocks N3 path together with live prereg file.
4. **Catalog series YAMLs** for GTR / Export Inspections when publication/release audit completes (P4 path).

---

## 16. Task H — no-go / contamination review

Confirmed this audit did **not**:

- enumerate a new real source archive for discovery
- run a source matcher or produce source hits
- create candidates or episodes
- select sample dates, corridors, or keywords
- inspect market outcomes
- infer absence from missing content
- execute D2 membership
- modify PR #12 or its branches
- edit, commit, push, branch, or open a PR *during the audit itself*

Actions taken during audit: `git fetch origin`; read canonical docs/code; grep for source references.

---

## Final verdict

**READY_FOR_CHATGPT_ADJUDICATION**

**Bottom line for Person A:** D3 and D7 **architecture** can go to an A+B ballot now without pretending historical coverage is complete. **Values** (endpoints, absence-generating family list, gap intervals, D1 dates) remain blocked until external evidence — especially SWL/MKARNS authority on completeness/retention/revision — is obtained and recorded as coverage metadata. No family may be promoted to `ABSENCE_GENERATING_READY` at this SHA. LNM stays `SUPPLEMENTARY_ONLY` by ratified contract.

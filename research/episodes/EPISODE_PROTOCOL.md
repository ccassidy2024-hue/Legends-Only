# Episode Candidate Research Protocol

**Milestone 1 — Episode Ledger pre-registration.**
Status: proposed. Governing decision record: `docs/decisions/0002-episode-preregistration.md`.

This document tells two researchers **how** to build 15–25 credible physical /
logistics stress episodes. It does not contain episodes. Populating the ledger
is a separate act, performed under these rules.

Machine-readable field spec: `research/episodes/episode_schema.yaml`
Worked fake example: `research/episodes/entries/EP-0000-000-example.yaml`
One-page admission test: `research/episodes/ADMISSION_CHECKLIST.md`
Validator: `python -m grainsys.episodes` (runs in `make all`)

---

## 0. The two locks

Everything here exists to enforce two ordering constraints. Violating either
invalidates the sample, and neither violation is detectable after the fact.

**Lock 1 — rules before candidates.**
Thresholds, corridors, sample period, severity cutpoints, event windows and
horizon sets are committed to git *before* the first candidate is written down.
Otherwise thresholds get tuned until the events you already remember qualify.

**Lock 2 — candidates before outcomes.**
No episode field, anchor, severity score, or accept/reject decision may be
informed by any market outcome. `market_outcomes_reviewed` stays `false` for
every entry until the ledger is frozen and tagged.

The second lock binds the **researchers' information set**, not just the file.
You cannot un-see a price chart. If you are accidentally exposed to a market
outcome for a candidate under consideration, log it in `outcome_exposure_log`
on that entry and hand the entry to the other researcher. This is not a
punishment; an honest exposure log is worth far more than a clean-looking one.

### Why this is the whole ballgame

`BLUEPRINT_REVIEW.md` §1 established that the effective sample size for this
project is the number of *independent episodes*, not the number of weekly rows.
That has two consequences most event studies get wrong:

1. Each admitted episode is worth roughly 4–6% of the total evidence in the
   project. One retrospectively-selected episode is not a rounding error.
2. The dominant failure mode is not "too few episodes." It is **false
   independence** — five manifestations of one shock counted as five episodes,
   producing standard errors that are too small by roughly √5.

The protocol is therefore deliberately biased toward exclusion. A 14-episode
ledger where every entry survives adversarial review is a better instrument
than a 25-episode ledger with six soft entries.

---

## A. Inclusion and exclusion rules

### A.1 Definition

> An **episode** is a dated interval during which a documented physical or
> operational constraint materially degraded the capability of a U.S. grain
> logistics corridor to move, load, transfer, or hold grain — where the onset
> can be anchored to a specific publicly observable date from primary sources.

Three load-bearing words:

- **Documented** — a physical state exists in a primary record, not in memory.
- **Capability** — the constraint binds on the physical system's capacity, not
  on the willingness of participants to transact at a price.
- **Onset** — there is a step, not a slope.

### A.2 Inclusion criteria (all six must hold)

| # | Criterion | Test |
|---|---|---|
| **I1** | **Physical nexus** | The constraint acts on grain-carrying infrastructure: navigable waterway, lock, port, export elevator, transfer terminal, rail line/service, or the vessels/equipment using them. |
| **I2** | **Operational materiality** | At least one *documented operational consequence*: closure, restriction, outage, embargo, queueing, capacity reduction, or a documented throughput decline. **A physical reading alone is never sufficient.** |
| **I3** | **Datability** | An anchor date is derivable from Tier 1/2 sources with `anchor_precision_days ≤ 7` (≤ 3 preferred). |
| **I4** | **Contemporaneous knowability** | The anchor-defining fact was publicly published at the time, via a named vehicle, with a date. |
| **I5** | **Independence** | Not a stage, echo, or sub-manifestation of an already-recorded episode (see §H). |
| **I6** | **Outcome blindness** | Discovered through a systematic source sweep, not through market memory; `market_outcomes_reviewed = false`. |

**On I2, the rule that does most of the work:** a gauge reading, a rainfall
anomaly, or a storm track is a *driver*, not an episode. Low water at a
navigation gauge becomes an episode only when a primary source documents an
operational response to it — a draft restriction, a tow-size limit, a closure,
a dredging notice, a documented barge-movement decline. Without this rule the
ledger silently becomes a weather index, and weather indices are exactly the
object that fails the exclusion restriction in `BLUEPRINT_REVIEW.md` §5.

### A.3 Candidate event classes

Controlled vocabulary for `event_class` (extend only by ADR):

| `event_class` | Covers |
|---|---|
| `low_water` | Low-stage navigation restrictions, draft/tow limits, groundings, dredging closures caused by low water |
| `high_water_flood` | High-stage restrictions, flood closures, levee/harbor events, current-speed restrictions |
| `lock_outage` | Lock/dam mechanical failure, gate failure, scheduled or emergency lock closure, chamber restriction |
| `channel_obstruction` | Groundings blocking channel, sunken barge/vessel, allision, bridge strike, dredge-related obstruction |
| `waterway_closure_other` | USCG safety closures not classified above (spills, security, ice) |
| `gulf_terminal_disruption` | Export elevator outage, fire/explosion, power loss, labor stoppage at terminal, force majeure |
| `hurricane_logistics` | Tropical system whose *logistics* consequences are the object (landfall near export/transfer infrastructure) |
| `rail_service_disruption` | Service crisis, embargo, derailment closing a grain lane, work stoppage, crew/power shortage |
| `port_infrastructure_outage` | Non-terminal port infrastructure: channel, anchorage, pilotage, ship-channel closure |
| `bridge_or_landside_outage` | Bridge closure/inspection, highway or landside access failure affecting grain flow |
| `ice_or_seasonal_closure` | Unscheduled ice closures and off-calendar Great Lakes / upper-river closures |
| `other_physical` | Anything else physical; requires ADR before use |

Note `hurricane_logistics` is defined by its *logistics* consequence. A storm
that devastated a growing region but left export infrastructure operating is
not an episode in this ledger; it is a crop-supply event and belongs nowhere in
this sample.

### A.4 Exclusion criteria

Reject if **any** apply (reason codes in §I):

- **X1** No documented operational consequence — driver only (`R3`).
- **X2** Anchor cannot be pinned within 7 days (`R1`).
- **X3** Only Tier 3 evidence, or Tier 1 sources materially contradict each other (`R2`, `R9`).
- **X4** The constraint develops without a step change over > 90 days (`R5` — regime, see §A.5).
- **X5** Subsumed by an existing episode (`R4`).
- **X6** Surfaced because of a remembered market move (`R6`).
- **X7** Constraint was not publicly knowable at the anchor (`R7`).
- **X8** Outside the pre-registered sample period or source coverage (`R10`).
- **X9** A first-order non-logistics shock occupies the same window such that no
  contrast exists (contamination class **D**) (`R8`).
- **X10** Any fabricated or unverifiable source (`R12` — see §L.5).

### A.5 One episode, several episodes, a regime, or unusable

Apply in order; the first rule that fires wins.

| Situation | Ruling | Recorded as |
|---|---|---|
| Continuous constraint, one driver, one corridor, never relieved for ≥ 21 consecutive days | **One episode** | Single entry; internal evolution in `stages[]` |
| Same driver and corridor, but a documented return to baseline operation for ≥ 21 days, then recurrence | **Two episodes**, same `cluster_id` | Two entries, `related_episode_ids` cross-linked |
| Same driver, two corridors with no shared infrastructure and independent operational status (e.g. Lower Mississippi and Columbia–Snake) | **Two episodes**, same `cluster_id` | Two entries; independence argued in writing |
| Same driver, two reaches of the same corridor | **One episode**, multi-geography | Scope becomes a severity dimension, not a second row |
| Constraint present > 90 days with no step onset, no single anchor, and no documented "before" state | **Regime, not episode** | `status: regime_context`; used as a control/state variable, never as an event |
| More than ~40% of the sample period is "in episode" for one class | **The class is a regime** | Redefine the class threshold by ADR; do not proceed |
| Anchor precision > 7 days, or the operational consequence cannot be dated at all | **Unusable** | `status: rejected`, reason `R1` |

The 21-day relief rule needs an operational definition: **relief** means a Tier 1
source documents restoration of unrestricted (or explicitly pre-episode
baseline) operation. Absence of further notices is *not* evidence of relief. If
relief cannot be documented, the episode is treated as continuing and
`end_date_basis` records why.

---

## B. Event anchor methodology

### B.1 The four dates, kept separate

Record all four when knowable. They answer different questions and conflating
them is the most common way an event study manufactures a "delayed reaction."

| Field | Definition | Knowable when? |
|---|---|---|
| `physical_onset` | The date the physical state actually crossed the constraint threshold | Often only ex post |
| `official_announcement` | First official notice by the operating authority (USACE notice, USCG MSIB, port/terminal notice) | Contemporaneous |
| `public_anchor` | **First date the constraining fact was publicly available** through any Tier 1/2 vehicle, with a timestamped document | Contemporaneous, by construction |
| `peak_severity_date` | Date of maximum documented physical severity | Usually ex post |

Plus `end_date` (documented relief) and `relief_confirmed_date` (when relief
became publicly known).

### B.2 Recommendation: `public_anchor` is primary t = 0

For the project's actual question — does the market underreact to information
about physical constraints? — `public_anchor` is the only defensible primary
anchor. Three reasons:

1. **It is the only anchor that cannot manufacture the finding.** If
   `physical_onset` precedes public knowledge by ten days, anchoring on onset
   inserts a ten-day "delay" into every response path before any behaviour
   occurs. Delayed underreaction is the hypothesis; it must not be baked into
   the clock.
2. **It matches the repo's existing information discipline.** `public_anchor`
   is the episode-level analogue of `release_ts` in `docs/decisions/0001`.
   Anchoring on `physical_onset` is look-ahead at the event level, and the
   panel builder's leakage protection cannot see it — `build_asof_panel` guards
   series vintages, not event dates. This is the one leakage channel the code
   does not cover, which is exactly why the rule lives here.
3. **It is the information set a participant actually had.** Storage,
   routing and shipping decisions respond to known constraints.

Retain the others as **pre-registered robustness anchors**, declared at freeze,
not chosen afterwards:

| Anchor | Use |
|---|---|
| `public_anchor` | **Primary.** All headline results. |
| `official_announcement` | Pure news-shock robustness; narrower and cleaner, but misses constraints that became known before officialdom acted |
| `physical_onset` | Physical-mechanism and instrument work (§E); the right clock for "did the river actually fall," the wrong clock for "did anyone know" |
| `peak_severity_date` | Dose-response / intensity robustness only |

Reporting on a non-primary anchor without declaring it at freeze is a
specification search. Pick the anchor set now; report all of them later.

### B.3 Anchor selection rule (mechanical, no market input)

> `public_anchor` = the earliest calendar date on which a document exists that
> (a) is Tier 1, or Tier 2 where no Tier 1 vehicle exists for the class;
> (b) was published on or before that date;
> (c) states either a binding operational restriction, or a physical value past
>     a **pre-registered** threshold together with an operational consequence; and
> (d) was publicly accessible at publication.

Tie-breaks, in order: earliest Tier 1 document → earliest document with an
explicit effective time → the operating authority's own notice over reportage.

Supporting fields:

- `public_anchor_precision` ∈ {`date`, `timestamp`} — what the primary source
  actually supports. If the source documents only `2022-10-05`, record
  `date` and leave `anchor_ts` null. **Never invent a midnight timestamp**
  merely because software prefers datetimes. If a primary source provides an
  exact publication timestamp (with timezone when known), record
  `timestamp` and store it in `anchor_ts`.
- `anchor_precision_days` ∈ {0, 1, 3, 7} — the width of the calendar-day window
  within which the anchor day is certain. Orthogonal to date-vs-timestamp.
  > 7 ⇒ reject (`R1`). 4–7 ⇒ `NEEDS REVIEW`.
- `anchor_basis` — one sentence naming the document that fixes the date.
- `anchor_source_ref` — pointer into `primary_sources`.
- `anchor_ts` — publication timestamp **only** when
  `public_anchor_precision == timestamp`; otherwise null.
- `anticipation_status` ∈ {`unscheduled`, `partially_anticipated`,
  `pre_announced_scheduled`}. A lock closure announced six months in advance is
  a real physical event with **no news content at the anchor**; pooling it with
  unscheduled failures attenuates every estimate toward zero. Scheduled events
  are admissible and useful — as a placebo/control group — but they are tagged
  and stratified, never silently pooled.

#### Mapping date-only / timestamp anchors into analysis windows (PRIMARY)

**Preregistered primary convention (conservative):**

- If `public_anchor_precision == date`: the event becomes usable at the **first
  analysis/panel anchor whose calendar date is STRICTLY AFTER**
  `public_anchor`. Do **not** interpret the date as midnight, noon, beginning-
  of-day, or end-of-day. In particular, if a date-only `public_anchor` falls on
  the same calendar date as a weekly analysis anchor, **do not** assume the
  information was available before that anchor — use the next eligible analysis
  anchor. Helper: `grainsys.episodes.first_usable_analysis_anchor`.
- If `public_anchor_precision == timestamp`: same-calendar-day use is permitted
  only when `anchor_ts <= analysis_anchor_ts` **and** the timestamp/timezone is
  actually supported by source evidence (`anchor_ts` is the public-anchor
  timestamp field).

Same-day / date-only mappings other than the rule above are **robustness
assumptions only**, must be explicitly labeled, and are **not** the
preregistered primary mapping. This mapping does not invent timestamps in the
ledger and does not change `panel.py`.

### B.4 Rules that keep the anchor honest

1. The anchor is fixed **before** severity is scored and **before** any
   contamination or substitution assessment.
2. The anchor is derived independently by both researchers (§K.3). Record
   `anchor_agreement` ∈ {`exact`, `within_precision`, `disagree`}. Disagreements
   are the single most informative error signal in the whole build.
3. **No anchor may be changed after freeze without an ADR** that states what
   changed, why, and re-runs every downstream result. An anchor edited after
   market data has been seen is an outcome-selected anchor, whatever the
   justification feels like at the time.
4. Never use "the week the story got picked up by the trade press" if an
   earlier Tier 1 notice exists. Press attention is partly an outcome.
5. If two candidate anchors sit either side of a weekend or holiday, take the
   earlier document date and let `anchor_precision_days` carry the uncertainty.
   Do not shift anchors onto trading days — that is an analysis-layer decision,
   and making it here couples the sample definition to market structure.

---

## C. Primary-source hierarchy

### C.1 Tiers

**Tier 1 — the operating or measuring authority's own contemporaneous record.**

- U.S. Army Corps of Engineers: Notices to Navigation Interests, lock status and
  closure notices, Lock Performance Monitoring System (LPMS) tonnage/queue data,
  channel and dredging notices, district navigation bulletins
- USGS: NWIS gauge stage and discharge
- NOAA / NWS: AHPS observed and forecast river stages, National Hurricane Center
  advisories and tropical cyclone reports, NCEI storm records
- U.S. Coast Guard: Marine Safety Information Bulletins, waterway closure and
  restriction notices, captain-of-the-port orders
- USDA AMS: Grain Transportation Report **data tables** (barged grain movements,
  lock delays, unload counts, secondary rail market), Transportation Situation
  updates
- USDA FGIS: export inspections by port region. USDA FAS where the physical
  claim is a shipment fact
- STB: rail service performance data and service-order dockets; FRA safety and
  incident records
- Port authorities, terminal operators, Class I railroads: official public
  notices, service advisories, embargo notices, public force-majeure statements
- State DOT / state water and emergency agencies: official closure orders

*Acceptable for:* every anchor date, every severity metric, geography,
infrastructure, duration, relief. In short — anything that becomes a number or
a date in the ledger.

**Tier 2 — reputable contemporaneous reporting with named sourcing.**

Reuters, Bloomberg, DTN/Progressive Farmer, AgriPulse, other established trade
press; regional news quoting named officials; industry bodies (NGFA, Waterways
Council, port associations); Federal Reserve district ag publications; academic
papers and USDA ERS/AMS retrospective studies.

*Acceptable for:* establishing that an event occurred and roughly when
(candidate generation); corroborating Tier 1; **contemporaneous public
knowability** — a dated news report is itself first-rate evidence for I4;
qualitative substitution and adaptation context; severity metrics **only** where
no Tier 1 vehicle exists for that class, flagged `source_confidence: medium`.

*Not acceptable for:* the anchor date when a Tier 1 document exists; any
severity metric a Tier 1 source publishes; superseding Tier 1 on a conflict.

**Tier 3 — everything else.**

Blogs, content aggregators, encyclopedias, undated web pages, retrospective
listicles, vendor marketing, unsourced summaries, and **all LLM output**.

*Acceptable for:* nothing. Tier 3 may be used **only** to locate Tier 1/2
documents, and is recorded in `discovery_trail`, never in `primary_sources` or
`secondary_sources`.

### C.2 Evidence rules

1. **Two-source rule.** Every accepted episode carries ≥ 2 *independent* Tier 1
   sources. Two documents from the same USACE district on the same notice are
   one source. If a class genuinely has only one Tier 1 vehicle, 1 Tier 1 + 2
   Tier 2 is permitted with `source_confidence: medium` and mandatory review.
2. **Quote-or-null.** Every factual field traces to a verbatim excerpt (≤ 75
   words) stored in the evidence pack. No quote ⇒ the field is `null`. This is
   the rule that makes LLM fabrication structurally impossible to launder into
   the ledger.
3. **A URL is not evidence.** Each source record carries publisher, title,
   identifier, URL, `retrieved_on`, `sha256` of the retrieved file, local
   archive path, and `supports` — the list of fields it substantiates. Link rot
   is certain over a 15-year sample; the quote and the hash are what survive.
4. **Archive outside git.** Snapshots live under `$GRAIN_DATA_ROOT/episodes/<episode_id>/`,
   consistent with `data/` being gitignored. The ledger stores hashes and
   quotes, not PDFs.
5. **Conflicts are recorded, not resolved silently.** Two Tier 1 sources
   disagreeing on a date is a `source_conflicts[]` entry and an automatic
   `NEEDS REVIEW`.

---

## D. Severity framework

### D.1 Recommendation: raw physical evidence **and** derived ordinal class

Both, with a strict division of labour:

- **Raw physical metrics** — record every metric in its native units with its
  own `as_of_date` and source (`severity_metrics[]`). These are the canonical
  severity evidence: river stage, draft restriction, lock closure duration,
  capacity offline, traffic backlog, tonnage restriction, operating condition,
  etc. Preserves information for continuous-treatment work later.
- **Derived ordinal class S0–S3** — assigned **only by committed code**, never
  typed by a human. Necessary because severity is not comparable across classes
  without a registered mapping. `severity_class` remains **null** until Phase 0
  registers reference distributions / cutpoints. Do not invent thresholds.

#### Contemporaneous vs ex-post descriptive classification

When a class is eventually computed:

- `severity_class_kind: contemporaneous` — classification uses only information
  available as of the episode's `public_anchor` (and metric `as_of_date`s on or
  before that anchor).
- `severity_class_kind: ex_post_descriptive` — classification may use
  full-sample physical history / post-episode observations. Allowed for
  description, **forbidden** to masquerade as contemporaneously known.

Full-sample percentile bands are `ex_post_descriptive` by default. The
validator errors if a class is labelled `contemporaneous` while any contributing
metric has `as_of_date` after `public_anchor`.

Deriving the class in code rather than by hand is the practical substitute for
blinding. The human records physical metrics; the algorithm assigns severity;
nobody's memory of "how big a deal it felt like" enters the score.

### D.2 The five dimensions

Each scored 0–3, summed to 0–15.

| Dim | Name | Measured by (class-specific, raw values recorded) |
|---|---|---|
| **D1** | **Magnitude** | Gauge stage vs. low water reference plane and its within-class historical percentile; draft restriction (ft); tow-size limit (barges/tow); terminal capacity offline; rail velocity/dwell deviation; cars offered vs. placed |
| **D2** | **Duration** | Days from anchor to documented relief; days of complete stoppage; days of partial restriction |
| **D3** | **Scope** | River miles affected; number of reaches/pools; number of locks; number of terminals or berths; number of corridors |
| **D4** | **Throughput impact** | Documented decline in barged grain tonnage; lock tonnage; queue length and average wait; tows/barges backlogged; inspections at affected port region |
| **D5** | **Restrictiveness** | Ordinal on documented operating condition: unrestricted → advisory → partial (draft/tow/daylight/one-way) → intermittent closure → full closure |

`severity_metrics[]` holds the raw records; `severity_subscores` holds D1–D5;
`severity_score` is their sum; `severity_class` is the band.

### D.3 Cutpoints: unregistered until a Phase 0 / ADR decision

`cutpoints_registered` remains **`false`**. Derived `severity_class` /
`severity_score` stay **null**. Raw physical severity metrics may be collected
during source research, but **no analytical severity classification is
authorized** until a later Phase 0 / ADR preregisters, at minimum:

- severity metric by episode class
- reference period
- as-of versus ex-post calculation
- cutpoints
- multidimensional combination rule
- missing-data treatment

Do **not** invent absolute thresholds or percentile cutpoints in this protocol
pass. When eventually registered, prefer class-specific physical history and
committed code over hand-typed classes (see §D.1).

### D.4 Prohibited severity inputs

Never, as a severity metric or as an input to one:

- Any futures price, spread, basis, or return
- **Barge freight rates** — the tempting one. AMS publishes them, they feel
  like logistics, and they are quoted in the same reports as tonnage. They are
  a *price*: endogenous, market-determined, and the direct input to the
  `spatial_residual` construct that `BLUEPRINT_REVIEW.md` §2 nominates as a
  study variable. Using a freight rate to grade severity would regress an
  outcome on a transform of itself.
- Cash bids, elevator bids, export premiums, ocean freight
- Trading-press commentary about how severe the market found the event
- Volume, open interest, positioning
- Any variable that a market participant sets

Physical quantities and operating conditions only. If you cannot tell whether a
metric is physical, ask whether it would still have the same value if the
futures market were closed that week. If not, it is a price.

---

## E. Contamination framework

### E.1 Why navigation basin ≠ growing region — the central identification issue

The project's causal claim depends on isolating a *transport capacity* channel.
Drought is a **common cause**: it lowers river stage and reduces yields and
moves prices, through three separate routes. If the same meteorological
anomaly drives both the instrument and the outcome, the exclusion restriction
fails outright and the estimated "logistics effect" is a supply effect wearing
a costume.

The escape is geographic. Mississippi navigation depends heavily on the Ohio
and Upper Mississippi basins; the corn and soybean belt has substantial but
imperfect overlap with those basins. Precipitation in the *navigation* basin
can plausibly affect barge capacity while being much weaker as a determinant of
national yield. That distinction — first raised in `BLUEPRINT_REVIEW.md` §5 —
is only usable later if the ledger records it **now**, per episode, in a
structured field. A ledger that logs "Midwest drought" as geography has
destroyed the information the instrument needs.

Hence two separate required fields, never merged:

- `navigation_basin[]` — controlled vocabulary of navigation basins/corridors
- `growing_region_overlap` ∈ {`none`, `minor`, `partial`, `substantial`} with
  written justification, plus `growing_regions[]` when overlap ≠ none

### E.2 Contamination classes

Assessed on two axes, each classified A–D.

`crop_contamination_class` — does the shock also move U.S. crop supply or
supply expectations?

| Class | Meaning | Typical shape |
|---|---|---|
| **A** | Clean | Mechanism is orthogonal to production. Equipment failure, allision, isolated infrastructure outage |
| **B** | Low | Weather-driven but the growing-region impact is documented as minor, or occurs at a crop stage with limited yield sensitivity |
| **C** | High | Shared meteorological driver plausibly moves both navigation and yields, or the event physically damages both logistics and local production |
| **D** | Irreducible | No contrast available: a first-order supply or non-logistics shock occupies the same window |

`macro_contamination_class` — same A–D scale for co-occurring non-crop shocks:
macro/monetary events, trade policy, export bans elsewhere, energy shocks,
Panama Canal restrictions, pandemic disruptions, other-origin supply events.

### E.3 Required contamination fields

- `crop_calendar_stage` at anchor ∈ {`pre_plant`, `planting`, `vegetative`,
  `pollination`, `grain_fill`, `harvest`, `post_harvest`}. The same weather has
  wildly different yield implications by stage; an October navigation drought
  and a July one are not the same object.
- `concurrent_shocks[]` — each with date, description, class, source. Populated
  from a **mechanical sweep** of a pre-registered list of shock types, not from
  memory.
- `contamination_direction` ∈ {`aggravating`, `attenuating`, `ambiguous`} — does
  the contaminating channel push the outcome the same way as the hypothesised
  logistics channel? Drought contamination is `aggravating`: it raises prices
  through the supply channel *and* constrains transport, so it **inflates** any
  apparent logistics effect. Signing the bias now lets you state later whether
  a positive finding is an upper bound.
- `contamination_rationale` — 2–4 sentences, mandatory for class C and D.

### E.4 Contamination gates sample membership, not admission

Contamination is a **stratification** variable, not a rejection reason (except
class D, which has no contrast at all). Rejecting on contamination invites the
judgment call to be made in whichever direction preserves the events you like.
Pre-register the split instead:

- **Sample P (primary)** — crop class ∈ {A, B} and macro class ∈ {A, B}
- **Sample X (extended)** — adds crop or macro class C
- **Excluded** — class D on either axis

Headline results run on Sample P. Sample X is the robustness check, and the
*difference* between them is itself evidence: if the effect exists only in
Sample X, you have found the drought channel, not the logistics channel.

Sample P will be small — quite possibly 6–10 episodes. That is the honest
sample size for this question, and `WORKFLOW.md` already names "fewer than 6
usable episodes" as a kill condition. Learning that at pre-registration, before
building the estimator, is the cheapest possible time to learn it.

---

## F. Substitution framework

### F.1 Availability now, usage only with evidence

At pre-registration you are documenting **what escape valves plausibly existed
at the time**, not which ones were used. Usage is a second-order behavioural
outcome — the object of Milestone 4+ — and inferring it now from flow data
would import outcome information into the sample definition.

Each channel therefore carries two fields:

- `available` ∈ {`yes`, `no`, `unknown`} — ex ante physical/structural
  plausibility, with a one-line `basis`
- `documented_use` ∈ {`not_assessed`, `documented`, `documented_absent`} —
  populated **only** from a contemporaneous Tier 1/2 statement that the shift
  did or did not occur; default `not_assessed`

Writing "grain shifted to rail" because tonnage moved is analysis, not
pre-registration. If a Tier 2 article from the event window quotes a shipper
saying they moved to rail, that is `documented`, cite it.

### F.2 Channels to assess (≥ 3 required, all recommended)

`alt_river_reach` · `alt_inland_waterway` (Illinois / Ohio / Arkansas /
Tennessee) · `rail_to_gulf` · `rail_to_pnw` · `truck_short_haul` ·
`pnw_export` · `alt_gulf_terminal` · `texas_gulf` · `great_lakes_seaway` ·
`storage_on_farm` · `storage_commercial` · `export_deferral` ·
`destination_switching` · `origin_substitution_south_america`

### F.3 Seasonal state — the part that makes substitution identifiable

Substitution availability is **state-dependent**, and that state-dependence is
what allows a later test to distinguish "the market ignored the shock" from
"the shock was absorbed." Record the state at anchor:

- `great_lakes_season_open` — the Seaway is closed in winter; the same shock in
  January and in July faces different escape valves
- `sa_export_season_active` — South American export capability is seasonal;
  origin substitution as a shock absorber is available in some months and not
  others
- `harvest_window` — on-farm storage as a buffer behaves differently during
  harvest delivery pressure than in mid-winter
- `concurrent_substitute_disruption` — if rail was *also* disrupted, the escape
  valve is shut. This both amplifies severity and flags contamination, and it
  is easy to miss because it lives in a different source family

### F.4 Fields

`substitution_channels[]` — one record per channel: `channel`, `available`,
`basis`, `documented_use`, `source_ref`, `notes`. Plus
`substitution_state` holding the seasonal fields above.

---
## G. Episode ledger schema

Authoritative machine-readable definition: `research/episodes/episode_schema.yaml`.
The table below is the human-readable rendering; on any discrepancy the YAML wins.

### G.1 Storage layout

Following the `catalog/series/*.yaml` precedent in `WORKFLOW.md` — one file per
record, because a single shared table is the guaranteed merge conflict and git
resolves tabular text badly enough to lose rows silently.

```text
research/episodes/
  EPISODE_PROTOCOL.md        this document
  ADMISSION_CHECKLIST.md     the one-page gate
  episode_schema.yaml        field spec (single source of truth)
  RULINGS.md                 append-only precedent log
  EPISODE_LEDGER.md          human-readable ledger; summary table generated
  entries/
    EP-0000-000-example.yaml fake worked example, never counted
    EP-YYYY-NNN-<slug>.yaml  one file per candidate, accepted or rejected
```

Rejected candidates **stay** as files with `status: rejected`. Deleting them
destroys the audit trail that lets a reviewer detect a selection pattern — the
rejects are how you check whether "unusable" quietly meant "undramatic."

The Markdown ledger's summary table is regenerated from the entries by
`python -m grainsys.episodes --write` between the generated-block markers, which
keeps the human-readable artifact reproducible from committed code
(`CLAUDE.md` hard rule 15).

### G.2 Fields

**Legend:** ● required for `status: accepted` · ○ optional · ◐ conditionally
required (condition stated) · ⚙ derived by code, never hand-entered.

#### Identity and lifecycle

| Field | Type | Req | Notes |
|---|---|---|---|
| `schema_version` | str | ● | e.g. `1.0`; validator refuses unknown versions |
| `episode_id` | str | ● | `EP-YYYY-NNN`, YYYY = anchor year; must match filename stem |
| `event_name` | str | ● | Short, physical, neutral. No market language |
| `slug` | str | ● | kebab-case, in filename |
| `status` | enum | ● | `draft` \| `needs_review` \| `accepted` \| `rejected` \| `superseded` \| `regime_context` |
| `event_class` | enum | ● | §A.3 vocabulary |
| `event_subclass` | str | ○ | Free text within class |
| `anticipation_status` | enum | ● | `unscheduled` \| `partially_anticipated` \| `pre_announced_scheduled` |
| `post_freeze` | bool | ● | `true` only for entries added after pre-registration freeze; requires ADR |

#### Timing

| Field | Type | Req | Notes |
|---|---|---|---|
| `public_anchor` | date | ● | **t = 0.** §B.2. Store as a date; do not invent midnight timestamps |
| `public_anchor_precision` | enum | ● | `date` \| `timestamp` — what the source actually supports |
| `anchor_precision_days` | int | ● | 0 \| 1 \| 3 \| 7. Calendar uncertainty; > 7 ⇒ reject |
| `anchor_basis` | str | ● | One sentence naming the fixing document |
| `anchor_source_ref` | str | ● | Key into `primary_sources` |
| `anchor_ts` | datetime | ◐ | Required iff `public_anchor_precision == timestamp`; else null |
| `physical_onset` | date | ◐ | Required when determinable from Tier 1 physical data |
| `official_announcement` | date | ◐ | Required when an official notice exists |
| `peak_severity_date` | date | ◐ | Required when a severity metric has a datable maximum |
| `end_date` | date | ◐ | Required unless `ongoing_at_sample_end: true` |
| `end_date_basis` | str | ● | How relief was established, or why it could not be |
| `relief_confirmed_date` | date | ○ | When relief became publicly known |
| `ongoing_at_sample_end` | bool | ● | Default `false` |
| `duration_days` | int | ⚙ | `end_date − public_anchor` |

#### Geography and physical mechanism

| Field | Type | Req | Notes |
|---|---|---|---|
| `navigation_basin` | list[enum] | ● | ≥ 1. Never merged with growing region |
| `river_reaches` | list[str] | ◐ | Required for waterway classes |
| `geography` | str | ● | Prose scope |
| `states` | list[str] | ● | Two-letter codes |
| `ports_or_nodes` | list[str] | ◐ | Required for terminal/port/rail classes |
| `growing_region_overlap` | enum | ● | `none` \| `minor` \| `partial` \| `substantial` |
| `growing_regions` | list[str] | ◐ | Required when overlap ≠ `none` |
| `affected_infrastructure` | list[str] | ● | Named locks, terminals, bridges, lines |
| `physical_mechanism` | str | ● | ≤ 150 words. What physically happened and what it prevented. No market language, no forecasts |

#### Severity

| Field | Type | Req | Notes |
|---|---|---|---|
| `severity_metrics` | list[obj] | ● | ≥ 2 **raw physical** records: `dimension`, `name`, `value`, `units`, `as_of_date`, `source_ref`, `quote_ref` |
| `severity_subscores` | obj | ⚙ | `d1_magnitude` … `d5_restrictiveness`, each 0–3 or null |
| `severity_score` | int | ⚙ | 0–15; null until Phase 0 cutpoints registered |
| `severity_class` | enum | ⚙ | `S0`–`S3`; null until cutpoints registered |
| `severity_class_kind` | enum | ⚙ | `contemporaneous` \| `ex_post_descriptive` \| null |
| `severity_completeness` | float | ⚙ | Share of dimensions with evidence; low ⇒ review |

#### Sources

| Field | Type | Req | Notes |
|---|---|---|---|
| `primary_sources` | list[obj] | ● | ≥ 2 independent Tier 1 (§C.2). Each: `ref`, `tier`, `publisher`, `title`, `identifier`, `url`, `retrieved_on`, `sha256`, `archive_path`, `quote`, `supports[]` |
| `secondary_sources` | list[obj] | ○ | Same shape, Tier 2 |
| `discovery_trail` | list[obj] | ● | How the candidate was found: `origin` ∈ `sweep` \| `llm` \| `press` \| `colleague` \| `memory`, with `detail`. `memory` ⇒ automatic review |
| `source_conflicts` | list[obj] | ○ | Any Tier 1 disagreement; presence ⇒ `needs_review` |
| `source_confidence` | enum | ● | `high` \| `medium` \| `low`; `low` cannot be `accepted` |

#### Contamination

| Field | Type | Req | Notes |
|---|---|---|---|
| `crop_contamination_class` | enum | ● | A \| B \| C \| D |
| `macro_contamination_class` | enum | ● | A \| B \| C \| D |
| `contamination_rationale` | str | ◐ | Required for C or D on either axis |
| `contamination_direction` | enum | ● | `aggravating` \| `attenuating` \| `ambiguous` |
| `crop_calendar_stage` | enum | ● | §E.3 vocabulary |
| `concurrent_shocks` | list[obj] | ● | May be empty **only** after a documented sweep; `sweep_performed` must be `true` |
| `sample_membership` | enum | ⚙ | `primary` \| `extended` \| `excluded` (§E.4) |

#### Substitution

| Field | Type | Req | Notes |
|---|---|---|---|
| `substitution_channels` | list[obj] | ● | ≥ 3 assessed; each `channel`, `available`, `basis`, `documented_use`, `source_ref` |
| `substitution_state` | obj | ● | `great_lakes_season_open`, `sa_export_season_active`, `harvest_window`, `concurrent_substitute_disruption` |

#### Knowability and independence

| Field | Type | Req | Notes |
|---|---|---|---|
| `publicly_knowable_at_anchor` | bool | ● | Must be `true` to accept |
| `publication_vehicle` | str | ● | Named vehicle that carried the fact |
| `knowability_evidence_ref` | str | ● | Pointer to the dated document |
| `episode_independence_notes` | str | ● | Why this is not a stage/echo of another entry |
| `driver_class` | str | ● | Broad causal-driver category (grows deliberately; not a giant premature enum) |
| `underlying_driver_id` | str | ● | Stable id for the underlying physical shock |
| `cluster_id` | str | ● | Statistical dependence grouping. **Default = `underlying_driver_id`** unless a documented independence/dependence ruling says otherwise |
| `parent_episode_id` | str \| null | ● | Null unless a child entry |
| `related_episode_ids` | list[str] | ● | May be empty |
| `dedup_rule_applied` | str | ● | Which §A.5/§H rule produced this partition |

#### Governance

| Field | Type | Req | Notes |
|---|---|---|---|
| `market_outcomes_reviewed` | bool | ● | **Must be `false`** pre-freeze; validator fails the build otherwise |
| `outcome_exposure_log` | list[obj] | ● | May be empty. Any accidental exposure: date, what was seen, by whom |
| `recorded_by` | str | ● | `A` \| `B` |
| `recorded_date` | date | ● | |
| `reviewed_by` | str | ◐ | Required for `accepted`/`rejected`; must differ from `recorded_by` |
| `reviewed_date` | date | ◐ | Same condition |
| `anchor_agreement` | enum | ◐ | `exact` \| `within_precision` \| `disagree`; required at review |
| `decision` | enum | ● | `accept` \| `reject` \| `review` |
| `decision_reasons` | list[enum] | ◐ | Required for `reject`/`review`; codes from §I |
| `researcher_notes` | str | ○ | Free text |
| `preregistration_frozen_at` | datetime \| null | ⚙ | Set by the freeze process |
| `freeze_commit` | str \| null | ⚙ | Git SHA at freeze |
| `content_hash` | str | ⚙ | Hash of substantive fields; detects post-freeze edits |

### G.3 Required-field summary

**Minimum to be `accepted`:** identity block · `public_anchor` +
`public_anchor_precision` + `anchor_precision_days` ≤ 7 + `anchor_basis` +
`anchor_source_ref` · `end_date` or `ongoing_at_sample_end` + `end_date_basis` ·
`navigation_basin` · `growing_region_overlap` · `affected_infrastructure` ·
`physical_mechanism` · ≥ 2 `severity_metrics` with source refs · ≥ 2 Tier 1
`primary_sources` with quotes and hashes · both contamination classes +
direction + crop stage + swept `concurrent_shocks` · ≥ 3
`substitution_channels` + `substitution_state` ·
`publicly_knowable_at_anchor: true` + vehicle + evidence ·
`episode_independence_notes` + `driver_class` + `underlying_driver_id` +
`cluster_id` + `dedup_rule_applied` · `recorded_by` ≠ `reviewed_by` ·
`source_confidence` ≠ `low` · `market_outcomes_reviewed: false`.

Everything else is optional or derived. If a required field cannot be filled
from evidence, the correct outcome is `needs_review` and then probably
`rejected` — never a plausible-looking guess.

---

## H. Duplicate and overlapping-event rules

False independence inflates precision without inflating evidence. With N ≈ 20,
counting one shock five times understates standard errors by roughly √5 and
turns a null into a "finding."

### H.1 Rules, applied in order

| # | Rule |
|---|---|
| **H1** | **Same driver + same corridor + no documented ≥ 21-day relief ⇒ ONE episode.** Internal evolution goes in `stages[]`, not new entries |
| **H2** | **Storm and its aftermath are one episode.** A hurricane followed by weeks of terminal downtime is one entry whose duration is long. Downtime is a severity dimension, not a second observation |
| **H3** | **Repeated closures within one river event are one episode.** The count of closures is a D3/D5 severity input. Five lock closures during one low-water period are five metrics and one episode |
| **H4** | **Multi-region, one driver ⇒ separate entries only if operationally independent** — different navigation basin, no shared infrastructure, independently documented operating status. Otherwise one multi-geography entry |
| **H5** | **Genuinely distinct secondary failure ⇒ child entry** with `parent_episode_id`, its own anchor and its own mechanism. **Only one of parent/child may enter the primary sample** — default the parent |
| **H6** | **Two episodes in one corridor in one crop year ⇒ mandatory review**, shared `cluster_id`, and written justification. Their errors are correlated whatever the calendar says |
| **H7** | **≤ 1 episode per (corridor, driver) per 60 days** without a written exception in `RULINGS.md` |
| **H8** | **Staged evolution stays inside one entry.** `stages[]` records date, description, source. Splitting stages is the most common way a ledger reaches 25 entries that are really 9 |
| **H9** | **Relief must be documented** to end an episode. Silence is not relief |

### H.2 The independence audit at freeze (mandatory)

Before the ledger is frozen, compute and record in `EPISODE_LEDGER.md`:

**Primary sample-size reporting (inferential):**

- `N_episodes` — accepted episode **rows**
- `N_independent_driver_clusters` — distinct `cluster_id`

**Descriptive metadata (not competing effective-N):**

- `N_underlying_drivers` — distinct `underlying_driver_id`

Taxonomy:

- `driver_class` — broad causal-driver category (grows as sweeps identify
  legitimate classes; no giant premature controlled vocabulary)
- `underlying_driver_id` — stable id for the underlying physical shock
- `cluster_id` — statistical dependence grouping for later inference.
  **Default: `cluster_id = underlying_driver_id`**, unless a documented
  independence/dependence ruling in `RULINGS.md` / the entry notes justifies
  otherwise

There is **no privileged ratio threshold**. Physically distinct episode rows are
**preserved** even when they share an underlying driver or cluster. Downstream
methods may use cluster-aware inference where justified; do not automatically
delete rows merely because they share a driver.

---

## I. Accept / reject / review

### I.1 States

| State | Meaning | Requirements |
|---|---|---|
| **ACCEPT** | Enters the ledger as sample | Every §G.3 required field · both researchers agree · admission checklist fully passed |
| **REJECT** | Recorded and retained, not in sample | ≥ 1 reason code · reviewer sign-off · file kept with `status: rejected` |
| **NEEDS REVIEW** | Unresolved | Reason code(s) + the specific evidence that would resolve it |

**Default is REJECT.** Burden of proof sits with inclusion. An entry that
cannot be resolved by the freeze deadline is rejected, not admitted "provisionally."

### I.2 Reason codes

| Code | Reason |
|---|---|
| `R1` | Anchor undatable — `anchor_precision_days` > 7 |
| `R2` | Insufficient source tier — no Tier 1, or the two-source rule fails |
| `R3` | No documented material grain-logistics consequence (driver only) |
| `R4` | Duplicate or subsumed by another entry |
| `R5` | Too gradual — regime, not event |
| `R6` | Outcome-selected — surfaced via market memory, no independent sweep confirmation |
| `R7` | Not publicly knowable at the anchor |
| `R8` | Irreducible contamination (class D on either axis) |
| `R9` | Physical evidence insufficient or Tier 1 sources contradictory |
| `R10` | Outside pre-registered sample period or source coverage |
| `R11` | Proposed post-freeze without an ADR |
| `R12` | Fabricated or unverifiable source (§L.5) |
| `R13` | Reviewer disagreement unresolved at freeze deadline |

### I.3 Automatic NEEDS REVIEW triggers

Fired by the validator, not by judgment:

- `anchor_precision_days` ∈ {4…7}, or `anchor_agreement: disagree`
- Single Tier 1 source, or `source_confidence: medium`
- Contamination class C or D on either axis
- `severity_score` within 1 point of a class boundary
- `severity_completeness` below the pre-registered floor
- `discovery_trail.origin` includes `memory` or `llm` with no `sweep` confirmation
- Two accepted entries sharing a `cluster_id` (H6)
- Any `source_conflicts` entry
- `market_outcomes_reviewed: true` before freeze — this one **fails the build**,
  it is not a review item

### I.4 Resolution

Reviews are resolved synchronously in the Monday session (`WORKFLOW.md` §4),
with no market data open. Every resolution is written to `RULINGS.md` as
precedent: situation, ruling, rule invoked, date. The second time a similar
edge case appears, it is decided by lookup rather than by re-argument — which
is how two people avoid drifting into two standards.

---

## J. Research workflow

Target: 15–25 accepted episodes from roughly 60–120 raw candidates. Budget
50–70 person-hours across two people. That estimate is deliberately not
optimistic; the evidence pack is most of the work.

### Phase 0 — Pre-register the rules (before any candidate). ~2–3 h, together

Commit, then tag:

- Sample period and corridor list
- `event_class` vocabulary and the physical thresholds per class
- Severity dimensions, percentile reference period, cutpoint rule, band edges
- Anchor rule and the robustness anchor set
- Contamination classes and the Sample P / Sample X split
- **Event window and horizon set** for later analysis (e.g. h = 0…26 weeks) —
  pre-registering the window now is what stops it being chosen later to fit
- Target count, and the kill condition (< 6 usable ⇒ the question is
  unanswerable with this data; say so and stop)

Output: ADR-0002, committed, tagged `prereg-rules-v1`. **No candidate may be
written down before this tag exists.**

### Phase 1 — Mechanical candidate sweeps. ~6–10 h, A leads

The single most important step. Candidates come from **systematically sweeping
a source**, never from recall.

Why: human and LLM recall of grain-logistics events is filtered through market
salience. You remember the years the market moved. Building a candidate list
from memory therefore selects on the outcome before you have looked at a single
price, and no amount of later care removes that.

Sweep protocol — for each source family, enumerate the whole archive across the
sample period and record every hit mechanically:

| Sweep | Source family | Mechanism |
|---|---|---|
| S1 | USACE navigation notices, by district, by year | Enumerate the archive; keyword-filter for closure/restriction/draft/dredge |
| S2 | USGS/AHPS gauges at pre-registered navigation gauges | Programmatic threshold breach detection over the full period |
| S3 | USCG MSIBs and closure notices | Enumerate by district and year |
| S4 | NHC storm archive | Landfalls within a pre-registered radius of grain export/transfer nodes |
| S5 | AMS Grain Transportation Report archive | Weekly issues; keyword scan of transportation-conditions sections |
| S6 | USACE LPMS | Outage/queue records exceeding pre-registered thresholds |
| S7 | STB service dockets and rail performance filings | Enumerate service orders and reported service events |
| S8 | Port authority / terminal operator notice archives | Enumerate published advisories where archives exist |

Every hit becomes a row in `candidates.csv` with `candidate_id`, `sweep_id`,
raw evidence pointer, and date. **No triage during the sweep** — filtering while
sweeping reintroduces the judgment the sweep exists to remove.

### Phase 2 — Triage. ~10 min per candidate

Against I1/I2/I3 only. Drop with a reason code. Record every drop; the drop log
is auditable evidence that the ledger was not curated.

### Phase 3 — Evidence pack. ~1–2 h per surviving candidate, A leads

Retrieve Tier 1 documents; capture verbatim quotes; hash and archive under
`$GRAIN_DATA_ROOT`; fill `primary_sources`. A candidate that cannot reach the
two-source rule stops here with `R2`.

### Phase 4 — Anchor. ~20 min, both, independently

Each researcher derives `public_anchor` from the evidence pack **without seeing
the other's answer**. Compare, record `anchor_agreement`, resolve disagreements
by the §B.3 rule. Anchors are fixed before severity is scored.

### Phase 5 — Severity. ~30 min, A records metrics, code scores

Human records raw physical metrics with sources. `python -m grainsys.episodes`
computes subscores, score and class. Nobody types a severity class.

### Phase 6 — Contamination and substitution. ~30 min

Contamination via the pre-registered concurrent-shock sweep, not memory.
Substitution: availability and seasonal state; usage only where documented.

### Phase 7 — Second-researcher verification. ~20 min per candidate

The reviewer re-derives the anchor from sources, spot-checks two quotes against
their originals, re-reads the mechanism for market language, and checks the
dedup ruling. Reviewer ≠ recorder, enforced by the validator.

### Phase 8 — Freeze. ~2 h, together

1. Resolve every `needs_review`; unresolved ⇒ `R13` reject
2. Run the independence audit (§H.2) and write `N_episodes`,
   `N_independent_driver_clusters`, and `N_underlying_drivers`
3. Adversarial pass (§L.4) on the whole ledger; log verbatim
4. `make all` green — validator, lint, tests
5. Compute `content_hash` per entry; set `preregistration_frozen_at` and `freeze_commit`
6. Tag `preregistration-v1`; write ADR-0003 recording the frozen sample
7. Confirm the kill condition: if Sample P < 6, write that up as the result

**Only after the tag exists may anyone open market data.**

Post-freeze additions are permitted but marked `post_freeze: true`, require an
ADR, and are analysed as a separate, clearly labelled sample. They never join
the primary sample retroactively.

---

## K. Two-researcher operating procedure

### K.1 Ownership, consistent with `TASKS_A.md` / `TASKS_B.md`

| Researcher | Owns |
|---|---|
| **A (data / plumbing)** | Source sweeps S1–S8, evidence pack retrieval, hashing and archiving, YAML authoring, `research/episodes/` |
| **B (statistics / modelling)** | Severity scoring code and cutpoints, dedup and `cluster_id` assignment, independence audit, inter-rater metrics, event-window/horizon spec, the validator's statistical checks |
| **Joint** | Anchor determination (independent, then reconciled), accept/reject decisions, `RULINGS.md`, freeze |

### K.2 Split by candidate parity, never by event class

Assign odd `candidate_id` to A, even to B. **Do not** split by class ("A takes
rivers, B takes rail"). Class-based splits produce class-specific standards —
one person's `S2` becomes systematically stricter than the other's — and that
shows up later as a spurious class effect that is really a rater effect. Parity
splitting forces both people through every class.

### K.3 Anti-drift mechanisms

1. **Calibration set first.** Before splitting anything, both researchers
   independently code the *same three* candidates end to end. Compare every
   field. Reconcile the rulebook. Expect this to change the protocol — that is
   the point, and it is far cheaper now than at entry 19.
2. **One schema, enforced by code.** `episode_schema.yaml` is the only source of
   truth, and CI enforces it. Standards held in memory diverge; standards held
   in a validator do not.
3. **Rotating review.** Whoever recorded does not review. Enforced by the validator.
4. **`RULINGS.md`** — append-only precedent log. Decide each edge case once.
5. **Inter-rater metrics**, computed and recorded at freeze: share of exact
   anchor agreement, mean absolute anchor difference in days, and agreement on
   severity class across the calibration set and any dual-coded entries. If
   anchor agreement is poor, the sample is noisier than any downstream
   confidence interval will admit — and you will only know if you measured it.
6. **Synchronous ledger sessions.** `WORKFLOW.md` already requires the ledger be
   edited together, on a call. Keep that for decisions; async is fine for
   evidence-pack assembly.

### K.4 The one asymmetry worth keeping

Anchor and dedup decisions get the same treatment `WORKFLOW.md` gives
`panel.py` and the leakage tests: **mandatory dual review, no self-merge.**
They are the episode-layer equivalent of look-ahead leakage — a silent error
there invalidates every downstream result and is undetectable afterwards.

---

## L. LLM evidence rules

Four models and several coding agents will touch this project. Undirected, they
will produce confident, plausible, wrong episodes.

### L.1 Permitted

- Generating search strategies and enumerating which document types exist
- Writing sweep code, parsers, and validators
- **Summarising a document the researcher has retrieved and can see**
- Drafting prose fields (`physical_mechanism`, rationales) *from supplied excerpts*
- Consistency checks against the schema
- Adversarial review (§L.4)

### L.2 Forbidden

- Producing any date, number, URL, identifier, gauge value, or document title
  not copied from a document in hand
- Filling any field the researcher has not verified against a source
- **Recalling historical events from training data as ledger candidates**
- Assigning severity, contamination class, or accept/reject
- Answering, or being asked, anything about market outcomes during
  pre-registration

### L.3 Why LLM recall is specifically disqualifying

An LLM's memory of grain-logistics events is drawn from text that exists
*because those events moved markets*. Asking a model to list Mississippi
low-water events returns the market-famous ones. That is outcome-selection with
extra steps, and it is worse than human memory because it arrives with fluent
detail and no hesitation. LLM-suggested candidates therefore enter
`discovery_trail` with `origin: llm` and **must** be independently confirmed by
a Phase 1 sweep. An `llm`-origin candidate with no sweep confirmation is
rejected `R2` — regardless of how real it looks.

### L.4 Adversarial pass (required before freeze)

Give the complete ledger to a **different model family** than the one used to
build it, with:

> These physical-logistics episodes were selected by researchers who have
> followed grain markets for years. Identify which entries were most likely
> selected because the researchers remember the market reaction rather than
> because of independent physical evidence. Identify which anchors are most
> likely mis-dated. Identify which entries are probably the same underlying
> shock counted twice. Assume the authors are fooling themselves.

Log the response verbatim in `EPISODE_LEDGER.md`, and dispose of each point
explicitly. This mirrors the red-team gate in `WORKFLOW.md` §3.

### L.5 Integrity mechanics

1. **Quote-or-null.** No verbatim quote in the evidence pack ⇒ the field is null.
2. **Open every URL.** A human opens each URL, records `retrieved_on`, the
   `sha256`, and a quote. Never accept an unopened LLM-supplied URL; fabricated
   URLs are syntactically perfect and frequently 404 or point somewhere else
   entirely.
3. **Fabrication contagion rule.** If one fabricated citation is found, every
   entry recorded in that batch is re-verified from source before any of them
   can be accepted. One fabrication is evidence about a process, not about a
   field.
4. **Agent scope.** Coding agents may write sweep and validation code; they may
   not write entry YAML content. Code that *finds* evidence is safe; text that
   *asserts* evidence is not.
5. `CLAUDE.md` hard rules 14 and 15 apply unchanged: no invented source IDs or
   release delays; no number that is not regenerable from committed code.

---
## M. Worked example — structure only, entirely fictional

Canonical copy: `research/episodes/entries/EP-0000-000-example.yaml`.

Everything below is **fake**. The river, the lock, the port, the agencies'
document numbers and every URL are invented and use the reserved `.invalid`
domain so they can never resolve. `example: true` excludes this entry from all
sample counts, and the validator refuses to accept any real entry carrying that
flag. It exists to show shape, density of evidence, and tone — particularly how
much source detail one accepted episode actually costs.

```yaml
schema_version: "1.1"
example: true                      # FICTIONAL — never counted in any sample

episode_id: EP-0000-000
slug: example
event_name: "FICTIONAL — Blue River Lock 99 lower gate failure"
status: accepted
event_class: lock_outage
event_subclass: "miter gate mechanical failure"
anticipation_status: unscheduled
post_freeze: false

# ---- timing -------------------------------------------------------------
public_anchor: 2099-03-14
public_anchor_precision: date      # calendar date only; no invented clock time
anchor_precision_days: 1
anchor_basis: >-
  FICTIONAL District navigation notice NTNI-0000-99, published 2099-03-14,
  states Lock 99 is closed to all traffic effective immediately.
anchor_source_ref: src_ntni_0000_99
anchor_ts: null                    # required null when precision is date
physical_onset: 2099-03-13         # gate failure logged in fictional LPMS record
official_announcement: 2099-03-14
peak_severity_date: 2099-03-19     # maximum queued tows in fictional record
end_date: 2099-04-02
end_date_basis: >-
  FICTIONAL District notice NTNI-0000-104 documents return to unrestricted
  two-way traffic; no further restriction notices for 21+ days.
relief_confirmed_date: 2099-04-02
ongoing_at_sample_end: false

# ---- geography and mechanism -------------------------------------------
navigation_basin: [fictional_blue_river]
river_reaches: ["Blue River Mile 000-000 (FICTIONAL)"]
geography: "Fictional Blue River, single pool above Lock 99"
states: [ZZ]
ports_or_nodes: ["Port of Nowhere (FICTIONAL)"]
growing_region_overlap: none
growing_regions: []
affected_infrastructure:
  - "Lock 99 (FICTIONAL) lower miter gate"
  - "Nowhere Transfer Elevator (FICTIONAL)"
physical_mechanism: >-
  A lower miter gate at Lock 99 fractured during a lockage, preventing chamber
  operation. Lock 99 is the only navigable passage on this fictional reach, so
  all loaded and empty barge traffic between the upper river and the transfer
  elevator halted. Tows queued above and below the lock; no alternative water
  route exists around this pool. The constraint was mechanical and unrelated to
  river stage, precipitation, or any agricultural condition.

# ---- severity: raw metrics in; class out (computed) ---------------------
severity_metrics:
  - dimension: d2_duration
    name: days_closed_total
    value: 19
    units: days
    as_of_date: 2099-04-02
    source_ref: src_ntni_0000_104
    quote_ref: q_relief_notice
  - dimension: d3_scope
    name: locks_affected
    value: 1
    units: count
    as_of_date: 2099-03-14
    source_ref: src_ntni_0000_99
    quote_ref: q_closure_notice
  - dimension: d4_throughput
    name: tows_queued_peak
    value: 00
    units: count
    as_of_date: 2099-03-19
    source_ref: src_lpms_0000
    quote_ref: q_queue_record
  - dimension: d5_restrictiveness
    name: operating_condition
    value: full_closure
    units: ordinal
    as_of_date: 2099-03-14
    source_ref: src_ntni_0000_99
    quote_ref: q_closure_notice
severity_subscores: {}             # DERIVED — leave empty, code fills it
severity_score: null               # DERIVED — null until Phase 0 cutpoints registered
severity_class: null               # DERIVED
severity_class_kind: null          # DERIVED: contemporaneous | ex_post_descriptive
severity_completeness: null        # DERIVED

# ---- sources ------------------------------------------------------------
primary_sources:
  - ref: src_ntni_0000_99
    tier: 1
    publisher: "FICTIONAL Corps District"
    title: "Notice to Navigation Interests NTNI-0000-99 (FICTIONAL)"
    identifier: "NTNI-0000-99"
    url: "https://fictional-district.example.invalid/ntni/0000-99"
    retrieved_on: 2099-05-01
    sha256: "0000000000000000000000000000000000000000000000000000000000000000"
    archive_path: "$GRAIN_DATA_ROOT/episodes/EP-0000-000/ntni-0000-99.pdf"
    quote: >-
      FICTIONAL QUOTE. "Lock 99 is closed to all vessel traffic effective
      immediately due to a lower miter gate failure. No estimated reopening."
    supports: [public_anchor, official_announcement, affected_infrastructure, d5]
  - ref: src_lpms_0000
    tier: 1
    publisher: "FICTIONAL Corps lock performance record"
    title: "Lock 99 daily queue and tonnage extract (FICTIONAL)"
    identifier: "LPMS-FICTIONAL-0000"
    url: "https://fictional-district.example.invalid/lpms/lock99"
    retrieved_on: 2099-05-01
    sha256: "1111111111111111111111111111111111111111111111111111111111111111"
    archive_path: "$GRAIN_DATA_ROOT/episodes/EP-0000-000/lpms-lock99.csv"
    quote: >-
      FICTIONAL QUOTE. Daily record showing queued tows above and below the
      chamber for the closure period.
    supports: [d4_throughput, peak_severity_date]
  - ref: src_ntni_0000_104
    tier: 1
    publisher: "FICTIONAL Corps District"
    title: "Notice to Navigation Interests NTNI-0000-104 (FICTIONAL)"
    identifier: "NTNI-0000-104"
    url: "https://fictional-district.example.invalid/ntni/0000-104"
    retrieved_on: 2099-05-01
    sha256: "2222222222222222222222222222222222222222222222222222222222222222"
    archive_path: "$GRAIN_DATA_ROOT/episodes/EP-0000-000/ntni-0000-104.pdf"
    quote: >-
      FICTIONAL QUOTE. "Lock 99 has returned to normal two-way operation."
    supports: [end_date, relief_confirmed_date, d2_duration]
secondary_sources:
  - ref: src_press_0000
    tier: 2
    publisher: "FICTIONAL Regional Wire"
    title: "Blue River lock closed after gate failure (FICTIONAL)"
    identifier: null
    url: "https://fictional-wire.example.invalid/2099/03/14/lock-99"
    retrieved_on: 2099-05-01
    sha256: "3333333333333333333333333333333333333333333333333333333333333333"
    archive_path: "$GRAIN_DATA_ROOT/episodes/EP-0000-000/wire-2099-03-14.html"
    quote: >-
      FICTIONAL QUOTE. Same-day report naming the district engineer and the
      closure; establishes contemporaneous public knowability.
    supports: [publicly_knowable_at_anchor]
discovery_trail:
  - origin: sweep
    detail: "Sweep S1, FICTIONAL district notice archive, year 2099, keyword 'closed'"
  - origin: sweep
    detail: "Sweep S6, LPMS outage records exceeding pre-registered threshold"
source_conflicts: []
source_confidence: high

# ---- contamination ------------------------------------------------------
crop_contamination_class: A
macro_contamination_class: A
contamination_rationale: null      # only required for class C or D
contamination_direction: ambiguous
crop_calendar_stage: pre_plant
concurrent_shocks: []
sweep_performed: true

# ---- substitution -------------------------------------------------------
substitution_channels:
  - channel: alt_river_reach
    available: "no"
    basis: "Lock 99 is the only navigable passage on this fictional pool"
    documented_use: not_assessed
    source_ref: src_ntni_0000_99
  - channel: rail_to_gulf
    available: unknown
    basis: "No evidence retrieved on rail access at the fictional transfer elevator"
    documented_use: not_assessed
    source_ref: null
  - channel: truck_short_haul
    available: "yes"
    basis: "Highway access to the fictional elevator is documented as unaffected"
    documented_use: not_assessed
    source_ref: src_press_0000
  - channel: storage_on_farm
    available: unknown
    basis: "Not assessed; no contemporaneous evidence retrieved"
    documented_use: not_assessed
    source_ref: null
substitution_state:
  great_lakes_season_open: unknown
  sa_export_season_active: unknown
  harvest_window: "no"
  concurrent_substitute_disruption: "no"

# ---- knowability and independence --------------------------------------
publicly_knowable_at_anchor: true
publication_vehicle: "FICTIONAL District navigation notice, same-day wire report"
knowability_evidence_ref: src_press_0000
episode_independence_notes: >-
  Mechanical failure with no shared driver with any other candidate. Nearest
  other fictional candidate is 8 months away in a different basin.
driver_class: mechanical_infrastructure_failure
underlying_driver_id: fictional_blue_river_gate_failure
cluster_id: fictional_blue_river_gate_failure   # default == underlying_driver_id
parent_episode_id: null
related_episode_ids: []
dedup_rule_applied: H1

# ---- governance ---------------------------------------------------------
market_outcomes_reviewed: false
outcome_exposure_log: []
recorded_by: A
recorded_date: 2099-05-01
reviewed_by: B
reviewed_date: 2099-05-03
anchor_agreement: exact
decision: accept
decision_reasons: []
researcher_notes: >-
  FICTIONAL example entry. Illustrates required structure only. The interesting
  property of this shape of episode is that it is contamination class A — a
  purely mechanical failure with no weather driver — which is the rarest and
  most valuable kind of entry for identification.
preregistration_frozen_at: null    # DERIVED at freeze
freeze_commit: null                # DERIVED at freeze
content_hash: null                 # DERIVED
```

Two things to take from the example. First, one accepted episode is roughly
four source records, four quotes, four hashes and four archived files — this is
why the workflow budgets 1–2 hours per candidate and why 25 well-evidenced
episodes is an ambitious target rather than a floor. Second, every derived
field is left null by the human; if you find yourself typing a `severity_class`,
you are working around the protocol rather than within it.

---

## N. Admission checklist

The one-page gate lives at `research/episodes/ADMISSION_CHECKLIST.md`, titled
**"Can this candidate enter the Episode Ledger?"**. It is the single source of
truth for admission and is designed to be printed and worked through per
candidate. Every item must be YES; any NO means the candidate is `rejected` or
`needs_review`, never `accepted`.

---

## What this protocol deliberately does not do

- It does not name a single historical event. Naming events here would seed the
  candidate list from memory and defeat Phase 1.
- It does not fix absolute physical thresholds. Those are computed from
  physical history in Phase 0, before candidates exist, and recorded in ADR-0002.
- It does not define event windows, estimators, or outcome variables beyond
  requiring that the window be pre-registered at freeze.
- It does not permit any market data — including barge freight rates — at any
  point before the freeze tag.

## References

- `CLAUDE.md` — hard rules, especially 5 (episodes from physical evidence), 12
  (navigation basin ≠ growing region), 13 (substitution channels), 14 (no
  invented IDs), 15 (regenerable numbers)
- `BLUEPRINT_REVIEW.md` §1 (effective N), §3 (substitution), §5 (instrument and
  the basin/growing-region distinction)
- `WORKFLOW.md` §1 (ownership, synchronous ledger), §3 (red-teaming, AI rules)
- `docs/decisions/0001-observation-schema.md` — `release_ts` discipline that
  `public_anchor` mirrors at the event level

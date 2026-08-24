# Can this candidate enter the Episode Ledger?

One page. One candidate. Work down. **Every box must be YES.**
Any NO ⇒ `rejected` or `needs_review` — never `accepted`.
Rules: `EPISODE_PROTOCOL.md`. Fields: `episode_schema.yaml`.

`candidate_ids: ________________` (≥1 D5 ID, ascending)  ·
`candidate_universe_version: ________________`  ·
`recorded_by: ___`  ·  `reviewed_by: ___`  ·  `date: __________`

### 0 · Lineage (ADR-0009)

- [ ] This YAML is one **episode record**, not one raw candidate hit
- [ ] `candidate_ids` lists every contributing D5 candidate ID (union under H1/H2/H3/H8)
- [ ] IDs are **unique**, **D5-valid**, **same width**, stored in **ascending D5 numeric order**
- [ ] `candidate_universe_version` matches the frozen `candidate_universe.yaml` for this build
- [ ] Do **not** store `lineage_candidate_id` — it is derived as `min(candidate_ids)` by code
- [ ] Candidates dropped without an episode will be recorded separately in the no-episode disposition ledger (not in this file)

### 1 · Is it an episode at all?

- [ ] A **physical or operational constraint** acted on grain-carrying infrastructure (I1)
- [ ] A primary source documents an **operational consequence** — closure, restriction, outage, queueing, documented throughput decline (I2)
- [ ] It is **not a driver only.** A gauge reading, rainfall anomaly or storm track with no documented operational response is not an episode
- [ ] There is a **step**, not a slope: onset is discrete, not a 90-day drift (A.5)
- [ ] It is inside the pre-registered sample period and corridor list

### 2 · Can it be dated, honestly?

- [ ] `public_anchor` derived by the §B.3 rule from a dated document
- [ ] `anchor_precision_days` ≤ 7 (4–7 ⇒ review; > 7 ⇒ reject `R1`)
- [ ] `anchor_basis` names the specific document that fixes the date
- [ ] The other researcher derived the **same anchor independently**; `anchor_agreement` recorded
- [ ] `anticipation_status` set — a pre-announced scheduled closure is tagged, not silently pooled
- [ ] `physical_onset`, `official_announcement`, `peak_severity_date`, `end_date` recorded separately where knowable — **never collapsed into one date**

### 3 · Was it knowable at the time?

- [ ] `publicly_knowable_at_anchor: true`, with a **named publication vehicle** and a dated document
- [ ] No field depends on information that only existed later

### 4 · Is the evidence real?

- [ ] ≥ **2 independent Tier 1 sources** (or 1 Tier 1 + 2 Tier 2 with `source_confidence: medium` and review)
- [ ] Every source carries publisher, title, URL, `retrieved_on`, `sha256`, archive path, and a **verbatim quote**
- [ ] A human **opened every URL.** No unopened LLM-supplied link
- [ ] Every factual field traces to a quote — **quote-or-null**, no exceptions
- [ ] Tier 1 sources do not contradict each other (`source_conflicts` empty)
- [ ] No Tier 3 source cited as evidence anywhere

### 5 · Is severity physical?

- [ ] ≥ 2 `severity_metrics`, each with units, `as_of_date`, source ref, quote ref
- [ ] Every metric would have the **same value if the futures market were closed that week**
- [ ] No price, spread, basis, **barge freight rate**, ocean freight, premium, volume or positioning anywhere in severity
- [ ] `severity_subscores` / `severity_score` / `severity_class` left **null** — the code assigns them

### 6 · Is contamination assessed and signed?

- [ ] `navigation_basin` and `growing_region_overlap` recorded **separately**
- [ ] `crop_contamination_class` and `macro_contamination_class` assigned (A–D)
- [ ] `crop_calendar_stage` at anchor recorded
- [ ] `concurrent_shocks` populated from the **pre-registered sweep**, not memory; `sweep_performed: true`
- [ ] `contamination_direction` states whether the confound inflates or attenuates the hypothesised effect
- [ ] Rationale written for any class C or D
- [ ] Class D on either axis ⇒ excluded (`R8`)

### 7 · Are substitutes documented, not inferred?

- [ ] ≥ 3 `substitution_channels` assessed for **ex ante availability**
- [ ] `documented_use` is `not_assessed` unless a contemporaneous source says otherwise — **never inferred from flow data**
- [ ] `substitution_state` recorded: Great Lakes season, South American export season, harvest window, concurrent substitute disruption

### 8 · Is it independent?

- [ ] Not a stage, echo, aftermath or repeat manifestation of an existing entry (§H1–H9)
- [ ] `driver_class` recorded (broad causal category; grow deliberately)
- [ ] `underlying_driver_id` assigned for the underlying physical shock
- [ ] `cluster_id` defaults to `underlying_driver_id`, or a documented ruling justifies otherwise
- [ ] `dedup_rule_applied` names the rule that produced this partition
- [ ] If it shares a `cluster_id` with an accepted entry, the written independence argument survived review (H6)
- [ ] Parent/child split, if any, admits **only one** of the pair to the primary sample (H5)

### 9 · Is it outcome-blind?

- [ ] `market_outcomes_reviewed: false`
- [ ] Confirmed by a **Phase 1 source sweep**, not surfaced from market memory (`discovery_trail` contains a `sweep` origin)
- [ ] No price chart, spread, basis or market commentary was consulted for any field
- [ ] Any accidental outcome exposure is written into `outcome_exposure_log`
- [ ] Honest answer to: *would I still have found this candidate if I had never followed grain markets?*

### 10 · Governance

- [ ] `reviewed_by` ≠ `recorded_by`
- [ ] Every required field in `episode_schema.yaml` §G.3 is filled from evidence, none guessed
- [ ] `python -m grainsys.episodes` passes with no errors for this entry
- [ ] Any edge-case ruling made here is written to `RULINGS.md`

---

**Decision:**  ☐ ACCEPT  ☐ REJECT  ☐ NEEDS REVIEW

Reason codes (reject/review): `_______________`

> Default is REJECT. The burden of proof is on inclusion. A 14-episode ledger
> where every entry survives this page beats a 25-episode ledger with six soft
> entries — because with N ≈ 20, one retrospectively-selected episode is worth
> about 5% of all the evidence in the project.

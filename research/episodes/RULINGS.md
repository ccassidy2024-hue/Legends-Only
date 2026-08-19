# Rulings — append-only precedent log

Every edge-case decision made while building the Episode Ledger is recorded
here, once, and then applied by lookup. Two people working from memory drift
into two standards; two people working from precedent do not.

Append only. Never edit or delete a ruling — supersede it with a new entry that
names the one it replaces.

## Format

```markdown
### YYYY-MM-DD · R-NNN · <short title>

- **Situation:** what came up, on which candidate
- **Rule invoked:** protocol section / rule id
- **Ruling:** what was decided
- **Generalises to:** the class of cases this now governs
- **Decided by:** A + B
- **Supersedes:** R-NNN or none
```

## Rulings

### 2026-08-10 · R-001 · Date-only public_anchor → analysis anchors (PRIMARY)

- **Situation:** Historical sources often support only a calendar date for
  `public_anchor`, while weekly analysis anchors carry intraday timestamps.
- **Rule invoked:** EPISODE_PROTOCOL.md §B.3 mapping; `first_usable_analysis_anchor`
- **Ruling:** If `public_anchor_precision == date`, the event becomes usable at
  the first analysis/panel anchor whose calendar date is **strictly after**
  `public_anchor`. Do not interpret the date as midnight, BOD, noon, or EOD.
  Same-calendar-day weekly anchors are not usable. If
  `public_anchor_precision == timestamp`, same-day use is allowed only when
  `anchor_ts <= analysis_anchor_ts` and the timestamp is source-supported.
  Other same-day/date-only mappings are labeled robustness assumptions only.
- **Generalises to:** All date-only and timestamp public anchors mapped into
  weekly (or other) analysis windows.
- **Decided by:** A + B (methodology approval)
- **Supersedes:** none

### 2026-08-10 · R-002 · driver_class / underlying_driver_id / cluster_id

- **Situation:** Need stable independence taxonomy without a premature giant
  controlled vocabulary.
- **Rule invoked:** EPISODE_PROTOCOL.md §H.2
- **Ruling:** `driver_class` = broad causal-driver category (grows deliberately).
  `underlying_driver_id` = stable id for the underlying physical shock.
  `cluster_id` = statistical dependence grouping; **default equals
  `underlying_driver_id`** unless a documented ruling justifies otherwise.
  Primary inferential reporting: `N_episodes` and
  `N_independent_driver_clusters`. `N_underlying_drivers` is descriptive only.
  Do not collapse physically distinct episode rows that share a driver.
- **Generalises to:** All episode independence / clustering fields and audits.
- **Decided by:** A + B (methodology approval)
- **Supersedes:** none

### 2026-08-10 · R-003 · Severity calibration remains unregistered

- **Situation:** No Phase 0 severity reference distributions or cutpoints have
  been preregistered.
- **Rule invoked:** EPISODE_PROTOCOL.md §D.3; `episode_schema.yaml` severity
- **Ruling:** Keep `cutpoints_registered: false`. Derived `severity_class` /
  `severity_score` remain null. Raw physical severity metrics may be collected.
  No analytical severity classification is authorized until a later Phase 0 /
  ADR registers metrics-by-class, reference period, as-of vs ex-post method,
  cutpoints, combination rule, and missing-data treatment.
- **Generalises to:** All severity scoring until that ADR exists.
- **Decided by:** A + B (methodology approval)
- **Supersedes:** none

### 2026-08-11 · R-004 · Date-only pre-treatment baseline (Person B PR #1)

- **Situation:** PR #1 CHANGES_REQUESTED — date-only t=0 mapping needs an
  explicit pre-treatment baseline rule.
- **Rule invoked:** EPISODE_PROTOCOL.md §B.3 (date-only mapping + baseline)
- **Ruling:** When `public_anchor_precision == "date"` and t=0 is the first
  analysis anchor strictly after `public_anchor`, the pre-treatment baseline
  MUST be the last analysis anchor strictly before `public_anchor` — not t=−1
  after remapping. Example: public_anchor Oct 19 → t=0 Oct 26; Oct 19 is not
  baseline; Oct 12 is. Same-calendar-date observations may contain same-day
  public information and are not automatically clean pre-treatment data.
  No timestamp-specific baseline rule and no `anchor_precision_days` behavior
  are invented here.
- **Generalises to:** All date-only primary event-study / LP alignments.
- **Decided by:** Person B review requirement on PR #1 (awaiting re-audit)
- **Supersedes:** none (extends R-001)

### 2026-08-11 · R-005 · Mandatory cluster-level downstream inference (Person B PR #1)

- **Situation:** PR #1 CHANGES_REQUESTED — “may use cluster-aware inference”
  is too weak for market event studies / IRFs / LPs.
- **Rule invoked:** EPISODE_PROTOCOL.md §H.2
- **Ruling:** Downstream market event studies, impulse-response plots, and
  local projections MUST either (A) collapse/average to `cluster_id`, or
  (B) use inverse-cluster weights `w_i = 1/K_c` and cluster-robust SEs by
  `cluster_id`. This is a downstream statistical requirement, not an episode
  schema change.
- **Generalises to:** All market-response estimation using the Episode Ledger.
- **Decided by:** Person B review requirement on PR #1 (awaiting re-audit)
- **Supersedes:** soft “may” language previously in §H.2

### 2026-08-11 · R-006 · Ex-post variables barred from t=0 / covariates (Person B PR #1)

- **Situation:** PR #1 CHANGES_REQUESTED — post-unfolding quantities can
  create look-ahead if used as treatment clocks or covariates.
- **Rule invoked:** EPISODE_PROTOCOL.md §B.5
- **Ruling:** `peak_severity_date`, `end_date`, and `duration_days` MUST NOT
  be used as the t=0 alignment anchor or as conditioning covariates in
  market-response event studies / LPs. They MAY be ex-post descriptive
  variables and/or preregistered duration-response targets.
- **Generalises to:** All market-response designs using the Episode Ledger.
- **Decided by:** Person B review requirement on PR #1 (awaiting re-audit)
- **Supersedes:** none

### 2026-08-11 · R-007 · Horizon preregistration before estimation (Person B PR #1)

- **Situation:** PR #1 CHANGES_REQUESTED — pre/post/reference horizons must
  be preregistered before market-response estimation.
- **Rule invoked:** EPISODE_PROTOCOL.md §J Phase 0
- **Ruling:** Before corresponding market-response estimation, Phase 0 MUST
  preregister pre-event horizon, post-event horizon, and reference/baseline
  horizon. Numerical values are an A+B Phase-0 human decision and are **not**
  invented here. Until recorded in an ADR / `prereg-rules` tag, estimation
  depending on those horizons is blocked.
- **Generalises to:** All market-response event studies and local projections.
- **Decided by:** Person B review requirement on PR #1 (awaiting re-audit)
- **Supersedes:** illustrative “e.g. h = 0…26 weeks” language in Phase 0

### 2026-08-11 · R-008 · PR #1 re-audit complete — R-004–R-007 operative

- **Situation:** R-004 through R-007 still carried “awaiting re-audit” governance
  wording after PR #1 was approved and merged to `main`. Append-only policy
  forbids rewriting those ruling bodies.
- **Rule invoked:** `RULINGS.md` append-only / supersession semantics; ADR-0002
- **Ruling:** PR #1 re-audit is complete. R-004, R-005, R-006, and R-007 are
  **operative**. No substantive rule text in those entries is changed by this
  ruling. Stale “awaiting re-audit” phrases in their “Decided by” lines are
  superseded for governance-status purposes only. ADR-0002 remains **proposed**
  because Phase 0 open items are still unresolved; merging PR #1 does not accept
  the full open-item package.
- **Generalises to:** Governance metadata for R-004–R-007 after PR #1 merge.
- **Decided by:** A + B (post-merge governance cleanup)
- **Supersedes:** governance-status implication of “awaiting re-audit” on
  R-004–R-007 only (not their substantive rulings)

### 2026-08-12 · R-009 · Anchor-fixing standard (P1)

- **Situation:** Republication vehicles (e.g. weekly digests) often prove only
  that a fact was public *by* a calendar date, while `public_anchor` requires
  the earliest date the underlying fact was public *on*; R-001/R-004 also leave
  nonzero `anchor_precision_days` downstream baseline behavior undefined.
- **Rule invoked:** EPISODE_PROTOCOL.md §B.3 / §B.4; R-001; R-004; ADR-0005 P1
- **Ruling:** Public-by evidence does not by itself fix `public_anchor`. The
  canonical anchor requires affirmative evidence of the underlying fact's public
  availability on the anchor date. For a republication vehicle, prior-issue
  silence never establishes the early bound. If the early side cannot be bounded
  within the existing `{0,1,3,7}` `anchor_precision_days` framework, the anchor
  fails closed (`needs_review` / `R1` if unresolved). Needs-review / rejected
  records remain auditable; the episode cannot be **accepted** with that
  unresolved anchor. No new one-sided or interval-valued anchor datatype is
  introduced. Separately: where `anchor_precision_days > 0`, market-response
  event-window / LP alignment is **blocked** until A+B separately preregister
  how nonzero anchor uncertainty affects t=0 and pretreatment baseline
  construction; ledger admission and descriptive use may proceed if otherwise
  admissible. Governing normative record: ADR-0005.
- **Generalises to:** All public-anchor fixing from republication / public-by
  evidence, and all market-response alignments when `anchor_precision_days > 0`.
- **Decided by:** A + B (independent ratification; no disagreement)
- **Supersedes:** none

### 2026-08-12 · R-010 · Originating-record independence (P2; clarifying)

- **Situation:** Cross-publisher republications, reprints, continuations, and
  derivatives of one underlying notice can be miscounted as a second independent
  Tier-1 source under a document-count reading of §C.2.
- **Rule invoked:** EPISODE_PROTOCOL.md §C.2 / §C.2.1; ADR-0005 P2
- **Ruling:** **Clarifying precedent** — §C.2 independence is assessed by
  independent evidentiary lineage / originating record, not document count.
  Republications, reprints, continuations, or derivatives from the same
  underlying notice never supply the second independent Tier-1 source regardless
  of publisher, vehicle, format, or file type. They may still provide
  corroboration, contemporaneous knowability evidence, and preservation
  evidence. The existing single-Tier-1-source fallback is unchanged. Governing
  normative record: ADR-0005.
- **Generalises to:** All §C.2 two-source independence assessments involving
  republication / derivative carriers.
- **Decided by:** A + B (independent ratification; no disagreement)
- **Supersedes:** none

### 2026-08-12 · R-011 · Document-lifecycle / relief firewall (P3; clarifying)

- **Situation:** Reissue, continuation, renumbering, amendment publication,
  cancellation, format change, or cross-vehicle migration can be mistaken for
  creating/splitting/merging/re-anchoring/terminating an episode, or for
  documented relief.
- **Rule invoked:** EPISODE_PROTOCOL.md §A.5; H1–H9; ADR-0005 P3
- **Ruling:** **Clarifying precedent** — document-lifecycle events do not by
  themselves create, split, merge, re-anchor, or terminate an episode; §A.5 and
  H1–H9 remain controlling. Cancellation counts as documented relief only when
  the cancellation itself or another qualifying Tier-1 source affirmatively
  establishes restoration of unrestricted operation or explicitly pre-episode
  baseline operation. Withdrawal, expiry, supersession, disappearance, or
  silence are not relief by themselves. Governing normative record: ADR-0005.
- **Generalises to:** All episode identity / relief determinations involving
  document lifecycle events.
- **Decided by:** A + B (independent ratification; no disagreement)
- **Supersedes:** none

### 2026-08-12 · R-012 · Release-identity invariant (P4)

- **Situation:** A defensible historical timestamp can be paired with a value
  from a mutable current-state store, or a later corrected vintage can inherit
  an earlier `release_ts`, defeating leakage-sensitive as-of analysis without
  changing the frozen ADR-0001 columns.
- **Rule invoked:** ADR-0001 observation schema; ADR-0003 ESMIS timestamp
  safety; ADR-0005 P4
- **Ruling:** For leakage-sensitive historical as-of analysis, an observation is
  admissible only when its `value` and `release_ts` resolve to the same
  identified historical release/vintage through stable release identity (report
  identifier + issue date, document/content hash, archive snapshot id, vintage
  endpoint id, or equivalent). `series_id` + `period_end` coincidence alone is
  insufficient. A mutable current-state value carries no historical release
  identity by itself and may not inherit an unrelated artifact's `release_ts`.
  Historical as-of use requires affirmative linkage to the same identified
  release under ADR-0005 P4. Each
  corrected/superseded vintage is its own release with its own availability; a
  later value never inherits an earlier vintage's `release_ts`. Platform/API
  timestamps establish publication availability only when source documentation
  establishes that semantic. Literal same-file provenance is not required where
  artifacts are affirmatively linked to one release identity. Full invariant and
  consequences: ADR-0005. ADR-0001's four-column interface is unchanged.
- **Generalises to:** All leakage-sensitive historical as-of observations and
  ingest paths that attach `release_ts` to values.
- **Decided by:** A + B (independent ratification; no disagreement)
- **Supersedes:** none

### 2026-08-12 · R-013 · Coverage zero-semantics (P5)

- **Situation:** Absence-generating sweeps need a frozen meaning for covered
  exposure and for `records_matched: 0` when archives have known intra-scope
  gaps, without adding new coverage schema fields.
- **Rule invoked:** ADR-0003 N2 / D1 coverage architecture; ADR-0005 P5
- **Ruling:** For absence-generating / exhaustive sweep families, covered
  exposure = union(enumerated scopes) minus affirmatively known gap
  subintervals. Known intra-scope gaps must be explicit interval-scoped coverage
  records, not prose in `notes`. For an affirmatively known gap, the
  absent/unknown coverage row must carry explicit `scope_start` and `scope_end`
  identifying the gap interval. `records_matched: 0` means zero matching
  records among accessible records actually enumerated over the resulting net
  covered scope; it does not prove no real-world event occurred. Archive
  endpoint reachability never proves retention completeness. Supplementary
  positive-evidence families do not generate absence exposure / swept-zero
  claims unless later promoted into an exhaustive sweep family. No new coverage
  fields. Governing normative record: ADR-0005.
- **Generalises to:** All absence-generating / exhaustive sweep families and
  their coverage / exposure denominators.
- **Decided by:** A + B (independent ratification; no disagreement)
- **Supersedes:** none

### 2026-08-12 · R-014 · LNM supplementary / non-discovery classification (P6)

- **Situation:** USCG Local Notices to Mariners can be mistaken for an
  independent candidate-discovery / absence-generating sweep family.
- **Rule invoked:** EPISODE_PROTOCOL.md §J Phase 1 sweep families; ADR-0005 P6
- **Ruling:** LNM is currently supplementary corroboration and
  public-knowability / public-by evidence: non-exhaustive, non-absence-
  generating, and **not** an independent candidate-discovery family. LNM may
  support an episode surfaced through a registered sweep; it does not
  independently generate candidate rows. Promoting LNM into a sweep family
  requires a future preregistered D3-compatible ADR defining scope/endpoints;
  P5 then applies. This ruling names no LNM endpoints, districts, keywords,
  dates, or clocks. Governing normative record: ADR-0005.
- **Generalises to:** Current LNM use across candidate discovery, corroboration,
  and public-knowability evidence.
- **Decided by:** A + B (independent ratification; no disagreement)
- **Supersedes:** none

### 2026-08-18 · R-015 · H7 deterministic resolution and relief-only exception

- **Situation:** H7 states ≤1 episode per `(corridor, driver)` per 60 days
  without a written exception, but does not define the driver key, the 60-day
  window arithmetic, survivor selection, or admissible exception conditions.
  In addition, §A.5 requires two episodes after an affirmatively documented
  return to unrestricted or explicitly pre-episode-baseline operation for
  ≥21 consecutive days followed by recurrence, creating a direct 21–60 day
  governance tension that must be resolved before candidate discovery.
- **Rule invoked:** EPISODE_PROTOCOL.md §A.5 and H1–H9; R-002; R-009;
  R-010; R-011; H7-GOVERNANCE-v1 joint A+B ratification.
- **Ruling:** H7 uses the key
  `(canonical corridor_id, underlying_driver_id)`.
  `driver_class` is never the H7 driver component.

  H1–H9 retain their canonical ordering. Cases already established as one
  episode by §A.5/H1/H2/H3 do not create an H7 survivor contest. H5 remains
  controlling for parent/child primary-sample treatment, and H6 review remains
  additive where applicable.

  For otherwise-admissible entries within one H7 key, sort by recorded
  `public_anchor` ascending. Admit the earliest. Thereafter admit an entry only
  when its recorded `public_anchor` is at least 60 calendar days after the
  `public_anchor` of the most recently admitted entry. An entry admitted under
  the exception below resets the 60-day window. The result is a derived
  function of committed fields and must be re-run when an input public_anchor
  changes pre-freeze. Discovery order confers no priority.

  Exact-public_anchor ties use ascending `candidate_id` only after D5 has
  frozen deterministic minting/order and deterministic candidate-to-episode
  lineage. If that lineage is unavailable, tied H7 resolution fails closed
  until A+B preregister another deterministic tie-break. This ruling chooses
  no D5 value.

  The sole ordinary H7 exception is documented relief and renewed onset:
  Tier-1 originating evidence must affirmatively establish restoration to
  unrestricted or explicitly pre-episode-baseline operation for at least
  21 consecutive days, followed by a later episode with its own independently
  evidenced public_anchor under R-009. The evidence may consist of one or
  multiple qualifying originating operational records, but silence between
  observations cannot manufacture continuity. Silence, cancellation, expiry,
  supersession, disappearance, non-reissue, and publication migration do not
  constitute relief.

  There is no residual H7 exception. Independent infrastructure within one
  canonical corridor and a claimed distinct physical mechanism are not H7
  exceptions. Driver/corridor identity errors are corrected through normal
  governance and H7 is re-run; they are never laundered as exceptions.

  Survivor/exception decisions may not use market outcomes, downstream
  statistical results, severity rankings, importance, document counts,
  salience, sample-size needs, power, estimator feasibility, identification
  convenience, or ex-post fields as selectors. D12 remains unregistered.

  Either researcher may propose the relief exception before acceptance; the
  other must review independently; A+B unanimity is required with no market
  data open. If disagreement remains unresolved at freeze, no exception is
  granted and the non-survivor carries R4 and R13.

  An H7 non-survivor is retained as:
  `status: rejected`;
  `decision: reject`;
  `decision_reasons: [R4]` (or `[R4, R13]` for unresolved exception
  disagreement);
  `dedup_rule_applied: H7`;
  with related entries cross-linked.
  This intentionally engages the existing accepted/rejected dual-review
  requirements. No schema change is required by this disposition itself.

  Entries admitted through the relief exception share `cluster_id`; an H7
  exception never establishes statistical independence or splits a cluster.

  The ruling is ratified now but remains operationally inert until
  D2-MEMBERSHIP/canonical corridor persistence and the required D5 deterministic
  lineage are closed.

  Pre-freeze anchor/evidence changes trigger deterministic re-resolution.
  Post-ledger-freeze changes never rewrite the frozen sample in place and require
  separately governed post-freeze versioning / ADR treatment.
- **Generalises to:** Every H7 collision, survivor determination, and H7
  exception adjudication after the required D2/D5 activation dependencies
  close.
- **Decided by:** A + B (joint human ratification of H7-GOVERNANCE-v1,
  2026-08-18; no disagreement)
- **Supersedes:** none

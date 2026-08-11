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

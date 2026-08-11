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

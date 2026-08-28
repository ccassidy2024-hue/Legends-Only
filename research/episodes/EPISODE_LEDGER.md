# Episode Ledger (pre-registration)

The project's pre-registration artifact. Built from **physical / logistics
evidence only**, before any market outcome is examined.

Effective sample size for mechanism work is the number of *independent
episodes* — closer to the driver count than to the number of weekly rows
(`BLUEPRINT_REVIEW.md` §1). This table is that sample.

| Artifact | Role |
|---|---|
| `EPISODE_PROTOCOL.md` | **How to research an episode.** Rules, tiers, anchors, severity, dedup |
| `episode_schema.yaml` | Machine-readable field spec — single source of truth |
| `ADMISSION_CHECKLIST.md` | The one-page gate applied per candidate |
| `entries/*.yaml` | One file per candidate, accepted **and** rejected |
| `RULINGS.md` | Append-only precedent log |
| This file | Ledger of record + generated summary |

Do not invent sources, dates, or release delays. Do not populate episodes from
memory — candidates come from the Phase 1 source sweeps
(`EPISODE_PROTOCOL.md` §J), never from recall, because recall of grain events is
filtered through market salience.

---

## Status

| Item | State |
|---|---|
| Protocol | accepted (ADR-0002) |
| Phase 0 — rules pre-registered (thresholds, cutpoints, windows) | committed (`prereg-rules-v1`); D12 cutpoints remain unregistered (R-003) |
| Phase 1 — source sweeps | complete for frozen D5 (S1 + S4) |
| Candidates recorded | **4234** frozen D5 candidates; **0** real episode YAML (plus 1 fictional example, excluded) |
| Mechanical triage (I1/I2/I3) | **4234** no-episode dispositions; S1=37 R12; S4=4197 R3; **survivors=0** |
| Admissible episode rows | **0** |
| Pre-registration freeze | **M1 closed as empty-ledger negative result** — market data remains unopened |
| Freeze tag | — (no admissible sample to tag) |
| Freeze commit | `e213aab007150d5287b07e476d0bb438ad1374a9` (PR #50 merge; reviewed head `5a76e2e3c8e83aed0956f8b8804c043ae8729206`) |

## M1 closeout (negative result)

Mechanical Phase-2 I1/I2/I3 triage of frozen D5=4234 produced 0 survivors and
therefore 0 admissible Episode Ledger rows. Sample P = 0 is below the
`WORKFLOW.md` kill condition of 6 usable episodes.

This is a **legitimate negative result** for Milestone 1 episode construction.
It is **not** a finding that no physical disruption occurred:

- UNKNOWN is not zero.
- Missing I2 operational evidence is not proof of no physical disruption.
- S4 POINT_ONLY 100NM HURDAT2 proximity is driver identity only in the absence of I2.

No episode YAML was invented. Dropped D5 candidates were not resurrected.
Market outcomes were not read. Disposition ledger:
`research/episodes/discovery/candidates/no_episode_dispositions.csv`.

Marker: `M1_CLOSEOUT_RETRY_AFTER_CURSOR_LAUNCH_FAILURE`
Follow-on marker: `M1_CLOSEOUT_GROK_TAKEOVER`

## Standing rules

1. Episodes are defined from physical/logistics stress, never from market moves.
2. `public_anchor` — the first publicly observable date — is primary t = 0.
   Physical onset and official announcement are recorded separately and may be
   preregistered robustness anchors as governed by the protocol. Peak severity
   is ex-post only and cannot be a t=0 market-response anchor or conditioning
   covariate.
3. Severity comes from physical metrics only. Barge freight rates are a
   **price**, not a severity metric.
4. `market_outcomes_reviewed` stays `false` on every entry until the freeze tag
   exists. The validator fails the build otherwise.
5. Contamination classes stratify the sample (Sample P / Sample X); they are
   pre-registered, not applied after the fact.
6. Substitution channels record ex-ante *availability*; usage only where a
   contemporaneous source documents it.
7. Rejected candidates are retained as files. Deleting them destroys the audit
   trail that shows the ledger was not curated.
8. After the freeze, any new or altered episode requires an ADR and is analysed
   as a separately labelled sample.

## Generated summary

Regenerate with `make episodes-write`. `make episodes` fails if this block is
stale, so the table is always reproducible from committed entries
(`CLAUDE.md` hard rule 15).

<!-- BEGIN GENERATED: episode-summary -->

<!-- Regenerate with `make episodes-write`. Do not hand-edit this block. -->

| episode_id | event_name | event_class | public_anchor | end_date | navigation_basin | severity_class | sample | status | outcomes_reviewed |
|---|---|---|---|---|---|---|---|---|---|
| *(none yet)* | | | | | | | | | *blank during pre-registration* |

**Independence audit (protocol H.2)**

- N_episodes (accepted rows): **0**
- N_independent_driver_clusters: **0** (primary inferential effective-N concept)
- N_underlying_drivers (descriptive only): **0**
- max episodes in one cluster: **0** · max episodes for one driver: **0**
- primary sample (Sample P): **0** · extended (Sample X): **0**
- shared driver present: **false** · below kill condition: **n/a**

Primary reporting: N_episodes and N_independent_driver_clusters. Do not auto-drop physically distinct rows that share a driver.

Excluded from counts: 1 fictional example entry/entries.

<!-- END GENERATED: episode-summary -->

## Freeze record

Empty-ledger closeout of Milestone 1. There is no admissible sample to freeze
into a tagged episode set. Market outcomes remain unopened.

| Item | Value |
|---|---|
| `preregistration_frozen_at` | n/a — no admissible rows |
| `freeze_commit` | `e213aab007150d5287b07e476d0bb438ad1374a9` |
| Git tag | none (empty sample; do not treat as authorization to open market data) |
| Accepted episodes / distinct drivers | 0 / 0 |
| Sample P size | 0 (below kill condition of 6) |
| Pre-registered event window and horizons | n/a — not estimable with 0 episodes |
| Robustness anchor set | n/a |

## Adversarial pass (required before freeze)

Not applicable: zero admissible rows; no sample to red-team. Honesty conditions
are the Status / M1 closeout statements above (UNKNOWN ≠ 0; missing I2 ≠ proof
of no disruption; S4 proximity is driver-only absent I2).

## Inter-rater agreement

Not applicable: 0 survivors, 0 admissible rows, 0 calibration-set entries.

| Metric | Value |
|---|---|
| Exact anchor agreement | n/a |
| Mean absolute anchor difference (days) | n/a |
| Severity-class agreement | n/a |
| Calibration-set entries dual-coded | 0 |

## Four-statement reminder

When later analysing an episode, keep separate: what the data show | why we
think it happens | what we expect next | how it could be traded.

M1 merge: PR #51, `b7d402713ef5eaed33cdff44f4128382e3b38be7` (reviewed head
`9812df348c053af3024fd007a4ee486494aac954`). Downstream empty-sample closeout
(M2–M5) lives in `research/milestones/` and
`research/memos/M5_EMPTY_SAMPLE_FOUR_STATEMENTS.md`. M6/M7 skipped under the
<6 kill. M8 written negative result:
`research/milestones/M8_WRITTEN_NEGATIVE_RESULT.md`. UNKNOWN is not zero.

## Change log

| date | episode_id | change | author |
|------|------------|--------|--------|
| 2026-08-28 | — | M1 empty-ledger negative-result closeout: 4234 candidates mechanically triaged, 4234 no-episode dispositions, 0 survivors, 0 admissible episode rows. Marker `M1_CLOSEOUT_RETRY_AFTER_CURSOR_LAUNCH_FAILURE`. | A (agent) |
| 2026-08-28 | — | M1 merged to main (PR #51). M2–M5 empty-sample closeout: `M2_NEGATIVE_RESULT_EMPTY_SAMPLE`; M3/M4 not-estimable; M5 four-statement memo. | A (agent) |
| 2026-08-28 | — | Kill closeout: M3 family size = 0 tests performed (never-run); M6/M7 skipped; M8 written unanswerable result. Marker `M1_CLOSEOUT_GROK_TAKEOVER`. | A (agent) |

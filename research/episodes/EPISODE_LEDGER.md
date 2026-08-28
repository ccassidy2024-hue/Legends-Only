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
| Protocol | in force (ADR-0002 and later closed ADRs) |
| Phase 0 — rules pre-registered (thresholds, cutpoints, windows) | committed (`prereg-rules-v2`); D12 severity cutpoints remain unregistered |
| Phase 1 — source sweeps | complete for frozen D5 (S1=37, S4=4197; S2–S8 added no D5 rows) |
| Frozen D5 universe | 4234 candidates |
| Phase 2 — I1/I2/I3 triage | complete (PR #50 head `5a76e2e3c8e83aed0956f8b8804c043ae8729206`) |
| Candidates recorded | 4234 |
| No-episode dispositions | 4234 (S1=37 R12; S4=4197 R3) |
| Phase-2 survivors | 0 |
| Admissible episode rows | **0** (fictional example `EP-0000-000` excluded, not counted) |
| Pre-registration freeze | **not frozen** — no admissible sample to freeze; market data remains closed |
| Freeze tag | — |
| Freeze commit | — |
| M1 result | **negative result** — Sample P = 0 < kill condition 6 |

### M1 closeout — empty admissible Episode Ledger

Mechanical I1/I2/I3 triage of the frozen 4234-candidate D5 universe produced
**0** survivors and therefore **0** admissible Episode Ledger rows. This is a
legitimate negative result. No episode YAML was authored to manufacture
survivors. The fictional example `entries/EP-0000-000-example.yaml` remains
protocol structure only (`example: true`).

Repo-native empty-ledger representation:

- `entries/` — no real episode YAML (accepted or rejected)
- generated summary below — 0 accepted rows, Sample P = 0, kill condition true
- `discovery/candidates/no_episode_dispositions.csv` — 4234 candidate-keyed
  rows (ADR-0009: candidates that produce no episode must not disappear)
- `python -m grainsys.episodes` enforces E ∪ N = C against that frozen universe

**UNKNOWN is not zero.** Unverified, fixture-bound, or incomplete evidence is
not a count of zero operational events.

**S4 proximity is driver-only absent I2.** The 4197 S4 dispositions are R3
(X1): POINT_ONLY 100NM HURDAT2 storm-node proximity is driver identity only.
A storm track is not an episode. Lack of documented operational consequence
is **not** proof of no physical disruption.

**S1 R12 is unverifiable source, not a zero-event finding.** The 37 S1
dispositions are R12 (X10): SHA-bound capture bodies are committed fixture
HTML, not live NTNI notices. That does not prove the originating notices
carried no operational restriction.

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
| *(none)* | | | | | | | | | *0 admissible rows; market outcomes unopened* |

**Independence audit (protocol H.2)**

- N_episodes (accepted rows): **0**
- N_independent_driver_clusters: **0** (primary inferential effective-N concept)
- N_underlying_drivers (descriptive only): **0**
- max episodes in one cluster: **0** · max episodes for one driver: **0**
- primary sample (Sample P): **0** · extended (Sample X): **0**
- shared driver present: **false** · below kill condition: **true**

Primary reporting: N_episodes and N_independent_driver_clusters. Do not auto-drop physically distinct rows that share a driver.

Excluded from counts: 1 fictional example entry/entries.

<!-- END GENERATED: episode-summary -->

## Freeze record

Not completed. Phase 8 freeze would lock a sample and then permit opening
market data. Sample P = 0, so there is no sample to freeze and market data
stays closed. This section remains empty by protocol.

| Item | Value |
|---|---|
| `preregistration_frozen_at` | — |
| `freeze_commit` | — |
| Git tag | — |
| Accepted episodes / distinct drivers | — |
| Sample P size | — |
| Pre-registered event window and horizons | — |
| Robustness anchor set | — |

## Adversarial pass (required before freeze)

Verbatim response from a different model family, per `EPISODE_PROTOCOL.md` §L.4,
with each point dispositioned.

Not run. Adversarial pass is required before freeze (§L.4). M1 closed with
0 admissible rows and no freeze tag; there is no ledger sample to red-team.

## Inter-rater agreement

Recorded at freeze, per §K.3.

| Metric | Value |
|---|---|
| Exact anchor agreement | n/a — 0 admissible rows |
| Mean absolute anchor difference (days) | n/a — 0 admissible rows |
| Severity-class agreement | n/a — 0 admissible rows; D12 unregistered |
| Calibration-set entries dual-coded | 0 |

## Four-statement reminder

When later analysing an episode, keep separate: what the data show | why we
think it happens | what we expect next | how it could be traded.

## Change log

| date | episode_id | change | author |
|------|------------|--------|--------|
| 2026-08-28 | — | M1 empty-ledger closeout: 4234 triaged, 4234 no-episode dispositions, 0 survivors, 0 admissible rows. S4 R3 driver-only absent I2; UNKNOWN ≠ 0. No freeze tag. | M1 closeout |

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
| Protocol | drafted, pending ADR-0002 acceptance |
| Phase 0 — rules pre-registered (thresholds, cutpoints, windows) | **not started** |
| Phase 1 — source sweeps | not started |
| Candidates recorded | 0 (plus 1 fictional example, excluded) |
| Pre-registration freeze | **not frozen** — no market data may be opened |
| Freeze tag | — |
| Freeze commit | — |

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

Completed at Phase 8. Until then this section stays empty.

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

*(not yet run)*

## Inter-rater agreement

Recorded at freeze, per §K.3.

| Metric | Value |
|---|---|
| Exact anchor agreement | — |
| Mean absolute anchor difference (days) | — |
| Severity-class agreement | — |
| Calibration-set entries dual-coded | — |

## Four-statement reminder

When later analysing an episode, keep separate: what the data show | why we
think it happens | what we expect next | how it could be traded.

## Change log

| date | episode_id | change | author |
|------|------------|--------|--------|
|      |            |        |        |

# M6 / M7 — skipped under the <6 kill

Not deferred. Not "next." The kill in `WORKFLOW.md` / `EPISODE_PROTOCOL.md`
Phase 8.7 / ADR-0002 stops the sequence when Sample P < 6.

## M6 — stronger identification

**Result: `SKIPPED_UNDER_KILL`.**

Revised Milestone 6 is "instrument with navigation-basin precipitation"
(`BLUEPRINT_REVIEW.md` table). That step assumes an identified episode/shock
sample. There is none (`N_episodes = 0`). Do not invent an instrument, a
precipitation treatment, or a new estimand to keep the chain moving. That
would be a new Tier A choice.

## M7 — historical replay

**Result: `SKIPPED_UNDER_KILL`.**

Replay needs a mechanism and an identified sample to replay. Neither exists.
Do not build a replay engine, trading UI, or NetworkX cascade graph.

## What remains

M8 is the written negative result: the question is unanswerable with this
data. See `M8_WRITTEN_NEGATIVE_RESULT.md`.

Honesty: UNKNOWN is not zero. Missing I2 is not proof of no physical
disruption. S4 proximity is driver identity only absent I2.

Machine-readable twin: `empty_sample_closeout.yaml`.

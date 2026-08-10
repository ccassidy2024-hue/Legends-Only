# Episode Ledger (pre-registration)

Hand-built primarily from **physical / logistics evidence**, before examining
downstream market outcomes whenever practical.

This table is the project's pre-registration artifact. Effective sample size for
mechanism work is closer to the number of independent episodes than to the
number of weekly observations.

During initial identification, **market outcomes remain intentionally blank**.

Do not invent sources, dates, or release delays. Do not populate episodes from
memory during scaffolding — add rows only from documented physical evidence.

See also: `docs/EPISODE_METHODOLOGY.md`.

---

## Identification rules

1. Define episodes from physical/logistics stress, not from market moves.
2. Prefer contemporaneously knowable information; record what was knowable as-of which dates.
3. Assign severity from physical metrics only (stage, closures, tonnage capacity), never from the size of a price move.
4. Log confounders and exclusion-restriction concerns explicitly.
5. Note substitution channels (PNW, rail, Brazil/other origins) when relevant.
6. Flag crop-production contamination risk for navigation-basin weather episodes.
7. Once market data has been inspected for a research pass, new episode definitions require an ADR.

## Candidate event classes (not yet populated as episodes)

- Mississippi low-water events
- Ohio / Upper Mississippi navigation-basin precipitation shocks
- Lock closures
- Barge disruptions
- Gulf terminal disruptions
- Hurricanes affecting logistics infrastructure
- Rail disruptions
- Extreme logistics congestion

---

## Ledger summary

| episode_id | event_name | event_class | start_date | end_date | geography | severity | defined_before_market_inspection | market_outcomes |
|------------|------------|-------------|------------|----------|-----------|----------|----------------------------------|-----------------|
|            |            |             |            |          |           |          |                                  | *blank during pre-registration* |

---

## Episode detail template

Copy one block per episode. Fill only evidence-backed fields.

### episode_id

`EP-YYYY-###` (assign when recording a real episode)

### event_name

### event_class

One of the candidate classes above, or a clearly named new class.

### start_date / end_date

`YYYY-MM-DD` — first date the constraint was **publicly observable**, not merely when it physically began if that was unknowable.

### geography

### navigation_basin

If applicable (e.g., Lower Mississippi, Ohio, Upper Mississippi, Columbia-Snake). Distinguish navigation-basin geography from crop-growing-region geography.

### physical_shock

What physically happened.

### severity

From physical/logistics evidence only.

### physical_logistics_evidence

Observable operational facts (flows, inventories, congestion, outages, stages, lock status, terminal status, etc.).

### information_available_at_the_time

What was knowable contemporaneously, with publication timing where known.

### source_citations_urls

Named sources only if known. No fabricated IDs.

### lock_river_terminal_rail_impacts

### crop_production_contamination_risk

Especially for weather: does the shock also hit yields/acreage, or is it primarily a transport/navigation shock?

### other_contemporaneous_macro_agricultural_shocks

### pnw_substitution_available

yes / no / unknown — with notes

### rail_substitution_available

yes / no / unknown — with notes

### brazil_or_other_origin_substitution_available

yes / no / unknown — with notes

### possible_confounders

### exclusion_restriction_concerns

### episode_defined_before_market_inspection

yes / no

### researcher_notes

### market_outcomes

**Intentionally left blank during initial identification.**

Populate only in a later, explicitly labeled outcome-documentation pass — never as the reason the episode was selected.

---

## Four-statement reminder

When later analyzing an episode, keep separate:

1. What the data show
2. Why we think it happens
3. What we expect next
4. How it could be traded

---

## Change log

| date | episode_id | change | author |
|------|------------|--------|--------|
|      |            |        |        |

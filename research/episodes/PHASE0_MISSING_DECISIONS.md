# Phase 0 — missing decisions before candidate discovery

**Status:** blocking. **Raised by:** A. **Date:** 2026-08-10.
**Trigger:** attempt to execute source sweep S1 (USACE navigation notices).
**Outcome:** sweep **not executed**. No candidate event was searched for, opened,
or recorded. No source archive was queried for event content.

This memo contains only the decisions that must be frozen before Phase 1 begins.
It proposes no sweep parameter and selects no default. Every item below is for
A + B to decide jointly and commit, per `EPISODE_PROTOCOL.md` §J Phase 0.

---

## 1. Why the sweep stopped

`EPISODE_PROTOCOL.md` §J Phase 0: *"Output: ADR-0002, committed, tagged
`prereg-rules-v1`. **No candidate may be written down before this tag exists.**"*

Current repo state:

| Check | State | Evidence |
|---|---|---|
| `prereg-rules-v1` tag | **absent** | `git tag -l` returns nothing |
| ADR-0002 status | **proposed**, not accepted | `docs/decisions/0002-episode-preregistration.md` L5 |
| ADR-0002 "Open items — must be closed in Phase 0 before any candidate is recorded" | **open** | ibid. L67–74 |
| Phase 0 — rules pre-registered | **not started** | `EPISODE_LEDGER.md` Status table |
| Phase 1 — source sweeps | **not started** | ibid. |

Proceeding anyway would violate Lock 1 (`§0`) — the thresholds and the scope
would end up settled *after* seeing which documents exist, which is the failure
mode the protocol exists to prevent, and it is not detectable afterwards.

---

## 2. What IS already sufficiently registered

These need no further decision; they are not the blocker.

- **Source tiers and admissibility** — §C.1 (Tier 1 explicitly names USACE
  Notices to Navigation Interests, lock status/closure notices, LPMS, channel and
  dredging notices, district navigation bulletins), §C.2 two-source rule,
  quote-or-null, "a URL is not evidence", hash + archive requirements.
- **Event-class vocabulary** — §A.3, 12 classes, extend only by ADR.
- **Inclusion / exclusion tests** — I1–I6, X1–X10, reason codes R1–R13.
- **Public-anchor rule** — §B.3 selection rule and tie-breaks; §B.4 honesty
  rules; date-vs-timestamp discipline; `RULINGS.md` R-001 (date-only anchors map
  to the first analysis anchor **strictly after** the calendar date; no invented
  clock times).
- **Severity** — `cutpoints_registered: false` (§D.3, R-003). Raw physical
  metrics only; no derived class. Prohibited inputs listed at §D.4, including
  barge freight rates.
- **Contamination** — §E classes A–D on both axes, Sample P / Sample X split,
  navigation basin vs growing region kept as separate required fields.
- **Dedup / independence** — H1–H9; R-002 taxonomy with
  `cluster_id = underlying_driver_id` by default.
- **Substitution** — §F channel list and seasonal-state fields.
- **Recording vocabulary for basins** — `episode_schema.yaml` L142–157.
- **Sweep families S1–S8 exist and S1 is named** — §J Phase 1 table:
  *"USACE navigation notices, by district, by year — enumerate the archive;
  keyword-filter for closure/restriction/draft/dredge."*

---

## 3. Blocking decisions — S1 cannot be reproducible without these

### D1 · Sample period (start and end dates)

- **Blocks:** X8 / `R10` ("outside pre-registered sample period") is
  unevaluable; §A.5's "> ~40% of the sample period is in episode ⇒ the class is a
  regime" test has no denominator.
- **Named as open in:** ADR-0002 L69.
- **Note for the decision:** the start date should be fixed by *archive
  coverage*, not by which years look eventful. See §5 for the permitted way to
  establish coverage without touching event content.

### D2 · Corridor list (which navigation basins are in scope)

- **Blocks:** `ADMISSION_CHECKLIST.md` §1 requires "inside the pre-registered
  sample period **and corridor list**". The `navigation_basin` enum in
  `episode_schema.yaml` is a *recording* vocabulary — it says what a basin may be
  called, not which basins the sample covers. These are different objects and the
  checklist requires the second.
- **Named as open in:** ADR-0002 L69.

### D3 · S1 search universe — the enumerated USACE district list and archive endpoints

- **Blocks:** §J specifies "by district, by year" but names no districts. Without
  a committed district list plus the specific archive endpoint per district, the
  sweep is not reproducible and the claim "we did not selectively stop after
  finding familiar events" is unverifiable by a reviewer.
- **Must also register:** what to do where a district publishes navigation
  notices through more than one vehicle, and whether non-district USACE vehicles
  (division bulletins, national navigation pages) are in or out of S1.

### D4 · S1 keyword vocabulary — frozen list

- **Blocks:** §J registers four filter concepts (`closure`, `restriction`,
  `draft`, `dredge`). A longer vocabulary is defensible but is an *expansion*,
  and choosing it mid-sweep makes the recall set tunable after the fact. Freeze
  the exact list, matching rule (stem / substring / case), and whether
  document title only or full text is matched.
- **Constraint from §J:** whatever is frozen, "**no triage during the sweep**".

### D5 · `candidates.csv` — location, schema, and `candidate_id` minting rule

- **Blocks:** §J Phase 1 requires every hit become a row with `candidate_id`,
  `sweep_id`, raw evidence pointer and date. No such file, path or schema exists
  in the repo, and no id format is registered.
- **Coupled to §K.2:** the A/B split is by `candidate_id` parity, so the minting
  order must be deterministic and specified (e.g. a stated sort key) — otherwise
  the workload split is a function of the order documents happened to be read.

### D6 · Raw-capture path for Phase 1 hits

- **Blocks:** §C.2.4 archives under `$GRAIN_DATA_ROOT/episodes/<episode_id>/`,
  but Phase 1 hits have no `episode_id` yet. Register the pre-episode capture
  path and the point at which a hit is rehomed under an episode id.

### D7 · Source-coverage map and the gap policy

- **Blocks:** `R10` also rejects "outside … source coverage", which presupposes
  a documented coverage record. Register how a district-year with no reachable
  archive is recorded — an explicit `coverage: absent` row is required, because
  a silent gap is indistinguishable from a swept-and-empty district.

---

## 4. Also required for the `prereg-rules-v1` tag (not blocking S1 mechanics)

Listed because the tag gates Phase 1, so these block the sweep in practice even
though S1 could technically run without them.

- **D8 · Per-class physical thresholds** (ADR-0002 L69). Specifically needed for
  the §B.3(c) anchor route "a physical value past a **pre-registered** threshold
  together with an operational consequence." Until registered, only the
  binding-operational-restriction route to an anchor is available.
- **D9 · Event window and horizon set** for later local projections
  (ADR-0002 L71).
- **D10 · The three-candidate calibration set** for inter-rater alignment
  (ADR-0002 L74; §K.3.1 requires it *before* any split of work).
- **D11 · The pre-registered concurrent-shock type list** driving §E.3's
  mechanical contamination sweep. Needed at Phase 6, not Phase 1, but it is a
  Phase 0 registration item and `sweep_performed: true` is a hard validator
  condition (E19).
- **D12 · Severity calibration** stays deliberately unregistered per R-003 —
  listed here only so it is not mistaken for an oversight.

---

## 5. What may be done now without breaking either lock

1. **Coverage census, not content.** Establishing which USACE district archives
   exist and which date ranges they span is a *coverage* fact, not an event fact.
   It is the honest input to D1 and D3. Constraint: record only
   `district · vehicle · endpoint · earliest available · latest available ·
   retrieved_on`. Do not open, read, summarise or list individual notices, and do
   not let any observation about what happened in a given year reach the memo.
2. **Write the sweep enumerator code.** Permitted explicitly by §L.1 and
   §L.5.4 — "coding agents may write sweep and validation code; they may not
   write entry YAML content."
3. **Draft the ADR** closing D1–D11 for A + B to review, decide and commit.

Note on division of labour for when S1 does run: under §L.5.2 a **human opens
every URL** and records `retrieved_on`, `sha256` and the verbatim quote. An
assistant may enumerate the archive and produce the raw hit list; it may not
author the evidence that a hit is real.

---

## 6. Recommended next action

Close D1–D7 (minimum) and D8–D11 (for the tag) in an ADR, commit, tag
`prereg-rules-v1`, then run S1. Until the tag exists, `discovery_trail` cannot
honestly carry `origin: sweep` for anything, and a candidate without a `sweep`
origin is rejected `R2` under §L.3 regardless of how well-evidenced it looks.

**Sign-off required:** A ☐   B ☐   ADR committed ☐   tag created ☐

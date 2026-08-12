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
- **Named as open in:** ADR-0002 L69; architecture hardened in ADR-0003.
- **Values remain unresolved:** do **not** invent `sample_start` / `sample_end`.
- **Jointly reviewed architecture (ADR-0003) — no dates chosen:**
  1. One global preregistered `sample_start` / `sample_end` remains mandatory.
  2. Per-source/per-class coverage masks supplement the global period.
  3. Masks affect R10 eligibility, exposure denominators, zero-event
     interpretation, and cross-source/class comparability.
  4. An uncovered interval is **unknown/unobservable** exposure, not zero events.
  5. A source/class beginning after global `sample_start` contributes no eligible
     coverage before its coverage start.
  6. Cross-class/source rates must use explicitly defined covered exposure or an
     explicitly defined common-mask intersection.
  7. §A.5 regime-duration denominators use applicable **covered exposure**, not
     blindly the full calendar length when coverage is incomplete.
  8. Do **not** move `sample_end` earlier merely to guarantee a full post-event
     estimation horizon; right-edge insufficient outcome horizon is an
     analysis-layer right-censoring / eligibility issue to preregister later.
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
- **D13 · Analysis-anchor grid** — **unresolved.** Date-only `public_anchor`
  mapping (R-001 / §B.3) depends on a registered analysis grid. Freeze, at
  minimum:
  - frequency
  - weekday / calendar convention
  - cutoff time
  - timezone
  - holiday treatment
  - missing-anchor handling
  
  **Do not invent these values here.** They depend on Person A's verified
  release-calendar audit and joint A+B ratification. The governing date-only
  mapping rule itself (first analysis anchor **strictly after** the calendar
  date; no invented clock times) is already settled and must not be altered
  by this decision.

### D14 · Source handling, anchor evidence, and historical-release rules — **CLOSED**

- **Status:** **CLOSED** by ADR-0005 (P1–P6) with append-only lookup entries
  R-009…R-014. Independently ratified by A and B; no disagreement.
- **Pointers:** `docs/decisions/0005-source-handling-and-vintage-rules.md`;
  `RULINGS.md` R-009 (P1), R-010 (P2), R-011 (P3), R-012 (P4), R-013 (P5),
  R-014 (P6).
- **Summary of what closed:**
  - anchor-fixing evidence (public-by ≠ public-on; republication early-bound
    rules; fail-closed `needs_review` / `R1`)
  - nonzero `anchor_precision_days` downstream market-response / LP alignment
    firewall pending separate A+B preregistration
  - originating-record independence (clarifying §C.2)
  - document-lifecycle / relief firewall (clarifying §A.5 / H1–H9)
  - release-identity invariant for leakage-sensitive historical as-of values
  - coverage zero-semantics for absence-generating sweeps
  - LNM supplementary / non-discovery / non-absence-generating classification
- **Explicit non-choice:** D14 chooses **no** parameter, endpoint, clock, or
  D13 value. Remaining Phase-0 open items stay D1–D11 and D13 (D12 remains
  deliberately unregistered).

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
3. **Draft the ADR** closing D1–D11 and D13 for A + B to review, decide and
   commit (D12 stays deliberately unregistered per R-003; D14 source-handling
   is already closed by ADR-0005 / R-009–R-014).

Note on division of labour for when S1 does run: under §L.5.2 a **human opens
every URL** and records `retrieved_on`, `sha256` and the verbatim quote. An
assistant may enumerate the archive and produce the raw hit list; it may not
author the evidence that a hit is real.

---

## 6. Recommended next action

D14 (source handling / vintage rules) is closed via ADR-0005 and R-009–R-014.
Close remaining open items **D1–D11 and D13** (D1–D7 minimum for S1 mechanics;
D8–D11 plus D13 for the tag / honest anchor mapping) in an ADR, commit, tag
`prereg-rules-v1`, then run S1. D12 stays deliberately unregistered. Until the
tag exists, `discovery_trail` cannot honestly carry `origin: sweep` for
anything, and a candidate without a `sweep` origin is rejected `R2` under §L.3
regardless of how well-evidenced it looks.

**Sign-off required:** A ☐   B ☐   ADR committed ☐   tag created ☐

---

## 7. Source-timing safety notes (no values invented)

### ESMIS release timestamps

An API timestamp field is not automatically evidence of an observed publication
clock time. For ESMIS, Person A observed identical `12:00:00+0000` time
components across all checked release records. Until official USDA documentation
establishes that clock component as the true publication instant, it MUST NOT be
treated as an observed intraday `release_ts`. Supported date information may be
retained at date precision. No clock time may be fabricated from the ESMIS field.
(Recorded in ADR-0003; generalized by ADR-0005 P4 / R-012 release-identity
invariant — platform/API timestamps establish publication availability only
when source documentation establishes that semantic.)

### Follow-up blocker (out of scope for discovery branches)

`panel.synthesise_release_ts` currently defaults `release_hour=12`. Changing
that shared leakage-sensitive helper requires a **separate** dual-reviewed PR
touching `src/grainsys/panel.py`. Do not attempt it on Phase-0 discovery /
hardening branches.
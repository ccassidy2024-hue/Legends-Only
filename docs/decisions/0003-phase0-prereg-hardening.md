# ADR-0003: Phase 0 pre-S1 preregistration hardening

- **Date:** 2026-08-11
- **Author:** A | B (jointly reviewed rules; Person A implements)
- **Status:** accepted
- **Gate:** A(data) | B(statistics) — Person B must cross-review the implementing PR

## Context

PR #1 (Episode Protocol) and PR #2 (fail-closed discovery infrastructure) are
merged. Before any Phase 1 source sweep, Person B identified enforcement gaps
(N1–N4) and architectural clarifications (D1 coverage masks; ESMIS timestamp
safety). This ADR records those **hardening rules** without selecting unresolved
preregistration *values* (sample dates, corridors, keywords, horizons, D13 grid).

## Decision

### N1 — Deterministic candidate minting

- Candidate order is determined **only** by explicit preregistered `ordering_keys`.
- Duplicate ordering tuples **raise**; input/enumeration position must not break ties.
- Optional source-native stable IDs may dedupe exact duplicate API/index
  representations before minting; conflicting representations raise.
- No invented source IDs.

### N2 — Coverage vs sweep execution

- Keep `coverage_status ∈ {present, absent, unknown}`.
- Add `sweep_status ∈ {not_attempted, attempted_failed, enumerated}`.
- `records_matched` is null unless `enumerated`; `enumerated` requires
  `coverage_status=present`, non-null `records_matched >= 0`, and explicit
  `scope_start` / `scope_end`.
- `earliest_available` / `latest_available` remain archive-history bounds and
  must not be silently reused as sweep scope.

### N3 — Ratification / execution guard

A live `config/discovery/prereg_rules.yaml` does **not** authorize a sweep.
`SweepEnumerator.from_repo` requires fail-closed ratification:

1. config names `governing_adr`
2. ADR status is `accepted`
3. tag `prereg-rules-v1` exists
4. tagged commit holds `config/discovery/prereg_ratification_manifest.yaml`
   with `prereg_config_digest`
5. live config digest matches
6. executing commit is a **descendant** of the tagged commit
7. manifest binds digests of load-bearing interpretation files (see below)
8. undecidable ⇒ block

Load-bearing interpretation files (smallest explicit set):

- `src/grainsys/discovery/config.py`
- `src/grainsys/discovery/sweep.py`
- `src/grainsys/discovery/candidates.py`
- `src/grainsys/discovery/coverage.py`
- `src/grainsys/discovery/governance.py`
- `src/grainsys/discovery/archive_listing.py`
- `src/grainsys/discovery/capture.py`
- `src/grainsys/ingest/ntni.py`
- `src/grainsys/episodes.py`
- `research/episodes/EPISODE_PROTOCOL.md`
- `research/episodes/ADMISSION_CHECKLIST.md`
- `research/episodes/episode_schema.yaml`
- `research/episodes/discovery/candidates/_schema.yaml`
- `docs/decisions/0002-episode-preregistration.md`
- `docs/decisions/0003-phase0-prereg-hardening.md`
- `docs/decisions/0005-source-handling-and-vintage-rules.md`
- `docs/decisions/0015-d3-d4-positive-only-s1.md`

`research/episodes/RULINGS.md` is **not** whole-file digest-bound (it must keep
growing under §I.4). Instead the N3 manifest binds each concrete `R-NNN`
section digest and bound order at canonical path
`research/episodes/RULINGS.md`: later appends after the bound tail are allowed;
edits, deletions, reorders, or insertions into the bound prefix fail closed.
Headings inside fenced examples are ignored; fenced content **inside** a real
ruling body is part of that ruling's digest. Each concrete section body is
canonicalized by stripping trailing blank CR/LF separator lines and ending with
exactly one LF (interior / fenced content and substantive trailing spaces are
preserved) so natural blank-line append and immediate-heading append remain
prefix-stable.

Manifest digests (`prereg_config_digest`, every interpretation digest, every
ruling digest) must be actual lowercase `[0-9a-f]{64}` strings — never
str-coerced. Unknown top-level manifest keys and extra/missing interpretation
paths fail closed.

**Fresh normalized checkout required for manifest build:** before digests are
computed, the live `config/discovery/prereg_rules.yaml` and every load-bearing
working-tree file must match its committed `HEAD` blob byte-for-byte (byte-safe
`git show`). Dirty trees and CRLF drift block. Ratify only from a clean,
normalized checkout.

At manifest build **and** authorization, every load-bearing
`docs/decisions/*.md` ADR in this list must have status `accepted`. The
governing ADR must resolve to a repo-relative path from this list (absolute /
out-of-repo / unbound paths fail closed).

ADR-0004 is **deferred** on branches where the file is absent (e.g. until PR #6
merges). It **must** be added to this load-bearing list before the real
`prereg-rules-v1` tag.

Future Phase-1 rows/captures must be stampable with
`SweepProvenance{prereg_tag, prereg_config_digest, execution_commit_sha, governing_adr}`.
`assert_sweep_authorized` always validates **actual HEAD**. An optional
`execution_commit` argument, if supplied, must be the full lowercase 40-hex SHA
of that HEAD; a caller-claimed different commit is refused. After HEAD is
resolved, the live prereg config and every load-bearing working-tree file must
match the corresponding actual-HEAD blob byte-for-byte; only then are those
bytes compared to the tagged manifest. Restoring old ratified file bytes over a
HEAD that already contains committed drift does not authorize a sweep.

Live `prereg_rules.yaml` is the ratified authority: exact keys at every mapping
and list-entry, no YAML duplicate keys, no unknown/missing keys, no duplicate
source-archive identities, no silently retained untrimmed strings.

Lock-1 remaining decisions D8, D9, D10, D11 and D13 target-date mapping M must
be present as explicit live blocks (value-empty in the template; no defaults).
D8 chooses `registered_thresholds` vs `binding_operational_restriction_only`.
D9 carries pre-event / reference / response horizons and mapping disposition.
D10 binds `count: 3` plus a deterministic selection rule. D11 carries nonempty
shock types plus a sweep rule. D12 remains deliberately unregistered.

P5 inputs live in config: `coverage.absence_generating_families` (S1–S8
subset that may be empty; an empty set means no family is permitted to
generate absence evidence and unknown remains unknown) and
`coverage.source_identity_keys` (nonempty unique subset of allowed identity
fields). Covered exposure is clipped to the registered D1
sample period. Per-event-class coverage masks (item 2 below) are **not** yet a
mechanical input to `compute_covered_exposure`; when registered they must
intersect net exposure. Do not describe current clipping as applying class
masks.

D6 `capture.sweeps_subdir` and D7 `coverage.records_dir` are unset in the
template; live files must supply explicit safe paths. `gap_policy_notes` is the
D7 policy text and must be an actual nonempty string in the live file.

### D1 architecture — global sample period + coverage masks

1. One global `sample_start` / `sample_end` remains mandatory.
2. Per-source/per-class coverage masks supplement the global period.
3. Masks affect R10 eligibility, exposure denominators, zero-event interpretation,
   and cross-source/class comparability.
4. An uncovered interval is **unknown/unobservable** exposure, not zero events.
5. A source/class that begins after global `sample_start` contributes no eligible
   coverage before its coverage start.
6. Cross-class/source rates use explicitly defined covered exposure or an
   explicitly defined common-mask intersection.
7. §A.5 regime-duration denominators use applicable **covered exposure**, not
   blindly full calendar length when coverage is incomplete.
8. Do **not** move `sample_end` earlier merely to guarantee a full post-event
   estimation horizon; right-edge insufficient outcome horizon is an
   analysis-layer right-censoring / eligibility issue to preregister later.

No actual dates or source frames are chosen in this ADR.

### N4 — Matching algorithm capability

Support explicit `whole_word` match mode (plus existing `substring`).
Case-folding is config-controlled. Explicit variants/suffixes are configured
terms only — no stemmer, no hidden morphology, no content-derived regex.
Unsupported modes fail closed. **D4 terms/fields remain unset.**

### ESMIS release-timestamp safety

An API timestamp field is not automatically an observed publication clock time.
For ESMIS: identical `12:00:00+0000` components were observed across checked
release records. Until official USDA documentation establishes that clock
component as the true publication instant, it MUST NOT be treated as an observed
intraday `release_ts`. Date precision may be retained; no clock time may be
fabricated from the ESMIS field.

**Follow-up (separate PR):** `panel.synthesise_release_ts` defaults
`release_hour=12`. That shared leakage-sensitive change is **out of scope** here
and must not be attempted on a discovery-only branch.

## Status of ADR-0002

ADR-0002 is now **accepted**. Merging PR #1 / encoding R-004–R-007 made them
operative. Phase 0 open items (sample period values, corridors, thresholds,
horizons, calibration set, etc.) were resolved via durable A+B Slack
ratifications and persisted to `config/discovery/prereg_rules.yaml` (2026-08-24).
D12 (severity calibration) remains deliberately unregistered per R-003.
See `RULINGS.md` R-008.

## Consequences

- Live sweeps remain blocked until Phase 0 values are chosen, ADR-0002 (or a
  successor) is accepted, `prereg-rules-v1` is tagged with a digest manifest,
  and the execution commit descends from that tag.
- Tests must prove the current repository **refuses** live sweep execution
  without creating the real tag.

## Evidence

`tests/test_discovery_infra.py` covers N1–N4, including isolated temporary git
fixtures for N3. No permanent tag is created.

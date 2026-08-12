# ADR-0003: Phase 0 pre-S1 preregistration hardening

- **Date:** 2026-08-11
- **Author:** A | B (jointly reviewed rules; Person A implements)
- **Status:** proposed
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
- `research/episodes/EPISODE_PROTOCOL.md`
- `docs/decisions/0002-episode-preregistration.md`
- `docs/decisions/0003-phase0-prereg-hardening.md`
- `docs/decisions/0005-source-handling-and-vintage-rules.md`

Future Phase-1 rows/captures must be stampable with
`SweepProvenance{prereg_tag, prereg_config_digest, execution_commit_sha, governing_adr}`.

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

ADR-0002 remains **proposed**. Merging PR #1 / encoding R-004–R-007 does **not**
accept the unresolved Phase 0 open-item package (sample period values, corridors,
thresholds, horizons, calibration set, etc.). See `RULINGS.md` R-008.

## Consequences

- Live sweeps remain blocked until Phase 0 values are chosen, ADR-0002 (or a
  successor) is accepted, `prereg-rules-v1` is tagged with a digest manifest,
  and the execution commit descends from that tag.
- Tests must prove the current repository **refuses** live sweep execution
  without creating the real tag.

## Evidence

`tests/test_discovery_infra.py` covers N1–N4, including isolated temporary git
fixtures for N3. No permanent tag is created.

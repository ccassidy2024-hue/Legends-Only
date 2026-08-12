# Discovery infrastructure (contamination-safe)

Person A ownership. Supports Phase 0 **coverage census** and Phase 1 **sweep
plumbing** without recording episode content.

Package: `grainsys.discovery` (intentionally retained after Episode Protocol
merge — do not rename for speculative redesigns).

Hardening rules: [`docs/decisions/0003-phase0-prereg-hardening.md`](../../../docs/decisions/0003-phase0-prereg-hardening.md)
(N1 minting, N2 coverage/sweep axes, N3 ratification guard, N4 match modes,
D1 mask architecture, ESMIS timestamp safety).

## Absolute constraints

- No historical episode search or ledger population here.
- No individual navigation-notice content is opened or stored by this package.
- Coverage records store archive existence / date-range metadata only; sweep
  execution is a **separate** axis (`sweep_status`).
- Candidate-hit tables stay empty until Phase 0 preregistration is committed
  **and** N3 ratification passes.
- District lists, endpoints, keywords, sample period, and ordering rules come
  **only** from committed preregistration config. Missing config ⇒ **fail closed**.
- A complete live config file alone does **not** authorize a sweep (N3).

## Layout

| Path | Role |
|------|------|
| `config/discovery/_prereg_rules.template.yaml` | Required keys for a future prereg file (nulls only) |
| `config/discovery/prereg_rules.yaml` | **Live** prereg config — intentionally absent until A+B decide Phase 0 items |
| `config/discovery/prereg_ratification_manifest.yaml` | Created only at `prereg-rules-v1` tag time (not present now) |
| `research/episodes/discovery/coverage/_template.yaml` | Coverage + sweep-execution field template |
| `research/episodes/discovery/candidates/_schema.yaml` | Candidate-hit field schema (no real rows) |
| `src/grainsys/discovery/` | Loaders, validators, governance guard, path helpers, sweep interface |

## Blocked by Phase 0 decisions

Authoritative list: [`PHASE0_MISSING_DECISIONS.md`](../PHASE0_MISSING_DECISIONS.md).
Until those are closed, a live `config/discovery/prereg_rules.yaml` is
committed, the governing ADR is `accepted`, and `prereg-rules-v1` is tagged with
a digest manifest:

| Decision | Blocks |
|----------|--------|
| D1 sample period | Global `sample_start`/`sample_end` + coverage-mask architecture |
| D2 corridor list | Which basins are in scope |
| D3 district/endpoint universe | Sweep enumeration targets |
| D4 keyword policy | Terms/fields (algorithm supports `substring` \| `whole_word`) |
| D5 candidate_id minting / candidates.csv location | Live hit table |
| D6 raw-capture path policy | Where pre-episode hits are archived (helpers exist; policy unset) |
| D7 coverage gap policy | How `coverage_status: absent` is required in census |
| D8–D11 | Thresholds / horizons / calibration / shock list (not this infra) |
| D12 | Severity cutpoints — deliberately unregistered (R-003) |
| D13 analysis-anchor grid | Date-only `public_anchor` → analysis-anchor mapping honesty |

### Coverage vs sweep vocabulary (N2)

| Field | Values | Meaning |
|-------|--------|---------|
| `coverage_status` | `present` / `absent` / `unknown` | Archive existence |
| `sweep_status` | `not_attempted` / `attempted_failed` / `enumerated` | Sweep execution |
| `records_matched` | `null` or `int >= 0` | Non-null **only** when `enumerated` |
| `earliest_available` / `latest_available` | dates | Archive history bounds — **not** sweep scope |
| `scope_start` / `scope_end` | dates | Explicit interval for an enumeration result |

Legal examples: `present + not_attempted`; `present + enumerated + records_matched=0`
(genuine swept-zero); `present + enumerated + records_matched>0`.

This package prepares **interfaces and schemas only**. It does not invent
Phase 0 values and does not create `prereg-rules-v1`.

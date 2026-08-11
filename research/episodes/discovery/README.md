# Discovery infrastructure (contamination-safe)

Person A ownership. Supports Phase 0 **coverage census** and Phase 1 **sweep
plumbing** without recording episode content.

Package: `grainsys.discovery` (intentionally retained after Episode Protocol
merge — do not rename for speculative redesigns).

## Absolute constraints

- No historical episode search or ledger population here.
- No individual navigation-notice content is opened or stored by this package.
- Coverage records store archive existence / date-range metadata only.
- Candidate-hit tables stay empty until Phase 0 preregistration is committed.
- District lists, endpoints, keywords, sample period, and ordering rules come
  **only** from committed preregistration config. Missing config ⇒ **fail closed**.

## Layout

| Path | Role |
|------|------|
| `config/discovery/_prereg_rules.template.yaml` | Required keys for a future prereg file (nulls only) |
| `config/discovery/prereg_rules.yaml` | **Live** prereg config — intentionally absent until A+B decide Phase 0 items |
| `research/episodes/discovery/coverage/_template.yaml` | Coverage-record field template |
| `research/episodes/discovery/candidates/_schema.yaml` | Candidate-hit field schema (no real rows) |
| `src/grainsys/discovery/` | Loaders, validators, path helpers, sweep interface |

## Blocked by Phase 0 decisions

Authoritative list: [`PHASE0_MISSING_DECISIONS.md`](../PHASE0_MISSING_DECISIONS.md).
Until those are closed and a live `config/discovery/prereg_rules.yaml` is
committed (and tagged `prereg-rules-v1` per protocol §J):

| Decision | Blocks |
|----------|--------|
| D1 sample period | Coverage interpretation vs sample bounds |
| D2 corridor list | Which basins are in scope |
| D3 district/endpoint universe | Sweep enumeration targets |
| D4 keyword policy | Sweep keyword filter |
| D5 candidate_id minting / candidates.csv location | Live hit table |
| D6 raw-capture path policy | Where pre-episode hits are archived (helpers exist; policy unset) |
| D7 coverage gap policy | How `coverage_status: absent` is required in census |
| D8–D11 | Thresholds / horizons / calibration / shock list (not this infra) |
| D12 | Severity cutpoints — deliberately unregistered (R-003) |
| D13 analysis-anchor grid | Date-only `public_anchor` → analysis-anchor mapping honesty |

### Coverage status vocabulary

`coverage_status` is one of:

| Value | Meaning |
|-------|---------|
| `present` | Covered / archive reachable for the recorded identity |
| `absent` | Unavailable / no reachable archive (explicit gap) |
| `unknown` | Not yet verified (explicit — never silent) |

Do not invent coverage facts; record only verified census metadata.

This package prepares **interfaces and schemas only**. It does not invent
Phase 0 values and does not create `prereg-rules-v1`.

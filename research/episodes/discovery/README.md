# Discovery infrastructure (contamination-safe)

Person A ownership. Supports Phase 0 **coverage census** and Phase 1 **sweep
plumbing** without recording episode content.

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
| `config/discovery/prereg_rules.yaml` | **Live** prereg config — intentionally absent until A+B decide D1–D11 |
| `research/episodes/discovery/coverage/_template.yaml` | Coverage-record field template |
| `research/episodes/discovery/candidates/_schema.yaml` | Candidate-hit field schema (no real rows) |
| `src/grainsys/discovery/` | Loaders, validators, path helpers, sweep interface |

## Blocked by Phase 0 decisions (D1–D11)

See `feat/episode-protocol` memo `PHASE0_MISSING_DECISIONS.md` (PR #1) for the
authoritative decision list. Until those are closed and a live
`config/discovery/prereg_rules.yaml` is committed:

| Decision | Blocks |
|----------|--------|
| D1 sample period | Coverage interpretation vs sample bounds |
| D2 corridor list | Which basins are in scope |
| D3 district/endpoint universe | Sweep enumeration targets |
| D4 keyword policy | Sweep keyword filter |
| D5 candidate_id minting / candidates.csv location | Live hit table |
| D6 raw-capture path policy | Where pre-episode hits are archived (helpers exist; policy unset) |
| D7 coverage gap policy | How `coverage: absent` is required in census |
| D8–D11 | Episode admission / horizons / calibration / shock list (not this infra) |

This branch prepares **interfaces and schemas only**. It does not invent D1–D11
values and does not create `prereg-rules-v1`.

# ADR-0014: REVIEW-ROUTING-v1

- **Date:** 2026-08-24
- **Author:** A | B
- **Status:** accepted / jointly ratified / CLOSED
- **Decision scope:** review-routing governance only (Tier A / B / C +
  independent agent delegation)
- **REVIEW-ROUTING:** CLOSED
- **Gate:** A(data) | B(statistics) — Person B must exact-head review
  persistence fidelity of this ADR if treated as load-bearing governance
  documentation; scientific methodology is unchanged by this ADR
- **Ratification:** Contract **REVIEW-ROUTING-v1** was jointly ratified by
  Human Person A and Human Person B by direct phone agreement on 2026-08-24.
  Human Person A: **AGREE**. Human Person B: **AGREE**. Joint scientific
  closure: **2026-08-24**. No AI review substitutes for either vote. This ADR
  is the operative durable record of that review-routing contract.

This ADR is documentation-only persistence of an already jointly ratified
human decision. It does not create the decision.

It is **forward-looking**. It does **not**:

- retroactively invalidate ADR-0013 or earlier reviews
- reopen CLOSED scientific decisions
- weaken N3 / `LOAD_BEARING_RELATIVE_PATHS`
- authorize discovery or a source sweep
- create `prereg_rules.yaml` or `prereg-rules-v1`
- change CODEOWNERS or GitHub branch-protection settings
- implement D6 capture mechanics
- choose scientific values

Human-readable operational authority remains `WORKFLOW.md`. Machine-readable
companion: `docs/governance/review_routing.yaml`.

## Context

Person A and Person B need a durable routing rule that separates:

1. joint scientific decisions,
2. high-blast-radius implementation that needs exact-head counterpart review
   before merge, and
3. routine faithful implementation of already-settled contracts,

while treating AI-agent mechanical execution as an independent axis that never
reduces human review requirements.

## Decision

Governing contract: **REVIEW-ROUTING-v1**.

Exactly **three** review classes exist: **A**, **B**, and **C**.

There is **no Tier D**.

### A — Joint scientific decision

Explicit Person A + Person B agreement is required before choosing or changing:

- a scientific ADR / ruling
- source / archive family selection
- source completeness / absence-generating classification
- episode eligibility or selection
- candidate / corridor membership
- H7 or exception logic
- severity methodology
- sample-period values
- preregistered estimands / horizons
- lag / alignment semantics
- `release_ts` / as-of interpretation
- outcome-access rules
- multiple-testing / inference methodology
- discovery / freeze / `prereg-rules-v1` authorization
- reopening a CLOSED scientific decision

Tier A is the **scientific decision**. Faithfully implementing an already
ratified decision is not automatically Tier A.

### B — Load-bearing implementation

No new scientific vote.

The owner may independently design, implement, test, push, and open a PR
without waiting for the counterpart.

Counterpart **exact-head** review is required **before merge** for
high-blast-radius shared implementation, including:

- panel / as-of alignment
- lag logic
- leakage tests
- statistical inference implementation
- freeze / accounting gates
- candidate identity / lineage mechanics
- capture immutability / provenance
- episode-schema validation logic
- governance authorization gates

Approval binds to the exact reviewed commit SHA.

Any subsequent code/content change to the reviewed implementation invalidates
approval and requires re-review. PR title/body-only changes do **not**
invalidate code approval.

Once valid counterpart approval exists, **either** researcher may press Merge.
The reviewer need not physically perform the merge.

Phone/text review may count only when:

- the exact head SHA is stated,
- the reviewer confirms they actually reviewed that exact diff/state,
- approval is durably transcribed to the PR, and
- no code changes occur afterward.

Do not impersonate the reviewer on GitHub.

### C — Routine implementation

No counterpart approval required.

The owner may self-merge after required CI passes when faithfully implementing
an already-settled contract, including:

- documentation / persistence of settled decisions
- ordinary tests that do not change scientific semantics
- already-registered source adapters
- deterministic parsing
- fixtures
- lint / type / CI fixes
- semantics-preserving refactors
- README / docs
- ordinary path / config plumbing

If implementation exposes a **new** scientific choice: **STOP** that point and
escalate to Tier A. Do not silently choose.

### Agent delegation (independent axis)

Agent delegation is **not** a review tier and is **not** Tier D.

Cursor / Claude Code / Codex / similar agents may mechanically execute an
authorized task or settled spec without approval for every individual step.
Agent delegation **never** reduces A/B/C review requirements.

Agents may mechanically:

- create branches
- implement settled specs
- run tests
- fix mechanical lint/type failures
- generate deterministic artifacts
- open PRs
- summarize diffs
- monitor CI
- sync branches
- produce status / handoff reports
- retrieve from an exact already-authorized endpoint / query

Agents may **not** independently:

- choose scientific values
- infer source completeness
- interpret silence / unknown as zero
- choose episodes
- inspect forbidden market outcomes
- weaken tests
- reinterpret a CLOSED ADR

## Human ratification

| Researcher | Vote | Date |
|---|---|---|
| Human Person A | AGREE | 2026-08-24 (direct phone agreement) |
| Human Person B | AGREE | 2026-08-24 (direct phone agreement) |

Joint scientific closure: 2026-08-24.

No AI review substitutes for either vote.

## Immediate consequence

**REVIEW-ROUTING-v1 is CLOSED.**

Operational rendering: `WORKFLOW.md`.
Machine-readable companion: `docs/governance/review_routing.yaml`.

This ADR does **not** authorize discovery, weaken N3, reopen CLOSED scientific
decisions, or start D6 mechanical implementation.

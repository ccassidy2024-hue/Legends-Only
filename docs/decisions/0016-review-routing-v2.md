# ADR-0016: REVIEW-ROUTING-v2

- **Date:** 2026-08-24
- **Author:** A | B
- **Status:** accepted
- **Decision scope:** review-routing governance only (Tier A / B-RED / B-STANDARD / C +
  independent agent delegation)
- **REVIEW-ROUTING:** CLOSED
- **Gate:** A(data) | B(statistics) — exact transcription of jointly ratified Slack
  decision; no new science
- **Ratification:** Contract **REVIEW-ROUTING-v2** was jointly ratified by
  Human Person A and Human Person B by direct phone agreement on 2026-08-24,
  with immediate authorization posted in Slack thread `1787597569.176769`.
  Human Person A: **AGREE**. Human Person B: **AGREE**. Joint scientific
  closure: **2026-08-24**. No AI review substitutes for either vote. This ADR
  is the operative durable record of that review-routing contract.

This ADR is documentation-only persistence of an already jointly ratified
human decision. It does not create the decision.

## Changes from REVIEW-ROUTING-v1

REVIEW-ROUTING-v2 addresses coordination inefficiencies observed during Phase-0:

- Science was often approved once, then effectively re-approved on implementation PRs
- Exact-head reviews were sometimes requested before the branch was truly frozen
- Stale audits treated "not yet persisted" as "not yet decided," reopening settled values
- Cursor + Claude sometimes duplicated the same mechanical audit
- Claude latency/nudging became unnecessary critical-path delay
- Routine docs/source/status work accumulated PR/review ceremony
- Human asks were drip-fed rather than batched into one decision packet

## Decision

Governing contract: **REVIEW-ROUTING-v2**.

Supersedes: **REVIEW-ROUTING-v1** (ADR-0014).

Exactly **four** review classes exist: **A**, **B-RED**, **B-STANDARD**, and **C**.

There is **no Tier D**.

### A — Joint scientific decision (batched)

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

One approval of a decision packet authorizes faithful downstream implementation.
Humans do **not** re-approve the same science per PR.

### B-RED — Counterpart human exact-head review required

No new scientific vote.

The owner may independently design, implement, test, push, and open a PR
without waiting for the counterpart.

Counterpart **exact-head** human review is required **before merge** only for
silent-invalidity code surfaces:

- `panel.py` / as-of joins / `release_ts` alignment
- lag-direction / alignment
- core leakage tests
- discovery authorization / N3 freeze / tag guard

Review request only **after** head is frozen + CI green. Any content change
invalidates approval.

Approval binds to the exact reviewed commit SHA. PR title/body-only changes do
**not** invalidate code approval. Once valid counterpart approval exists,
**either** researcher may press Merge.

### B-STANDARD — No second human required

Load-bearing but deterministic implementation of already-ratified science:

- D2 constructor / membership mechanics
- candidate identity / lineage
- capture provenance
- source adapters / normalization
- episode-schema validation
- deterministic parsers
- prereg value persistence that introduces no new science

Requirements:

- Owner-scoped branch
- Green CI
- Independent exact-head **agent** review

Automation may merge when those pass. If reviewer discovers a new scientific
choice: **STOP** and escalate to Tier A.

### C — Self/automation merge on green CI

No counterpart approval required.

- Documentation / persistence of settled decisions
- Source notes / status sync
- Ordinary tests / fixtures
- Registered adapters
- Paths / config plumbing
- Semantics-preserving refactors
- Lint / CI fixes

If implementation exposes a **new** scientific choice: **STOP** and escalate to
Tier A.

### Agent delegation (independent axis)

Agent delegation is **not** a review tier and is **not** Tier D.

Cursor / Claude Code / Codex / similar agents may mechanically execute an
authorized task or settled spec without approval for every individual step.
Agent delegation **never** reduces A/B-RED/B-STANDARD/C review requirements.

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

## Process rules

1. Batch all genuine A+B decisions into one smallest packet; no one-field-at-a-time approvals.
2. No review request until CI green + head frozen.
3. No duplicate agent audits unless Tier A or B-RED risk justifies an independent red-team.
4. Claude is optional red-team, never routine critical path.
5. After strongest official-source verification fails to prove completeness, preserve UNKNOWN / positive-only where allowed instead of repeating the same source hunt.
6. Maintain one concise operational checkpoint after merges: `CURRENT_MAIN | OPEN_PR | SCIENCE_GATES | REVIEW_GATES | NEXT_ACTION`.
7. Do not create a new ADR for routine implementation detail; ADRs are for durable scientific/governance decisions.

## Human ratification

| Researcher | Vote | Date |
|---|---|---|
| Human Person A | AGREE | 2026-08-24 (direct phone agreement) |
| Human Person B | AGREE | 2026-08-24 (direct phone agreement) |

Joint scientific closure: 2026-08-24.

No AI review substitutes for either vote.

Authorization posted: Slack thread `1787597569.176769` in #legends-only.

## Immediate consequence

**REVIEW-ROUTING-v2 is CLOSED.**

Operational rendering: `WORKFLOW.md`.
Machine-readable companion: `docs/governance/review_routing.yaml`.

This ADR does **not** authorize discovery, weaken N3, reopen CLOSED scientific
decisions, or start D6 mechanical implementation.

# ADR-0005: Source handling, anchor evidence, and historical-release rules

- **Date:** 2026-08-12
- **Author:** A | B
- **Status:** proposed
- **Gate:** A(data) | B(statistics) — Person B must cross-review the implementing PR
- **Ratification:** Propositions P1–P6 were independently ratified by both
  researchers with **no disagreement**. This ADR is the operative normative home
  of that package. Precedent lookup entries R-009…R-014 in `RULINGS.md` point
  here; they do not replace this ADR.

## Context

Phase 0 hardening (ADR-0003) and the Episode Protocol leave several source-
handling edge cases under-specified in ways that would become irreversible once
candidate discovery begins under Lock 1:

1. **Anchor evidence** when the only document in hand is a late republication
   vehicle (public-*by* evidence vs affirmative public-*on* evidence).
2. **Independence** when republications cross publishers/formats.
3. **Document lifecycle** events mistaken for episode identity or relief.
4. **Historical release identity** for leakage-sensitive as-of values (value
   provenance vs timestamp provenance).
5. **Coverage zero-semantics** for absence-generating sweeps with known gaps.
6. **LNM classification** relative to registered sweep families.

This ADR records the jointly ratified P1–P6 package for binding at
preregistration. It selects **no** Phase-0
parameter values and does **not** create `prereg-rules-v1`.

## Decision

### P1 — Anchor-fixing standard

Evidence that a fact was public **by** a date does not by itself fix
`public_anchor`.

The canonical anchor requires affirmative evidence supporting the underlying
fact's public availability **on** the anchor date.

For a republication vehicle, prior-issue silence may never establish the early
bound. The early side of any window must be bounded within the existing
`{0,1,3,7}` `anchor_precision_days` framework by affirmative evidence (the
document's own dated statement of the underlying order's issuance or
publication, quote-or-null; or the originating document itself). An issuance
date may bound public availability only when the source semantics establish
that issuance itself made the information public; an internal or operational
issuance date is not automatically public availability.

If the early side cannot be so bounded, the anchor fails closed:
`needs_review` / reason code `R1` if unresolved. Rejected and needs-review
records remain auditable; the correct meaning is that the episode **cannot be
accepted** with that unresolved anchor — not that the record "does not enter
the ledger."

No new one-sided or interval-valued anchor datatype is introduced. R-001 / R-004
continue to govern point-date / date-only mapping.

**Downstream firewall (also part of P1).** R-001/R-004 establish the
point-date/date-only mapping but explicitly do **not** define how nonzero
`anchor_precision_days` changes downstream baseline behavior. Therefore:

> Where `anchor_precision_days > 0`, market-response event-window / local-
> projection alignment is **blocked** until A+B separately preregister how
> nonzero anchor uncertainty affects t=0 and pretreatment baseline
> construction.

Ledger admission and descriptive use remain possible if the episode is otherwise
admissible. This ADR does **not** invent that later alignment rule.

### P2 — Originating-record independence (clarifying precedent)

§C.2 source independence is assessed by independent evidentiary lineage /
**originating record**, not document count. The underlying principle is already
in §C.2.1 (same-district same-notice example); this proposition records the
cross-publisher / cross-format case as clarifying precedent.

Republications, reprints, continuations, or derivative documents from the same
underlying notice never supply the second independent Tier-1 source regardless
of publisher, vehicle, format, or file type.

They may still provide:

- corroboration
- contemporaneous knowability evidence (I4)
- preservation evidence

The existing fallback for genuinely single-Tier-1-source classes (§C.2.1:
1 Tier 1 + 2 Tier 2, `source_confidence: medium`, mandatory review) is unchanged.

### P3 — Document-lifecycle / relief firewall (clarifying precedent)

Document lifecycle events including reissue, continuation, renumbering,
amendment publication, cancellation, format change, and cross-vehicle migration
do **not by themselves** create, split, merge, re-anchor, or terminate an
episode. §A.5 and H1–H9 remain controlling. Lifecycle facts may be retained in
the supporting source record and relevant existing descriptive fields, but do
not by themselves determine episode identity or relief.

Cancellation counts as documented relief only when the cancellation itself or
another qualifying Tier-1 source affirmatively establishes restoration of:

- unrestricted operation, **or**
- explicitly pre-episode baseline operation.

Withdrawal, expiry, supersession, disappearance, or silence are not relief by
themselves and do not start the ≥21-day relief / recurrence clock.

### P4 — Release-identity invariant

P4 is a **normative historical-release provenance invariant** at this stage. It
states the admissibility rule for leakage-sensitive as-of analysis; it does
**not** by itself add mechanical enforcement in existing code paths.

For leakage-sensitive historical as-of analysis, an observation
`(series_id, period_end, release_ts, value)` is admissible only when its
`value` and `release_ts` resolve to the **same** identified historical
release/vintage through stable release identity.

The current four-column observation interface remains unchanged:
`series_id`, `period_end`, `release_ts`, `value`. This ADR does **not** add
`source_release_id` or any other observation column. ADR-0001 is not modified.

**Exact invariant:**

> An observation may enter leakage-sensitive as-of construction only if there
> exists a single identified historical release R such that:
>
> 1. `release_ts` is R's defensible public availability, established under the
>    project's applicable source-timing rules; no intraday publication time may
>    be fabricated, and a platform/API/system timestamp may establish
>    publication availability only when source documentation establishes that
>    semantic;
> 2. `value` is the value **as stated in R**, evidenced by R itself or by an
>    immutable archive/capture of R (hash, snapshot, vintage endpoint);
> 3. the link value→R is by **stable release identity** — report identifier +
>    issue date, document/content hash, archive snapshot identifier, vintage
>    endpoint identifier, or equivalent — never by `(series_id, period_end)`
>    coincidence alone.

**Consequences:**

- A value from a mutable current-state store does not carry historical release
  identity merely because it describes an old period. It may **not** inherit an
  older `release_ts` from an unrelated historical artifact.
- Every corrected/superseded vintage is a distinct release with its own
  availability. A later corrected value may never inherit the earlier vintage's
  `release_ts`.
- Platform/API/system timestamps establish publication availability only when
  source documentation establishes that semantic (ESMIS and similar cases are
  instances of this one rule; see also ADR-0003).
- Literal same-file provenance is **not** required where multiple artifacts are
  affirmatively linked to the same release identity; the identity burden is
  affirmative and stable.
- Current descriptive use without a historical `release_ts` claim remains
  possible where otherwise allowed; §D.4 bars (e.g. barge freight rates as
  severity inputs) remain independent of vintage status.

Mechanical enforcement of P4 belongs in later ingestion/provenance work and
requires the normal dual-review process where leakage-sensitive. The current
absence of such enforcement must **not** be read as though existing code
already proves the invariant.

### P5 — Coverage zero-semantics

For absence-generating / exhaustive sweep families:

- covered exposure = union(enumerated scopes) minus affirmatively known gap
  subintervals;
- known intra-scope gaps must be explicit interval-scoped coverage records
  (`absent` / `unknown` rows), not prose hidden in `notes`; for an
  affirmatively known gap, the absent/unknown coverage row must carry explicit
  `scope_start` and `scope_end` identifying the gap interval;
- multiple interval-scoped rows per source are permitted under the existing
  coverage schema (no new fields);
- `records_matched: 0` means zero matching records among the accessible records
  actually enumerated over the resulting **net** covered scope — it does **not**
  prove no real-world event occurred;
- historical archive retention completeness is an acknowledged shared
  limitation and is never presumed merely because an archive endpoint exists;
- supplementary positive-evidence families do not generate absence exposure /
  swept-zero claims unless later promoted into an exhaustive sweep family.

No `enumeration_completeness` field (or other new `coverage.py` field) is
introduced by this ADR.

### P6 — LNM classification

USCG Local Notices to Mariners are currently:

- supplementary corroboration evidence
- public-knowability / public-by evidence
- non-exhaustive
- non-absence-generating
- **not** an independent candidate-discovery family

LNM may support an episode surfaced through a **registered** sweep. It does not
independently generate candidate rows under the current architecture.

Promoting LNM into a sweep family requires a future preregistered D3-compatible
ADR defining scope/endpoints. P5 then applies. This ADR does **not** perform
that promotion and names no LNM endpoints, districts, keywords, dates, or clocks.

## Ratification binding (N3)

ADR-0005 is added to `LOAD_BEARING_RELATIVE_PATHS` in
`src/grainsys/discovery/governance.py` and to ADR-0003's documented load-bearing
list. When `prereg-rules-v1` is later created, this ADR's content is bound into
the ratification manifest's interpretation digests. Post-tag drift of this file
must fail closed under `assert_sweep_authorized`.

`research/episodes/RULINGS.md` deliberately remains **outside**
`LOAD_BEARING_RELATIVE_PATHS`. EPISODE_PROTOCOL §I.4 requires the precedent log
to continue growing during later phases; binding it would force digest churn on
every new ruling. R-009…R-014 are append-only lookup entries that cite this ADR
as the governing normative record.

This ADR does **not** create the live `prereg_rules.yaml`, the
`prereg-rules-v1` tag, or the ratification manifest.

## What this ADR does NOT decide

This ADR chooses **no**:

- D1 dates
- D2 corridors
- D3 endpoints
- D4 keywords
- D5 candidate parameters
- D6 capture values
- D7 actual coverage endpoints
- D8 thresholds
- D9 horizons
- D10 candidate-selection mechanics
- D11 shock types
- D13 grid values
- release clock / timezone
- severity cutpoints
- timestamp baseline methodology for nonzero `anchor_precision_days`

D12 remains deliberately unregistered (R-003).

It also does not invent the later market-response alignment rule for nonzero
`anchor_precision_days` (P1 firewall only), does not modify ADR-0001's frozen
observation schema, and does not reopen R-001…R-008.

## Consequences

- Source-handling disputes covered by P1–P6 are decided by this ADR; R-009…R-014
  are the append-only lookup layer.
- Unresolved republication anchors fail closed (`needs_review` / `R1`); they are
  not silently accepted and are not erased from the audit trail.
- Market-response event-window / LP alignment remains blocked for any accepted
  episode with `anchor_precision_days > 0` until a separate A+B preregistration
  closes that firewall.
- Historical as-of ingest must satisfy the release-identity invariant; mutable
  current-state values do not acquire historical `release_ts` by coincidence.
- Absence-generating sweeps must represent known gaps as explicit interval rows;
  `records_matched: 0` is scoped to net covered exposure only.
- LNM does not mint candidates until a future D3-compatible promotion ADR exists.
- Live Phase-1 sweeps remain blocked until remaining open Phase-0 items are
  closed, a governing ADR is accepted, and `prereg-rules-v1` is tagged under
  ADR-0003 N3 rules.

## Evidence / enforcement staging

**This branch (pre-tag):**

- ADR-0005 text (this file)
- `RULINGS.md` R-009…R-014 append-only entries
- load-bearing path registration in `governance.py` + ADR-0003 list sync
- D14 closed pointer in `PHASE0_MISSING_DECISIONS.md`
- coverage template comment documenting P5 semantics
- isolated N3 regression proving ADR-0005 digest binding and post-tag drift block

P4 is normative at this stage only. Existing code does not mechanically prove
the release-identity invariant; this PR does not add `source_release_id` or
change the four-column observation schema.

**Later (ordinary dual-reviewed lanes; not this ADR):**

- ingest-layer / provenance mechanical enforcement of P4 (leakage-sensitive;
  dual review required)
- optional validators / `source_role` schema for P1/P2 enforcement
- optional cross-row coverage overlap checks for P5 (pre-tag only if touching
  digest-bound `coverage.py`)
- separate preregistration of nonzero-`anchor_precision_days` baseline /
  event-window alignment
- any future LNM sweep-family promotion ADR

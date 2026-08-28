# Mechanism Memo: empty-sample negative result (no identified shock-to-flow arrow)

Status: **Gate C FAIL signed; M5 complete**. Negative-result retained. Not a
positive thesis, not evidence of no disruption, and not evidence of market
efficiency. This file is the M5 mechanism / literature memo required by
`BLUEPRINT_REVIEW.md` revised milestone 5 and `research/memos/MEMO_TEMPLATE.md`.
It does **not** reopen market outcomes, mint episodes, or claim a trade thesis.

Marker: `M5_SIGNED_FINAL_STATE`

Regenerable counts: frozen D5 / Phase-2 / catalog / ledger artifacts plus
`tests/test_m5_negative_result_memo.py`. `make all` must pass. No empirical
beta, lag, HAC t, or max-t p is claimed.

School academic-database search (`WORKFLOW.md` AJAE / JCM / AEPP / TRE / Fed):
**not performed**. A Gate C FAIL memo does not become a PASS by literature
volume.

---

## 1. Claim

There is no admissible Episode Ledger shock, so no authorized statement of the
form "X shock causes Y to move Z direction over H weeks, via M" can be
estimated. The M5 result is a **negative result for sample construction**, not a
finding that U.S. grain logistics were undisrupted and not a finding that
calendar spreads do not respond to river stress.

---

## 2. What the data show

Effective N = number of episodes = **0**. Unconditional vs regime-conditional
effects: **not estimable**. Best lag, beta, HAC t, max-t corrected p: **not
estimable** (none invented). Naive p is not reported.

| Object | Value | Regenerable from |
|---|---|---|
| Frozen D5 candidates | **4234** (S1=37, S4=4197) | `research/episodes/discovery/candidates/` |
| No-episode dispositions | **4234** (S1=37 R12, S4=4197 R3) | `no_episode_dispositions.csv` |
| Survivors / admissible episode rows | **0** / **0** | ledger generated summary |
| Real episode YAML | **0** (example `EP-0000-000` excluded) | `research/episodes/entries/` |
| Catalogued real series / real as-of rows | **0** / **0** | `catalog/series/` |
| M2 | `M2_NEGATIVE_RESULT_EMPTY_SAMPLE` | `research/milestones/` |
| M3 event-window screener | `NOT_ESTIMABLE`; family size 0, never-run | `m3_empty_family_multiplicity.yaml` |
| M4 local projections | `NOT_ESTIMABLE` (zero identified shocks) | same |
| Sample P | **0** (< `WORKFLOW.md` kill of 6) | ledger + closeout YAML |
| M8 | `M8_WRITTEN_NEGATIVE_RESULT_UNANSWERABLE` | `M8_WRITTEN_NEGATIVE_RESULT.md` |

Honesty conditions (not optional):

- UNKNOWN is not zero.
- Missing I2 operational evidence is not proof of no physical disruption
  (`ADMISSION_CHECKLIST.md` §1).
- S4 POINT_ONLY 100 NM HURDAT2 proximity is driver identity only absent I2.
- M3 "nothing survived max-t" is false: the family was never run.

Market outcomes remain unopened. No freeze tag authorizes opening them.

---

## 3. Why we think it happens

Two layers. Do not collapse them.

### 3a. Why the sample is empty (construction, not a grain-flow mechanism)

Phase-2 I1/I2/I3 triage of frozen D5 produced 0 survivors under already-closed
science. Episode YAML was not invented. Real series were not catalogued; source
IDs and `release_ts` were not invented (ADR-0001). A non-empty real panel would
be fabrication. Do not infer "no disruption occurred" from failed I2 or UNKNOWN.

### 3b. Hypothesized physical/behavioural arrows (labeled **hypothesis**, not findings)

These are the project's pre-registered *questions* from `BLUEPRINT_REVIEW.md`.
None is estimated here.

1. **Spatial residual duration (hypothesis).** When barges cannot clear
   arbitrage, `(gulf_bid − interior_bid) − barge_cost` stays positive. The
   *duration* of that residual, not its level, is the object that could
   rationally change a storage decision. Level is hypothesized to be priced
   immediately by desks that watch freight every day.
2. **Substitution / adaptation (hypothesis).** When the river binds, the
   marginal bushel may go rail/PNW; the marginal world buyer may switch to
   Brazil/Argentina. If those valves work, U.S. futures need not move much.
3. **Navigation-basin instrument (hypothesis, M6 skipped).** Upstream
   precipitation/snowpack may shift barge capacity without being crop-yield
   weather. Growing-region precipitation is a common driver and would invalidate
   the exclusion restriction. Not implemented: Sample P < 6.
4. **Agents.** Elevators, merchandisers, and barge lines decide whether to wait,
   store, or reroute. Futures speculative flow is a different agent. Whether
   those information sets diverge is Gate F, not a result.

Hurricane Ida (Aug–Sep 2021) is named in `BLUEPRINT_REVIEW.md` §5 as an
*illustrative* Gulf-outage natural experiment (public NHC storm context, not a
ledger row). It is **not** in the Episode Ledger and must not be treated as a
sample episode.

---

## 4. Prior literature

Gate F depends on this section. Databases searched with school credentials:
**none**. Terms below are the project's own vocabulary plus the named sources.
This is a bounded institutional/method map, not an exhaustive review.

### Established institutional / method facts (not our estimates)

- **Theory of storage / carrying charge.** Working, Holbrook. 1948. "Theory of
  the Inverse Carrying Charge in Futures Markets." *Journal of Farm Economics*
  30(1): 1–28. DOI [10.2307/1232678](https://doi.org/10.2307/1232678). Working,
  Holbrook. 1949. "The Theory of Price of Storage." *American Economic Review*
  39(6): 1254–1262. JSTOR stable
  [1816601](https://www.jstor.org/stable/1816601). Do not label `10.2307/1816601`
  a resolving DOI. These papers motivate why percent-of-full-carry is the
  natural Y *if* a shock existed. They do not estimate this project's arrow.
- **Local projections.** Jordà, Òscar. 2005. "Estimation and Inference of
  Impulse Responses by Local Projections." *American Economic Review* 95(1):
  161–182. DOI [10.1257/0002828053828518](https://doi.org/10.1257/0002828053828518).
  Method for M4; unused because there is no identified shock.
- **USDA AMS Grain Transportation Report.** Weekly barge/rail/truck/ocean
  volumes and prices, including origin-to-export spreads and barge rates
  (review-named GTR Tables 2A/2B and 9).
  https://www.ams.usda.gov/services/transportation-analysis/gtr
  Barge quotes as percent of a 1976 origin-specific tariff cannot be compared
  across origins without tariff bases (`BLUEPRINT_REVIEW.md` §2).
- **FAS Export Sales** are *forward commitments*, published weekly by USDA FAS.
  https://www.fas.usda.gov/programs/export-sales-reporting-program
  Query system: https://apps.fas.usda.gov/export-sales/
- **FGIS inspections** are *physical shipments* under official inspection /
  weighing, not the same object as Export Sales (`BLUEPRINT_REVIEW.md` §8).
  The AMS FGISonline page is the application portfolio for official inspection
  and weighing processes, not a substitute for a weekly inspections series
  YAML (none is catalogued).
  https://www.ams.usda.gov/services/fgisonline
- **NASS Grain Stocks** is a quarterly Principal Federal Economic Indicator
  (on- and off-farm; March/June/September/December reference dates). It is not
  a fresh weekly level. `BLUEPRINT_REVIEW.md` §8 additionally warns of revision
  behavior; that warning is a project rule, not a fact established by the NASS
  survey page cited here.
  https://www.nass.usda.gov/Surveys/Guide_to_NASS_Surveys/Off-Farm_Grain_Stocks
- **HURDAT2** is NHC best-track, used here only as S4 *driver identity*.
  Format: Landsea, Franklin, Beven, May 2015,
  https://www.nhc.noaa.gov/data/hurdat/hurdat2-format-atlantic.pdf
  Landsea, Franklin, Blake, Tanabe, Feb 2016,
  https://www.nhc.noaa.gov/data/hurdat/hurdat2-format-nencpac.pdf
  Frozen archives (in-repo SHA256): Atlantic
  `1b9b0c7beed5b4505838658b1d30e159fc84330c60891a58cfcf43ae55c37202`; Pacific
  `db65f8bc538d5c05e15f738c96111861d6ce3572c007879de58e44d4d05a9cd6`.
- **USACE NTNI** is positive-evidence-only, not completeness
  (`docs/sources/USACE_NTNI_S1_POSITIVE_ONLY.md`).

### Project conjecture (not findings)

Duration-of-residual; PNW/rail and Brazil origin substitution as escape valves;
navigation-basin IV; delayed underreaction. "Someone published the residual-
duration event study in 2016" was **not** checked. "Nobody has" is therefore
**not** claimed, and cannot be used as Gate F evidence.

Venues still required before any future Gate C *pass*: *American Journal of
Agricultural Economics*, *Journal of Commodity Markets*, *Applied Economic
Perspectives and Policy*, *Transportation Research Part E*, USDA AMS/ERS
reports, Kansas City / Minneapolis Fed ag finance (`WORKFLOW.md`).

---

## 5. Confounders considered and how ruled out

Not estimable. There is no estimate to confound. Standing landmines for a
*future* non-empty sample (`BLUEPRINT_REVIEW.md` §8), not ruled out:

- Seasonality / week-of-year (full-sample seasonal demeaning is look-ahead for
  OOS claims).
- Common driver: drought moves river stage *and* yield *and* price.
- Release-timing artifacts (`release_ts`; Export Sales vs inspections; quarterly
  Grain Stocks).
- Origin substitution (PNW, Brazil) absorbing a U.S. price effect.
- Roll artifacts on generic continuous front-month contracts.

---

## 6. Why this is not an accounting identity

Two separations:

1. **This memo's result** (empty sample) is a construction outcome, not
   `spread = price difference − freight`.
2. **The hypothesized research object**, if a future sample existed, would have
   to be a *residual or duration*, not the raw interior-to-Gulf spread versus
   barge rate. USDA publishes both sides of that identity. A significant
   `barge_rate → interior_basis` scan would be plumbing (`BLUEPRINT_REVIEW.md`
   §2). That identity was not "found" here because no scan was run.

---

## 7. Falsification

**Of this negative-result memo (construction):** it is false if committed
artifacts without new science show a real accepted episode YAML, a catalogued
real series with documented `release_ts`, a non-empty ADR-0001 real as-of panel,
a claim that UNKNOWN / missing I2 equals zero, or an invented beta/lag.

**Of the hypothesized arrows (only in a future non-empty sample):** a residual
that never persists; substitution that fully absorbs interior stress; an LP
path on corn DEC–MAR percent-of-full-carry that is zero at all horizons after
honest HAC and episode-clustered errors; or a result that is the accounting
identity in disguise.

---

## 8. Red-team output

Independent adversarial review from a **different non-Anthropic, non-Grok**
model, launched read-only against the frozen *draft* SHA of this memo.
The block below is verbatim. A later SHA may correct citation labels; it does
not rewrite this critique.

**Provenance**

- Draft SHA reviewed: `74c4120f195b701ed5f09a2c050c5d39abed1026`
- Reviewer agent: `bc-459fb6f8-3172-50ba-971d-0bfb19da93ac`
- Reviewer model: GPT-5.6 (`gpt-5.6-sol-high`)
- Date: 2026-08-28
- Verdict: `FAIL_MEMO_OVERCLAIMS`

**Verbatim reviewer block**

```
The narrow result holds: this frozen repository contains zero admissible episode rows, so no shock-to-flow estimate or trade thesis is authorized. The memo does not establish that no admissible shock exists. Its zero is primarily a source-discovery and provenance failure: 4,197 observations are storm-node proximity pairs—not independent episode candidates—and their identical R3 dispositions merely restate that HURDAT2 cannot supply operational evidence. The 37 S1 candidates were rejected because their capture bodies were fixture HTML rather than verifiable historical notices. S2 and S8 were not attempted, while several other families scanned listing pages but left underlying documents UNKNOWN. NTNI’s short retention window also creates severe survivorship bias. Describe this as “no episodes identified by this incomplete, positive-only evidence pipeline,” not a substantive negative result about disruptions.

Hurricane Ida is correctly excluded, but calling it an illustrative natural experiment still imports a memory-selected positive mechanism. A storm track or NHC context does not prove a grain-logistics outage, public anchor, or usable instrument. Likewise, persistent spatial residuals, rail/PNW rerouting, and South American substitution remain conjectures. A positive residual could reflect mismatched locations, grades, timing, handling charges, tariff conversion, or omitted all-in freight costs—not binding capacity or delayed adaptation.

Gate F is overstated. With no identified effect, no market outcomes, and no academic-database search, mispricing was not assessed. “No mispricing” may be a conservative decision rule, but it is not an evidentiary result. The defensible conclusion is “no trade authorized; Gate F not estimable.”

The Working citations distinguish 1948 from 1949 correctly, but `1816601` is a JSTOR stable identifier; `https://doi.org/10.2307/1816601` does not resolve, so it should not be labeled a DOI. The NASS page supports quarterly publication and scheduled revisions, not the unqualified description “heavily revised.” The FGISonline URL describes an authenticated application portfolio and is weak support for the claim that inspections equal physical shipments; cite the actual export-inspection report or methodology. HURDAT2 is post-storm best-track data and cannot establish contemporaneous public knowledge.

The falsification section also conflates invalid procedure with falsification: a future claim equating UNKNOWN with zero would invalidate the analysis, not falsify the current artifact count. The relevant falsifiers are a reproducible count mismatch or an admissible row produced from the same frozen universe and rules.

RED-TEAM VERDICT: FAIL_MEMO_OVERCLAIMS
```

Author note (not part of the critique): Gate F #5 remains the closed-list
*decision rule* from `BLUEPRINT_REVIEW.md` §7 and M8, not an estimated finding
that markets are efficient. The empty ledger is an identification/pipeline
result, not proof that disruptions did not occur. JSTOR 1816601 is not labeled
a DOI in §4 of later SHAs. Ida stays out of the sample.

---

## 9. Gate decision

Gate C: **fail / negative-result retained**

Allowed template values: `pass | fail | unexplained-but-retained`.
This memo uses **fail**, with the negative result retained as the M5 record
(aligned with M8 `M8_WRITTEN_NEGATIVE_RESULT_UNANSWERABLE`).

Human signatures are **signed**. They were not forged in this commit. They
record the Slack A+B approval of frozen memo head
`0e58688260e8fe42f210a70cf55a04dd19ac3c59` (PR #54), which is an ancestor of
post-merge `origin/main` `52c3bcb47e677f081300d9b250cbc5712111be4b`.

Provenance: Slack TS `1787903087.410749` (channel C0BS23LRC05):
`M5_GATE_C_SIGN @ 0e58688260e8fe42f210a70cf55a04dd19ac3c59 | A=SIGN_FAIL_NEGATIVE_RESULT | B=SIGN_FAIL_NEGATIVE_RESULT`

| Role | Decision | Signature | SHA bound |
|---|---|---|---|
| Person A | `SIGN_FAIL_NEGATIVE_RESULT` | signed | `0e58688260e8fe42f210a70cf55a04dd19ac3c59` |
| Person B | `SIGN_FAIL_NEGATIVE_RESULT` | signed | `0e58688260e8fe42f210a70cf55a04dd19ac3c59` |

**Gate C FAIL signed; M5 complete.** This remains a negative-result retained,
not a PASS, not a trade thesis, and not a finding that disruptions did not
occur or that markets are efficient.

---

## Four-statement separation (principle 10)

| Statement | This memo |
|---|---|
| What the data show | D5=4234, all disposed, 0 survivors, N_episodes=0, no real event-window screener/LP; UNKNOWN is not zero; missing I2 is not no disruption |
| Why we think it happens | Construction: closed I1/I2/I3 plus no invented series. Hypotheses (not findings): residual duration, substitution, navigation-basin IV |
| What we expect next | M5 complete as Gate C FAIL signed. M6/M7 stay skipped. Market data stays closed. |
| How it could be traded | It cannot. Gate F #5 **no mispricing** is the default. Items 1–4 cannot be evidenced. No thesis. |

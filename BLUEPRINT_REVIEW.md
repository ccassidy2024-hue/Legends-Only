# Blueprint Review

The blueprint is well-organised and the epistemics are unusually disciplined
for a project at this stage — the gates, the "what this is NOT" section, and
the separation of *what the data show* from *why we think it happens* are all
genuinely good and should survive unchanged.

The problems are structural, not cosmetic. Eight of them, ranked by how much
damage they do if left alone.

---

## 1. The effective sample size is about 6, not about 800 — **fatal if unfixed**

The blueprint's entire statistical apparatus — FDR control, rolling stability,
walk-forward validation, 26-lag scans — presumes hundreds of roughly
independent observations. Fifteen years of weekly data looks like 780 rows.

It isn't. The regime the project cares about is *Mississippi low-water
constraint*, which has occurred in roughly 2012, 2022, 2023, and 2024. High
water adds 2011 and 2019. Weekly observations *within* an episode are close to
perfectly autocorrelated: the river doesn't independently redraw its stage each
Friday. **Your effective N is the number of episodes.**

Consequence: you cannot data-mine your way to a discovery here. There is not
enough independent information in the dataset to support an unconstrained
search, and any screener output will be an artifact with high probability.

I measured this. Two **independent** AR(1) series (φ = 0.9, like real
logistics and price data), 780 weekly observations, scanning 27 lags and
reporting the best one:

```
best-lag naive p < 0.05 fires:         32.3%     (should be 5%)
median max|t| under the null:           1.58
95th percentile max|t| under the null:  3.28
honest |t| threshold:                   3.28     (not 1.96)
```

**One in three "discoveries" from a naive 27-lag scan on pure noise clears
p<0.05.** Reproduce it yourself: the simulation is in this repo's history and
the corrected estimator is `screening/lagscan.py::maxt_pvalue`.

### The fix — invert Milestone 1

Milestone 1 should not be the screener. It should be the **Episode Ledger**:
a hand-built table of 15–25 dated system-stress events, constructed *before
looking at any market data*, with start dates set to when the constraint became
publicly observable and severity assigned from physical data only.

Template is at `research/episodes/EPISODE_LEDGER.md`. That table *is* your
sample. The screener then runs within and around those windows, which
collapses the multiple-testing problem and makes the exercise an event study
rather than a fishing expedition.

This is a genuine reordering of the project, not a caveat. §20–21 should be
rewritten around it.

---

## 2. Half of what the screener will find is an accounting identity

Spatial arbitrage means:

```
gulf_bid − interior_bid  ≈  freight cost interior→Gulf
```

USDA publishes **both sides of this** — GTR Table 2A/2B is literally "origins
to export position price spreads," and Table 9 is the barge rates. A screener
pointed at `barge_rate → interior_basis` will return a beautiful, stable,
highly significant edge, and it will mean nothing. It's plumbing. It is true
by construction and every trade desk knows it.

### The fix — screen the residual, not the spread

Define it explicitly and make it a first-class series:

```
spatial_residual = (gulf_bid − interior_bid) − barge_cost_per_bu
```

Near zero when barges clear the arbitrage. Persistently positive when capacity
is binding and grain physically *cannot* move regardless of price.

**Hypothesis worth actually testing:** it is the *duration* of a positive
residual, not its level, that predicts downstream inventory redistribution and
calendar-spread response. Level is priced instantly; persistence requires
someone to conclude the constraint is not transitory and change a storage
decision. That's where a lag can plausibly live.

Stub is at `catalog/series/spatial_residual_corn.yaml`. Note the units trap:
AMS quotes barge rates as **% of a 1976 benchmark tariff that differs by
origin**. You cannot compare 550% at St. Louis to 550% at Twin Cities without
each origin's tariff base. Conversion helper is in
`ingest/agtransport.py::barge_pct_tariff_to_dollars_per_bushel`, but you must
source the tariff schedule first. This will eat a day. Budget it.

---

## 3. The system map omits the two substitution channels that decide the answer

§6 runs Production → Storage → Transport → Elevators → Gulf → Export. It is
Gulf-only and closed. Two things are missing, and they are the whole game:

**PNW / rail substitution.** When the river binds, the marginal bushel goes by
rail to the Pacific Northwest. AMS now publishes a Columbia-Snake barge rate
series and shuttle-train secondary market bids. The Gulf–PNW spread is the
single best observable of adaptation in the system. It belongs in the catalog
as a `role: adaptation` series.

**Brazil / Argentina origin substitution.** This is the likely answer to "why
doesn't the market react?" When Gulf freight spikes, the marginal *world buyer*
switches origin to Paranaguá. US futures don't need to move much, because
global supply is unchanged — only the routing is. Any thesis that ignores
Brazilian FOB premiums and the Brazilian interior freight situation will get
run over by exactly this.

Add both, or the mechanism is missing its own escape valve and every result
will be biased toward finding a US price effect that substitution actually
absorbs.

---

## 4. Replace the graph-path cascade search with local projections

§8 and Milestone 4 build a NetworkX graph and search for length-3 and length-4
paths. Two problems:

- **Errors compound.** Three edges at 70% confidence is 34% confidence in the
  path. Four is 24%. Reported as a "cascade," this dramatically overstates what
  you know.
- **Lags don't add.** A 1-week edge plus a 2-week edge is not a 3-week effect.
  Overlapping dynamics don't compose that way.

### The fix

**Jordà local projections.** Identify *one* shock (a low-water episode, or the
residual crossing a threshold), then run a separate regression of each response
variable at each horizon h = 0…26 on that same shock:

```
y_{t+h} = α_h + β_h · shock_t + controls_t + ε_{t+h}
```

The path of β_h *is* the cascade — first order at short h, adaptation at medium
h, the inventory/spread consequence at long h — estimated off one identified
shock with correct (HAC) standard errors and honest confidence bands. It
answers the project's actual question ("what are the 1st/2nd/3rd order
effects?") directly, in a single estimator, and it produces a chart that is
publishable rather than a graph that is suggestive.

Keep NetworkX, but demote it: it's for **documenting** the hypothesised system,
not **discovering** cascades.

---

## 5. You have a real instrument — name it and use it

§11 says "instrumental variables if a credible instrument exists." One does.

Mississippi river stage is driven by **upstream basin precipitation and
snowpack**, which are plausibly exogenous to corn *prices* while directly
determining barge capacity. That's a textbook instrument, and it upgrades the
project from "predictive pattern" to "identified causal effect."

Caveat that must be handled explicitly, not waved at: drought is a **common
driver** — it moves river stage *and* yields *and* prices simultaneously.
The exclusion restriction only holds if you instrument with precipitation in
the *navigation basin* (Ohio, Upper Mississippi) rather than in the *growing
region*. That distinction is the difference between a valid instrument and a
completely spurious one, and it's why Hurricane Ida (Aug–Sep 2021) is the most
valuable row in your episode ledger: a Gulf terminal outage with a known start
date and no drought confound at all. It is as close to a natural experiment as
this system offers.

---

## 6. Name the tradeable instruments now, because it changes what's worth researching

§3.5 lists twelve possible outputs. Most aren't tradeable by you:

- **Cash basis** — not a tradeable instrument
- **Barge freight** — no liquid derivative
- **Crush spread** — tradeable, but it's a soybean processing story, largely orthogonal to river logistics

What's actually left:

| Instrument | Why | Liquidity |
|---|---|---|
| **Corn CZ–CH calendar spread** | Direct expression of storage economics. Full carry = pays to store; inverse = pays to ship now. **This is the natural target.** | Good |
| Corn CH–CK, CK–CN | Same logic, later crop year | Good |
| Soybean SX–SF | Bean equivalent, shorter storage window | Good |
| ADM, BG, ANDE | Own the physical assets that monetise dislocation | Good, but noisy — logistics is a small share of the story |
| UNP, NSC | Rail substitution beneficiaries | Very noisy; second-order at best |

**Recommendation: anchor the project on the corn DEC–MAR spread as the default
Y from day one, and broaden only if the screener forces it.** Expressed as
*percent of full carry* rather than raw cents — that normalises across price
levels and interest-rate regimes, and it is how the trade actually thinks about
it. You'll need the prevailing rate and commercial storage rate to compute it.

Building a spread series correctly matters more than it sounds: construct
explicit contract pairs per crop year. **Never a generic continuous
front-month.** Roll artifacts at contract change look exactly like signal and
they arrive seasonally, which is precisely when your shocks arrive.

---

## 7. Gate F needs a menu, and the honest prior is that it fails

§23's Gate F asks whether the effect is "delayed, underfollowed, misunderstood."
As written it's an invitation to motivated reasoning — you will always be able
to tell yourself a story.

Be blunt about the prior: **basis and barge freight are followed obsessively.**
Cargill, ADM, Bunge and CHS employ people whose entire job is the interior-to-
Gulf spread. The base rate on "we found free money in the most-watched physical
grain spread in the world" is very low.

So force Gate F to pick from a closed list and produce evidence:

1. **Segmentation** — cash traders know; futures speculative flow doesn't; transmission is slow. *Evidence: COT positioning lag, or basis moving before spreads.*
2. **Capital constraint** — monetising requires physical storage/ownership, so financial players structurally can't. *Evidence: the effect is largest in cash, smallest in futures.*
3. **Horizon mismatch** — a 6–12 week effect is too slow for CTAs, too fast for macro. *Evidence: fund-flow horizons.*
4. **Seasonal narrowness** — tradeable eight weeks a year, so nobody builds infrastructure for it. *Evidence: effect concentrated in harvest/post-harvest.*
5. **No mispricing.** ← the honest default

If you can't evidence one of 1–4, write up #5 and stop. That's still a real
result, and it's a much better artifact than a thesis nobody believes.

---

## 8. Data landmines the blueprint doesn't flag

These will each cost you days:

- **Export Sales ≠ Export Inspections.** FAS weekly Export Sales are *forward
  commitments*; FGIS inspections are *physical shipments*. Different objects,
  different release timing, different revision behaviour. §13 lists inspections
  as an "inventory/stock proxy" — it's a flow. Conflating them will produce
  nonsense.
- **Grain Stocks is quarterly and heavily revised.** The Sept 1 corn stocks
  number is one of the most-revised statistics USDA publishes. Use it as a
  quarterly *anchor* only. Never forward-fill it into a weekly panel as a level
  — `Panel.drop_stale()` exists for exactly this, and the `age_days` frame
  shows you when a "current" value is 11 weeks old.
- **Vintages.** §14 mentions revisions as a caveat; it needs to be an
  architectural requirement. Every observation carries `release_ts`. This is
  enforced in `panel.py` and tested in `tests/test_leakage.py` — the panel
  builder will refuse data that would leak.
- **Seasonality.** §14 mentions week-of-year controls; the Milestone 1 spec
  doesn't require them. Make seasonal demeaning the **default**, not an option.
  Note the honest distinction: full-sample seasonal demeaning is mildly
  look-ahead and is fine for *screening*, not for anything reported as
  out-of-sample — use `expanding_seasonal_demean` there.
- **Control for `y[t-1]`.** The difference between "x predicts y" and "x
  predicts something already visible in y's own history" kills most spurious
  commodity results on contact. On by default in `ScanConfig`.

---

## What to keep, unchanged

- §14 statistical guardrails — better than most professional research plans
- §18 "what this is NOT" — reread it monthly
- §23 gates A–E
- §26 separating *what the data show* / *why* / *what's next* / *how to trade*
- §22's list of things not to solve yet — and add "the NetworkX graph" to it

---

## Revised milestone order

| # | Was | Now |
|---|---|---|
| 1 | Screener V0 | **Episode Ledger** (pre-registered, no market data) |
| 2 | Robustness | **As-of panel + leakage tests** (done — see `panel.py`) |
| 3 | Regime engine | **Screener with max-t correction**, run inside episode windows |
| 4 | Cascade graph | **Local projections** off the identified shock |
| 5 | Mechanism research | Mechanism memos + **literature review** (new, and required) |
| 6 | Causal modelling | Instrument with navigation-basin precipitation |
| 7 | Historical replay | Keep as-is — this is the best milestone in the blueprint |
| 8 | Trade thesis | Corn DEC–MAR spread, in percent-of-full-carry, **or a written negative result** |

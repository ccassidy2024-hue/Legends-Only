# Working Agreement — Two People, One Repo, Five AI Assistants

Read this before writing any code. It exists to solve one problem: two people
and a fleet of AI agents can generate work far faster than they can generate
*trustworthy* work, and this project dies from unreproducible results long
before it dies from a lack of ideas.

---

## 1. The parallelism problem, and the fix

Two people in one research repo collide in three predictable places:

| Collision | Why it happens | Fix |
|---|---|---|
| Shared catalog file | Both add series to `catalog.csv` → conflict every commit, git resolves CSV badly, rows silently vanish | **One YAML per series** in `catalog/series/`. `catalog.csv` is a gitignored build artifact. Two people can add 40 series in parallel with zero conflicts. |
| Notebooks | `.ipynb` is JSON with embedded output; every run rewrites every cell → unmergeable | **Notebooks are gitignored.** Use `.py` files with `# %%` cells (VS Code interactive). Cursor and Claude Code also handle `.py` dramatically better than `.ipynb`. |
| Data files | Binary parquet in git bloats the repo and diffs are meaningless | **`data/` is gitignored.** Data is reproducible from `src/grainsys/ingest/`. Raw pulls cache to a shared folder via `$GRAIN_DATA_ROOT`. |

### Ownership boundaries

The single most effective move is **contract-first ownership**: agree the
interface in hour one, then never touch each other's directory.

```
Person A — "the plumbing"          Person B — "the statistics"
  src/grainsys/ingest/               src/grainsys/screening/
  src/grainsys/panel.py              src/grainsys/modeling/
  catalog/series/*.yaml              tests/fixtures/ + # %% scripts
  research/episodes/                 research/memos/
```

See also `TASKS_A.md` and `TASKS_B.md`.

**The interface between you is frozen and short:**

```python
# long-format observations
columns = ["series_id", "period_end", "release_ts", "value"]

# and the panel builder that consumes them
Panel = build_asof_panel(obs, anchors)   # .values, .age_days
```

That is the whole contract. A changes how data arrives; B changes what is done
with it; neither blocks the other.

### The trick that actually unblocks B on day one

**A's first commit is a synthetic fixture, not real data.** A writes
`tests/fixtures/make_synthetic_panel.py` that emits a panel matching the schema
exactly — right shape, right dtypes, right release-lag behaviour, fake numbers.

B then builds the entire screener, the regime engine, and the local-projection
code against that fixture, before a single byte of USDA data exists. When A
swaps in real data, B's code already runs. Without this, B spends week one
waiting and week two rewriting.

### Shared, append-only, never conflicts

- `docs/decisions/NNNN-*.md` — one file per decision, numbered. Both write freely.
- `research/memos/` — one file per mechanism.
- `research/episodes/EPISODE_LEDGER.md` — the one shared table. Edit it
  **together, on a call**, not asynchronously. It is short and it is the
  project's pre-registration; it deserves the synchronous time.

---

## 2. Git

Trunk-based, short-lived branches.

```bash
git switch -c feat/barge-ingest
# work, commit early and often
git push -u origin feat/barge-ingest
# open PR
```

**Review rules — deliberately asymmetric:**

| Change touches | Review needed |
|---|---|
| `src/grainsys/panel.py`, `screening/lagscan.py`, `tests/` (esp. leakage/lag) | **Mandatory** review by the other person. No exceptions, no self-merge. |
| Anything else in `src/` | PR + other person's 👍, self-merge OK |
| `docs/`, `research/`, `notebooks/` | Push straight to main |

The asymmetry is the point. Alignment and lag code is the surface where a
silent bug invalidates every downstream result, and it is also exactly where
AI-generated code fails in ways that look correct. Everything else can be
fixed later; leakage cannot, because you won't know it happened.

CI (`.github/workflows/ci.yml`) runs `ruff` + `pytest` on every PR. If the
leakage tests fail, the PR does not merge. Do not weaken a test to make CI
green — that is the one unforgivable move in this repo.

---

## 3. Assigning the AI fleet

You have more assistants than the project needs. Undirected, they will produce
five contradictory versions of the same analysis. Assign them roles.

| Tool | Role | Rule |
|---|---|---|
| **Claude Code** | Repo-level implementation, refactors, writing tests | One person runs it at a time, on their own branch, in their own directory. **Never two agents on overlapping files.** |
| **Cursor** | Inline edits during interactive exploration | Fine to use simultaneously — scope is a single file |
| **Perplexity Pro / Gemini Deep Research** | Source discovery: finding the data, finding the release calendars, finding the tariff schedules | Output lands in `docs/sources/` with the URL, never pasted numbers |
| **School academic databases** | **Gate F literature review** — see below | Highest-value tool you have, and the blueprint doesn't use it at all |
| **ChatGPT Pro / a second Claude thread** | Adversarial red-team | Formal gate step, see below |
| **Refinitiv Workspace** | Futures settlement history, contract-pair spreads, crush | Only source for market data. Build contract pairs explicitly, never continuous front-month |
| **Capital IQ** | Segment financials for the equity expression layer (ADM, BG, ANDE, UNP, NSC) | Late-stage only, Milestone 8 |

### The literature review is your actual edge

The blueprint has no literature review step. This is its largest omission,
because Gate F ("is the market underweighting this?") is unanswerable without
knowing what is already published.

Agricultural transportation economics is a real, mature literature. Before any
mechanism memo passes Gate C, search — with your school credentials — across
*American Journal of Agricultural Economics*, *Journal of Commodity Markets*,
*Applied Economic Perspectives and Policy*, *Transportation Research Part E*,
plus USDA AMS and ERS technical reports and the Kansas City / Minneapolis Fed
ag finance publications.

Two outcomes, both valuable:

- **Someone published this in 2016.** You just saved six weeks, and the paper
  hands you a specification, a sample period, and a set of confounders.
- **Nobody has.** That is genuine evidence for Gate F — the first real evidence
  you'll have that the effect might be underfollowed.

Neither outcome is available to someone without library access. Use it.

### Red-teaming as a required gate

Before a mechanism memo passes Gate C, paste it into a **different model** with
an explicitly adversarial prompt:

> Here is a proposed causal mechanism and the evidence for it. Argue that it is
> spurious. Identify the confound, the accounting identity, the seasonal
> artifact, or the survivorship effect that most likely explains it. Assume the
> author is fooling themselves.

Log the response verbatim in §8 of the memo. Different model families fail
differently; using Claude to red-team Claude's own reasoning is much weaker
than using GPT or Gemini.

### The rule that makes AI assistance safe

> **No number enters a memo unless it survives `make all` on a clean clone.**

AI assistants produce plausible numbers in chat windows. Those numbers are not
results. If it isn't regenerable from committed code, it does not exist.

---

## 4. Cadence

For two people working part-time around other commitments:

- **Monday, 60–90 min, synchronous.** Scope the week, assign, update the
  episode ledger together, make gate calls.
- **Async midweek.** Push daily even if incomplete. A branch nobody has seen
  in five days is a merge problem.
- **Thursday, 45 min.** Review PRs, walk through the week's charts, log ADRs.

**Timebox the whole thing.** The blueprint has eight milestones and no dates,
which is how a side project quietly becomes a permanent one. Proposed:

| Week | Target | Kill condition |
|---|---|---|
| 1 | Repo, catalog schema, episode ledger, synthetic fixture | — |
| 2–3 | 15 verified series, as-of panel builds, leakage tests green | Can't get clean release timestamps for the core series → rescope |
| 4–5 | Screener + max-t correction running on real data | Nothing survives max-t correction → go straight to episode study, skip the screener |
| 6–7 | Episode/event study on the ledger; local projections | Fewer than 6 usable episodes → the question is unanswerable with this data; say so and stop |
| 8 | 2–3 mechanism memos, red-teamed, lit-reviewed | — |
| 9–10 | Trade thesis **or** a written negative result | — |

A well-written negative result is a real deliverable. "We tested whether
Mississippi low-water episodes predict the corn DEC–MAR spread beyond what
freight costs mechanically imply, and they do not, for these reasons" is a
credible piece of research and a far better outcome than a tortured thesis.
Agree now that this counts as success, before either of you is emotionally
invested in a positive finding.

---

## 5. Day one, in order

1. Both: read `BLUEPRINT_REVIEW.md`, agree or argue about the structural changes.
2. Together, 30 min: agree the observation schema. Write ADR-0002 recording it.
3. A: `python -m grainsys.ingest.agtransport --catalog` → dump the full
   AgTransport dataset list, verify the four-by-four ids, fill in
   `catalog/series/*.yaml`, flip `verified: true` as each is confirmed.
4. B: build the synthetic fixture, get `pytest` green, start the regime engine
   against fixture data.
5. Together, 60 min, on a call: fill in the episode ledger. Dates and severity
   from physical data only. **Do not open a price chart during this session.**
6. Both: pick your red-team model and stick with it.

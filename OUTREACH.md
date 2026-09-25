# Outreach: where this paper should go, and in what shape

The paper measured three judgment layers and found **transferable defects** in two of them.
That makes outreach a different job from "announcing a paper": a maintainer who receives
"here is my paper about your project" has to work out whether it is a favour or an attack.
A maintainer who receives **a specific defect with a reproduction** can act on it.

So there are **three channels with three different shapes**, and mixing them is what gets a
submission ignored or resented.

Last verified against the live repos: 2026-09-23.

---

## Posted 2026-09-23 — all six, in parallel

<!-- BEGIN GENERATED: status -->
### Status, regenerated from the live APIs

*Derived by `src/analysis/p99_refresh_outreach_status.py`; the most recent change among these items
is 2026-09-25 01:38 UTC. Nothing in this block is typed by hand.*

| # | What was sent | Where | Status |
|---|---|---|---|
| 1 | **Defect report** — truncated flag fires at a fixed 3,193 characters regardless of the loaded checkpoint, so it is 111 characters late on one and thousands early on the others | [NandhaKishorM/laya#174](https://github.com/NandhaKishorM/laya/issues/174) | **OPEN** — 3 comment(s), last change 2026-09-23 07:30 UTC |
| 2 | **Defect report** — conflicted and undecided unreachable in 7 live jev_check readings; genuine contradiction returns insufficient | [typesafe-ai/typesafe-sdk-python#11](https://github.com/typesafe-ai/typesafe-sdk-python/issues/11) | **CLOSED** (`not_planned`) 2026-09-24 12:06 UTC |
| 3 | One entry, *Open reproductions and research* — Add an independent measurement of Jev's typed decisions (Open reproductions and research) | [cobanov/awesome-jev#77](https://github.com/cobanov/awesome-jev/pull/77) | ✅ **MERGED** 2026-09-22 17:37 UTC by `cobanov` |
| 4 | One entry, *Evaluations and independent research* — Add an independent measurement of Jev's typed decisions (Evaluations and independent research) | [AbdelStark/awesome-typesafe-jev#99](https://github.com/AbdelStark/awesome-typesafe-jev/pull/99) | ✅ **MERGED** 2026-09-22 19:51 UTC by `AbdelStark` |
| 5 | One table row, *Benchmarks, calibration, and open reproductions* — Add an independent three-layer measurement (Benchmarks, calibration, and open reproductions) | [Anil-matcha/awesome-jev-by-typesafe#63](https://github.com/Anil-matcha/awesome-jev-by-typesafe/pull/63) | ✅ **MERGED** 2026-09-22 19:56 UTC by `Anil-matcha` |
| 6 | One entry, *Calibration & Research* (source file and README mirror) — Add an independent measurement of Jev's calibrated fields (Calibration & Research) | [yibie/awesome-jev#155](https://github.com/yibie/awesome-jev/pull/155) | ✅ **MERGED** 2026-09-23 02:06 UTC by `yibie` |

### This account's footprint in `NandhaKishorM/laya`

| | count |
|---|---|
| PRs **merged** | **24** |
| PRs open | 14 |
| PRs closed unmerged | 1 |
| issues closed | 7 |
| issues open | 4 |

**Merged:** #94, #169, #210, #211, #212, #222, #227, #228, #230, #231, #232, #234, #236, #237, #249, #299, #368, #371, #375, #376, #378, #379, #380, #381

**Open now:** #174, #208, #377, #389, #394, #416, #418, #419, #420, #422, #423, #424, #425, #426, #427, #428, #454, #455

### Reach

| | value |
|---|---|
| `NandhaKishorM/laya` | ≈23,100 stars |
| Zenodo, English paper | [22901853](https://zenodo.org/records/22901853) — 180 views · 14 downloads |
| Zenodo, Chinese paper | [22902025](https://zenodo.org/records/22902025) — 8 views · 1 downloads |
| Zenodo, artifact | [22901248](https://zenodo.org/records/22901248) — 16 views · 0 downloads |
| this repository, clones (last 14 days) | 142 (75 unique) |
| this repository | ≈0 stars |
<!-- END GENERATED: status -->

> **Every status in the table above read `OPEN` when it was first written, and that was true for
> about a day.** It is the same failure the paper documents — a field correct at the moment it was
> typed, attached to an object that then moved. It then went stale **a second time**, which is why
> that block is **generated from the APIs and not typed**: run
> `python src/analysis/p99_refresh_outreach_status.py` to refresh it, `--check` to see whether it is
> current. Everything below this line is hand-written, and deliberately carries no status that can
> rot.

Every one declares the `laya-mcp` maintainership, and every one states that Jev is **one of
three** layers measured rather than the sole subject. Item 2 declares in the body that its
seven readings have **no artifact behind them**; items 3–6 each name their own weakest point
in the entry text rather than leaving it to be discovered.

### What came back

**The defect reports did what they were for.** Both were acted on by people who did not have to.

- **`laya#174` (the truncation flag).** A third party, `@bunnysayzz`, traced it to
  `build_sequence` in `laya/common.py` — the state is cut with `st[:room]` and the function
  returns only `(ids, markers)`, so no caller can know evidence was dropped — and opened
  [#176](https://github.com/NandhaKishorM/laya/pull/176) with an opt-in `return_info`.
  The maintainer replied that **[#181](https://github.com/NandhaKishorM/laya/pull/181) is the fix
  he is taking**, and that it reports `truncated`, the dropped token count and the affected
  questions **from the budget actually applied** — precisely the constraint the report raised,
  that the window depends on the loadout and not on the checkpoint name. Neither has merged yet.
- **A second, larger defect found on the way: `laya#168`.** Investigating the flag led to
  `detect_script`, which counts an alphabetic character only when a listed range claims it, so
  text in any unlisted script was routed to the **English** checkpoint. Measured: **92,529 of
  Unicode's 136,104 alphabetic codepoints (68%)** match no range. Fixed by
  [PR #169](https://github.com/NandhaKishorM/laya/pull/169) — **merged 2026-09-23**, the
  maintainer recording that fullwidth Latin now reads as Latin and that no English text changed
  route across 20,000 states.
- **`laya#156` (the `noul` label defect)** is the one the paper records as defect 6. It did not
  come from this round of posting but ran in the same window: three independent reproducers
  (`@MrJev`, `@AlKor13` and this author), maintainer confirmation, and — the outcomes that
  matter — **the shipped README documents it**, and **the issue is now closed**. Two fixes landed
  around the close: an opt-in `labels` override
  ([#163](https://github.com/NandhaKishorM/laya/pull/163)), and
  [#249](https://github.com/NandhaKishorM/laya/pull/249) — **authored in this project** — which
  turns a `noul` `criteria` dict keyed anything but `true`/`false` from a **silent substitution**
  into an **error**. **The bias itself is unfixed**; it needs a retrained checkpoint. Under
  *Honest limits* in `NandhaKishorM/laya`, shipped since tag `v0.3.7`:

  > **`noul` can follow its option labels instead of the state, most strongly on `laya`
  > (English).** `noul` renders its two options as `false:` / `true:`, and on the English
  > checkpoint that label pair can dominate the answer, returning a confident "no" for clearly
  > positive input (#156). *Until a retrained checkpoint lands, check `noul` answers on your own
  > data.* … ask the same question as a two-option `choice` with neutral keys …

  The recommended workaround is a two-option `choice` with **neutral keys** — which is *not* the
  path this project's P19 battery used (`noul`, with `"true"`/`"false"` criteria keys).
  Upstream's own guidance therefore corroborates the qualification the paper places on
  `explicit_support 0.9909`. One caveat, measured by a third party on 0.3.20: the `labels`
  override helps on `laya` but is **worse than the default on `laya-typed-decisions`**, so the
  mitigation is checkpoint-dependent.

**One report landed on the wrong project.** `typesafe-sdk-python#11` was closed on 2026-09-24 as
**`not_planned`**, because `jev_check` is not a TypeSafe tool or endpoint — it comes from
third-party community MCP servers that wrap `typesafe_sdk`, and *"the verdict mapping and
`jev_check` harness do not exist in the official SDK"*. **The paper was already right about
this**: it names the Jev-side access layer as **the DSH plugin** and calls the verdict vocabulary
*"**the plugin's**"*, never TypeSafe's. So what was wrong was the **venue, not the attribution** —
the same family of error as everything in `results/ERRATA.md`, committed in the outreach rather
than in the paper. A maintainer also asked for a reply *"yourself and not via the AI"*; that is
recorded here rather than argued with, because it is a fair thing to want.

**What the larger footprint is.** Beyond the six posts, this account filed a long series of
defect reports and fixes into `NandhaKishorM/laya` over 2026-09-22…24 — the counts, the merged
list and the reach figures are in the generated block at the top of this file, because they
change faster than a hand-written table survives. Two facts from it are worth keeping in prose:
the reports were **defects with reproductions rather than announcements of a paper**, which is
why they were acted on; and **two of this paper's own defects ended up with upstream fixes or
documentation**, which is a larger effect than the paper's own download counts.

**Two things went wrong while posting, both caught before they became public:**

- The draft's `typed-decisions` row carried **multilingual's** clamp onset (7,966 instead of
  6,967), which also made the derived error wrong. Found by reading
  `results/P3-clamp-calibration.json` instead of trusting the draft.
- The first clone of the yibie fork was the **wrong fork** — `PerryLink/awesome-jev` is the
  fork of `cobanov/awesome-jev`; yibie's is `PerryLink/awesome-jev-1`. The clone was verified
  to have no `categories/` directory before anything was committed.

---

## Channel map

| Channel | What to send | Why |
|---|---|---|
| **[NandhaKishorM/laya](https://github.com/NandhaKishorM/laya)** (★18,608 as of 2026-09-23, Apache-2.0, issues on) | **A bug report, not the paper.** One scoped defect with a repro. | The paper's Laya findings are *critical* (accuracy 0.225 on 77-class, Δ_catch negative in 3/3 draws and the failure correlation φ positive in 3/3). Sending it framed as "measurement of your system" reads as an attack. The context-clamp finding has already surfaced there once — your PR [#94](https://github.com/NandhaKishorM/laya/pull/94) was merged on 2026-09-21 — so it is a live, welcome topic. |
| **[typesafe-ai](https://github.com/orgs/typesafe-ai/repositories)** (10 repos; **no `jev` repo**) | **A bug report against the SDK/adapter.** Verdict-vocabulary defect. | The natural target is [`system-one-adapter-python`](https://github.com/typesafe-ai/system-one-adapter-python) (★257, issues on) or [`typesafe-sdk-python`](https://github.com/typesafe-ai/typesafe-sdk-python) (★200, issues on). Both take issues. |
| **The four `awesome-jev` lists** | **A one-line link entry**, in their required format, each in its own PR. | These are the discovery channel. All four explicitly accept research/reproduction entries, and two already carry independent Jev-1.13 studies. |

> ⚠️ **`https://github.com/typesafe-ai/jev` returns 404 — that repo does not exist.** You
> guessed the URL. The org is real; the repo is not.

---

## Channel 1 — Laya: ONE defect, with a reproduction

**Do not send the paper's conclusions here.** Send the clamp finding, which is a fact about
the input path that a maintainer can verify and fix.

### Report draft

> **Title:** `truncated` flag fires at a fixed 3,193 characters regardless of the loaded
> checkpoint, so it is both late and early depending on the loadout
>
> Launching with three checkpoints loaded:
>
> ```
> --model english --also multilingual --also typed-decisions --device cuda --max-len 1024 --head-max-len 512
> ```
>
> the truncation flag first becomes true at **3,193 characters on all three checkpoints**,
> but the character counts at which each checkpoint actually stops carrying its input differ
> by more than 2×:
>
> | checkpoint | token window | actual clamp | flag fires | error |
> |---|---|---|---|---|
> | `english` | 512 tok | **3,082 chars** | 3,193 | **+111 — flag is LATE** |
> | `multilingual` | 1024 tok | **7,966 chars** | 3,193 | **−4,773 — flag is EARLY** |
> | `typed-decisions` | 1024 tok | **6,967 chars** | 3,193 | **−3,774 — flag is EARLY** |
>
> The 111-character window on `english` is the dangerous direction: input is discarded while
> the flag still reports not-truncated, so a caller that trusts the flag proceeds on a state
> it did not supply. The early direction is the annoying one: the flag fires while the full
> input is still present, so callers truncate themselves for no reason.
>
> Both follow from one cause, and the artifact localises it: **the output is frozen at the
> real clamp (3,082 / 7,966 / 6,967), while the flag fires at 3,193 on all three.** The clamp
> knows which checkpoint it is serving; the flag does not — it behaves as though driven by a
> fixed character estimate rather than by the token budget actually in force. The truthful
> signal is the frozen output; the flag is a second, inconsistent one.
>
> **Related:** the window is a function of *(launch loadout × queried checkpoint)*, not of
> the engine — `english` clamps at 512 tokens in this three-checkpoint loadout but at 1024
> when loaded alone, while `multilingual` and `typed-decisions` measure 1024 on the same
> machine. So the flag cannot be computed from the checkpoint name alone.
>
> Measured with a direct sweep against the serving process; raw readings and the sweep script
> are in the artifact, DOI 10.5281/zenodo.22901248. A fuller write-up with the surrounding
> measurements is at DOI 10.5281/zenodo.22901853. Happy to supply the sweep as a standalone
> reproduction script if that is easier to act on than a pointer.

**Also worth reporting, but only after the first is acknowledged** — the paper also found
Laya's probability field inverting an item's conclusion on two different systems, and
near-perfect accuracy where the answer is stated (0.9909) collapsing to 0.3091 where it must
notice an absence. Those are harder to act on and easier to hear as criticism. **Lead with
the fixable mechanical defect.**

---

## Channel 2 — TypeSafe: the verdict-vocabulary defect

### Report draft

> **Title:** `conflicted` and `undecided` are unreachable under real input; genuine
> contradiction is reported as `insufficient`
>
> `jev_check` exposes a five-value verdict vocabulary, and the tool description lists six
> (adding `unknown`). In a set of seven live readings spanning support, negation, explicit
> contradiction, symmetric contradiction, irrelevance, weak/rumour and a single unsigned
> note, **`conflicted` and `undecided` never appeared** — the five-value vocabulary behaves
> as three-valued.
>
> The consequential direction is contradiction: **when the evidence genuinely contradicts
> itself, the call returns `insufficient`.** Those two are not interchangeable to a caller.
> "Insufficient" reads as *supply more material*; the actual condition is *the material
> disagrees, and more of it will not help*. A caller that acts on the difference makes the
> wrong next move.
>
> Alongside it: `sufficient` stayed **≤ 0.14 across five `insufficient` calls**, so the field
> that would let a caller distinguish "thin evidence" from "contradictory evidence" is not
> carrying that distinction either.
>
> Separately, the tool description and the implementation disagree on the size of the
> vocabulary (six listed, five reachable). If `unknown` is intended, it did not appear; if it
> is not, the description overstates the contract.
>
> Readings are from live calls; the raw rows are in the lab record rather than a
> `results/` JSON, which the paper discloses. Full write-up: DOI 10.5281/zenodo.22901853.

> ⚠️ **Send this to `system-one-adapter-python` or `typesafe-sdk-python`, not to a `jev`
> repo — there isn't one.** Pick whichever the defect actually reproduces against, and say
> which in the report.

---

## Channel 3 — the four awesome lists

**A different document entirely: one factual line each, no argument, no summary of findings.**

### Rules that apply to all four

1. **Do not propose a summary of the results.** These lists index resources; a paragraph of
   findings is what their CONTRIBUTING calls promotional or out of scope.
2. **Disclose that you maintain `laya-mcp`.** `cobanov/awesome-jev` requires it in the PR
   description — *"Disclose in the pull-request description if you built or maintain the
   project."* `laya-mcp` is the access layer the paper measures one of the three systems
   through, and `AbdelStark/awesome-typesafe-jev` wants submissions "without promotional
   superlatives". Declaring it up front is what keeps this a submission rather than a plug.
3. **`cobanov/awesome-jev` has the exact section for this** — *"Open reproductions and
   research"* — whose own text says these are independent efforts, not verified reproductions
   of TypeSafe's architecture. That wording fits this paper precisely. Use that section.
4. **One PR per list.** They are independently curated and their formats differ.
5. **Expect to be asked for an artifact.** These lists request the file that calls the API,
   the method, or an evaluation artifact. The artifact DOI and the 62-check suite answer that;
   have `PUBLISHED.md` ready to link.

### Entry drafts

**`cobanov/awesome-jev`** — suggested format is
`- [Name](url) - What Jev decides and how the result is used.`:

```md
- [When a Judgment Layer's Self-Reported Fields Lie](https://doi.org/10.5281/zenodo.22901853) - Independent measurement of three judgment layers on one item set, including Jev's typed decisions and its self-reported access-layer fields, with a reproduction artifact and a 62-check verification suite; reports Jev's verdict vocabulary collapsing to three reachable values and a truncation flag that does not track the clamp actually in force.
```

**`AbdelStark/awesome-typesafe-jev`** — its CONTRIBUTING asks evaluations to "include the
method":

```md
- [When a Judgment Layer's Self-Reported Fields Lie](https://doi.org/10.5281/zenodo.22901853) - Independent evaluation of Jev's typed-decision interface on a controlled item set, with a published method, an artifact carrying every raw reading (DOI 10.5281/zenodo.22901248), and a Chinese translation (DOI 10.5281/zenodo.22902025). Method: identical items to all three judgment layers, ledger-based cost accounting, and Murphy/Brier/ECE calibration against binary ground truth.
```

**`Anil-matcha/awesome-jev-by-typesafe`** — its evidence checklist wants the primitive used:

```md
- [When a Judgment Layer's Self-Reported Fields Lie](https://doi.org/10.5281/zenodo.22901853) - Independent measurement using Jev's `noul`, `choice` and `score` primitives on a fixed item set, reporting the access-layer fields (`fits`, `truncated`, `band`, verdict vocabulary) as things to calibrate against ground truth rather than to trust. Artifact: DOI 10.5281/zenodo.22901248.
```

**`yibie/awesome-jev`** — wants concrete projects and practices:

```md
- [When a Judgment Layer's Self-Reported Fields Lie](https://doi.org/10.5281/zenodo.22901853) - A controlled measurement of Jev's typed decisions alongside two other judgment layers, with reproducible per-reading artifacts; the practical takeaway is a list of Jev's self-reported fields that a caller should verify rather than trust.
```

---

## Suggested order

1. **Laya clamp report** — fixable, mechanical, and that repo already merged work from you.
2. **TypeSafe verdict report** — fixable, and lands on a repo that takes issues.
3. **`cobanov/awesome-jev`** — it has the section this belongs in and states the independence
   caveat itself.
4. **The other three lists**, one PR each, after the first lands and you know the maintainers'
   tolerance.

**Do not send all of it at once.** A first submission that is one defect is a contribution; a
first submission that is four PRs and two issues is a campaign, and gets read as one.

---

## What is already done, so nothing here is about the paper itself

The paper, the artifact and the Chinese translation are published, DOI-linked both ways, and
verified — see [`PUBLISHED.md`](PUBLISHED.md). Nothing in this file is required for the work
to stand; it is about who else might act on it.

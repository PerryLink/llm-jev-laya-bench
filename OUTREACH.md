# Outreach: where this paper should go, and in what shape

The paper measured three judgment layers and found **transferable defects** in two of them.
That makes outreach a different job from "announcing a paper": a maintainer who receives
"here is my paper about your project" has to work out whether it is a favour or an attack.
A maintainer who receives **a specific defect with a reproduction** can act on it.

So there are **three channels with three different shapes**, and mixing them is what gets a
submission ignored or resented.

Last verified against the live repos: 2026-09-23.

---

## Channel map

| Channel | What to send | Why |
|---|---|---|
| **[NandhaKishorM/laya](https://github.com/NandhaKishorM/laya)** (★15,466, Apache-2.0, issues on) | **A bug report, not the paper.** One scoped defect with a repro. | The paper's Laya findings are *critical* (accuracy 0.225 on 77-class, Δ_catch negative in 3/3 draws and the failure correlation φ positive in 3/3). Sending it framed as "measurement of your system" reads as an attack. The context-clamp finding has already surfaced there once — your PR [#94](https://github.com/NandhaKishorM/laya/pull/94) was merged on 2026-09-21 — so it is a live, welcome topic. |
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
   the method, or an evaluation artifact. The artifact DOI and the 59-check suite answer that;
   have `PUBLISHED.md` ready to link.

### Entry drafts

**`cobanov/awesome-jev`** — suggested format is
`- [Name](url) - What Jev decides and how the result is used.`:

```md
- [When a Judgment Layer's Self-Reported Fields Lie](https://doi.org/10.5281/zenodo.22901853) - Independent measurement of three judgment layers on one item set, including Jev's typed decisions and its self-reported access-layer fields, with a reproduction artifact and a 59-check verification suite; reports Jev's verdict vocabulary collapsing to three reachable values and a truncation flag that does not track the clamp actually in force.
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

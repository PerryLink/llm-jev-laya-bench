# AI-assistance disclosure

*(English translation of `paper/13-ai-disclosure-draft.md`. Terminology follows
`paper/TRANSLATION-GLOSSARY.md`.)*

**Author: PerryLink (Independent Researcher).**

The experimental design, probe and instrument code, data collection, statistical computation
and first draft of this paper were produced by an AI agent under the author's direction. **The
author takes full responsibility for the entire contents and for every number in `results/`.**

We state this plainly rather than blurring it, and not only for compliance. arXiv's [policy on
generative AI](https://info.arxiv.org/help/moderation/index.html) requires three things:
**report** the use, **take full responsibility**, and **do not list AI as an author**. This
paper does all three. What binds is the enforcement: arXiv's Computer Science section chair has
stated that the penalty for a submission containing *"incontrovertible evidence that the authors
did not check the results of LLM generation"* is a **one-year ban** — the two named examples of
such evidence being **hallucinated references** and **leftover model chatter**.

**This paper contains neither, and that is checkable rather than asserted**: `paper/verify_all.py`
scans the manuscript for both, and every entry in the reference list was opened and checked by
the author against its primary source. **Nothing here is cited unverified.**

## What was machine-produced versus human-decided

| Component | Produced by | Human role |
|---|---|---|
| Experiment design | AI agent | Approved scope; chose which claims to test |
| Probe and instrument code | AI agent | Reviewed; ran the pinned launcher |
| Measurement runs | AI agent | Authorised spend; confirmed the sidecar loadout |
| Statistical analysis | AI agent | Audited by **multiple rounds of adversarial sub-agents** |
| Manuscript drafting | AI agent | Directed the framing; **decided every claim's strength** |
| **Every published claim** | **Author** | **Sole responsibility** |

## Checkability: the verification path ships with the paper

So that the above is **checkable rather than merely asserted**, the whole verification path is
delivered alongside:

- **`paper/verify_all.py`** — **62 automated checks** covering numbers, citations, translation
  consistency, retraction propagation and publication readiness, including a scan for residual
  model-generated text;
- **`src/analysis/p28_recompute_all_stats.py`** — recomputes every interval and exact test in
  the paper using **only the standard library**, runnable independently;
- **`src/analysis/p30_inventory.py`** — **derives** the evidence count from the directory rather
  than asserting it;
- **`results/ERRATA.md`** — **13 sections** recording self-reported defects.

## The audit rounds are not decoration

**They overturned four of this paper's own earlier conclusions, and those are RETRACTED IN THE
TEXT rather than quietly corrected:**

1. **"The ground-truth fix attenuated the effect"** — a counterfactual showed the fix's
   contribution was **exactly zero**; the movement came from **re-sampling at an unpinned
   temperature**.
2. **"Two of four confidence intervals exclude zero"** — that was a **zero-cell** artifact;
   under a zero-cell-valid method, **all four intervals include zero**.
3. **"The same script run twice differs greatly"** — **the second run does not exist**: the
   figure was the **pre-repair value of a derived field**.
4. **"Truncation explains about 6/10 of the effect"** — that control arm **has no artifact at
   all**, and its state size matches a **discarded prototype**.

There are further corrections besides: a **sign error** (the cluster correlation −0.243 should
be **+0.243**), a **cost ceiling taken from the wrong battery** (understating the measured
maximum by **70.4%**), and a **conflation of a battery's size with a statistic's own n**.

**A paper whose thesis is "verify, do not trust" has to be willing to be the thing that gets
verified.** The four retractions are recorded in `results/ERRATA.md` and in the ⚠️ annotations
throughout the text, so a reader can inspect the reason and the evidence behind each change.

## Conflict of interest

**The author maintains `laya-mcp`**, which is the access-layer implementation of one of the
three judgment layers this paper evaluates (Laya), and this paper reports it scoring **0.225**
end-to-end. The same disclosure appears in `README.md` and `THIRD-PARTY.md`. In addition,
`protocol/instrument-snapshot/` is a **byte-identical copy** of `laya-mcp` 0.2.1 (Apache-2.0, a
separate project rather than a fork); its hash is verified and it must never be edited.

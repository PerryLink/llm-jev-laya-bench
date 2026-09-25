# AI-assistance disclosure — DRAFT FOR AUTHOR APPROVAL

**Status: not yet inserted into the manuscript.** This is a proposal. The wording appears
under your signature, so you decide it. `paper/verify_all.py` check **G5** stays a warning
until the text you approve is in the drafts.

---

## Why this is being drafted rather than skipped

arXiv's policy, [*Policy for authors' use of generative AI language tools*](https://info.arxiv.org/help/moderation/index.html),
requires three things, and this project is affected by all three:

1. **Report** significant use of sophisticated tools — "we now include in particular
   text-to-text generative AI among those that should be reported".
2. **Take full responsibility** for all contents, "irrespective of how the contents were
   generated".
3. **Do not list** generative AI as an author.

The enforcement matters more than the policy. arXiv's Computer Science section chair has
stated the penalty for submissions containing *"incontrovertible evidence that the authors
did not check the results of LLM generation"*: a **one-year ban**, after which submissions
must first be accepted at a peer-reviewed venue. The two named examples of such evidence are
**hallucinated references** and **leftover model chatter** (e.g. *"here is a 200 word
summary; would you like me to make any changes?"*).

**This repository contains neither**, and that is checkable rather than asserted:
`paper/verify_all.py` scans the manuscript for both, and every reference in the list being
built is verified against a fetched primary source.

---

## The honest situation, stated precisely

Most AI policies are written for the case *a human researcher used an LLM to help draft*.
**This project is the other case**: an AI agent designed the experiments, wrote the code, ran
the measurements, computed the statistics, and drafted the paper, under the human author's
direction and review.

That is a category difference worth stating plainly rather than blurring, because the
policies' operative requirement — the signing author is responsible for the content — is
*satisfiable* here, and arguably better satisfied than in a typical paper. What follows is
the evidence for that, and it is the same evidence a reader can re-run.

---

## Option A — short form (recommended if space is tight)

### 中文

> **AI 辅助声明。** 本文的实验设计、代码实现、数据采集、统计计算与初稿撰写由 AI 代理在作者指导下完成，作者对全文内容与 `results/` 中每一个数字负全部责任。为使这一声明可被检验而非仅被声明，全部核验途径随文公开：`paper/verify_all.py` 执行 62 项自动检查（含 AI 残留文本扫描）、`src/analysis/p28_recompute_all_stats.py` 以纯标准库重算论文中每一个区间与精确检验、`src/analysis/p30_inventory.py` 从目录推导证据清点而非手写、`results/ERRATA.md` 以 14 节记录自查发现的缺陷——其中两节推翻了作者此前的结论。参考文献均由作者逐条打开原文核对；本文不引用任何未经核对来源。

### English

> **AI-assistance disclosure.** The experimental design, code, data collection, statistical
> analysis and first draft of this paper were produced by an AI agent under the author's
> direction. The author takes full responsibility for the entire contents and for every
> number in `results/`. So that this is checkable rather than merely asserted, the whole
> verification path ships with the paper: `paper/verify_all.py` runs 62 automated checks
> (including a scan for residual model-generated text); `src/analysis/p28_recompute_all_stats.py`
> recomputes every interval and exact test in the paper using only the standard library;
> `src/analysis/p30_inventory.py` derives the evidence count from the directory instead of
> asserting it; and `results/ERRATA.md` records ten sections of self-reported defects, **two
> of which overturned the authors' own earlier conclusions**. Every reference was opened and
> checked against its primary source; nothing is cited unverified.

---

## Option B — long form (if a venue asks for detail)

Adds a table of what was machine-produced versus human-decided:

| Component | Produced by | Human role |
|---|---|---|
| Experiment design | AI agent | Approved scope; chose which claims to test |
| Probe and instrument code | AI agent | Reviewed; ran the pinned launcher |
| Measurement runs | AI agent | Authorised spend; confirmed sidecar loadout |
| Statistical analysis | AI agent | Audited by five rounds of adversarial sub-agents |
| Manuscript drafting | AI agent | Directed framing; decided every claim's strength |
| **Every published claim** | **Author** | **Sole responsibility** |

and adds this sentence, which is a claim the artifact can actually support:

> The five audit rounds are not decoration: they are the reason two of this paper's own
> earlier conclusions are **retracted in the text rather than quietly corrected** — the
> claim that a ground-truth fix attenuated the effect (it contributed exactly zero; the
> movement came from re-sampling at an unpinned temperature), and the claim that two of four
> confidence intervals excluded zero (a zero-cell artifact; the corrected intervals all
> include zero). A paper whose thesis is "verify, do not trust" has to be willing to be the
> thing that gets verified.

---

## What I recommend, and why

**Option A, plus one sentence from Option B.** Reasons:

1. A reader's real question is *"can I trust this?"*, and the answer is a runnable test suite,
   not a paragraph. Option A leads with the artifact.
2. Option B's table is good but risks reading as defensive. The strongest line in it is the
   retraction sentence, which is short enough to keep.
3. **The disclosure is not the risky part — the unnamed gap is.** A reader who discovers the
   AI involvement from the commit history will discount everything. A reader who is told up
   front, and handed `verify_all.py`, will run it.

---

## Two things you must decide, not me

1. **Whose voice?** Both drafts say "the author takes full responsibility". If there will be
   co-authors, this must be rewritten — and every co-author must actually agree, since the
   policies bind each signatory individually.
2. **Scope of the admission.** Option A says the *draft* was AI-produced. Option B says the
   *experiments* were. Both are true. Option A is quieter about the experiments. Given that
   the paper's contribution is the measurement, I think the fuller statement is both safer
   and more interesting — but it is your name on it.

---

## Also needed before this can ship

- **Author block** for `CITATION.cff` and the manuscript front matter (name, ORCID if you
  want one — free, no affiliation required, `https://orcid.org`; affiliation may be written
  as *Independent Researcher*).
- **Confirmation on the conflict-of-interest sentence**, which is separate from AI disclosure
  and already drafted in `README.md`: the author maintains `laya-mcp`, one of the systems
  being evaluated, and the paper reports it scoring 0.225 end-to-end.

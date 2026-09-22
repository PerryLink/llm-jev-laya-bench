# §1 Introduction

*(English translation of `paper/01-intro-02-related-draft.md` (§1 Introduction, §2 Background and
Related Work). Faithful, not abridged: every hedge, every ⚠️ marker, every blockquote, every n and
every decimal place is carried across. Terminology follows `paper/TRANSLATION-GLOSSARY.md`.
Citation keys `[@key]` resolve against `paper/references.bib`.)*

## 1.1 A design choice mistaken for a question of money

When an agent has to make judgments repeatedly in a long-horizon task — is this step right, does this piece of evidence support that claim, which action should be chosen next — there is a natural engineering division of labour: **hand the judgment to a cheap, specialised judge, and bring in a frontier model only when it is uncertain.**

The **selling point of this division of labour is usually stated as "saving money"**. This paper's first conclusion is: **at this scale, saving money is not a defensible claim.**

Take the three-way comparison measured in this project as the example (§5):

| Judge | Per-call cost | Running all 120 checkpoints |
|---|---|---|
| Local judge model | marginal ≈ $0 | ≈ $0 |
| Remote judge service (Jev) | $0.0000146–0.0002406 | $0.0018–0.0289 |
| Frontier LLM (DeepSeek-V4.1-Flash) | $0.0000326–**$0.00009645** | $0.0039–$0.0068 |
| Same, most expensive `max` reasoning setting | $0.0001010 | **$0.0121** |

**All three sit at the 10⁻⁵ dollar order of magnitude; the most expensive combination's judgment layer, over one complete run, is about 1.2 cents.**

And **latency spans about 25–32×** (37.4 ms / 671 ms / **0.9–1.2 s**; n is 30 / 48 / 35 respectively, and all three are **client-side wall clock**. **The interval is taken from two same-script runs on the Jev side**: 24.5× (p50 915 ms) to 31.9× (p50 1,192 ms); the pooled n=35 median is 28.7×), **and the direction favours the local judge**; **the usable state window spans about 4.9×** (3,082 characters vs the access layer's 15,002 characters; **when the direct route is pushed to 39,927 characters the tokens still grow monotonically with characters ⇒ the "16,000-character cap" belongs to the access layer, not to the provider**), **and the direction favours the remote service**; and **failure observability** also differs (**local silently discards** vs **remote warns**).

→ **The real axis is latency and window, not dollars.** And this matters because **it determines whether the architecture is worth deploying**: a judge that does not occupy a sequential round trip and a judge that must wait a one-second round trip on every judgment have completely different engineering implications in a long-horizon task.

## 1.2 The second conclusion, which is also this paper's main contribution

If cost is not the problem, then **whether using these judges is safe** becomes the only question that matters. This paper's main contribution is **a set of measured results about "the judge's self-reported fields are not trustworthy"** (§3), which converge on **a single shape** (§6):

> **The judge is near-perfect on tasks where "the answer is explicitly stated" (`explicit_support` 0.9909, n=220), and collapses on tasks where it "must notice that something is absent or that something does not match" (`explicit_contra` 0.2727 / `no_support` 0.3091 / `partial_contra` 0.5818 / `partial_support` 0.6818, each n=220); and the confidence it self-reports is not low in either case.**

Three independent instances:

| Instance | What must be "noticed" | Consequence | What the self-reported fields say |
|---|---|---|---|
| **Silent truncation** | the input was discarded | the answer flips wrong, the decisive evidence disappears | `fits: true`, no `truncated`, no warning |
| **`no_support`** (n=220) | the evidence does not exist | asserts that that value is the current value (P(true)=0.564) | `noul` above 0.5 |
| **Cross-language** (n small) | what is being read is not English | false items reach P(true) 0.4795 | confidence is not low | (**⚠️ Eighth-round correction: 0.912 was measured with the SCORING RUBRIC WRONG** -- in the same artifact the true-item arm, whose rubric was correct in both script versions, reproduces 48 of 48 fields identically across all eight languages, while the false-item arm, whose published rubric named the wrong value, differs on 22. **Re-measured with the corrected rubric the figure is 0.4795** (non-Latin false-item mean P(true)). 0.912 was really measured, but what it measured is a judge that was asked a malformed question, not a judge that failed to notice an absence, so 0.4795 is the figure of record. **The qualitative finding stands on it** -- 0.4795 is still far above what a calibrated judge returns on items with no support.)

**Why this is far more serious than "the judge is not accurate enough"**:
- a judge with **low accuracy** will be exposed in evaluation;
- a judge that **is confidently wrong at low probability, and whose instrument reports "pass"**, will be silently trusted in production.

**The sharpest piece of evidence comes from a component with no judgment capability at all** (§3.1): the answer of Jev's mock provider is determined entirely by an input hash, and **rewriting the question into the opposite meaning will not move the numbers either**. Yet on a **14-item** calibration battery it produced a **plausible confidence distribution** (on the **10 items** that carry binary ground truth, Brier = **0.359**, worse than a constant 0.5's 0.25) — **Brier 0.359**, worse than a constant predictor (0.25), but **in the results table it will not read as "broken"**.

> **A judge with no judgment capability can produce a completely credible results table.**

## 1.3 The third conclusion: a negative result

This paper originally also wanted to examine **the complementarity of heterogeneous judges**. Existing cascading and routing work ([FrugalGPT](https://arxiv.org/abs/2305.05176), [RouteLLM](https://arxiv.org/abs/2406.18665), [AutoMix](https://arxiv.org/abs/2310.12963), [Cascaded LMs](https://arxiv.org/abs/2506.11887)) **mostly has LLMs judging LLMs, but not all of it**: RouteLLM itself reviews Hybrid-LLM as "relies on a single **BERT-based router**" and Zooter as "explores only a **BERT-style router**", and its body also sets aside a "4.2.3 BERT classifier" section; learning-to-defer is likewise a deferred decision of "classifier + expert".
→ **So this paper's increment is not "the first use of a non-generative discriminator as the first tier"** (that practice has precedent), **but rather**: treating it as a **controlled first tier**, running a **paired complementarity** test against a frontier generator on **the same frozen items**, and reporting that **no established** incremental coverage was **found** (**⚠️ ninth-round qualification**: regime one's prose arm gives a **positive** point estimate whose interval contains 0, so "not found" must not be read as "does not exist", see §8.2).

**Across three task regimes, the answer is negative** (§8): regime one **gives different answers in its two answer formats** — the forced-choice arm has the LLM at 48/48 (error structure not measurable), while **the prose arm is measurable and its Δ_catch point estimate is +0.0435 (positive, interval containing 0)**; in regime two the LLM is at the ceiling (0.750–0.900), which thins its error structure, but **Δ_catch is negative in 4/4 draws**; in the third regime the ceiling has been broken and the items were **re-judged after the ground-truth fix**, where Δ_catch is uniformly negative and the **failure correlation is positive in 3/3 draws pooled** (**⚠️ ninth-round correction**: this sentence previously printed "the failure correlation is **significantly** positive" — that wording was withdrawn in §8.6.1, where stratifying by difficulty leaves none of the three draws significant; this was a missed propagation, see §8.6.1):

| Regime | LLM | Judge | Typed-only correct | LLM-only correct | Δ_catch |
|---|---|---|---|---|---|
| Authority location (**forced-choice arm**) | **1.0000** | 0.4583 | **0** | 26 | not definable (LLM zero errors) |
| Authority location (**prose arm**, same 48 items) | **0.9583** | 0.4583 | **1** | **25** | **+0.0435** (interval containing 0) |
| 77-class intent classification (n=40, **LLM 4 draws**) | **0.750–0.900** | 0.2250 | **0–2** | **23–27** | **negative in 4/4 draws** (−0.033…−0.257) |
| Multi-hop chained verification (n=68, **3 draws**) | **0.662–0.677** | 0.2941 | — | — | **negative in 3/3 draws** (−0.182…−0.247) |

→ **Heterogeneous does not automatically mean complementary, and does not automatically mean independent**: in the third regime, the judge's accuracy where the LLM fails (0.13–0.17) is **below** its own marginal accuracy (0.294), while where the LLM succeeds (0.36–0.38) it is **above** the marginal — i.e. the two **fail in the same direction** (φ > 0 in 3/3 draws; but the significance is limited, see §8.6.1). We report this result as a **methodological warning**: **an architectural choice needs positive complementarity evidence and cannot be assumed from a difference in species** — and we give the boundary on **why this conclusion cannot be extrapolated** (§8.5).

## 1.4 Contribution list

1. **Measurement of seven judge failure modes** (§6), including **23** mandatory protocol clauses;
2. **One unifying shape** (§6): "capability collapse" happens at the position where one "must notice an absence", and the self-reported confidence does not change with it — supported by three independent instances, one of which is a quantitative calibration curve at n=220;
3. **A measured three-way cost/latency/window comparison** (§5), on the basis of which **we rewrite the central claim from "cheaper" to "does not occupy a sequential round trip"**;
4. **A negative result on heterogeneous complementarity** (§7), together with an argument as to **why** it is a methodological result rather than a universal conclusion;
5. **A set of transferable methodological lessons** (§4): the same class of error appeared **four times** in this project, **each time disguised as a finding about the model**, and **each time caught by a control rather than by review**.

---

# §2 Background and Related Work

## 2.1 Three kinds of judge: discriminative vs generative

The three systems this paper compares **are not the same species**, and this determines the whole experimental design:

- **Autoregressive generative model** (DeepSeek-V4.1-Flash): accepts arbitrary context, **outputs free text and can take actions**;
- **State-conditioned discriminator** (TypeSafe Jev, Laya): **accepts one state and a set of declarative questions, returns labels and probabilities, cannot generate text, cannot act**.

→ **"Jev/Laya independently performing a task" is physically impossible.** Every comparison in this paper is therefore a **judgment-layer comparison**: the generator is held constant and only the judgment layer varies.

**⚠️ The distinction "decision model vs generative model" must be restated (sixth-round correction).** The first draft wrote "it is not an existing academic category" — **that claim holds only for the "wording" and does not hold for the "substance"**. A model that maps (state, declarative question) to "label + probability" and cannot generate is, in the standard taxonomy, a **discriminative (conditional) probabilistic classifier** (Ng & Jordan, 2001). The paper's position should therefore be **"an instance of that distinction"**, not "a new category":

- **Architecture axis**: **discriminative / conditional model** (Ng & Jordan, 2001 [@ng2001discriminative]) — the existing name for a "decision model";
- **Output axis**: **calibrated probabilistic classifier** (Guo et al., 2017 [@guo2017calibration]);
- **Abstention axis**: **selective prediction / classification with a reject option** (Chow, 1970 [@chow1970optimum]; Geifman & El-Yaniv, 2017 [@geifman2017selective]);
- **Cannot-act axis**: **learning to defer** (Madras et al., 2018 [@madras2018predict]; Mozannar & Sontag, 2020 [@mozannar2020consistent]);
- **Inability to generate as a property rather than a defect**: the **energy model / scoring function** framework (LeCun et al., 2007 [@lecun2007ebm]; Du & Mordatch, 2019 [@du2019implicit]) — inference takes an argmin over answers rather than sampling;
- **Vocabulary of the LLM era**: the abstention survey (Wen et al., 2024 [@wen2024abstention]).

**One precise definition that must be kept distinct**: "verifier" and "judge" name a **role** in a system, whereas "discriminative" names an **architecture**. In the existing literature that role is usually played by a **generative** model. **So the paper's real claim should be stated as: requiring the role of "verifier" to be held by a discriminative model that is provably incapable of generating, rather than by a generative model that is prompted to score.** This statement survives checking; the statement "that category does not exist" does not.

**Two analogies must be qualified**: **non-autoregressive decoding** (Gu et al., 2018 [@gu2018nonautoregressive]; Xiao et al., 2022 [@xiao2022narsurvey]) is still **generating a sequence** (just in parallel), whereas this paper's judge outputs a single label per forward pass and **never generates** — the analogy is loose. **Energy models** are also only an analogy: this paper's judge **is not** an MCMC-trained energy model.

## 2.2 Cascades and deferred decisions

This paper's **architecture is not new**, and that must be said plainly:

| Work | Claim | Relation to this paper |
|---|---|---|
| FrugalGPT [@chen2023frugalgpt] | cascading to save money | same family (LLM judging LLM) |
| RouteLLM [@ong2025routellm] | routing to a cheaper/stronger model | **not the same family**: the Hybrid LLM and ZOOTER it reviews both use a **BERT-style non-generative router** |
| ↳ Hybrid LLM [@ding2024hybrid] | routing between a small/large model by quality | the first tier is a **BERT router** [@devlin2019bert], non-generative — **the same kind as this paper's first tier** |
| ↳ ZOOTER [@lu2024zooter] | reward-guided ensemble routing | as above; a routing function rather than a generator |
| AutoMix [@aggarwal2024automix] | self-verification then escalation | same family |
| Cascaded Language Models [@fanconi2025cascaded] | layering + deferred decisions + abstention + human | same family; this paper's point of comparison |
| learning-to-defer [@madras2018predict] [@mozannar2020consistent] [@mozannar2023who] (classifier + expert) | learning when to hand over to an expert | **not the same family**: the first tier is a discriminative classifier, not an LLM |
| decision-focused learning [@elmachtoub2022smart] [@mandi2020interior] [@mandi2024decision] | training the predictor by downstream decision quality | **a different question**: what it optimises is the predictor's **training objective**, whereas this paper measures **where an already-trained judge fails** |

→ **This paper's increment is not in the architecture**, but in:

1. **the first tier is a real, local, non-generative judge model** (rather than another LLM);
2. **the complementarity of heterogeneous judges is directly tested pairwise** (§7) — non-generative discriminators already have precedent in existing work, but **were not treated as a controlled first tier and compared pairwise against a frontier generator**;
3. **the reliability of the judge's self-reported fields is taken as an independent object of study** (§3).

## 2.3 LLM-as-a-judge and confidence calibration

- LLMs as judges are already widely used, and their **biases** (position, verbosity, self-preference) have been systematically studied (Zheng et al., 2023; Wang et al., 2023; Saito et al., 2023; Panickssery et al., 2024);
- **verbalized confidence and internal logit-based probability differ systematically** (Tian et al., 2023). **⚠️ The attribution must be precise**: **"LLMs, when verbalizing their confidence, tend to be overconfident" should be cited to Xiong et al. (2024)** (its abstract reads, verbatim, "LLMs, when verbalizing their confidence, tend to be overconfident"); **the abstract of Kadavath et al. (2022) says the opposite qualification** — larger models are **well calibrated** under a suitable format. The first draft attributed overconfidence to Kadavath, which is an **attribution error**, and the citations have been changed separately.
- **⚠️ And this section's novelty claim must be narrowed (sixth-round finding, the most important correction)**: the first draft wrote "these fields are likewise self-reported and likewise untrustworthy, and as far as we know this has not previously been systematically examined". **That claim does not hold.** Existing work includes:
  - **PhantomFill** (Usman, 2026): **the input is constructed so that the question cannot be answered**; in free text GPT-5.5 says "there is no data" 98% of the time, whereas **when required JSON fields are given, the same model fabricates in 40/40 cases**; of 13 models, 10 reach a 100% fabrication rate under required fields. **This is exactly a controlled version of this paper's central phenomenon (explicit 0.9909 vs absent 0.27–0.31) under schema pressure**, and it already has named metrics (Coerced Fabrication Rate / Escape Utilization Rate).
  - **CONSTRUCT** (Goh & Mueller, 2026): scores the trustworthiness of structured output **field by field**, including nested JSON, and is usable as a black box.
  - **Judge Circuits** (Feldhus et al., 2026 [@feldhus2026judgecircuits]): **the same model gives systematically different scores merely because the output format changed**, and its abstract states explicitly that cross-format comparisons of judge reliability **are in part measuring the format stage**.
  - **Protocol Sensitivity** (Kim & Kang, 2026 [@kim2026protocolsensitivity]): the comparison of the merits of verbalized confidence against log probabilities **reverses with protocol details**; an audit of 12 studies found that 5 of them never state how the answer/context was chosen.
  - **Format constraints themselves change the answer** (Tam et al., 2024 [@tam2024letmespeakfreely]): the tighter the constraint, the more pronounced the degradation.
  - **Agreement among judges is also limited** (Thakur et al., 2025 [@thakur2025judging]): the best judge still does not reach inter-human agreement; a high percentage agreement can mask large score differences.
- **This paper's real, defensible increment**: we do not claim that "format harms generated content", "the trustworthiness of structured-output fields" or "confidence extraction is sensitive to protocol" are new — **all three already have work**; what this paper claims is the narrower point: **treating the protocol/metadata fields that the judge reports about *itself* (`fits`, `truncated`, `band`, the verdict vocabulary) as objects that need calibration measurement against ground truth**, and testing them **jointly** with the "absent vs explicit" asymmetry.

**⚠️ There is another existing result *pointing in the opposite direction* that must be addressed head-on (sixth-round finding; otherwise a reviewer will certainly juxtapose them)**: **Ferrer et al. (2026)** reports that self-reported confidence is **the best calibrated** (avg ECE 0.166 vs self-consistency 0.229), and **recommends simply having the model report its confidence** — **apparently contrary** to this section's conclusion (this paper's ECE 0.2259, AUC 0.7136).
> **The two are not contradictory, but they are non-contradictory only once this paper states precisely what it is accusing.** What this paper accuses is **not** "scalar confidence is unusable as a ranking signal" — **on that point this paper's data agree with Ferrer** (AUC 0.7136 is even slightly higher than its 0.668). What this paper accuses is the **joint phenomenon** of "high confidence being reported at the same time as a judgment that has already silently failed": the judge collapses to 0.27–0.31 when it must notice an absence, and its self-reported confidence **does not fall in step**.
> ⇒ **This is precisely why this paper is worth reporting**, and it is a passage that must be written clearly: **it is not "confidence is useless", but "confidence did not fail along with the judgment".**
> ⇒ **Terminology**: use **verbalized confidence** as the primary term (Tian et al., 2023; Xiong et al., 2024; Kim & Kang, 2026 all use this word), noting the synonym self-reported confidence at first occurrence (Ferrer et al., 2026 uses the latter). Do not coin "expressed uncertainty"; that phrasing comes from a colloquial expression in Lin et al. (2022), and is not a term.
> ⇒ **Provenance of the measures**: the reliability / resolution / uncertainty three-way Brier decomposition is cited to **Murphy (1973)**, the Brier score itself to **Brier (1950)**; **ECE is cited to Guo et al. (2017)** — note that what Naeini et al. (2015) propose is a calibration **method** (BBQ), **not** ECE.

## 2.4 Verifiers and process supervision

- **Process reward models / verifiers**: scoring intermediate steps is the mainstream form of "using a model to judge" (Lightman et al., 2023; Uesato et al., 2022; Wang et al., 2023);
  **⚠️ Wording correction (sixth round)**: the first draft wrote "using a **cheap** model to judge". **This is not supported by the cited literature** — in Lightman et al., process reward models are precisely the side that is **more accurate and also more expensive** relative to outcome supervision. The word "cheap" has been deleted; if this paper wants to use "cheap", a separate source must be found.
- [Generative Verifiers](https://arxiv.org/abs/2408.15240) shows that **verification is moving in the generative direction** (Zhang et al., 2025) — this paper **cites it and does not attempt to refute it**;
- **This paper's increment**: verifier research focuses on **verification quality**; this paper focuses on **the verifier's self-reported fields and where it fails**.

## 2.5 Long-horizon degradation and contamination-aware evaluation

- **Long-horizon degradation**: the **position effect** has peer-reviewed empirical work — lost-in-the-middle (Liu et al., **2024**, TACL 12:157–173: performance degrades significantly when the relevant information sits in the middle of the context); **error compounding** itself, however, has **no** authoritative peer-reviewed source (verified: no such classic citation exists), and the closest peer-reviewed anchor is "LLMs cannot yet self-correct their reasoning" (Huang et al., 2024, ICLR: **performance actually drops after self-correction**); one may also cite survey-style preprints on long-horizon agents, but **their non-peer-reviewed status must be marked**.
  **⚠️ One category error must be corrected (sixth round)**: the first draft listed **context rot** alongside lost-in-the-middle as "existing empirical research". **context rot is not academic literature; it is a technical report from a commercial company (Chroma, a vector-database vendor)** (Hong et al., 2025), **with no peer review and no independent replication**; it appears in a number of 2026 preprints, and therefore **looks** like a term. **And the two do not measure the same thing**: lost-in-the-middle is a **position** effect and is peer-reviewed, whereas context rot is a vendor's name for **length**. This paper therefore **deletes that term** and keeps only the one that has been reviewed; should the reader need it, a footnote can explain the term's provenance and nature.
- **Contamination-aware evaluation**: this paper adopts its conclusion — **the "official test split" does not constitute a contamination defence** (Sainz et al., **2024**, EMNLP Findings; Jacovi et al., 2023, EMNLP — the latter's text itself points out that "guaranteeing unseen test data" is expensive and "becomes fragile over time").
  **⚠️ One wording must be narrowed (sixth round)**: D3's verification result is that **neither DeepSeek's API documentation nor its model card gives a knowledge cutoff date for the model** (checked 2026-09-22: the Models & Pricing table, the release announcement, the changelog, and the official model card README — **the field is absent in all four places**). **⚠️ But residual risk remains, and the paper must state it truthfully**: `DeepSeek_V41_Tech_Report.pdf` (that document is hosted only on huggingface.co) **could not be read in this round**, and it is the place where a cutoff date is most likely to appear. The paper's accurate statement is therefore **"DeepSeek's public documentation and model card do not declare a cutoff date"**, **not** "the model is uncontaminated" — **with no published cutoff date, one can neither conclude that contamination exists nor that it does not.**
  ⇒ Therefore the line of defence of **"using post-cutoff datasets"** does not exist.
- **This paper's handling**: ground truth is **computed by construction** (no human annotation, no model annotation), and public data serve only as **secondary/descriptive** evidence; and it is recorded explicitly that Laya's **prior collections** (AG News / DAIR / Banking77 [@casanueva2020banking77]) are **never used as headlines**.

## 2.6 This paper's position

Taking the above together: **this paper is a measurement and characterisation paper, not an algorithm paper.**

> It does not propose a new architecture; it provides a **controlled comparison across three kinds of judgment layer**, whose main findings are that **these components' self-reported fields are not trustworthy** and that **their failures concentrate in the same place**.

---

## Appendix: Note on Citation Conventions

This project enforces a distinction by **source tier** (`recon\R2-verified-externals.md`):
- **First-hand**: measured in this project, or read directly from a local file;
- **Official first-hand**: vendor documentation (URL and retrieval date required);
- **Third-party relay**: **must not be used as paper evidence** (e.g. a competitor's numbers relayed in a vendor README).

Wherever this paper cites a vendor's self-reported numbers (e.g. "the base model is close to random on typed-decisions"), it is marked as **our own measurement, not an independent replication**.

# Abstract

*(English translation of `paper/00-abstract-draft.md`. Faithful, not abridged: every hedge,
every ⚠️ marker, every n and every decimal place is carried across. Terminology follows
`paper/TRANSLATION-GLOSSARY.md`. Citation keys `[@key]` resolve against
`paper/references.bib`.)*

## Abstract

Handing the judgment work in a long-horizon task to a cheap, specialised judge is a division
of labour usually sold on the grounds that it **saves money**. This paper measures that claim
against a controlled three-way comparison, and reports four claims — one of which our own
data refutes.

**First, cost is not the binding constraint.** We measured the per-call cost of three
judgment layers: a local non-autoregressive judge (Laya, marginal cost ≈ 0, excluding
hardware amortisation), a remote typed-decision service (TypeSafe Jev, **$0.0000146–$0.0002406**,
rising monotonically with input tokens, over 8 measured points on the direct route), and a
frontier autoregressive model (DeepSeek-V4.1-Flash, $0.0000326–**$0.00009645**; at its highest
reasoning setting $0.0001010, or 2.54× the thinking-disabled setting). **At their respective
smallest states** all three sit in the 10⁻⁵ dollar range (**the most expensive LLM
configuration costs about 1.2 cents to complete one 120-checkpoint run**) — **but that order
of magnitude does not survive an increase in state size**: Jev costs **$0.0002406** for a
single call at its largest measured state (39,927 characters / 5,728 tokens), which projects
to about **2.9 cents** per 120 checkpoints; the LLM, extrapolated from its final state of
1,751 tokens, projects to about **2.4–3.9 cents**. So "an order of magnitude cheaper" does
not hold on any accounting, while "absolutely small" holds **only at short state sizes**.
What actually separates the three is **latency** (p50 spans about **25–32×**: 37.4 ms /
671 ms / **1.19 s** (one run of n=20; the pooled n=35 median is 1.07 s) — Jev measured as **independent wall clock**, a single run of n=20 at p50 1,192 ms, with the
pooled n=35 median at 1,073 ms; **only one run has an artifact behind it, so no run-to-run
range can be reported**) and the **usable
state window** (local english clamps at 512 tokens, about 3,082 characters; the remote service
measured ≥15,002 characters — about 4.9× — **and that multiple is bounded by this harness's
access layer: pushing the direct route to 39,927 characters still showed input tokens growing
monotonically with characters, which proves the "16,000-character cap" is the plugin's, not
the provider's**), and the **observability of failure** (the local one discards input
silently; the remote one warns). We therefore restate our central claim from "cheaper" to
"does not occupy a sequential round trip".

**Second, and this is the paper's main contribution: these judges' self-reported fields are
not trustworthy, and their failures cluster in one place.** Seven independent phenomena were
reproduced — **six from real calls**, the other from a synthetic backend driven purely by an
input hash (which produced a **completely credible results table**: Brier 0.359 on the 10 of
14 battery items that carry binary ground truth, worse than a constant 0.5 predictor's 0.25).
The six on the real-call side are: the truncation flag is wrong in both directions (english
lags by 111 characters; multilingual and typed-decisions false-positive 4,773 and 3,774
characters early), while all three checkpoints' flags fire at the same point, 3,193
characters, even though their real clamps differ by a factor of two; `fits: true` can coexist
with input that has already been truncated; the probability field inverts the item's verdict
in two separate systems (on one of them it affects half the items); and the two verdict
labels `conflicted` and `undecided` are unreachable under real inputs. These converge on a
single shape: **the judge is near-perfect when the answer is explicitly stated (0.9909,
n=220), and collapses when it must notice that something is absent or mismatched
(`no_support` 0.3091, n=220), while its self-reported confidence is high in both cases.**
That shape recurs in **three independent settings** (**silent truncation, `no_support`,
cross-language** — the basis for treating these three as parallel is in §7.5/§7.7; multi-hop
chained verification is a **fourth** setting, but its Laya failure mode differs, so it is not
counted among the three); the sharpest of them is that when the candidate value never appears
in the input at all, the judge returns a mean **P(true) = 0.5643** — reading "not stated" as
support (n=220).

> **A correction that must be given alongside it**: we previously described this judge as
> carrying "negative information". A Murphy decomposition of the n=1100 calibration corpus
> gives **REL 0.0556 / RES 0.0397 / UNC 0.2400**, and **AUC = 0.7136 (95% CI [0.682, 0.745])**
> — **the resolution is real; the failure is in calibration, not in information.** The correct
> statement is **poorly calibrated**: its Brier (0.2571) is indeed worse than a constant
> predictor's (0.2400), and its ECE is 0.2259.

**Third, a negative result.** In the routing and cascading literature, using a non-generative
discriminator as the first tier already has precedent (the BERT-style routers that RouteLLM
[reviewed] [@ong2025routellm]), but as far as we know no work treats it as a **controlled
first tier** and runs a **paired complementarity** test against a frontier generator. We ran
that paired comparison across **three** task regimes (the LLM arm is API-sampled, so every arm
reports **multiple independent draws** rather than a single point):

- **Authority location**: on the **forced-choice arm** the LLM was correct 48/48, the judge 0.4583,
  and it **caught none of the items the LLM missed**; **⚠️ the same 48-item battery's prose arm is
  the opposite**: LLM **46/48**, **1 judge-only item**, **Δ_catch = +0.0435** (95% CI [−0.386,
  +0.471], resting on **2** items where the LLM errs). **Among the regime-level readings of the
  three regimes, this is the only Δ_catch point estimate that is positive**, and we report it as
  it stands, with its width and its denominator (§8.2);
- **77-class intent classification** (n=40, **4 draws**): LLM **0.750–0.900** (the four are
  0.750 / 0.900 / 0.875 / 0.875; **median 0.875, mean 0.850**),
  judge **0.225** (bit-identical across all 4); **judge-only-correct 0–2 items against
  LLM-only-correct 23–27**, and **Δ_catch negative in 4/4 draws** (−0.033 / −0.250 / −0.029 /
  −0.257) — the recorded draw being the one **most favourable** to complementarity;
- **Multi-hop chained verification** (re-judged after the ground-truth fix, n=68, **3 draws**):
  LLM **0.662–0.677**, judge **0.294**; **Δ_catch = −0.182 to −0.247, negative in 3/3 draws**
  — but **the interval evidence is limited** (under an unpaired Wald interval 2 of 3 exclude
  zero; under score/Newcombe **only 1 robustly excludes and 1 sits at the boundary**), and
  **the failure correlation φ is not significant in any of the three draws once stratified by
  difficulty** (CMH permutation p = 0.059 / 0.055 / 0.201; **⚠️ this group of p-values is not
  traceable — no artifact, no script, no recorded seed, see §8.6.1(d)**).

→ **The conclusion is therefore stronger than "no complementarity found"**: the judge does not
merely fail to cover the generator's errors — its failures run **in the same direction** as the
generator's. `P(judge correct | LLM wrong)` = 0.13–0.17, **below** its marginal accuracy of
0.294, while `P(judge correct | LLM right)` = 0.36–0.38, **above** the marginal. The failure
correlation φ is positive in **3/3** draws (+0.19…+0.26).

> **⚠️ Strength qualification**: the 2×2 Fisher exact p for that correlation is **0.086 /
> 0.049 / 0.163** (r1/r2/r3) — **uncorrected, only 1 of 3 is significant at α=0.05; under this
> paper's own pre-specified Holm rule, 0 of 3 survive**. And the one-sided test of
> "conditional accuracy − marginal" has a 95% CI **containing 0 in 3/3 draws**. This is
> therefore evidence **consistent with shared failure**, not an established significant
> effect. **A heterogeneous judge does not automatically mean complementary, and does not
> automatically mean independent.**

> **Power and reproducibility must be given alongside the conclusion**: for the third regime
> (after the ground-truth fix), Δ_catch has **MDE (80% power) = 0.28–0.30**, **still larger
> than the pre-declared +0.10 gate** — so although the point estimate is negative in **3/3**
> draws, **the interval evidence is limited**: under an unpaired Wald interval 2 of 3 exclude
> zero, **but under the zero-cell-valid Newcombe interval only 1 robustly excludes and 1 sits
> at the boundary** (§8.3). **The precision remains limited.** The second regime's Δ_catch
> magnitude is unstable (−0.029 to −0.257) **but its sign is negative in 4/4 draws**.
> **⚠️ The sampling scope must be stated**: **only two complementarity regimes** (the chain
> battery `P22b` and the 77-class regime `P15b`) were repeatedly sampled at `temperature=0`
> with per-item label agreement reported (chain regime **86.8–89.7%**; judge arm **100%**).
> **The remaining LLM arms (P14 authority location, P19 calibration, P21 thinking cost, P23
> logprobs, P24 horizon) are still single draws**, and their point estimates should likewise
> not be read as precise values (§10.1).

**Methodologically**, the paper reports four instances of one error class — **a
specification-level semantic defect masquerading as a finding about the model** — each caught
by a control rather than by review, and from them derives **23** mandatory protocol clauses.

**We state the boundaries of this paper explicitly**: every conclusion comes from measured
**single-step judgments**; **autonomous long-horizon (multi-step cumulative) runs were not
executed**, and the horizon slope was downgraded to descriptive by a pre-declared ruling. All
Laya judgment measurements use the **english checkpoint**, with a window of **512 tokens**
(1024 when english is loaded alone, while multilingual/typed-decisions measured 1024 on the
same machine) — so the window is a function of **(launch loadout × queried checkpoint)**, and
"window = 512" is not a general property of the engine. On verification-style tasks the LLM
hits the ceiling (correct on n=1100), so **complementarity is not measurable in that regime**,
not "absent". The multi-hop chained verification battery **was executed** (96 items designed;
**68 entered the pool after the ground-truth fix**, §8.6.1), and its result is the negative
result above.

---

## Keywords

Decision models · Calibration · Silent truncation · Cascade architectures · Evaluation
methodology · Long-horizon agents

---

## Disclosure compliance check (editor's record, submitted with the paper)

**Rule (self-imposed by this project, arising from D2's reviewer test)**: **key n's and the
MDE must appear in the abstract**, not only in the limitations section.

**Check**:
- **n values**: n=220 (`no_support`, and each of the five levels), n=1100 (calibration),
  n=48 / n=40 / **n=68 (three complementarity regimes; the chain regime's n is post-fix)**,
  **n=35 (Jev latency, independent wall clock)**, n=120 checkpoints (cost);
- **MDE and reproducibility**: the third regime (post-fix) has **MDE = 0.28–0.30**, still
  above the +0.10 gate; Δ_catch is negative in 3/3 draws, with **2 of 3 excluding zero under
  an unpaired Wald interval and only 1 robustly excluding (1 at the boundary) under
  Newcombe**. The second regime is negative in 4/4. **All must be reported as multiple draws,
  never as a single point**;
- **Reproducibility clause**: any API-sampled judge arm must pin `temperature` and report the
  **per-item label agreement between repeated draws**. **Both are now in the abstract** (an
  earlier version omitted them).

**Why this abstract is long**: the paper's core contribution is **negative** (against
"cheaper", against "heterogeneous complementarity", against "self-reported fields are
trustworthy"). A negative paper with a short abstract reads as "we did not accomplish much".
So the abstract gives, item by item, the object being refuted and the numbers supporting it.

**Deliberately absent from the abstract**:
- Laya's **0.867** (conditional within-layer skill, §7.1.1) — **no abstract may cite it**;
- any capability number self-reported by a vendor.

**One-sentence alternative** (if a venue limits length):

> We measured the cost, latency and window of three judgment layers and found that cost is not
> the binding constraint (the most expensive configuration costs about 1.2 cents per run); the
> real cost is that self-reported fields are untrustworthy — the judge collapses where it must
> notice that something is absent and is near-perfect where the answer is explicitly stated,
> with no difference in reported confidence between the two; and a heterogeneous judge showed
> **no** incremental coverage across **three** task regimes (two of which are unmeasurable
> because the LLM hits the ceiling, and the third of which lacks the power to exclude a
> moderate effect).

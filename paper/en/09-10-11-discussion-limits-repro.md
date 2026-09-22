# §9 Discussion: if you are going to use a judge of this kind, what should you do

*(English translation of `paper/09-10-11-discussion-limits-repro-draft.md` (§9 Discussion, §10 Limitations,
§11 Reproducibility), carried in one file: §9 first, then §10, then §11. Faithful, not abridged: every hedge,
every ⚠️ marker, every ⬜, ✅ and ❌, every n and every decimal place is carried across. Terminology follows
`paper/TRANSLATION-GLOSSARY.md`; field names, verdict vocabulary, artifact IDs, paths, statistics and model
IDs are left untranslated. Cross-references `§N.M` are reproduced exactly as the Chinese draft writes them,
so that `paper/_assemble.py` remaps them identically in both builds. The draft's own audit annotations and
their round numbers are retained. The source contains no citation keys `[@key]`.)*

This section gives only recommendations that are **supported by measurement**, each with its basis and its
cost stated. We do not write engineering opinions that have no evidence behind them.

## 9.1 Put input validation in the harness, not in the judge

**Basis**: Laya returns `ok: true`, **no error, no warning, `fits: true`** for an **empty state and a
pure-noise state** (R13). For empty input it still gives `choice: "technical"`.
**Basis two**: the `no_support` stratum (n=220) — **when the candidate value does not appear at all, it
returns a mean P(true)=0.564**.
**What to do**: reject empty / low-information states before the call, and **explicitly check "does the
evidence actually exist"**, instead of letting the judge answer a question for which it has no detection
channel.
**Cost**: it requires harness-side implementation, and a definition of "exists" has to be defined for every
task class.

## 9.2 Never gate on a self-reported field; always compute it yourself

**Basis**: `truncated` **is wrong in both directions** (english lags by 111 characters; multilingual
false-reports **4,773** characters early; typed-decisions **3,774** early) (§3.2). All three checkpoints'
flags fire at **the same point, 3,193 characters**, while their real clamps differ by **a factor of 2**.
**Basis two**: `fits: true` and **input that has already been truncated** can hold at the same time (§3.3).
**What to do**:
- **count with the checkpoint's own tokenizer**, and compare against `512 − head_tokens − 1`;
- treat `truncated`/`fits` as **descriptive reporting only**, and **also report the "flag error"** metric;
- **put the decisive evidence first** — what Laya discards is the **tail**.

## 9.3 Do not compare confidence across systems or across framings

**Basis**:
- Jev's `probability` is **P(the selected option)**, not P(true) — recording `probability` as P(true)
  **reverses the sign of every item answered `false`** (about half of that corpus); and **in the same
  response `band` points toward true while `probability` points toward the selected option** (§3.4);
- the LLM's `prob` is **the confidence of the label it answered**, the same trap (this project stepped on
  it once on each side);
- Laya's `confidence` is a **concentration statistic**: the same p under different framings is **0.5399 vs
  0.0046** (a 117× difference).
**What to do**: **record only the quantity oriented toward true** (for Jev record `noul`; for the LLM
record P(true) derived from the label); **report the full distribution** rather than the winner.

## 9.4 Choose tasks by "will it notice an absence", not by "is it accurate"

**Basis** (§6's unified shape):
| Task shape | Laya, measured |
|---|---|
| the answer is explicitly stated | **0.9909** (n=220) |
| requires finding an authoritative source | 0.4583 (n=48) |
| the evidence does not exist | **0.3091** (n=220) |
| requires semantic interpretation (77 classes) | 0.0333 (n=30) |
**What to do**: **treat "does the evidence exist" as a first-class check**; on these judges, do not deploy a
pipeline that says "a judgment should be given even when the evidence is missing".

## 9.5 If you need a large state, reconsider the loadout

**Basis** (P18, one launch per loadout; **no repeated launches were done, so we do not claim determinism**):
| Checkpoints loaded | Usable window |
|---|---|
| **1** | **1024 token** |
| **≥2** | **512 token** |
**What to do**: **loading only one checkpoint doubles the usable window**, at the cost of losing the
multilingual and specialised checkpoints.
→ **And the window must be recorded together with the launch loadout** — "window = 512" may be wrong by 2×
for another operator.

## 9.6 Hybrid architectures: do not assume complementarity, measure it first

**Basis** (§7): on **three** regimes, the heterogeneous judge provided no incremental coverage at all —
- regime one (authority location, n=48): it **caught none** of the items the LLM missed (judge-only correct
  **0**, against LLM-only correct **26**);
- regime two (77-class intent classification, n=40, **4 draws of the LLM arm**): judge-only-correct **0–2**
  items against LLM-only-correct **23–27**, **Δ_catch negative in 4/4 draws** (−0.033 / −0.250 / −0.029 /
  −0.257); the judge's accuracy is bit-identical across the 4 (0.225);
- regime three (multi-hop chained verification, **re-judged after the ground-truth fix**, n=68, **3 draws**):
  LLM **0.662–0.677**, judge **0.294**, **Δ_catch = −0.182 to −0.247**, **2 of the 3 have a 95% CI excluding
  zero**, **failure correlation φ = +0.19…+0.26**; `P(judge correct \| LLM wrong)` = 0.13–0.17, **below**
  its marginal of 0.294 ⇒ **consistent with shared failure** (but Fisher p = 0.049/0.086/0.163, significant
  in only 1/3);
  **⚠️ But MDE = 0.28–0.30, still larger than the pre-declared +0.10 gate ⇒ the point estimates are
  consistently negative, yet the precision remains limited.**
**What to do**:
- **before choosing "a cheap first tier + escalation", run a paired complementarity measurement**;
- the criterion is **the sign of Δ_catch**, not the count of "first tier only correct";
- if the first tier **provides no incremental coverage**, it is **a worse second tier** and should simply be
  removed — **the latency advantage is not enough to compensate** (§8.3.1: the tier is a **net gain** for
  Laya, but end-to-end it is only **0.200**, far below the LLM's flat 0.750–0.900).

## 9.7 One honest sentence about "long-horizon"

**This project's long-horizon evidence is a "reduced version", not a complete autonomous run.** The horizon
slope was **downgraded to descriptive** by D2's ruling, and **was not executed**.
P24 provides a **cumulative measurement of 3×20 steps inside the same process** (window erosion 23%, final
state 3.4× the clamp); P26 demonstrated **that truncation does happen** (all 20 calls `in_pad=512`,
`truncated=true`), but **because the option order was perfectly collinear with the answer, it could not
demonstrate that truncation changed the answer** (§5.3.2).
But there was **no tool use, no cross-process resumption, and the judge was invoked in the judging role
rather than as an autonomous agent**.
→ The recommendations of this section **rest on single-step judgments and reduced-version accumulation**,
and **must not be upgraded into a conclusion about "autonomous long-horizon running"**. ⬜

---

# §10 Limitations

## 10.1 Experiments not executed (by importance)

| # | Not done | Impact |
|---|---|---|
| 1 | **A complete autonomous long-horizon run** (cross-process resumption, tool use, multi-session scheduling) | the central theme, "long-horizon", **is validated only by the reduced version** (P24, 3×20 steps in the same process); **the reliability of autonomous running was not measured** |
| 2 | **The error-compounding curve over a long horizon** (`token_ratio(t)` along a real run, drift across sessions) | P24 measured window erosion and no drift in the LLM (at ceiling), but **no dose–response was done** |
| 3 | **The calibration curve covers templated items only** | usable for **differences between curve shape and difficulty**, **not usable for estimating absolute capability** |
| 4 | ~~the LLM's logprobs ladder~~ | ✅ **Completed** (P23): verbal and internal probabilities agree (difference −0.0033) |
| 5 | **The prompt-variant band (P1–P4) was not run** | R16's anti-strawman requirement is **unmet**; the LLM arm used only one wording |
| 6 | **Multilingual mis-routing was not tested** (and it has been corrected: this interface does no routing) | we **must not** make any statement about the plugin's Python `Router` |
| 7 | the exact truncation point of Jev's **plugin-side** 16,000-character constant | proved only up to **15,002** (the vendor documentation's `state` cap is 32k token; not measured) |
| 8 | the live behaviour of `rank`'s over-limit rejection | the formula comes from the mock (it agrees across 4 points); **not re-verified on live** |
| 9 | the abstention comparison | **unavailable for every judge**: neither the LLM's nor Laya's option set has an abstain channel; Jev's check has one, but the semantics differ |
| 10 | **Repeated sampling of the remaining LLM arms** | P14 (authority location), P19 (n=1100 calibration), P21 (thinking cost), P23 (logprobs), P24 (horizon) **are still single draws**. The two complementarity regimes have been changed to `temperature=0` × 3–4 draws with agreement reported; the rest have not, and **their point estimates should not be read as precise values** |
| 11 | ~~Jev's live reproduction~~ | ✅ **Completed** (round three, P27): an independent direct-HTTP route was built (`src\instrument\jev_client.py`), **field-by-field identical** to the DSH plugin at the same state size; it produced **5 JSON files** (latency n=35, cost by tier, the two-way `probability` semantics, the per-primitive field inventory, derived summary). **Jev's column now has machine-readable artifacts.** Not touched: **the provider-side window cap** (proved only that at 39,927 characters tokens still grow monotonically with characters) |

## 10.2 Methodological limitations

1. **A single LLM configuration**: `deepseek-flash`, non-thinking mode. **Not tested**: `deepseek-v4-pro`, a
   self-consistency sampling arm, the quality difference under thinking mode (because the corpus is at
   ceiling, **all four P21 tiers have accuracy 1.00, so "does thinking buy quality" cannot be answered**).
   → **The sampling protocol has been partly tightened**: the two complementarity regimes (P15, CHAIN-AUDIT)
   are now **repeatedly sampled 3–4 times at `temperature=0`** with the item-level label agreement reported.
   **The remaining LLM arms (P14, P19 calibration, P21 cost, P23 logprobs, P24 horizon) are still single
   draws**, and their point estimates likewise must not be read as conclusions at the four-decimal level;
   this clause has been entered in §10.1.
2. **One machine, one device, one network path, one collection period**: latency and cost **vary with
   location and period** (a 2× peak/off-peak price spread; the collection period was not recorded).
3. **Laya's cost is not monetised**: self-hosted compute; "≈$0" is a **marginal** cost and excludes hardware
   amortisation.
4. **Several conclusions rest on synthetic/templated items**: absolute accuracy is not a capability estimate.
5. **n is extremely small for the cross-language items** (2 each for English and Russian): qualitative only.
6. **The hierarchy grouping is procedurally generated** (label-name token similarity): **the quality of the
   top-level grouping is itself the bottleneck** (group selection 0.275). **A semantically better grouping
   might improve Laya's end-to-end** — this is the explanation §7 least rules out.

## 10.3 On the scope of "a component with no judgment capability produces a credible results table"

This conclusion rests on **Jev's mock provider**, that is, a **deliberately constructed synthetic backend**.
→ **Its value is a methodological warning, not an assessment of Jev.** We must not let it be read as "Jev is
unreliable".
→ But it **extrapolates to any judging component that returns probabilities**: there is no distinguishable
difference between the mock and a real judge in **the shape of the results table** — that is exactly where
the danger lies.

## 10.4 The list of what cannot be extrapolated

| Cannot be said | Because |
|---|---|
| "Jev/Laya are generally worse than the LLM" | only **three** regimes were measured: the first two put the LLM at ceiling (**not measurable**), the third had its ceiling broken and was **re-judged after the ground-truth fix** (n=68), where Δ_catch is negative in 3/3 draws but **the precision is limited** (MDE = 0.28–0.30) |
| "No complementarity exists under any circumstances" | as above; the negative result holds only on the regimes measured, and the third regime **lacks the power to exclude** a moderate effect (MDE far larger than the pre-declared threshold of +0.10) |
| "Laya's window is 512 token" | it is a function of **"launch loadout × checkpoint queried"**: 1024 when english is loaded alone, 512 when three are loaded, while multilingual/typed-decisions is still 1024 under three loads |
| "The architectural claim has been falsified" | all one can say is that **no complementarity was found**, and that the third regime is **consistent with "shared failure" but did not reach significance** (Fisher p = 0.049/0.086/0.163) |
| "Perceptrons are generally unreliable" | not tested; this paper does not touch it |
| "On cost the judge is cheaper" | all three sit in the same 10⁻⁵ order of magnitude; and the LLM can use caching to push input down to $0.003/1M |

---

<!-- TRANSLATION-CONTINUES-HERE -->

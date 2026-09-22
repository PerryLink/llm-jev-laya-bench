# R16 — Baseline Ladder, Cost Accounting, Related Work, Defensible Claims

> **Unit:** R16 (baselines & positioning). **Date:** 2026-09-22.
> **Consumes:** [R1-architecture-and-threat-model.md](R1-architecture-and-threat-model.md) (concept base, threat model, design commands), [R2-verified-externals.md](R2-verified-externals.md) (verified external facts registry).
> **Feeds:** R15 (arms & equal-budget design, statistics), R12/R13 (measurement tasks), R14 (item battery), paper §Method / §Related Work / §Limitations.
>
> **Evidence discipline (binding, same rule as R2):** every number in the paper must trace to a line in R2's registry or to a first-party measurement. In this document, each factual claim is tagged **[VERIFIED-2026-09-22]**, **[SECOND-HAND]**, or **[NOT VERIFIED]**. A citation here is a link I fetched successfully unless marked otherwise. Prices, token counts and latencies are **empirical**: none are invented below; every one is either a dated snapshot of an official page or an explicit R12/R13 measurement task.

---

## 0. The fairness contract (read this before the ladder)

R1 §1–§2 fixes what the comparison can even mean: Jev/Laya cannot execute a task, so the only physically meaningful design is **one LLM executor, three interchangeable judgment layers**. R1 §7 adds three design commands (same executor, mandatory structured self-check arm, frontier as the main figure).

This unit adds a fourth command, which the baseline ladder exists to satisfy:

> **Symmetry command.** Every affordance, budget rule and scoring rule that is available to a typed judge must be available to the LLM judge, and vice versa. An affordance granted to one arm only is not a finding, it is a rigged comparison.

Three corollaries that R15 must implement literally:

1. **Abstention symmetry.** If Jev may return `insufficient`/`undecided` and Laya may return a low-confidence answer, the LLM arm must have an explicit `uncertain` key. **Abstention is a first-class output, not a parse failure.** Any arm's abstention is charged to coverage, never scored as an error (see §A.4).
2. **Retry symmetry.** If the typed arm may re-ask, the LLM arm may re-ask, and **every retry is charged to that arm's budget**.
3. **Structure symmetry.** The typed services force a typed question (noul/choice/score or Laya equivalent); the LLM arm therefore gets a *structured* container of the same shape (lettered options with descriptions, explicit boundary, explicit probability field). The free-prose arm is an additional ecological rung, not a substitute for the structured one.

**Comparison universe.** Only **(B) discriminative** sub-decisions (R1 §2) enter the main table: same/different, which option, what score, does the evidence support the claim, which item is more relevant. No arm is compared on generative work.

---

# PART A — THE BASELINE LADDER

## A.0 Ladder overview and the fair/padded verdict

Six rungs. Each rung is one *arm configuration*, not one *model*. "Fair" below means: the rung can be reported in the paper without a reviewer being able to attribute the result to prompt phrasing or budget asymmetry. "Padded" names which arm the rung accidentally favours, so R15 can pre-empt it.

| # | Rung | What it controls for | Known bias it carries | Cost driver | Verdict |
|---|---|---|---|---|---|
| 1 | LLM, free prose, unaided | Ecological validity: what agents actually do | Self-preference/verbosity if an LLM judge scores it; no probability; unparseable | completion tokens (long) | **FAIR as ecology; PADDED-FOR-LLM as a scored comparison** — must be scored by external rubric, never by an LLM judge |
| 2 | LLM, forced choice + stated probability (best-effort calibrated) | Format effects; makes the comparison honest | Overconfidence; position/option-order bias; phrasing sensitivity | prompt + short completion (+ reasoning tokens) | **FAIR — the mandatory headline LLM number** |
| 3 | LLM, self-consistency at **matched cost** | Variance reduction and sampling budget | Majority vote sharpens confidence; shared systematic error unaffected | k × (prompt + completion + reasoning) | **FAIR only if total spend is matched**; PADDED-FOR-LLM if call counts are matched |
| 4 | LLM + retry/re-ask with `uncertain` | Abstention availability | Retry can manufacture accuracy by spending more | extra calls + reasoning | **FAIR only if budget-charged and symmetric** |
| 5 | Majority vote over 3 samples vs single sample | Cheap variance reduction | Calibration distortion | 3× single | **FAIR if charged**; PADDED-FOR-LLM if uncharged |
| 6a | Cheaper LLM route: same model, `reasoning_effort: none` | The cheapest credible LLM judge | Non-thinking mode loses CoT gains | prompt + completion only | **FAIR** — verified cost lever, not a different model |
| 6b | Classical non-LLM baseline: frozen embedding + linear head (SetFit-style) on classification items only | Where typed judges sit vs classical methods | **Gets training labels** — the typed judges are zero-shot; note the asymmetry explicitly | one forward pass per item | **FAIR as an upper reference if the label advantage is stated** |

### A.0.1 The ladder must be mirrored on the typed side

A ladder only on the LLM side is itself asymmetric. R15 must run the **same rung structure** for Jev and Laya:

| Rung | LLM implementation | Typed implementation |
|---|---|---|
| 1 | free prose | (no counterpart — typed services cannot produce prose; declare this, do not fake it) |
| 2 | forced choice + stated probability, logit readout available | native noul/choice/score; native `probabilities` |
| 3 | k samples, majority/mean aggregation, cost-matched | k repeated calls, aggregate probabilities; **plus batch-q questions per state** |
| 4 | `uncertain` key + budget-charged retry | `insufficient`/`undecided`/low confidence + budget-charged retry |
| 5 | 3-sample majority | 3 repeats, aggregate |
| 6a | `reasoning_effort: none` | smallest/cheapest checkpoint actually shipped (Laya multilingual / `laya-typed-decisions`) |
| 6b | — | classical embedding+linear head, same labelled split |

---

## A.1 Rung 1 — LLM, free prose, unaided (the realistic agent baseline)

**Prompt/harness shape (template).**

```
SYSTEM: You are an autonomous agent working on a long-horizon task.
        No output format is imposed on you.
USER:   [state / trajectory so far]
        [the question a judge would have answered]
        Answer in your own words. Say whatever you think is useful.
```

**What it controls for.** Ecology. This is what an agent does when nobody inserts a judge: it narrates, hedges, and moves on. Including it prevents the objection "your structured prompt is not how anyone uses an LLM".

**Biases and how to neutralise them.**
- *Self-preference / verbosity*: Zheng et al. document position, verbosity and self-enhancement biases in LLM judges ([arXiv:2306.05685](https://arxiv.org/abs/2306.05685)); bias has been systematically quantified ([arXiv:2410.02736](https://arxiv.org/abs/2410.02736)) and linked to low-perplexity preference ([arXiv:2410.21819](https://arxiv.org/abs/2410.21819)). **Therefore: rung 1 is never scored by an LLM judge in the primary analysis.** Score it with an external rubric: two annotators, pre-registered rubric, report Cohen's κ (R1 §4.2, external ground truth only).
- *Unfalsifiable scoring*: if a prose answer does not commit to a label, the item is recorded as **abstention**, not as partially correct.
- *Extraction*: if the prose does contain a commitment, extract it **mechanically** with a regex/parser frozen before data collection; report the extraction failure rate.

**Verdict.** FAIR as ecology, and must be reported as a separate panel — never averaged into the structured comparison.

---

## A.2 Rung 2 — LLM, forced choice + stated probability, best-effort calibrated (**the rung that makes the comparison honest**)

This is the single most important rung. If it is weak, every typed-service advantage in the paper is a prompt artifact. It is therefore specified to be *as strong as the instrument allows*, and three facts about the instrument are now verified:

- **Logprobs are available.** The Chat Completions API exposes `logprobs` (bool) and `top_logprobs` (0–20) and returns per-token `logprob`/`top_logprobs` for both `content` and `reasoning_content` ([Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion)). **[VERIFIED via docs mirror snapshot fetched 2026-09-18]** So the "logit-style" rung is real, not hypothetical — the LLM arm can produce a genuine token-distribution readout, the thing the typed services produce natively.
- **Sampling is constrained in thinking mode.** `temperature` *has no effect* in thinking mode; `top_p` has a lower bound of 0.95 in thinking mode and is pinned to 1.0 in non-thinking mode ([Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode), same snapshot). **Consequence for rungs 3 and 5:** a k-sample self-consistency arm cannot be "temperature 0 vs temperature 0.7" inside thinking mode. R15 must run the sampling arm in non-thinking mode (where `temperature` is honoured) and/or with thinking at `top_p ≥ 0.95`, and must report which. This is the kind of detail that decides whether a self-consistency rung is a real baseline or decoration.
- **Reasoning effort values are `none | low | high | max`, default `high`.** The disabling value is `none`, not `off` — the brief's "off" should be normalised to `none` in the protocol. Same source: `max_tokens` defaults to 8K (non-thinking), 64K (thinking), 128K (`max`); `max_tokens` ≤ 384K; model id `deepseek-flash` = DeepSeek-V4.1-Flash, 1M context ([Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/), **[VERIFIED-2026-09-22]**).

### A.2.1 Strongest prompt format (template, run as-is)

```
SYSTEM
You are a decision component, not an assistant. You will receive a STATE and exactly one
typed QUESTION. Return one JSON object and nothing else.

RULES
R1. "key" must be exactly one of the option keys below (or "uncertain" if the question permits it).
R2. "p" is your probability in [0,1] that "key" is the CORRECT answer.
R3. "p_all" gives a probability for EVERY option key; entries must sum to 1.00 (±0.02).
R4. "boundary" below states what true/false (or each scale level) means. If it says NOT STATED,
    do not treat the missing text as evidence for any option; answer from the information
    actually present and lower your "p" accordingly.
R5. If the evidence in STATE does not settle the question, prefer "uncertain" over guessing.
R6. No prose, no extra keys, no markdown.

USER
STATE:
<<<{state}>>>

QUESTION: {instructions}

OPTIONS (key — meaning):
A — {option_text_or_criteria_description}
B — {option_text_or_criteria_description}
C — {option_text_or_criteria_description}
(…)

BOUNDARY: {boundary_text | "NOT STATED"}

Return JSON:
{"key": "<A|B|C|…|uncertain>",
 "p": 0.00,
 "p_all": {"A": 0.00, "B": 0.00, "C": 0.00},
 "evidence_1line": "<=12 words"}
```

Harness details that must be fixed in the protocol:

- **Constrained output.** `response_format: {"type":"json_object"}` guarantees valid JSON, but the provider requires the prompt itself to instruct JSON, warns about whitespace-only degeneration, and warns that content can be truncated when `finish_reason="length"` (same API reference). So: `response_format` **plus** the prompt instruction **plus** a `finish_reason=="length"` → *invalid* rule.
- **Do not plan on forced tool calls in thinking mode.** `tool_choice` values `required` and named tools return HTTP 400 in thinking mode (same API reference). If R15 wants schema-forced decoding, it must run non-thinking, or accept JSON mode + validation.
- **Logit readout variant (run as a second configuration of rung 2).** Ask for a single letter, `max_tokens=1`, `logprobs=true`, `top_logprobs=20`, run **non-thinking** (`reasoning_effort: none`) so the first generated token *is* the answer token; read the probability mass on each option letter; renormalise over the letters actually present; discard and count samples whose top-1 token is not an option letter. In thinking mode the first token is reasoning, so a naive first-token readout is invalid — the protocol must pin the position or pin non-thinking.
- **Option-order randomisation.** Present options in randomised order per item (with the order logged) and, if budget allows, run both orders as a position control. Rung 1 of this ladder would otherwise inherit the position bias documented in [arXiv:2306.05685](https://arxiv.org/abs/2306.05685) and [arXiv:2305.17926](https://arxiv.org/abs/2305.17926).
- **Descriptions are mandatory in the primary configuration.** Lettered options *with* descriptions is the strongest format; a bare-letters variant exists only to *measure* the band (§A.2.3).

### A.2.2 What to do about LLM overconfidence

The literature is genuinely split, and the protocol must reflect the split rather than pick the convenient side:

- Verbalized confidence from RLHF-tuned models can be **better** calibrated than conditional token probabilities — reported as up to a relative 50% ECE reduction on TriviaQA/SciQ/TruthfulQA ([Just Ask for Calibration, arXiv:2305.14975](https://arxiv.org/abs/2305.14975)).
- Verbalized confidence is also documented as **systematically overconfident**, with white-box methods better but the gap narrow (AUROC 0.522 → 0.605) ([Can LLMs Express Their Uncertainty?, arXiv:2306.13063](https://arxiv.org/abs/2306.13063)).
- Calibrated verbalized uncertainty is achievable under the right training regime ([Teaching Models to Express Their Uncertainty in Words, arXiv:2205.14334](https://arxiv.org/abs/2205.14334)), and larger models are well calibrated on multiple-choice in the right format ([Language Models (Mostly) Know What They Know, arXiv:2207.05221](https://arxiv.org/abs/2207.05221)).
- Sample-consistency/semantic-entropy signals are strong uncertainty estimators without logits ([Semantic Uncertainty, arXiv:2302.09664](https://arxiv.org/abs/2302.09664)).
- Post-hoc **temperature scaling** is the standard single-parameter fix ([On Calibration of Modern Neural Networks, arXiv:1706.04599](https://arxiv.org/abs/1706.04599)).
- Calibration has a floor: sufficiently calibrated generative models must hallucinate at a rate tied to singleton facts ([Calibrated Language Models Must Hallucinate, arXiv:2311.14648](https://arxiv.org/abs/2311.14648)) — cite this when arguing that no judge can be perfectly calibrated.

**Rule (pre-registered, four readouts, all reported):**

1. **raw stated `p`** (verbalized);
2. **logit-readout `p`** (token distribution, non-thinking configuration);
3. **sample-consistency `p`** (fraction of k samples agreeing with the majority label; semantic-equivalence-free because the answer space is a discrete key set);
4. **post-hoc temperature-scaled `p`** — **scalar temperature fitted on a held-out calibration split only**, never on test items; report both raw and scaled, and report the fitted temperature. Fit the typed arms' temperature the same way (R2 §B notes Laya's multilingual checkpoint ships at temperature 1.0 and will readily emit 100%/0%: **both sides get the same repair budget**).

Metric: binned reliability curves + ECE, **never** a direct numerical comparison of a `confidence` field across systems (R1 §4.4: Laya's `confidence` for `choice`/`score` is an entropy-derived concentration statistic, and for `noul` it is distance from the 0.5 boundary — it is not P(correct)).

### A.2.3 Prompt-sensitivity band (the anti-straw-man instrument)

Pre-register **four** prompt configurations and report all four as a band; the headline LLM number is the **best** configuration at equal spend, not the mean:

| ID | Configuration | Purpose |
|---|---|---|
| P1 | bare lettered options, no descriptions, no boundary clause | measures the downside of a lazy baseline |
| P2 | lettered options **with** descriptions (primary) | strongest realistic format |
| P3 | P2 + explicit boundary clause + `uncertain` permitted | mirrors typed semantics exactly |
| P4 | P2 with `reasoning_effort` swept over `{none, low, high, max}` | separates format effect from reasoning-budget effect |

Report `min / median / max` accuracy and ECE across P1–P4. **The typed services get the analogous band** (option order, option count up to the documented accuracy cliff, and — for Laya — the `laya_plan`-style pre-check on/off). Anything less is asymmetric.

**Verdict.** FAIR. PADDED-FOR-TYPED if run only as P1, or with one frozen phrasing, or without the logit readout.

---

## A.3 Rung 3 — Self-consistency at **matched cost** (k samples, majority vote / averaged verbalized confidence)

**Template.**

```
[P2 prompt, unchanged]
Sampling configuration (must be stated; see the thinking-mode constraint in §A.2):
  non-thinking: reasoning_effort = "none", temperature = 0.7, top_p = 1.0 (pinned by provider)
  thinking:     reasoning_effort ∈ {low, high, max}, top_p ≥ 0.95 (values below are raised), temperature ignored
Draw k independent samples per item. Aggregate:
  (a) majority key (vote over "key"; ties → "uncertain");
  (b) mean of "p_all" vectors, renormalised;
  (c) sample-consistency p = fraction of samples whose key equals the majority key.
Charge k × (prompt + completion + reasoning) tokens to the LLM arm's budget.
```

**Cost equalisation — the algebra.** Let `B` be a fixed total budget in USD for an item battery, and let `C̄_LLM`, `C̄_Jev`, `C̄_Laya` be *measured* mean costs per decision (Part B gives the formulas; R12/R13 supply the values — no values may be assumed):

```
k_LLM  = floor(B / (N_items · C̄_LLM))          # samples per item the LLM arm can afford
k_type = floor(B / (N_items · C̄_typed))        # repeats per item the typed arm can afford
```

**Both directions must be reported:**

- **Direction 1 (primary analysis): fixed spend, quality as the dependent variable.** Quality at spend `B`, swept over a grid of `B`. This is the **equal-budget quality frontier** argued for in Part B.
- **Direction 2 (secondary): fixed decision count, cost as the dependent variable.** `k=1` everywhere; report dollars, tokens, wall-clock and human-review minutes per decision and per completed task.

**State the primary explicitly in the paper:** *primary = fixed total spend (Direction 1); the fixed-count comparison (Direction 2) is reported as the cost table.* Rationale: the treatment in this study is the judgment layer's *price/performance*, and equal-call-count comparisons systematically favour whichever arm has the cheaper marginal call while hiding how many more decisions the budget could have bought.

**Known bias.** Majority voting over a discrete label set **sharpens** the confidence distribution: it can raise accuracy and worsen ECE at the same time. Report accuracy and calibration as separate panels (this is also why the sample-consistency `p` is not automatically the best `p`). Majority vote cannot repair *shared* systematic error — with a single model family, all k samples share the same blind spots; say so rather than implying `k→∞` is a cure.

**Verdict.** FAIR only at matched spend. PADDED-FOR-LLM if `k` is matched instead of dollars; PADDED-FOR-LLM if the LLM's samples are not charged (§A.5).

---

## A.4 Rung 4 — LLM + retry/re-ask loop with a deferral option

**Template.**

```
[P2 prompt, with "uncertain" admitted as a key]
R5 becomes: "Choosing 'uncertain' is scored as ABSTENTION, not as an error. Coverage is reported
             separately from selective accuracy. You are not penalised for abstaining."
Retry policy (identical for every arm, pre-registered):
  if key == "uncertain"  OR  p < τ        → re-ask ONCE with the same prompt and the new instruction
                                            "Previous answer was uncertain; commit or abstain."
  the retry call is charged to this arm's budget.
  after the retry: key or "uncertain" (final).
```

**Why it matters.** Abstention must be available to the LLM or the comparison is rigged: selective prediction is a well-established regime with a coverage/risk trade-off ([Selective Classification for Deep Neural Networks, arXiv:1705.08500](https://arxiv.org/abs/1705.08500)), and deferral to a better decision-maker is a formal learning problem ([Predict Responsibly, arXiv:1711.06664](https://arxiv.org/abs/1711.06664); [Consistent Estimators for Learning to Defer to an Expert, arXiv:2006.01862](https://arxiv.org/abs/2006.01862)); the design space for LLM abstention is surveyed in [Know Your Limits, arXiv:2407.18418](https://arxiv.org/abs/2407.18418).

**Calibration warning to cite.** Abstention is *not* solved by scaling, and reasoning fine-tuning **degrades** abstention by 24% on average across 20 datasets ([AbstentionBench, arXiv:2506.09038](https://arxiv.org/abs/2506.09038)). Since rung 4's τ and the reasoning-effort sweep interact, R15 should report the abstention rate **per effort level** — this is a cheap, genuinely interesting measurement (a judge that abstains more when you pay for more thinking is a finding, either way).

**Scoring.** Report selective accuracy, coverage, and the risk–coverage curve per arm at matched spend; charge the retry to the arm; count "final uncertain" as abstention. Also report the **abstention-behaviour difference**: Laya's `noul` confidence is distance from the 0.5 boundary and Jev returns `insufficient`/`undecided`/`unknown` verdicts, so the *mechanisms* of abstention differ — compare the curves, not the labels.

**Verdict.** FAIR only with abstention on all sides and budget-charged retries. PADDED-FOR-TYPED if the typed arm may re-ask (or batch quiet questions) while the LLM may not.

---

## A.5 Rung 5 — Majority vote over 3 samples vs single sample

**Template.** As rung 3 with `k=3`, plus a `k=1` control from the identical prompt and sampling configuration.

**What it buys.** Self-consistency is a strong, cheap variance-reduction baseline for multi-step reasoning ([arXiv:2203.11171](https://arxiv.org/abs/2203.11171)) and often closes much of an apparent gap. This is precisely why it must be in the paper: a reviewer's first thought is "3 samples would fix that".

**Bias.** Uncharged samples = free accuracy. **Charge all 3.** Report `k=1` vs `k=3` **and** `k=3` at the same spend as the typed arms (which may then get, e.g., 3 repeats plus many more items). Also report the per-item disagreement rate — items where 3 samples disagree are the items where a judge is actually needed, and that is a process-level result the paper can use.

**Verdict.** FAIR if charged; PADDED-FOR-LLM otherwise.

---

## A.6 Rung 6 — Cheaper LLM route and a classical non-LLM baseline

**6a — cheap LLM route (`reasoning_effort: none`).** Verified lever: `none` disables thinking; `low`/`high`/`max` enable it; default `high` ([Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode)). Because reasoning tokens are reported separately in `usage.completion_tokens_details.reasoning_tokens` ([API reference](https://api-docs.deepseek.com/api/create-chat-completion)) and billed as output tokens, effort is a **first-order cost lever** (R2 §A.1.3). This rung is the honest "cheap LLM" arm and should be swept, not fixed.

*Do not invent a smaller model name.* The verified catalog on the pricing page lists exactly two routes: `deepseek-flash` and `deepseek-v4-pro` (the larger one). Any additional third-party "small LLM" route must be named from a catalog entry fetched at protocol-freeze time, and recorded in R2.

**6b — classical baseline for pure classification items.** A frozen sentence encoder + linear head, or SetFit-style few-shot fine-tuning ([Efficient Few-Shot Learning Without Prompts, arXiv:2209.11055](https://arxiv.org/abs/2209.11055)); train on a small labelled split, report accuracy and post-temperature-scaling ECE. **State the asymmetry**: this baseline *receives training labels*, while Jev/Laya are used zero-shot via typed questions. It is a reference point for "where do typed judges sit relative to non-LLM classical methods", not a like-for-like competitor.

**Verdict.** FAIR; the label asymmetry must be printed next to the number.

---

## A.7 Straw-man audit checklist (print this in the paper's appendix)

A reviewer should be able to tick every box:

| # | Gate | Pass condition |
|---|---|---|
| 1 | Shared executor | Every arm uses the same executor model, prompt and seeds; only the judgment layer changes (R1 §7) |
| 2 | Structured self-check arm present | The LLM must answer the *same typed question* it is being compared on |
| 3 | Prompt band reported | P1–P4 (§A.2.3) with min/median/max, plus the typed-side band |
| 4 | Best LLM variant is the headline | Not the mean, not the laziest |
| 5 | Logit readout attempted | Including parse-failure rate |
| 6 | Budget matched in dollars | Both directions reported; primary named |
| 7 | Retries and samples charged | No free accuracy |
| 8 | Abstention available to all | `uncertain` / `insufficient` / low-confidence treated identically in scoring |
| 9 | Calibration repair symmetric | Same held-out split, same temperature-scaling budget per arm |
| 10 | Ground truth external | Never defined by any arm's output (R1 §4.2) |
| 11 | Clustered statistics | Cluster by run, not by decision (R1 §4.3) |
| 12 | Latency device-qualified | CPU vs GPU stated; warm-up before timing (R2 §B) |

---

# PART B — COST ACCOUNTING MODEL

R1 §3 already fixed the shape (unit costs are not commensurable; must be modelled explicitly) and named the equal-budget frontier as the recommended main figure. This part supplies the terms, the required lookups, the sensitivity analysis, and the argument for and against the frontier as Figure 1.

## B.1 Symbols

| Symbol | Meaning | Source status |
|---|---|---|
| `T_prompt_hit`, `T_prompt_miss` | prompt tokens served from / missing the context cache | measured per call (`usage.prompt_cache_hit_tokens` / `prompt_cache_miss_tokens`) **[VERIFIED field names]** |
| `T_out`, `T_reason` | completion tokens; reasoning tokens (`usage.completion_tokens_details.reasoning_tokens`) | measured per call |
| `p_hit`, `p_miss`, `p_out` | price per token, cache-hit input / cache-miss input / output | dated price page; snapshot below |
| `k` | samples per item (LLM) or repeats per item (typed) | design |
| `q` | questions asked of **one** state in one typed call | design |
| `E(state)` | state-encoding cost of a typed judge call | **must measure** (R12/R13) |
| `c_q` | marginal cost of one typed question | **must measure** (R12/R13) |
| `λ` | orchestration overhead per round-trip (harness CPU, serialisation, retries) | **must measure** (R11) |
| `L` | wall-clock latency (p50/p95), device-qualified | **must measure** |
| `m` | machine-hour rate for local inference (amortised hardware + power) | **team policy parameter, swept — not a fact** |
| `h` | human-review hourly cost | **team policy parameter, swept — never imported from another paper** |
| `τ_retry`, `τ_esc` | thresholds for re-ask / escalation | design |
| `N` | items in the battery | design (R14) |

**Dated price snapshot [VERIFIED-2026-09-22, first-party].** `deepseek-flash` (DeepSeek-V4.1-Flash), USD per 1M tokens ([Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/)): input cache-hit **$0.003 off-peak / $0.006 peak**; input cache-miss **$0.15 / $0.30**; output **$0.60 / $1.20**. Off-peak is exactly half of peak; peak = UTC Mon–Fri 01:00–04:00 and 06:00–10:00, excluding Chinese public holidays. Concurrency limit 2500. **Re-verify this page at protocol freeze and at submission; record the fetch date in the paper's cost table.** (This duplicates R2 §A deliberately: R2 is the registry, and the paper must cite it there.)

## B.2 Cost per decision

**LLM, one decision, one sample**

```
C_LLM_1 = T_prompt_hit · p_hit + T_prompt_miss · p_miss
        + (T_out + T_reason) · p_out
        + λ · R
```
with `R` = round-trips (1 for a single call; retries add). *Reasoning tokens are reported in usage and billed among output tokens; confirm the billing treatment by reconciling one invoice against logged usage — treat it as a measurement, not an assumption.*

**LLM arm, k samples**

```
C_LLM(k) = k · C_LLM_1 + C_retry · 1[key = uncertain] + C_judge_side
```
where `C_judge_side` = orchestration for aggregation (negligible for a key-vote; measure it anyway, λ is where such claims die).

**Typed judge (remote, e.g. Jev)**

```
C_typed = E(state) + q · c_q + λ · R
```
per R1 §3. Note the batching asymmetry: `E(state)` amortises over `q` questions asked of the same state.

**Typed judge (local, e.g. Laya)**

```
C_local = (encode_ms(state) · q_reencode + decode_ms) · (m / 3.6e6)
        + energy/power term if measured
```
The load-bearing empirical fact (R2 §B, upstream issue #49, **[SECOND-HAND — R13 must confirm]**) is that Laya re-encodes the same state per question, so `q_reencode ≈ q` rather than `1`. If that holds, **"N cheap calls" is not cheap locally** and the protocol must treat *judgment cadence and batch size* as an independent variable (R1 §3).

**Per-decision cost is not the paper's efficiency claim** — it is the input to it.

## B.3 Cost per completed task

```
C_task = Σ_{d ∈ decisions(task)} C_decision(d)
       + P_retry · C_retry_avg
       + P_esc   · C_escalation
       + P_human · (human minutes · h)
       + C_harness(session)
```

And the two derived quantities that must both appear:

```
Cost per completed task        = C_task / 1
Cost per SOLVED task           = C_task / success_rate        ← the honest efficiency number
```

`C_task / success_rate` is the shape used by cost-aware cascades (FrugalGPT reports matching a frontier model's quality at a large cost reduction rather than a quality gain per se — [arXiv:2305.05176](https://arxiv.org/abs/2305.05176)). Report it with clustered CIs (R1 §4.3).

## B.4 The cache-hit counterexample (must be reported, not buried)

The LLM arm is entitled to a cache-friendly prompt layout: **stable prefix = state, variable suffix = question.** With that layout, repeated questions against the same long state can hit the context cache at **$0.003/1M** off-peak instead of **$0.15/1M** — a 50× input discount (**[VERIFIED-2026-09-22]**, and R2 §A.1 flags it as the strongest counter-argument to the paper's efficiency claim).

Combined with Laya's per-question re-encoding, the honest statement is:

> **A typed judge is not automatically cheaper per decision when the state is long, shared, and cache-resident for the LLM.**

Therefore the cost model must carry `p_hit`/`p_miss` **separately** (never a blended input price), the achieved cache-hit rate must be **logged**, and the frontier must be recomputed at `h ∈ {0, 0.5, 0.9, 1.0}`. If the typed arm only wins at low `h`, the paper says exactly that.

## B.5 MUST LOOK UP / MUST MEASURE registry (no invented numbers)

| # | Quantity | Owner | Status |
|---|---|---|---|
| 1 | `p_hit`, `p_miss`, `p_out`, peak/off-peak window, at run time | R11 | snapshot **[VERIFIED-2026-09-22]**; re-verify at freeze |
| 2 | Per-call `prompt_cache_hit_tokens`, `prompt_cache_miss_tokens`, `completion_tokens`, `reasoning_tokens` | R11 | field names **[VERIFIED]**; logging to be built |
| 3 | Reasoning tokens by effort `{none, low, high, max}` on the real battery | R11/R13 | **measure** |
| 4 | Achieved cache-hit rate of the chosen prompt layout | R11 | **measure** |
| 5 | `T_out` per rung (P1–P4) | R11 | **measure** |
| 6 | Latency p50/p95 per arm, device-qualified, post-warm-up | R11/R13 | **measure**; Laya cold start 25–35 s is **[SECOND-HAND]** and must not pollute means |
| 7 | Jev price, latency, state cap, calibration state | R12 | **[NOT VERIFIED]** — R2 §C: no first-party source yet; without it the Jev cost comparison does not exist |
| 8 | Laya per-question re-encoding and batching | R13 | **[SECOND-HAND]** (upstream issue #49) |
| 9 | `λ` orchestration overhead per round-trip | R11 | **measure** |
| 10 | `m` local machine-hour rate | R15/lead | **policy parameter, swept** |
| 11 | `h` human-review rate | R15/lead | **policy parameter, swept**; state jurisdiction/date if a real rate is used |
| 12 | Option-order / position sensitivity per arm | R12/R13 | **measure** |
| 13 | Whether reasoning tokens are billed exactly as output tokens | R11 | **reconcile one invoice against usage logs** |

**Prohibition.** No cost number in the paper may come from a blog, a README, or a model card. Latency claims from vendor READMEs are explicitly excluded (R2 §D).

## B.6 Sensitivity analysis (pre-register the grid)

| Factor | Values | Why |
|---|---|---|
| Time-of-day pricing | off-peak / peak | exactly ×2 on every LLM term |
| Cache-hit rate `h` | 0, 0.25, 0.5, 0.9, 1.0 | 50× input-price lever (§B.4) |
| Reasoning effort | `none`, `low`, `high`, `max` | R2 §A.1.3: an order-of-magnitude swing is *expected*, must be measured |
| Typed-service price multiplier | 0.1×, 0.5×, 1×, 2×, 10× of measured LLM cost/decision | Jev pricing unknown → break-even must be published as a **price**, not an assumption |
| Retry/escalation rates | measured, plus ±50% perturbation | retries are the hidden budget sink |
| Human-review rate `h` | 0, low, high | determines whether deferral is a cost saving or a cost transfer |

**Deliverable: break-even statements.** Not "the typed judge is cheaper" but *"the typed-judge advantage in the equal-spend frontier survives any typed-service price below X USD per 1,000 decisions (off-peak, h = 0.5); above 2× the measured LLM cost per decision the frontier inverts."* The break-even price is defensible; the point estimate is fragile.

## B.7 Equal-budget comparison design

At fixed total spend `B` on a fixed battery:

```
Decisions affordable = B / C̄_decision(arm)
```

`C̄_decision` for the typed arm is (measured) far below the LLM arm's, so the typed arm buys **many more decisions** at the same spend — the exact multiple is an empirical output of this study, not a claim to be asserted in the introduction (R12/R13 first). Two consequences:

1. **Depth per item vs breadth over items.** With a cheap judge you can afford a *judgment cadence* (a check after every step) that is unaffordable with an LLM judge. The frontier is therefore not only "same decisions, less money" but "more decisions, same money" — which is what a long-horizon agent actually needs.
2. **The frontier is a curve, not a point.** Plot quality (final task success) against spend `B` for each arm, each arm drawn at its *best* pre-registered configuration, with clustered bootstrap CIs. Sweep `B` over at least 4 levels spanning the regime where the LLM arm can afford 1 and ≥8 samples per item.

## B.8 Is the frontier the paper's most defensible figure? — argument both ways

**FOR (I recommend it as Figure 1).**
- It is robust to the exact failure the threat model ranks highest (R1 §4.1): a single accuracy number is a prompt artifact, whereas *dominance across a spend grid, at each arm's best prompt variant,* is not.
- It matches what a practitioner must decide (a budget), not what a benchmark finds convenient (a call count).
- It is falsifiable and can come out negative: if the LLM arm wins the frontier, that is a publishable, honest result, and the paper survives.
- It is the natural home for the two asymmetric facts this study uniquely measures: cache-hit economics and per-question state re-encoding.

**AGAINST (report these limits in the caption).**
- A frontier is only as good as its cost model: omit human review or cache hits and the curve is fiction (hence §B.4–§B.6 are not optional).
- Dollars are not the only budget. Wall-clock latency and human attention are separate axes; a judge that is cheap in dollars but serialises the loop can lose on wall-clock. **Recommendation: report the frontier in dollars as primary and duplicate it in wall-clock and in human-minutes as supplementary panels.**
- A frontier can conceal a narrow win: if the typed arm dominates only for `B` between two values, the figure must show it, not average it away.
- The frontier is a *comparative efficiency* figure; it is not the paper's novelty. The distinctive measurements are the process metrics R1 §5 already names — **error-detection lead time vs horizon** and **truncation/budget-overflow rate vs horizon**. Recommend: Figure 1 = equal-spend frontier; Figure 2 = error-detection lead time vs horizon. The frontier is the most defensible *comparative* claim; the lead-time curve is the most *novel* content.

---

# PART C — RELATED WORK AND POSITIONING

Every link below was fetched successfully unless tagged otherwise. "Establishes" states what the cited item actually claims (abstract-level unless noted).

## C.1 LLM-as-a-judge and its biases

| Work | Establishes | Delta here |
|---|---|---|
| [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685) (Zheng et al., NeurIPS 2023 D&B) | Strong LLM judges reach >80% agreement with human preference, but carry position, verbosity and self-enhancement biases; proposes mitigations | Classic LLM-judge framing. **Delta:** the present paper does not judge with an LLM; it replaces the judge's *species*. Bias controls (order randomisation, external rubric) are inherited, not invented |
| [Large Language Models are not Fair Evaluators](https://arxiv.org/abs/2305.17926) (Wang et al.) | Ranking can be hacked by reordering candidates; calibration framework (multiple evidence, balanced position, human-in-the-loop) | **Delta:** order sensitivity is treated here as a *measured arm property for every judge* (including the typed ones — Laya needs its own order test), not only as an LLM flaw |
| [Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge](https://arxiv.org/abs/2410.02736) (Ye et al.) | 12 bias types quantified automatically (CALM); biases persist in advanced models | Supplies the bias taxonomy to pre-empt for the LLM arm |
| [Self-Preference Bias in LLM-as-a-Judge](https://arxiv.org/abs/2410.21819) (Wataoka et al.) | Quantitative self-preference metric; preference tracks low perplexity of the output | Justifies the rule that a free-prose rung is never scored by an LLM judge here |
| [A Survey on LLM-as-a-Judge](https://arxiv.org/abs/2411.15594) (Gu et al.) | Comprehensive survey of reliability, consistency, bias mitigation, plus a benchmark | The positioning target: this paper must not re-derive the survey's claims, only cite them |
| [Security in LLM-as-a-Judge: A Comprehensive SoK](https://arxiv.org/abs/2603.29403) (Al Masoud et al., 2026) | 45 studies, 2020–2026; judges are both attack targets and attack instruments | **Delta:** a typed non-generative judge removes prompt-injection *of the judge itself* as an attack surface (it never generates), while adding a new one (state truncation). Worth one paragraph, not a claim of security |

## C.2 Calibration of LLM confidence; verbalized vs internal

Covered in §A.2.2 with links: [Just Ask for Calibration](https://arxiv.org/abs/2305.14975) (verbalized beats conditional probabilities for RLHF LMs, up to ~50% relative ECE reduction), [Can LLMs Express Their Uncertainty?](https://arxiv.org/abs/2306.13063) (verbalized confidence overconfident; white-box better but narrowly: AUROC 0.522→0.605), [Teaching Models to Express Their Uncertainty in Words](https://arxiv.org/abs/2205.14334), [Language Models (Mostly) Know What They Know](https://arxiv.org/abs/2207.05221), [Semantic Uncertainty](https://arxiv.org/abs/2302.09664), [On Calibration of Modern Neural Networks](https://arxiv.org/abs/1706.04599), [Calibrated Language Models Must Hallucinate](https://arxiv.org/abs/2311.14648).

**Honest positioning.** The verbalized-vs-internal question is *contested*, and the present paper is a **new measurement site** for it: it can report four readouts (verbalized, logit, sample-consistency, temperature-scaled) on the same items for one model, plus the same reliability curves for two typed judges that output a probability natively. What it cannot do is settle the general question — one model, one battery, one language set.

## C.3 Selective prediction, abstention, learning-to-defer, cascades and escalation

| Work | Establishes | Delta here |
|---|---|---|
| [Selective Classification for Deep Neural Networks](https://arxiv.org/abs/1705.08500) (Geifman & El-Yaniv) | User-set risk level with coverage trade-off; a reject option with guarantees | Ancestor of the abstention rung and of the risk–coverage curve |
| [Predict Responsibly: Improving Fairness and Accuracy by Learning to Defer](https://arxiv.org/abs/1711.06664) (Madras et al., NeurIPS 2018) | A model may "Pass" the decision downstream; generalises rejection learning | Direct ancestor of "the judge abstains and something else decides" |
| [Consistent Estimators for Learning to Defer to an Expert](https://arxiv.org/abs/2006.01862) (Mozannar & Sontag, ICML 2020) | Consistent surrogate losses for classifier+rejector with an expert | **The escrow hybrid arm is a cascade with a non-LLM judge; the *learning* of the deferral policy is prior art.** The present paper must not claim a new deferral algorithm |
| [Know Your Limits: A Survey of Abstention in LLMs](https://arxiv.org/abs/2407.18418) (Wen et al., TACL 2024) | Framework over query/model/human values; metrics and benchmarks | Positions the "uncertain is a first-class output" rule |
| [AbstentionBench](https://arxiv.org/abs/2506.09038) (Kirichenko et al., 2025) | 20 datasets, 20 models: abstention unsolved; reasoning fine-tuning degrades it by 24% on average; prompting helps but does not fix | Pre-registers the expectation that higher reasoning effort may *worsen* the LLM arm's abstention → measure it per effort level |
| [FrugalGPT](https://arxiv.org/abs/2305.05176) (Chen, Zaharia, Zou, 2023) | LLM cascade matches the best single model with large cost reduction, or improves accuracy at equal cost | **The cheapest-judge-first architecture is prior art.** The delta is the judge's species, not the architecture |
| [RouteLLM](https://arxiv.org/abs/2406.18665) (Ong et al., 2024) | Preference-data routers cut cost >2× at comparable quality; routers transfer across model pairs | Prior art for routing; here the routing signal is a typed judge's calibrated probability |
| [AutoMix](https://arxiv.org/abs/2310.12963) (Aggarwal et al., NeurIPS 2024) | Few-shot self-verification + POMDP router; >50% cost reduction at comparable performance | Closest "LLM self-verifies then escalates" baseline; the present paper's structured self-check arm is its cousin, and must be cited as such |
| [Cascaded Language Models for Cost-effective Human-AI Decision-Making](https://arxiv.org/abs/2506.11887) (Fanconi & van der Schaar, 2025) | Two-stage deferral + abstention + online learning, with a human tier; beats single models at lower cost | **Closest architectural ancestor of the "escrow hybrid".** It already has tiers + deferral + abstention + human. The delta is that the middle tier is a *non-LLM, local, non-autoregressive* judge |
| [Calibrate-Then-Delegate](https://arxiv.org/abs/2604.14251) (Pona et al., 2026) | Delegation value probe: uncertainty is a poor proxy for the *benefit* of an expert call; threshold calibrated with finite-sample guarantees | Sharpest modern statement of why "escalate on low confidence" is not optimal — cite it and **do not claim optimal escalation**: the paper's τ rules are heuristic |
| [Knowing When to Ask for Help: Bayesian Self-Escalation](https://arxiv.org/abs/2608.24087) (Shaikh, 2026) | Intra-generation escalation as Bayesian optimal stopping; regret bound governed by posterior calibration; 1/√n finite-sample result | Sets the bar for any "optimal policy" language: without a calibrated posterior and a regret analysis, escalation here is a heuristic, and the paper should say so |
| [Confident Adaptive Language Modeling](https://arxiv.org/abs/2207.07061) (Schuster et al., NeurIPS 2022) | Per-input/timestep compute allocation with confidence, up to 3× speedup at maintained quality | Prior art for "spend compute where the model is unsure" — same logic, different granularity |

## C.4 Non-autoregressive, energy-based, discriminative and decision-focused framing

| Work | Establishes | Delta here |
|---|---|---|
| [Non-Autoregressive Neural Machine Translation](https://arxiv.org/abs/1711.02281) (Gu et al., ICLR 2018) | Parallel output generation, ~10× lower latency, at some quality cost | Establishes the speed/quality trade of non-autoregressive decoding — **and that "non-autoregressive" is a decoding property, not a claim of better judgment** |
| [Mask-Predict](https://arxiv.org/abs/1904.09324) (Ghazvininejad et al., EMNLP 2019) | Iterative parallel decoding, within ~1 BLEU of left-to-right | The mature form of the NAR family |
| [Residual Energy-Based Models for Text Generation](https://arxiv.org/abs/2004.11714) (Deng et al., ICLR 2020) | Sequence-level unnormalised EBMs in the residual of a locally normalised LM | Energy-based text models are prior art; relevant because a "one forward pass decision" is closer to a discriminative scorer than to generation |
| [Energy-Based Transformers are Scalable Learners and Thinkers](https://arxiv.org/abs/2507.02092) (Gladstone et al., 2025) | Verify-then-optimise prediction; EBTs scale faster and gain more from System-2-style inference | The strongest recent statement of "prediction as verification/optimisation" — a legitimate academic anchor for the decision-model idea, without needing the marketing term |
| [On Discriminative vs. Generative Classifiers](https://papers.nips.cc/paper/2001/hash/7b7a53e239400a13bd6be6c91c4f6c4e-Abstract.html) (Ng & Jordan, NIPS 2001) | Discriminative learning has lower asymptotic error; generative can approach its (higher) asymptote faster | **This is the established framing** for what Jev/Laya are relative to an LLM. Use it |
| [Smart "Predict, then Optimize"](https://arxiv.org/abs/1710.08005) (Elmachtoub & Grigas) | SPO loss measures *decision* error, not prediction error; consistent convex surrogate | The established academic home for "optimise the decision, not the prediction" — better vocabulary than "decision model" |
| [Decision Transformer](https://arxiv.org/abs/2106.01345) (Chen et al., 2021) | RL as conditional sequence modelling | **Disambiguation only:** "decision model/transformer" already names an unrelated, established RL method. Never use the bare phrase without a definition |

**Terminology verdict.** *"Decision model vs generative model"* is **not** an established academic category. What is established is: **discriminative vs generative** (Ng & Jordan), **non-autoregressive decoding**, **energy-based models**, and **decision-focused learning**. "System One decision model" is currently *industry* vocabulary circulating around this product family (Laya's own card and the `von` repository both use it; see C.6). **Recommendation:** define the term explicitly at first use ("we use *decision model* to mean a state-conditioned, non-generative, typed-question classifier that returns calibrated probabilities"), cite the four established framings above, and never write "we introduce decision models".

## C.5 Long-horizon agent evaluation: degradation, context limits, benchmarks

| Work | Establishes | Delta here |
|---|---|---|
| [Lost in the Middle](https://arxiv.org/abs/2307.03172) (Liu et al., TACL 2023) | Performance depends on where relevant information sits; degrades in the middle of long contexts | Canonical position-sensitivity result; motivates logging *where* the judge's evidence sits in state |
| [RULER](https://arxiv.org/abs/2404.06654) (Hsieh et al., COLM 2024) | NIAH is superficial; most models degrade well before their claimed context size | Establishes that claimed context ≠ usable context |
| [NoLiMa](https://arxiv.org/abs/2502.05167) (Modarressi et al., ICML 2025) | Without literal matches, 11 of 13 models drop below 50% of short-context baselines at 32K | The strongest evidence that judge inputs degrade with length |
| [Context Rot](https://www.trychroma.com/research/context-rot) (Hong, Troynikov & Huber, Chroma technical report, 2025-07-14) | 18 models; performance degrades non-uniformly as input length grows even on trivial tasks; distractors hurt; adding irrelevant context costs a retrieval step; structured haystacks perform *worse* than shuffled ones | **The closest empirical analogue to the present paper's core risk** — and it is a *report*, not a peer-reviewed paper: cite precisely, do not over-generalize. Its LongMemEval and AbsenceBench references are useful ([AbsenceBench](https://arxiv.org/abs/2506.11440), [LongMemEval](https://arxiv.org/abs/2410.10813), [Michelangelo](https://arxiv.org/abs/2409.12640)) |
| [Measuring AI Ability to Complete Long Software Tasks](https://arxiv.org/abs/2503.14499) (Kwa et al., METR; NeurIPS 2025) | 50%-task-completion time horizon as a metric; frontier horizon doubling roughly every 7 months; gains driven by reliability and error recovery | Supplies the horizon-as-a-metric vocabulary, and the reason "reliability budgeting" matters |
| [SWE-bench](https://arxiv.org/abs/2310.06770) / [OSWorld](https://arxiv.org/abs/2404.07972) / [GAIA](https://arxiv.org/abs/2311.12983) / [τ-bench](https://arxiv.org/abs/2406.12045) / [RE-Bench](https://arxiv.org/abs/2411.15114) / [TheAgentCompany](https://arxiv.org/abs/2412.14161) | Long-horizon, execution-scored agent benchmarks; τ-bench's `pass^k` measures reliability across trials; TheAgentCompany: best agent completes ~30% of realistic workplace tasks | The battery should borrow *execution-scored* ground truth and a `pass^k`-style reliability metric rather than accuracy alone |
| [LongDS-Bench](https://arxiv.org/abs/2605.30434) (Xu et al., EMNLP 2026) | Long-horizon multi-turn data analysis: 68 tasks, 2,225 turns; best model 48.45%; ~47-point drop from early to late turns; long-horizon errors 52–69% of failures; more steps do not help | **Most direct external support for the R1 §5 premise** that the interesting measurement is state maintenance and process quality, not step budget |
| [The Horizon Gap](https://arxiv.org/abs/2608.06663) (Chen, Wang & Qu, 2026) | Survey of 1,547 papers (2024–2026); disambiguates long-horizon / long-context / long-term memory; outcome-only signals grow uninformative as horizons lengthen, and the field manufactures denser step-level signals | Places the paper's process metrics inside a recognized research need — and warns that process-level signals used for both training and evaluation carry correlated bias |
| [Benchmarking the Residual](https://arxiv.org/abs/2607.27283) (Peng et al., 2026) | Position paper: to claim a "long-horizon failure", compare full-task success against a baseline prediction built from short individual stages using the **same agent configuration**; the log-ratio is the **horizon residual** | **A direct constraint on this paper's headline.** Any long-horizon claim needs the matched short-stage baseline, pre-registered. See Part D |
| [How Fast Do Agents Rot?](https://arxiv.org/abs/2609.01660) (Mittal, 2026) | Nine+ models, 10,664 trajectories; success follows a geometric law in a single per-step reliability parameter that saturates below 1; agentic tasks collapse within ~16 steps; degradation tracks **step count rather than context length** | **A competing explanation the paper must address:** if failure is per-step reliability, a cheap judge helps by raising per-step reliability — which is testable here. Note the context-length finding complicates a pure "truncation" story, and it is a preprint: **[NOT peer-reviewed]** |

## C.6 Process reward models, verifiers, tool-augmented verification — the closest mainstream analogue

| Work | Establishes | Delta here |
|---|---|---|
| [Let's Verify Step by Step](https://arxiv.org/abs/2305.20050) (Lightman et al., 2023) | Process supervision substantially outperforms outcome supervision on MATH; PRM800K released | The canonical "verify the step, not the answer" result. **Jev/Laya as step-level judges are a verifier with a non-LLM implementation** |
| [Generative Verifiers: Reward Modeling as Next-Token Prediction](https://arxiv.org/abs/2408.15240) (Zhang et al., ICLR 2025) | GenRM beats discriminative/DPO verifiers and LLM-as-judge; large Best-of-N gains; scales with test-time compute | **Most direct challenge to the typed-judge thesis:** verification is currently moving *toward* generation, not away from it. The paper must cite this and frame typed judges as a different cost/robustness point on the same axis, not as a refutation |
| [Chain-of-Verification](https://arxiv.org/abs/2309.11495) (Dhuliawala et al., 2023) | Draft → plan verification questions → answer independently → revise; fewer hallucinations | The LLM's own "typed verification" loop: this *is* the structured self-check arm's ancestor |
| [CRITIC](https://arxiv.org/abs/2305.11738) (Gou et al., ICLR 2024) | Tool-interactive critiquing and revision improves QA, program synthesis, toxicity | The "external verifier changes generator behaviour" mechanism the paper's (B)→(A) transmission claim needs — cite it there |

## C.7 What is honestly new here (and what is not)

**Not new (say so in the paper):**

1. Cascade/escalation with a cheap first judge — FrugalGPT, RouteLLM, AutoMix, cascaded human-AI decision-making, Calibrate-Then-Delegate, Bayesian self-escalation.
2. Deferral/abstention as a learned policy — rejection learning, learning-to-defer.
3. LLM-as-judge bias and mitigation — Zheng et al. onward.
4. Verifiers/PRMs improving agents — Let's Verify Step by Step, GenRM, CRITIC, CoV.
5. Non-autoregressive and discriminative decision models — NAR MT, EBMs, Ng & Jordan.
6. Long-horizon degradation and context limits — Context Rot, Lost in the Middle, NoLiMA, agents-rot, Horizon Gap.
7. A "decision model" as a *category name* — industry vocabulary, not an established academic term.

**Thin or absent prior art (the defensible new space):**

1. **A real, local, non-autoregressive decision model used as the judgment layer of a long-horizon agent**, characterized against an LLM judgment layer with the *same executor*, a pre-registered prompt ladder, and matched spend. Prior cascades judge with LLMs or with task-specific trained probes; the joint "local + non-generative + typed question + long-horizon loop" configuration is not the subject of the works above.
2. **The truncation/horizon interaction as a measured curve.** Laya silently truncates oversized states from the end (R1 §4.5), and long-horizon states grow monotonically. "Judge budget overflow rate vs horizon" appears to be unmeasured in the literature above — and it is a negative result about the tool, which is exactly the kind of finding that survives review.
3. **Device-qualified, first-party latency and per-decision cost for local judges** (R2 §B documents contradictory second-hand latency figures: 34 ms vs 139 ms vs 32.8 ms, no device noted). Publishing reproducible, device-qualified numbers is a real, if modest, contribution.
4. **Error-detection lead time as a process metric** for judgment layers (R1 §5, "本文最有价值的过程指标"), i.e. how many steps *before* failure does a judge flag the problem — a reliability-budgeting quantity that the horizon literature says is needed (Horizon Gap) but that the cascade literature does not report per judge.
5. **Cross-species calibration comparison done properly**: four LLM probability readouts vs two typed judges' native probabilities, on identical items, with the same temperature-scaling repair budget, and *without* pretending the `confidence` fields are commensurable.

**One-line positioning (recommended abstract sentence).** *"We do not propose a new cascade; we replace the judge inside one — with a local, non-generative, typed-question decision model — and measure what that substitution costs and buys over a long-horizon task, at matched spend."*

---

# PART D — RECOMMENDED CLAIMS

## D.1 SAFE (defensible from this design, provided R11–R15 execute)

| # | Claim | Why it is safe |
|---|---|---|
| S1 | A dated, first-party, device-qualified characterization of per-decision cost, latency, calibration and truncation behaviour for three judgment layers (LLM / remote typed / local typed) on an identical discriminative battery, with all usage fields logged | It is a measurement; it is true whatever the numbers turn out to be. Requires R12/R13 to actually run |
| S2 | On this battery, the LLM judge's stated-probability, logit, sample-consistency and temperature-scaled readouts differ measurably in calibration, and we report all four | Pure description; the split literature (§C.2) makes any outcome interesting |
| S3 | The local judge's truncation rate (and the rate at which its answer fails to flag truncation) grows with state length/horizon | Design-level consequence of a documented mechanism; a *negative* result about the tool, which reviewers reward |
| S4 | Per-decision cost is not a single number: it depends on reasoning effort, cache hit rate, batch/cadence and human review, and we publish the sensitivity grid and break-even prices | Methodological claim, fully under the authors' control; R2 §A.1 already establishes the levers |
| S5 | The equal-spend frontier is reported for every arm at its best pre-registered configuration, with clustered CIs, in both directions (fixed spend; fixed decision count) | Reporting commitment, not an outcome claim |

## D.2 CONDITIONAL (true only under the stated conditions)

| # | Claim | Conditions |
|---|---|---|
| C1 | Typed judges improve final long-horizon task quality at matched total spend | Holds only if (a) it survives all four prompt variants at their best, (b) the cost model includes cache hits and human review, (c) clustered CIs exclude zero, (d) the battery is discriminative-heavy. Otherwise report the negative result |
| C2 | Typed judges make **more** decisions affordable at fixed spend, enabling a denser judgment cadence | Requires R12/R13 measurements and the cache-hit sensitivity; the local judge's per-question state re-encoding (§B.2) can erase it |
| C3 | Abstention is available to all arms and improves cost-adjusted quality | Requires the symmetric, budget-charged retry policy; and the abstention mechanism differs by judge, so compare risk–coverage curves, not labels |
| C4 | The typed judge delivers equal quality at lower latency | Only with device-qualified, post-warm-up timings, and only if the local path is not serialised by per-question re-encoding; wall-clock, not dollars |
| C5 | The judgment layer causally affects the executor's trajectory (the (B)→(A) transmission) | Only if the judge-on/off ablation holds the executor fixed (same prompt, same seeds). Otherwise it is association |
| C6 | One readout class beats another *for this model on this battery* (e.g. logit > verbalized) | Conditional by construction: one model family, one battery, stated language set |

## D.3 NEEDS MORE WORK (beyond this design's reach)

| # | Claim | What would be needed |
|---|---|---|
| N1 | Generalization across judge implementations (Jev vs Laya vs `von`-style third-party judges; multiple checkpoints) | A backend-agnostic replication study. R2 §D already recommends backend-agnostic protocol design — do that, but do not claim generality from one instance each |
| N2 | Any optimal-escalation or optimal-deferral-policy claim | A learned/regret-bounded policy ([CTD](https://arxiv.org/abs/2604.14251), [Bayesian self-escalation](https://arxiv.org/abs/2608.24087)); heuristic thresholds cannot support optimality |
| N3 | A mechanistic explanation of long-horizon degradation | Targeted experiments, per [Benchmarking the Residual](https://arxiv.org/abs/2607.27283); a residual only shows *that* full rollouts differ from the short-stage baseline |
| N4 | Transfer to open-ended/generative tasks, or to arbitrary languages | Laya's state window and language routing limit this (R2 §B) — a separate portability study |
| N5 | Cost claims about production-scale deployment (concurrency, rate limits, peak pricing) | Load testing at concurrency; note the verified 2500 concurrency limit but do not extrapolate cost from it |

## D.4 Claims the team should NOT make

1. **"Jev/Laya outperform DeepSeek-V41-Flash."** They are different species and cannot perform the same task (R1 §1); the LLM is the executor in every arm.
2. **"We introduce a decision model / a new paradigm / the first non-generative judge."** See §C.4 and §C.7 — the framing is Ng & Jordan's, and the term is industry vocabulary.
3. **"Typed judges are better calibrated than LLMs" as a general law.** n = 1 per family; Laya's multilingual checkpoint ships at temperature 1.0 and emits 100%/0% (R2 §B); calibration is corpus- and language-dependent. Claim only the measured curves.
4. **"We propose a cascade / escalation architecture."** Prior art in §C.3.
5. **"LLM judges are biased, therefore typed judges are better."** Bias is documented; inferiority does not follow, and the LLM arm is entitled to the same mitigations.
6. **Any dollar number not traceable to a logged usage record plus a dated price page**; any latency number without a device qualifier.
7. **"Cheaper per task"** without naming the budget basis (dollars? wall-clock? human minutes?) and the cache-hit assumption.
8. **Any horizon claim without the matched short-stage baseline** required by [Benchmarking the Residual](https://arxiv.org/abs/2607.27283) — a full-task success rate alone is not evidence about horizon.
9. **Novelty claims resting on the LLM-as-judge bias literature** — the survey ([arXiv:2411.15594](https://arxiv.org/abs/2411.15594)) already occupies that ground.

## D.5 The single most likely reviewer objection, and its control

> **Objection #1 (most likely): "Your LLM baseline is a straw man. A better-prompted LLM judge, given the same budget, would match or beat your typed judges — and your result is a prompt artifact."**

**Defusing control (all four are required; any one alone is insufficient):**

1. **Pre-registered prompt band P1–P4** (§A.2.3), with the **best** variant as the headline, and the typed side given an analogous structural band.
2. **The structured self-check arm** (R1 §7): the LLM answers the *identical typed question*, so format is no longer a confound.
3. **Equal-spend, both directions** (§B.7), with the k-sample self-consistency arm charged in full — the reviewer's own remedy ("try 3 samples") is already inside the LLM arm's budget.
4. **A pre-registered negative-result commitment**: if the best-prompted LLM arm dominates the frontier at equal spend, the paper reports that as the finding, with the same prominence. This converts the objection from a threat into the paper's credibility.

> **Objection #2 (runner-up): "Full-task success cannot support a long-horizon claim without a matched short-stage baseline."** Control: compute the **horizon residual** ([arXiv:2607.27283](https://arxiv.org/abs/2607.27283)) — log-ratio of actual full-task success to the prediction built from short individual stages under the same agent configuration — and pre-register how stages, checkpoints, information and budgets are chosen.

> **Objection #3: "Your hundreds of decisions per run are not independent."** Control: R1 §4.3 — cluster by run, hierarchical model or cluster-robust SEs, reported for every headline number.

> **Objection #4: "Your ground truth is defined by one of your judges."** Control: R1 §4.2 — external execution results, dataset truth, or independent annotation with an inter-annotator coefficient.

---

## Appendix — citation status ledger

**Fetched successfully by R16 on 2026-09-22 (safe to cite):** arXiv abs/API pages for 2306.05685, 2305.17926, 2410.02736, 2410.21819, 2411.15594, 2603.29403, 2305.14975, 2306.13063, 2205.14334, 2207.05221, 2302.09664, 1706.04599, 2311.14648, 1705.08500, 1711.06664, 2006.01862, 2407.18418, 2506.09038, 2305.05176, 2406.18665, 2310.12963, 2506.11887, 2604.14251, 2608.24087, 2207.07061, 2211.17192, 2302.01318, 1711.02281, 1904.09324, 2004.11714, 2507.02092, 1710.08005, 2106.01345, 2307.03172, 2404.06654, 2502.05167, 2506.11440, 2410.10813, 2409.12640, 2503.14499, 2310.06770, 2404.07972, 2406.12045, 2411.15114, 2412.14161, 2311.12983, 2605.30434, 2608.06663, 2607.27283, 2609.01660, 2305.20050, 2408.15240, 2309.11495, 2305.11738, 2203.11171, 2209.11055; plus [papers.nips.cc Ng & Jordan 2001](https://papers.nips.cc/paper/2001/hash/7b7a53e239400a13bd6be6c91c4f6c4e-Abstract.html), [Chroma Context Rot](https://www.trychroma.com/research/context-rot), [DeepSeek Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/).

**URL resolves but content not retrieved:** [Spring AI — TypeSafe Jev](https://spring.io/blog/2026/09/21/spring-ai-typesafe-structured-judgment/) (HTTP 200, body truncated); [github.com/wfzyx/von](https://github.com/wfzyx/von) (page title only: *"The open-source System One decision model. Sub-15ms, non-autoregressive, local drop-in alternative to TypeSafe Jev"*; README fetch failed); [github.com/PerryLink/dsh-laya](https://github.com/PerryLink/dsh-laya) (title only: *"Laya decision engine as a first-class Cordis service and model-visible tools for DeepSeek Harness"*).

**NOT VERIFIED (do not cite without checking):** Jev pricing, latency, state cap, calibration state (R2 §C — R12 task); Laya's measured params/limits/latency (R2 §B — R13 task); [docs.aimlapi.com Jev reference](https://docs.aimlapi.com/api-references/decision-models/typesafe/jev) (search-result only, never fetched); `huggingface.co/convaiinnovations/laya` model card (R2 reports fetch failure; local copy at `D:\Projects\laya-research\hf_modelcard.md` is second-hand); the exact billing treatment of reasoning tokens (reconcile an invoice).

**Corrections to common mis-citations (do not repeat them):** arXiv:1805.09458 is *Invariant Representations without Adversarial Training*, **not** a learning-to-defer paper (the deferral papers are 1711.06664 and 2006.01862). arXiv:2306.13887 is a recommender-systems paper, **not** an LLM-calibration paper. arXiv:2503.14499's current title is *Measuring AI Ability to Complete Long Software Tasks*.

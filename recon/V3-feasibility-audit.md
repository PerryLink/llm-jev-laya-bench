# V3 — Feasibility Audit of R5

> **Unit:** V3 (adversarial verification — can this actually be measured?)
> **Audits:** `recon/R5-synthesis.md` (the merged design)
> **Evidence base:** R11 (testbed), R13 (Laya probe), R3 (corrected economics), R4 (blockers), R2 (verified externals), R15 (arms/budget)
> **New first-hand measurements made by this unit** are marked **V3-MEASURED**; every one is reproducible with the decoder described in §A.
> **Stance:** I set out to find where the design promises a number nobody can produce. Where I expected to break a claim and could not, I say so — that is also a result.

---

## 0. Summary of verdicts

| # | Question | Verdict |
|---|---|---|
| 1 | Per-judge latency comparisons | **feasible-with-fix** — one promised comparison is impossible, one is not constructible, one is mis-specified |
| 2 | Cost reconstruction | **feasible-with-fix** — reproducible only for the LLM arm; Laya/Jev lines are modelled, not measured |
| 3 | Calibration as a headline | **feasible-with-fix** — three plan defects that would each produce a publishable wrong number |
| 4 | Silent-truncation curve | **feasible-with-fix** — the design's own gate destroys the phenomenon it wants to measure |
| 5 | Wall-clock feasibility | **feasible-with-fix** — machine time ~2 days, elapsed 5–9 weeks; not "one long session" |
| 6 | Silent-wrong-number register | see §7 |

**Headline result of this audit.** Two of the design's own numbers are arithmetically self-contradictory (R15's `$3,802` gold-evaluation line and its `115 h ÷ 8 = 1.4 days` line, both inherited by R5 §7). Two more are anchored to measurements that cannot apply to the design's own measurement plane (Laya's `3.2 ms/question` batch-20 amortisation, and Jev's third-party `p50 126.81 ms`). The most dangerous single risk is **not** any of these: it is that R5's hard 450-token state cap and its truncation-survival curve are **mutually exclusive**, so a compliant run produces a truncation rate of exactly zero and a beautiful, meaningless flat curve (§4, §7 row 7).

---

## A. Method and the anchors I measured myself

R11 established that `.jsonl.zstd` transcripts record per-step `usage{inputTokens, outputTokens, cacheReadTokens, cacheWriteTokens, totalTokens}`, ms timestamps, model id, and tool args/results verbatim. I decoded **12 sessions (185 usable steps)**, walking the concatenated zstd frames by magic-scan + per-frame `zstdDecompressSync`, and paired `step/start` → `assistant/message` to get model time exclusive of tool execution.

**V3-MEASURED anchors** (deepseek-flash, `reasoningEffort: max`, this host):

| Quantity | Value | n |
|---|---|---|
| Decode throughput (pooled) | **213.9 output tok/s** | 185 steps |
| Per-step model time | p50 **3,087 ms**, p90 **28,472 ms**, mean 9,616 ms | 63 steps |
| Output tokens per step | mean **2,057**, p50 464, p90 6,000 | 185 steps |
| Cache-hit share of prompt | **95.4 %** (13,896,320 cacheRead vs 674,821 fresh) | 185 steps |
| `cacheWriteTokens` | **0 in 185/185 records** | 185 steps |
| Usage key union | exactly the five keys R11 reported — **no separate reasoning-token counter** | 188 records |
| Message blocks | `tool-call` 375, **`reasoning` 188**, `text` 113 | 188 messages |
| Measured cost | **$0.002007/step** off-peak vs R15's assumed $0.000585 | 185 steps |

Two of these settle open questions in the corpus:

1. **`outputTokens` includes reasoning tokens.** A `reasoning` block is present on 188/188 assistant messages, there is no second output counter anywhere, and individual steps show 6,000–15,742 output tokens whose serialized reasoning content accounts for essentially all of it while visible text is tiny. So the provider's billed completion count is already the reasoning-inclusive number. **Consequence:** any cost model that sizes output from *visible text* (as R15 does with "900 out/step", "120 out/judgment") is not merely imprecise, it is measuring the wrong quantity. R15's 900 must be compared against a measured mean of **2,057**.
2. **`cacheWriteTokens` is present and always zero on this route.** A zero cannot be distinguished from *billed-but-unrecorded*. This is the exact shape of a silent wrong number: a cost column that omits a price class because the harness never populates it.

**Caveat I must state against my own numbers.** These 185 steps are DSH *agentic coding* sessions (mean prompt 78,763 tokens, 2.01 tool calls/step, large tool results). They are a sound anchor for the **route's decode rate** and for **output tokens per thinking-mode step**, which are properties of the model and the effort setting. They are **not** a sound anchor for the benchmark's prompt sizes. I therefore use 213.9 tok/s and 2,057 out/step as measured, and treat prompt size as an explicit scenario variable (§5).

---

## 1. Latency — what is obtainable and what is not

### 1.1 The three judge arms are measured by three different clocks

The design (R5 §4.4 rule 14, §6 ③; R3 §6 table) promises a wall-clock latency comparison across judges. There are four arms and they do not share a measurement domain:

| Arm | What "latency" even is | Obtainable? | Mechanism |
|---|---|---|---|
| **A0** LLM prose-in-generation | **No separate call exists.** The verdict is emitted inside the generation step | **No — and it is 0 by construction** | Only `tool/call` *count* attributable to judging, which is 0 |
| **A1** LLM structured judge | One extra model turn at horizon `t` | **Partly** — not as a self-report (none exists); yes as a step delta | `assistant/message.data.<time> − step/start.time`, serial only |
| **A2** Jev | Remote network + queue + inference | **No today** (mock: `latencyMs 0`). Under live: only as a separate domain | vendor `latencyMs` (self-report) + harness wall-clock |
| **A3** Laya | Local forward pass over a ≤512-token window | **Yes — two independent mechanisms** | self-reported `latency_ms`, and client wall-clock on a single-issue call |

**The A1 mechanism is real and I measured it.** `assistant/message.time − step/start.time` is the model's own turn duration: p50 3,087 ms, p90 28,472 ms. That is a defensible per-decision latency for the structured LLM judge, and it is **~83× Laya's warm median**, not R15's assumed "≈2.5 s" (and not a number with a bounded tail: p90 is 9.2× p50, driven by uncontrolled reasoning length).

### 1.2 Three promised comparisons that are impossible

1. **Laya vs A0 latency.** A0 has no round trip. A table listing "A0: 0 ms" beside "A3: 37 ms" compares a by-construction zero against a measurement and A0 wins every latency frontier trivially. The honest form of the design's own claim ("zero extra round-trips", R5 §5.3) is an **integer count of sequential round-trips per checkpoint**, which is exactly recoverable from `tool/call` records and needs no clock.
2. **Laya vs A5b as a "matched round-trip" frontier.** A5b is "≤8 checkpoints per call" (R5 §5.3). Batching 8 *checkpoints* requires 8 *states* in one request. `laya_ask` / `laya_noul` / `laya_plan` each take **one** `state` plus a **map of questions**; `laya_rank` takes one query plus candidates. R13's entire throughput table (§8.2: batch 1/5/10/20) was built by adding *questions against the same state*. **There is no Laya entry point that batches across states.** Therefore:
   - A5b is implementable for the LLM only. The matched frontier has no Laya side.
   - R5 §3 (conflict 1) calls A5b "绝不可删" (never to be deleted) because it prevents the LLM arm being strawmanned on latency. It cannot serve that purpose against Laya. **The claim must be restated as round-trip counts, or A5b must be paired against only the LLM arms.**
   - Corollary, and it is the design's most-cited number: **R5 §7's "Laya 每问仅 3.2 ms，极廉价" is not achievable on the design's own measurement plane.** 3.2 ms is the batch-20 amortisation. The plane has one question per distinct state, so **batch = 1 is forced**, and the correct figure is R13's own batch-1 row: **37.4 ms median wall / 30.0 ms self-reported**. R5 §7 is **12× optimistic** about the cost of the one thing it says is trivially cheap.
3. **Laya vs Jev, the "36× faster" framing.** R13 measured `api.typesafe.ai` returning an unauthenticated **403 refusal** in 1,011–2,349 ms (median 1,361 ms) from this host. R3 §6 then places Jev `p50 126.81 ms` in the same table as Laya's `34 ms` — but 126.81 ms is a **third-party colocated** figure (R2 §C.3, LiteLLM, Haiku as the comparator), and it lies *below this host's measured transport floor for a rejection that contains zero inference*. The two numbers are not the same instrument. Publishing them side by side as "Laya 3.7× faster than Jev" would be wrong in a way no reader could detect.

### 1.3 What IS obtainable, and the fair-comparison conditions

Obtainable, in decreasing order of confidence:

| # | Metric | Source | Status |
|---|---|---|---|
| L1 | Sequential round-trips per checkpoint, per arm | count `tool/call` records between `step/start` and `step/end` | **exact, free, all arms** |
| L2 | Batch wall-clock per step | `tool/result.time − step/start.time` | measured (batch max, not per call) |
| L3 | Laya per-call latency distribution at batch 1 | `latency_ms` (self-report) **and** client wall | measured, n=30 in R13 |
| L4 | LLM judge turn duration at horizon t | `assistant/message.time − step/start.time` | measured here, n=63 |
| L5 | Laya batch amortisation (k questions / one state) | R13 §8.2 | measured, **not applicable to the replay** |
| L6 | Jev decision latency | — | **blocked** (mock). Under live: network+queue+vendor, ≥ transport floor |
| L7 | Per-call latency from a parallel batch | — | **impossible**: 5 calls shared a result stamp within 3 ms (R11 §4.1) |

**Conditions under which Laya-vs-A1 is a fair comparison** (all six must hold and be reported):
1. **Batch size 1 on both sides.** The replay forces it for Laya; the LLM must also be one judgment per turn. Any batched series is reported as a *separate* series and never mixed into the frontier.
2. **Warm state on both sides, asymmetrically defined and declared.** Laya: discard ≥3 calls after every sidecar start (`/health.calls < 3`) because cold start is 389.9 ms (R13) to 4,935.9 ms (R11) versus 37 ms warm. LLM: a *cold prefix cache* is the same hazard in a different guise — the first call of a run prefills at cache-miss price and slower TTFT. Record `cacheReadTokens / (cacheReadTokens + inputTokens)` **on every timed call** and exclude the first call of each run from medians.
3. **Same clock semantics.** Either both client-side wall-clock including transport, or both vendor self-report. R13 shows Laya's wall exceeds its self-report by ~12.8 ms of loopback HTTP + JSON, while the LLM's turn delta includes a WAN round trip. Mixing them is a category error.
4. **Device pinned and *asserted*, not assumed.** `device: cuda`; the answer payload does not report device, only `/health.degraded` does, and a CPU fallback is 10–15× slower. A fallback mid-run would be read as a *horizon* effect. Assert `device == "cuda"` on `/health` snapshots bracketing every run and abort on mismatch.
5. **Concurrency forced to 1 for the latency block**, and the forcing declared as a protocol deviation. `maxParallelToolCalls = 20` is the normal case (R11 §4.1), so serial latency measurement changes the arm being measured.
6. **Latency reported as a function of horizon `t`, not as one median.** The LLM's per-call cost includes prefill of the whole run state, which grows with `t`; Laya's is capped at 512 tokens by construction. A single pooled median would average away the design's own thesis.

**VERDICT: feasible-with-fix.** Minimal fix: replace the promised per-judge *millisecond* comparison with **(a)** an exact sequential-round-trip count per checkpoint (all arms, free, no clock), plus **(b)** a per-arm wall-clock series *labelled by clock domain* (local forward pass / harness-timed model turn / remote round-trip), reported **against horizon** with batch size, warm-up rule, device, concurrency and cache-hit rate declared per point. Delete the A5b-matched frontier for Laya (it cannot exist) and delete any Jev latency number that is not first-party and authenticated from the experiment host; until a credential exists, report the transport floor **as a floor on a rejection**, never as "Jev latency".

---

## 2. Cost — exact reconstruction, every input, and its status

### 2.1 The accounting identity

There is no monetary field anywhere in a session transcript (R11 §2.5: zero cost fields in 147 records; `token-meter` prices *tokens*, not currency). Every dollar figure in the design is therefore a **reconstruction**, and must be written as one:

```
cost(arm j) = Σ_calls [ miss_j × P_in_miss(period)
                      + hit_j  × P_in_hit(period)
                      + cw_j   × P_cache_write(period)      ← P unknown, cw measured 0
                      + out_j  × P_out(period) ]            ← out includes reasoning
              + Laya_local_amortisation(convention)           ← no price exists
              + evaluator_arm(units, oracle_coverage, grader_route, k_per_cell)
```

### 2.2 Every input, with its status

| Input | Needed for | Status |
|---|---|---|
| `inputTokens, outputTokens, cacheReadTokens, cacheWriteTokens` per step | all LLM arms | **AVAILABLE** — transcript, verbatim (R11; re-verified here over 188 records) |
| `P_in_miss` off-peak $0.15/M, peak $0.30/M | LLM arms | **AVAILABLE, first-party** (R2 §A) |
| `P_in_hit` off-peak $0.003/M, peak $0.006/M | LLM arms | **AVAILABLE, first-party** (R2 §A) |
| `P_out` off-peak $0.60/M, peak $1.20/M | LLM + evaluator | **AVAILABLE, first-party** (R2 §A) |
| Peak windows: UTC Mon–Fri 01:00–04:00 & 06:00–10:00, excl. CN statutory holidays | period allocation | **AVAILABLE** (R2 §A) — but see row 16 of §7 |
| `P_cache_write` | cache-write line | **UNKNOWN — in no recon file.** Measured `cacheWriteTokens = 0` in 185/185 steps, so the line is either genuinely zero or invisible |
| Whether `outputTokens` includes reasoning | the dominant cost line | **RESOLVED HERE: yes** (§A). No separate multiplier needed *if* priced verbatim |
| `reasoningEffort` per run | output volume | **PARTIAL** — recorded once per session in `request/header` (R11 §2.5), not per step. R2 §A.1 calls effort "the main independent variable on the cost axis". R5 never sweeps it |
| Tokens per generation step | generation arm | **ASSUMED** by R15: 1800 in + 900 out. Measured here: **2,057 out** |
| Tokens per structured LLM judgment | A1/A4/A5 arms | **ASSUMED**: 1500 in + 120 out. No measurement exists; at effort=max the JSON label is a small fraction of the turn |
| Tokens per grading unit | evaluator arm | **ASSUMED**: 1600 in + 250 out |
| Cache-hit rate | all LLM lines | **ASSUMED 85 %** by R15; **MEASURED 95.4 %** here (route property) |
| State token count per call | horizon-dependent cost | **COMPUTABLE** from the frozen serializer + the checkpoint tokenizer — but R3/R5 cost tables use a flat 1500 tokens, which contradicts the paper's own thesis (§2.4) |
| Jev `P_in` $0.042/M | Jev arm | **AVAILABLE, first-party integration doc** (R2 §C.1) |
| Jev `P_out` = $0 | Jev arm | **UNVERIFIED** — flagged in R2 §C.5 and R5 §8.7; Jev responses contain output tokens |
| Jev billable input scope (state only, or state + head + options) | Jev arm | **UNKNOWN** — the design's 1500-token assumption ignores the ~113-token head and option text |
| Laya marginal price | Laya arm | **DOES NOT EXIST.** "Marginal $0" is an accounting convention. A dollar figure requires GPU capex/rental, power tariff, amortisation horizon, utilisation, and whether the host is otherwise idle. None are recorded |
| Evaluator model id / route / effort | evaluator arm | **UNKNOWN** — R15 says "grader-LM" and "5 judges" inconsistently; R5 never names it |
| Oracle-coverage fraction | scales the evaluator by up to 3.3× | **UNKNOWN** — R15 targets "≥70 %" as a *lever*, not a plan |
| Grader calls per cell (1 vs k-vote) | evaluator arm | **UNKNOWN** |
| `tol = 0.05` | evaluator arm | available as a design constant (R15 §5.6) |

### 2.3 Measured-anchored bottom-up cost (full battery, 576 runs × 120 steps = 69,120 steps)

Prices: R2 §A off-peak. Units priced verbatim from `usage`. Scenarios: **S-A** = the design's own assumptions; **S-M** = measured output (2,057/step) with the design's prompt; **S-C** = measured output **and** a horizon-realistic mean prompt of 52,000 tokens (a two-parameter model: prompt grows linearly 4,000 → 100,000 over 120 steps) at 90 % hit. Peak = 2×.

| Line | Units | S-A (design) | S-M (measured out) | S-C (measured out + horizon prompt) |
|---|---|---|---|---|
| Generation, 69,120 steps | 69,120 | $40.4 | $88.4 | **$148.9** |
| A1 structured LLM replay, 1 pass | 69,120 | $7.6 | $19.2 | **$68.6** |
| A5c self-consistency k=8 (LLM only) | 92,160 | $10.1 | — | **$91.5** |
| Jev replay, 1 pass | 69,120 | $4.4 | $4.4 | **$150.9** |
| Laya replay, 1 pass | 69,120 | $0 (modelled) | $0 | **$0** (convention) |
| Evaluator, 0 % oracle | 69,120 | $13.1 | $49.7 | **$94.7** |
| Evaluator at 70 % oracle | 20,736 | $3.9 | $14.9 | **$28.4** |
| **Battery subtotal (off-peak, 70 % oracle)** | | **$66.5** | **$127** | **$488** |
| **Same at peak (×2)** | | **$133** | **$254** | **$976** |
| Calibration corpus P5 (19,200 steps) | 19,200 | $18 | $35 | **$136** |
| Pilot P7 (8,640 steps) | 8,640 | $8 | $16 | **$61** |
| **Programme total, off-peak** | | **$93** | **$178** | **$685** |

**Conclusion that survives adversarial re-derivation:** even with measured output tokens, a horizon-realistic prompt model, peak pricing on the whole programme, a live Jev arm and zero oracle coverage, the API cost is **under $2,000**. R3's central claim — *money is not the constraint* — is correct with roughly a **20× margin**, and it is correct for a stronger reason than R3 gave: the dominant term is output tokens, and output is only 2.3× off the assumption. This is a robustness result the paper should state explicitly, because it is the one place where an aggressive audit *strengthened* the design.

### 2.4 The design's own cost table contradicts the design's own thesis

R3 §5 derives the paper's central economic story: the Jev-vs-LLM cost crossover lies at **2,100–7,100 input tokens, "and the state size grows with horizon, so the cost advantage disappears"**. R5 §6 then adopts this as a headline ("判定美元 vs 错误发现提前量"). But **every cost line in R3 §2–3 and R15 §6.1 is computed at a flat 1,500-token state.** At a horizon-realistic mean state of 52,000 tokens the Jev column is **$150.9** against the LLM judge's **$68.6** — Jev is **2.2× more expensive**, the opposite sign to R3's per-call table. The paper's most quotable economic claim is therefore *not evaluated anywhere in its own budget*; the budget silently prices the one regime (short state) in which the claim is true. This is a silent wrong number of exactly the dangerous kind: a cost table that looks complete, is arithmetically correct, and answers a different question than the paper asks.

### 2.5 Third-party reproducibility: no, as specified

A third party **can** recompute the generation arm's dollars from the packaged transcripts, *if* the delivery includes: (a) the price table **and** the peak/off-peak rule with each call's UTC timestamp; (b) a declaration that `outputTokens` is priced verbatim and includes reasoning; (c) a declaration for `cacheWriteTokens` (consistently zero, with a provider statement or an invoice reconciliation for ≥20 calls); (d) the run's `reasoningEffort`; (e) the frozen serializer + checkpoint tokenizer, so state sizes are reproducible.

A third party **cannot** reproduce: the Laya line (no price, no recorded machine parameters — the figure is a model output, and R15's "$0.008/run cloud-equivalent ledger" has no published derivation); the Jev line (no credential, `costUsd` only exists under live, and the output-price claim is unverified); the evaluator line (grader route, effort, oracle coverage and calls-per-cell are all unstated); or any peak/off-peak allocation, because the transcript records wall-clock but no experiment-level declaration of which period each call was billed in.

**VERDICT: feasible-with-fix.** Minimal fix: (1) publish the cost model **as the identity in §2.1**, per-call priced from that call's own `usage` and its own UTC timestamp binned against the published peak windows — never a run-level average; (2) declare `cacheWriteTokens` policy explicitly, with an invoice reconciliation for a sample; (3) **price every cost row at that run's measured state token count and report cost as a function of horizon** — this is the only form in which the design's own crossover claim is true or false; (4) name the evaluator route, effort, oracle coverage and calls-per-cell; (5) report Laya's line as an **amortisation convention with its parameters printed**, clearly separated from measured cost; (6) since R2 §A.1 identifies effort as the dominant cost variable, add a small effort sweep (off / low / max) on ≥100 judge calls — it costs cents and it is the difference between a cost claim and a cost guess.

---

## 3. Calibration

### 3.1 What a defensible calibration measurement requires

R5 makes calibration a headline (R5 §3 conflict 2: N ≥ 1000 "because ECE is one of the paper's core deployment conclusions"; §5.3 A3; §6). Given Laya's measured properties, a defensible measurement needs **eleven** things:

1. **A frozen item set with externally derived binary truth**, not labels from any arm's output (R5 §5.1 F2 achieves this via a coverage function over machine-readable annotations — good).
2. **A pre-registered indeterminacy rule and adjudication.** R13 excluded 2 of 12 items (17 %) as indeterminate. At N = 1000 that is ~170 items needing adjudication by ≥2 annotators with reported agreement; the indeterminate fraction must be reported, not silently dropped.
3. **N ≥ 500 for a curve (10 bins × ≥50), ≥ 1000 to compare two judges' ECE** (R13 §4.2). Planned ✓.
4. **The binned quantity must be the judge's own probability, never `confidence`.** R13 §5.3a: the same `p ≈ 0.54` yields `confidence` **0.5399** (bare `noul`, scale `max(p,1−p)`) or **0.0046** (noul-with-criteria, scale `1−H/log k`) — a **117×** discrepancy for identical evidence and identical question. R5 §4.3 rule 10 forbids `confidence` for gating, and that is nearly sufficient — but the prohibition must extend to *reporting*.
5. **One framing per row, and framings never pooled.** The design's own question bank carries `noul` both bare and as a two-option choice with `criteria` (R5 §5.1 F2; R13 §2.1 does exactly this). Pooling them mixes the two confidence scales *and* two different option counts (`choice:2` carries temperature 1.906 in the shipped checkpoint).
6. **Brier decomposition — reliability, resolution, uncertainty — plus the base rate, sharpness, and AUC.** ECE alone is not merely incomplete, it is **actively misleading**: on a battery with positive rate π, a judge that returns the constant π every time has **ECE ≈ 0** and **zero resolution**. It will top a pure-ECE leaderboard while carrying no information. This is the single most likely way the design publishes a wrong calibration result that looks excellent.
7. **Per-checkpoint reporting, never pooled.** The sibling checkpoints differ in ways that change the meaning of `p`: `english` ships 6 fitted temperature buckets; **`multilingual` ships `temperature [1.0,1.0,1.0]`, `temperature_by_options {}`, `fitted_temperature_buckets: 0` — i.e. entirely uncalibrated, raw softmax**; and english deliberately applies `choice:11+ = 0.1006`, which sharpens logits ~10× and produced the probe's most confident wrong answer (p 0.9993, confidence 0.9981). Any pooled "Laya ECE" averages a calibrated model, an uncalibrated model, and a deliberately miscalibrated high-cardinality regime.
8. **Clustering at the task-family level.** Items nested in a family share the decisive document; R15 §5.5 clusters for `T90` but says nothing about calibration. R2 §C.4 (the LiteLLM template the design adopts) requires exactly this.
9. **A paired comparison on identical items with a cluster bootstrap** (10,000 resamples by task family), reporting the ECE *difference* with a CI, not two point estimates.
10. **Order-sensitivity propagation.** Criteria permutation moved `p` by up to **0.052** and `confidence` by **0.111** (R13 §6.2). A 0.052 shift moves items across bin edges. Recompute ECE under ≥2 frozen permutations and report ΔECE; a single frozen order does not make the number order-free, it merely makes the sensitivity invisible.
11. **A negative control.** Run a constant-at-base-rate judge and a random judge through the identical pipeline. The constant judge must produce ECE ≈ 0 and resolution ≈ 0; if the pipeline reports it as "well calibrated", the pipeline is measuring nothing.

### 3.2 Where the plan does not meet it — and where a number would be produced but untrustworthy

| Defect | Mechanism | Why it is dangerous |
|---|---|---|
| **No held-out split between τ\* fitting and the reported ECE** | R5 §7 P5: the calibration corpus (4 families × 40 runs) is run *first* "to fit the escalation threshold τ\*". If the headline ECE is computed on that same corpus, τ\* was fitted on the reported data | The reported calibration is the deployed system's *training* calibration. R15 §6.4 shows awareness of leakage for τ\* but the design never excludes the corpus from the reported number |
| **No resolution floor / no Brier decomposition** | Specified nowhere in R5 or R15 | A constant-predictor judge passes an ECE-only criterion. This is the classic silent-pass |
| **Calibration corpus spans 4 task families** | If ECE borrows this corpus, a task-family cluster bootstrap has **4 clusters**. With a design effect of 2.2 (R15 §5.5's own ICC estimate), 1,000 items behave like ~450 | The X-of-2-judges ECE comparison cannot reach significance for any effect small enough to be plausible |
| **Determinism misread as sampling adequacy** | Laya is bit-identical on repeat (R13 §6.1), so repeats contribute **zero** information; all variance is in the item draw | Any CI built from repeats is degenerate (width 0) and would be reported as "extremely precise". R5 §4.3 rule 13 gets the *rule* right ("repeats only for near-ties") but the calibration plan does not state that the ECE CI must come from item/cluster resampling |
| **`band` never calibrated** | R5 §4.3 rule 10 makes `band` the *only* sanctioned uncertainty channel and A4's escalation depends on it. R13 shows `uncertain` at p = 0.5001 (one item) | The design leans on a signal whose calibration it never measures. It is cheap: it is a one-dimensional reliability check on the same items |
| **The R13 12-item table** | accuracy 0.80, Wilson [0.49, 0.94] | R13 already forbids its use as a calibration result. R5 must enforce it: no figure in the paper may be sourced from the probe table |

**VERDICT: feasible-with-fix.** Minimal fix: split the calibration corpus by run into a **τ\*-fitting half** and a **reported-ECE half** (or fit τ\* on the pilot and report ECE on the full battery); add Brier decomposition with a pre-registered minimum resolution *and* a constant-predictor negative control; draw calibration items across **all** task families rather than four; define the calibration CI as a task-family cluster bootstrap; report every calibration row per checkpoint with `fitted_temperature_buckets` and `temperature_by_options` printed; recompute under ≥2 frozen criteria permutations; and add the (cheap) `band` reliability check.

---

## 4. The silent-truncation curve

### 4.1 How each point must be computed

For each checkpoint `(r, t)` in each run:

```
S(r,t)  = frozen-serializer render of the state, as a string
N(r,t)  = len( encode_checkpoint( S(r,t) ) )        # the tokenizer the checkpoint actually loaded
H(q)    = len( encode_checkpoint( render_head(q) ) )  # measured, including template + specials
B       = the checkpoint's MEASURED runtime clamp   (defined below)
Z_harness(r,t) = 1[ N(r,t) + H(q) + 1 > B ]           # predicted state truncation
token_ratio(r,t) = min(1, (B − H(q) − 1) / N(r,t))    # fraction of the state actually seen
Z_laya(r,t)      = 1[ truncated.state present ∨ fits == false ∨ truncation warning present ]

TR(t)          = mean over runs of Z_harness(r,t)     # truncation-rate-vs-horizon
token_ratio(t) = median/IQR over runs                 # the survival curve
```

`H(q)` must be **measured**, not taken from the planner's `head_tokens_estimated`, which is produced by the same `chars/4 × 1.15` model that errs in **both** directions — over-reserving on prose, **under-reserving on JSON, code and CJK**, which is the dangerous direction. **⚠️ 2026-09-23 correction:** this line previously read "1.8× wrong", a figure that described only the synthetic sweep state and only the safe direction. See `results/ERRATA.md` §12 and `results/P31-token-density.json`. R13 §2.3 gives a validation identity for the whole computation: `input_tokens_padded ≈ N + H + 1` on a small warm state (it measured `state + 61` exactly). Assert that identity on ≥20 small states before trusting the budget arithmetic — an error of ±50 tokens in `H` is the same size as the entire silent window.

`B` must be **measured per checkpoint**, by the output-freeze probe (grow the state until the answer stops changing bit-identically), and never imported. The 512 clamp is measured on `english` only. R13 §0c records the sibling configs as **`multilingual`: `max_len 1024`, `head_max_len 256`; `typed-decisions`: `max_len 1024`, `head_max_len 256`** — while `english` is `512 / 192`. The most parsimonious hypothesis for the un-isolated "why does the runtime clamp at 512 under a `--max-len 1024` override" question (R5 §8.4 says the paper must not assert a mechanism) is that **the clamp is the english checkpoint's own `max_len: 512`**, and that `--max-len` reaches the planner but not the checkpoint config. I do not assert it. But I do assert its consequence: **if that is right, the multilingual arm clamps at ~1024, and R5 §4.2 rule 5's hard 450-token cap — derived entirely on english — is wrong by 2.3× for the P10 regime**, and the P10 truncation curve would be computed against a budget that does not exist. This is testable in ten minutes with the freeze probe on each checkpoint.

### 4.2 False negatives that corrupt the curve

| # | Mechanism | Effect on the curve |
|---|---|---|
| FN1 | **Computing the curve from Laya's fields.** On Path A, `truncated` is absent, `fits: true` and no warning fires across the whole ~300-char / ~47-token silent window (2,850 → 3,148 chars), while the tail has already been discarded and the answer has already flipped to wrong | Every checkpoint in the silent band is scored clean → curve is a **lower bound** and non-monotone in a way that tracks the *character-count* flag, not the token cut |
| FN2 | **The horizon grid does not sample the band.** The dial is `d ∈ {0, 4, 28, 124}`. If a state grows a few tokens per step, the 47-token silent band may fall entirely between two measured horizons | The band is invisible in the figure while being the paper's motivating phenomenon |
| FN3 | **Harm without a behavioural signal.** A truncated state whose surviving prefix happens to contain the deciding evidence answers correctly and emits nothing | `Z_harness` still catches the *event*; nothing catches the *harm* except a planted-evidence probe. This is R5 §8.3's own unresolved item (T3 contamination survival), and it is the gap between "truncation happened" and "the judge lost the evidence" — which is the paper's actual claim |
| FN4 | **Harness-side truncation scored as Laya truncation.** If the protocol caps the state at 450 tokens, every state above 450 was already cut *by the harness* | The curve measures the harness |

### 4.3 False positives that corrupt the curve

| # | Mechanism | Effect |
|---|---|---|
| FP1 | **Path B's flags lead the cut by ~1,440 chars.** At 1,399 chars `truncated` + `fits:false` + warning + recommendation all fire while `input_tokens_padded` is 265 of 512 — no truncation at all | Any curve from Path B over-reports enormously. R5 §4.1 pins Path A for main analysis and Path B for a "robustness comparison" — that comparison will show a large, publishable, entirely artifactual difference between hosts |
| FP2 | **`truncated.options` conflated with state truncation.** `plan_questions` sets `fits = not any_truncation` where `any_truncation` **only considers `would_truncate_state`**; option compression does **not** clear `fits` (R13 §3.4, with a verbatim 20-option response showing `truncated.options` present and `fits: true`) | In the P10 high-cardinality regime (11–20 options) *every* call carries `truncated.options`, so a metric defined as "any non-empty `truncated`" reads **100 % by construction** and means something different from state truncation |
| FP3 | **Wrong checkpoint tokenizer.** Three sibling checkpoints with different encoders (`ModernBERT-large` vs `mmBERT-base`) — token counts for identical text differ | A silent multiplicative offset in `N`, i.e. a shifted `TR(t)` |
| FP4 | **`H` estimated rather than tokenized**, or `B` imported across checkpoints | Offsets of the same magnitude as the window itself |

### 4.4 Does the design's own gate resolve this, or move the uncertainty?

It moves it — and it does something worse. Three specific relocations:

1. **It resolves detection, not consequence.** Knowing `N = 480` tells you the tail is gone. It cannot tell you whether the deciding evidence was in the tail. That is precisely R5 §8.3 item 3, and it is the falsifiable content of the paper's claim.
2. **It converts an observable failure into a prevented one — destroying the curve.** R5 §4.2 rule 5 sets a hard ceiling of **450 state tokens**; the measured real cut is at `N > 450`. These are the same number. A **compliant** run therefore never truncates, and `TR(t) ≡ 0` for all `t` — a clean, monotone, publishable flat line that is an artifact of the protocol, not a property of Laya. A **non-compliant** run violates the design's own "违反即结论作废" constraint. **The gate and the curve cannot both be satisfied by one population.** This is the single most dangerous silent wrong number in the design (§7 row 7), because the broken output is not missing — it is a perfect-looking zero.
3. **It leaves three residual estimates**: which tokenizer, which clamp `B` per checkpoint, and whether `H` was tokenized with the identical template. Each is individually resolvable and none is currently specified as an assertion.

**The fix the design is missing.** R5 has the right instrument in R4 (P0-2 option 3, the "active probe": paired calls on the full state vs the state with its last 20 % deleted) but did **not** carry it into the R5 protocol. That probe is a **direct** measurement of truncation that depends on **none** of `B`, `N`, `H`, the tokenizer, or Laya's flags: if the answer is bit-identical with and without the tail, the tail is not being read. Cost: 2 × 69,120 × 37 ms ≈ **85 minutes** for the entire battery, or ~2,000 stratified probes in under 3 minutes. **Make it the primary evidence**, with `Z_harness` as corroboration and `Z_laya` as the *finding about the flags* rather than the measurement.

**VERDICT: feasible-with-fix.** Minimal fix, four parts: (1) run **two populations** — a **gated** one (≤400 tokens) for all headline process metrics, and an **ungated observational** one whose states are allowed to grow past the clamp, used *only* for the truncation curve, with the gate flag as a per-checkpoint covariate; without this split the curve is either 0 % or non-compliant; (2) make the **paired tail-deletion probe** the primary truncation measurement and report `Z_harness`, `Z_laya` and the probe as three separately labelled series whose **disagreement region is itself a figure** (silent truncation = `Z_laya=0 ∧ probe=1`; false alarm = `Z_laya=1 ∧ probe=0`); (3) measure `B` per checkpoint by output-freeze and `H` by tokenizing the rendered head, asserting `input_tokens_padded ≈ N + H + 1` on ≥20 states; (4) define the metric as **`truncated.state` only** and never count `truncated.options`.

---

## 5. Wall-clock feasibility — bottom-up

### 5.1 Assumptions (explicitly marked)

| Id | Assumption | Basis |
|---|---|---|
| W1 | Decode rate **213.9 output tok/s** | **V3-MEASURED**, 185 steps |
| W2 | Generation output per step: 900 tok (**design**) → 4.2 s; 2,057 tok (**measured**) → 9.6 s | R15 §6.1 vs V3-MEASURED |
| W3 | Prefill is not separately costed (95.4 % of the prompt is cache-read) | **V3-MEASURED** — flagged as an omission, not a finding |
| W4 | One structured LLM judge turn ≈ **3.0 s** | supported by measured p50 3,087 ms on short-output steps (R13's flow gives no self-report for the LLM arm) |
| W5 | Laya replay at **batch = 1 = 37.4 ms**; batching across states is impossible | R13 §8.2 + the API's one-state-per-call shape |
| W6 | **16 concurrent runs** | API concurrency limit is 2,500 (R2 §A); a run is internally sequential, so parallelism = concurrent runs. `maxParallelToolCalls = 20` is irrelevant per-run |
| W7 | Grader call ≈ **4.0 s** with reasoning; oracle coverage 70 % | R15 §6.5 target; 4.0 s from W1/W4 with ~500 reasoning tokens |
| W8 | Jev live ≈ **1.2 s/call** | R13's measured 403-refusal floor (1,011–2,349 ms) — a **lower bound**, not a measurement |
| W9 | A5b batched LLM call ≈ **7.5 s** (8 states in prompt, ~1.2× output) | **unmeasured**; flagged as the weakest assumption in this table |
| W10 | A5c self-consistency k = 8, LLM only | Laya is deterministic (R13 §6.1), so k = 8 yields eight bit-identical samples — **not constructible for Laya** |

### 5.2 Machine time

| Block | Volume | Design's claim | **My estimate (serial → at 16 streams)** |
|---|---|---|---|
| **Generation, P8** | 69,120 steps | 115 h serial; "8 streams ≈ 1.4 days" | **80.6 h** (W2-design) → 5.0 h; **184.3 h** (W2-measured) → **11.5 h** |
| **Judgment, Laya** | 69,120 checks | "576×120×140 ms ≈ 2.7 h CPU; ~25 min on 8 cores" | **0.72 h** single-process — the sidecar is one process on one GPU, so "8 cores" does not apply |
| **Judgment, Laya — as R5 §7 assumes** | 69,120 checks | "3.2 ms/question, 极廉价" | would be 0.06 h — **12× optimistic**; the batch-20 rate is unattainable (W5) |
| **Judgment, LLM structured replay** | 69,120 calls | **not costed anywhere** | 57.6 h → **3.6 h** |
| **Judgment, Jev replay (if live)** | 69,120 calls | "~40 min on one M1 Max GPU" (Laya's number, reused) | 23.0 h → **1.4 h** (rate limits unknown) |
| **A5c self-consistency (LLM only)** | 92,160 calls | not costed | 76.8 h → **4.8 h** |
| **Evaluation** | 69,120 units (70 % oracle) | "≈6 h" | 23.0 h → **1.4 h**; 0 % oracle → 76.8 h → 4.8 h |
| **Battery machine total (W2-measured, 70 % oracle, live Jev)** | | design implies ~1.4 days | **≈23.4 h ≈ 1.0 day continuous** |
| Calibration corpus P5 | 19,200 steps | listed under "one long session (4–6 h)" | **4.6 h** machine, but it is a **serial gate** before P7/P8 |
| Pilot P7 | 8,640 steps | "4–6 h" | **≈2.0 h** machine + analysis |
| A5 sweep P9 | 50,400 steps | own session block | ≈6 h machine |
| Fine-tune branch | 1 checkpoint | not sized | ~2 GPU-h of compute (R13: the shipped english fine-tune took 1.96 h at `world_size 1`) **plus item construction, which the design never sizes** |

### 5.3 Elapsed calendar (one experienced person, once the harness exists)

| Stage | Elapsed |
|---|---|
| Harness: frozen serializer `SER`, question bank, hashing, tokenizer gate, oracle grader, replay engine, survival/RI statistics | **8–15 working days** |
| P5 calibration corpus → τ\* freeze (serial gate) | 1 day |
| P6 fault-injection validation | 1–2 days |
| P7 pilot + ICC re-size decision | 1–2 days |
| P8 full battery | 1–2 days wall (≈1 day machine) |
| P9 A5 sweep + fine-tune branch (incl. independent training split — unsized) | 3–5 days |
| P10 multilingual + high-cardinality regime | 1 day |
| Human adjudication of indeterminate items (~170 at N=1000) + ≥200-cell grader audit | 2–4 days |
| P11 analysis + P12 writing | 15–25 working days |
| **Total elapsed** | **≈5–9 weeks**, of which machine time is **~2 days ≈ 4 %** |

### 5.4 Does it fit in one long session?

**No — and R5 §7 partially contradicts R15 §6.6 on this point.** R5 §7 lists "P1–P3, P6, **P5**, **P7**, Laya latency benchmark, high-cardinality and mis-route regimes" as doable in one long session. P5 alone is 19,200 generation steps (4.6 h machine) and is a *serial gate* before the pilot; P7 needs the LLM judge replay that R15's budget never costed. What genuinely fits in one session is what R5 §7 lists *first*: P1–P3 (interface freeze, mock pipeline, tokenizer gate) — those are engineering, and the mock-Jev drill is free.

R15's own arithmetic is also wrong in the direction that matters for scheduling: it states "576 × 120 × ~6 s ≈ 115 h serial; with 8 parallel streams ≈ **1.4 days**". 115 h ÷ 8 = **14.4 h = 0.6 days**; 1.4 days corresponds to 3.4 streams. R5 §7 inherits "~1.4 天". The error is conservative, but it is an error, and it means no schedule line in the design was checked against its own parallelism.

### 5.5 Minimum viable reduction that preserves the headline

R5 §0's headline is **"cost is not the constraint; silent degradation is"** — *not* the T90 lead-time story, which is R5 §5.5's secondary endpoint. Three of the four evidence legs for the headline need **no generation battery at all**:

| Evidence leg | What it actually needs | Battery needed? |
|---|---|---|
| Silent truncation + output-freeze + `token_ratio(t)` | the paired tail-deletion probe on **synthetic states of increasing length** — R13's own method, at scale, per checkpoint and per host | **No** |
| `confidence` decoupling + high-cardinality saturation | ~500 Laya calls on synthetic ticket-like states (R13 §3.1's ladder, at n≥200 per rung instead of 1) | **No** — Laya is free and 37 ms |
| Latency + cost with device qualification, and the crossover-vs-horizon curve | a **state-length ladder** (synthetic states at 1.5 k / 5 k / 20 k / 52 k tokens) × {Laya, LLM judge, Jev} ≈ 300 serial calls | **No** |
| T90 lead time, drift `D(r,t)`, recovery, `CER` | the real battery | **Yes** |

So the minimum viable reduction is:
1. **Drop A5a entirely** (R5 already did) and **drop A5b/A5c from the Laya comparison** — A5b is not constructible for Laya (§1.2) and A5c is degenerate for Laya (determinism, W10). Keep them as LLM-only arms if a round-trip frontier is wanted.
2. **Keep exactly what the headline needs**: the synthetic truncation/calibration/latency programme above (~800 Laya calls ≈ 30 s of GPU; ~300 serial LLM judge calls ≈ 15 min; no generation).
3. **Use R15's own reduced battery (12 × 2 × 6 = 144 runs × 60 steps = 8,640 steps) for the T90/drift claims**, not 576 runs — an **8×** reduction on generation and on the LLM judge replay.

Net effect: generation 69,120 → 8,640 steps; machine time **~23 h → ~4 h**; API dollars **~$490 → ~$90**; elapsed **5–9 weeks → ~3–5 weeks**. And the honest observation: **the reduction buys machine time the design was never short of.** Elapsed time is dominated by engineering and analysis, which the reduction barely touches. The reduction's real value is that it removes *infeasible* arms (Laya A5b/A5c) and a 288-run sweep with no discriminating power on the dollar axis (R3 §4).

**VERDICT: feasible-with-fix.** Minimal fix: rescope to the reduced battery for the process metrics, run the truncation/calibration/latency claims on synthetic state ladders where they are actually measurable, correct the two arithmetic errors in the schedule, and replace the "matched latency frontier" — which cannot exist against Laya — with exact round-trip counts, which are free and immune to every clock problem in §1.

---

## 6. Cost and wall-clock summary table (assumptions marked ⚠ = assumed, ✅ = measured)

| Line | Units | Per-unit basis | Off-peak cost | Source / status |
|---|---|---|---|---|
| Generation (full battery) | 69,120 steps | 2,057 out ✅ + 52 k prompt ⚠ (90 % hit ✅-route) | **$148.9** | W1/W2; R2 §A |
| Generation (reduced battery) | 8,640 steps | same | **$18.6** | W2 |
| A1 structured LLM replay | 69,120 calls | 52 k in ⚠ + 120 out ⚠ | **$68.6** | R3 shape, horizon-priced |
| A5c self-consistency k=8 (LLM only) | 92,160 calls | as A1 | **$91.5** | W10 |
| Jev replay | 69,120 calls | 52 k in, $0.042/M | **$150.9** | R2 §C.1; output-price claim unverified |
| Laya replay | 69,120 calls | **no price exists** | **convention only** | 0.72 h GPU wall |
| Evaluator (70 % oracle) | 20,736 calls | 52 k in ⚠ + 750 out ⚠ | **$28.4** | route UNKNOWN |
| Evaluator (0 % oracle) | 69,120 calls | same | **$94.7** | R15's ≥70 % is a target, not a plan |
| Calibration corpus P5 | 19,200 steps | pro-rata | **$136** | R5 §7 P5 |
| Pilot P7 | 8,640 steps | pro-rata | **$61** | R5 §7 P7 |
| **Programme total, off-peak** | | | **≈$685** | vs the design's own **$93** |
| **Same at peak (×2)** | | | **≈$1,370** | R2 §A |
| **Reduced programme, off-peak** | | | **≈$90** | §5.5 |
| Generation wall clock | 69,120 steps | 9.6 s ⚠ (W2-measured) | **184 h serial → 11.5 h at 16 streams** | W1 |
| Laya judgment wall clock | 69,120 calls | 37.4 ms ✅ batch 1 | **0.72 h** (single process) | R13 §8.2 |
| LLM judgment wall clock | 69,120 calls | 3.0 s ⚠ | **57.6 h → 3.6 h** | W4 |
| Evaluation wall clock | 20,736 calls | 4.0 s ⚠ | **23.0 h → 1.4 h** | W7 |
| **Machine total** | | | **≈23 h ≈ 1 day** | |
| **Elapsed total** | | | **5–9 weeks (machine = 4 %)** | §5.3 |

---

## 7. SILENT-WRONG-NUMBER REGISTER

Metrics that can be **computed, look fine, and be wrong** — ranked by danger. (A missing measurement is obvious; these are not.)

| # | Metric | How it goes wrong | The check that catches it |
|---|---|---|---|
| **1** | **Truncation rate vs horizon `TR(t)`** | R5 §4.2 rule 5 caps states at 450 tokens; the measured real cut is at `N > 450`. A **compliant** run never truncates → `TR(t) ≡ 0`, a clean flat curve that is a protocol artifact. A non-compliant run voids the design | Assert every plotted `t` has ≥1 run with `N > 400` **and** ≥1 with `N > 500`; if no state crosses 450, report `TR(t)` as **not estimable**, never as 0 %. Run the ungated observational population for this curve only |
| **2** | **Calibration / ECE** | A judge that returns the base rate π constantly has **ECE ≈ 0** and zero resolution. Pure-ECE reporting crowns a useless judge. Compounded by τ\* being fitted on the same corpus that produces the headline ECE | Require Brier **reliability *and* resolution**, the base rate, sharpness and AUC on every reliability figure; assert τ\*-fit rows and ECE rows are disjoint; add a constant-predictor negative control that must score ECE ≈ 0 **and** resolution ≈ 0 |
| **3** | **Laya per-decision latency** | `3.2 ms` is the batch-20 amortisation over *20 questions on one state*. The replay has one question per state, so batch = 1 = **37.4 ms**. Using 3.2 ms understates Laya ~12× and makes it look better than measured | Log `usage.questions` per call; compute amortisation only within calls where `questions > 1`; assert the replay's median batch size is 1; never quote an amortised rate without its batch size adjacent |
| **4** | **Jev latency in a cross-judge table** | R3 §6 places Jev `p50 126.81 ms` (third-party, colocated) beside Laya's `34 ms` (first-party, local). This host's measured transport floor for an unauthenticated **rejection** is 1,011–2,349 ms — the 126.81 figure is below the floor of doing nothing | Assert each latency row declares: measurement host, clock (vendor self-report vs client wall), authentication present y/n, and batch size. Refuse to place third-party colocated figures in the same column as first-party local ones |
| **5** | **A0 judge latency = 0 ms** | A0's verdict lives inside the generation step; there is no call to time. Reporting `0 ms` makes A0 the winner of every latency frontier by construction | Assert A0 has **zero** `tool/call` records attributable to judging; report A0 as `round-trips = 0` (an integer), never as a duration; if a duration is wanted, attribute the whole generation step to it |
| **6** | **Per-call latency from transcripts** | 5 parallel calls shared one result timestamp within 3 ms (R11 §4.1); `maxParallelToolCalls = 20` makes this the normal case. `tool/result.time − tool/call.time` returns the batch **max** | Force concurrency 1 for the latency block and assert the count of `tool/call` records between `step/start` and `assistant/message` equals the count of timed units; assert all per-call deltas are pairwise distinct |
| **7** | **Cost column: reasoning tokens** | R15 sizes output from visible text (900/step, 120/judgment). Measured mean is **2,057 out/step**, with a `reasoning` block on 188/188 messages and steps at 6,000–15,742 output tokens where reasoning is essentially all of it. Any model that omits reasoning understates the dominant cost line | Price `usage.outputTokens` **verbatim** — never a text-length estimate. Assert `usage.outputTokens` is non-null on every priced step and record `reasoningEffort` per run. Add an off/low/max effort sweep on ≥100 judge calls |
| **8** | **Cost column: cache writes** | DSH records `cacheWriteTokens`; it was **0 in 185/185 measured records**. A zero cannot be distinguished from *billed but never populated* — a cost column silently omitting a price class | Assert either a documented provider statement that cache writes are not separately billed, or reconcile `cacheWriteTokens` against the provider's own `usage`/invoice for ≥20 sampled calls |
| **9** | **Cost table that answers the wrong question** | R3 §5's thesis is that the Jev/LLM crossover (2,100–7,100 tok) is crossed as the state grows. Every budget line in R3 §2–3 and R15 §6.1 is priced at a flat **1,500-token** state. At 52 k tokens Jev is **2.2× more expensive** than the LLM judge — the opposite sign | Assert every cost row is priced at **that run's measured state token count**; report cost as a function of horizon; pre-register the crossover point and show it crossed |
| **10** | **Peak/off-peak allocation** | Peak is 2×. P8 generation is >11 h of machine time, so a block necessarily crosses a UTC boundary. A single-rate figure is wrong by up to 2× | Bin every call by its own `time` converted to UTC against R2 §A's published windows; assert `billed_total == Σ per-call bins`; report the call fraction in each bin |
| **11** | **Gold-evaluation line `$3,802`** | R15's row is labelled "5 judges × 120 checkpoints × 576 runs (69,120 calls)", but 5×120×576 = **345,600** ≠ 69,120, and $3,802 ÷ 69,120 = **$0.055 = exactly 100× the stated $0.00055/unit**. Two independent internal contradictions in one row | Recompute every budget line from its own stated assumptions: assert `units == judges × checkpoints × runs` **and** `row_total == units × per_unit_price` before publishing. *(This resolves R5 §8.1's open item: R15's $3,802 is a 100× decimal slip in the per-unit price, compounded by a judge multiplier that was written into the label but never applied.)* |
| **12** | **Schedule lines** | R15: "115 h serial ÷ 8 streams ≈ **1.4 days**". 115 ÷ 8 = 14.4 h = 0.6 days. R5 §7 inherits "~1.4 天" | Assert `parallel_wall == serial / streams` on every schedule line; record the stream count actually used |
| **13** | **Laya cold-start contamination** | First call after model load is 389.9 ms (R13) to 4,935.9 ms (R11) versus a 37 ms warm median — 10–130×. The sidecar dies *silently* mid-run (R13 §0, R4 P0-4), so cold calls appear at arbitrary points | Discard the first ≥3 calls after every sidecar start; join the call log against `/health.uptime_s` and `/health.calls`; assert no latency sample comes from a call with `calls < 3`; log restart count |
| **14** | **CPU-fallback latency read as a horizon effect** | A device fallback is 10–15× slower and is reported only in `/health.degraded`, **never in the answer**. A mid-run fallback would show Laya slowing down as the horizon grows — the paper's own thesis, fabricated | Assert `device == "cuda"` on `/health` snapshots bracketing every run; abort the run on mismatch; report device per run alongside latency |
| **15** | **`TR(t)` computed from Laya's own flags** | Path A's flags lag the real cut by ~300 chars / ~47 tokens (so truncated checkpoints score clean); Path B's lead it by ~1,440 chars (so clean checkpoints score truncated). The Path A/B "robustness comparison" then shows a large, purely artifactual difference | Compute `TR(t)` from the harness tokenizer **and** report `Z_laya` as a separate series; make the disagreement region its own figure; cross-validate with the paired tail-deletion probe (which depends on no estimate at all) |
| **16** | **`truncated` treated as one metric** | `plan_questions` sets `fits = not would_truncate_state` only; option compression never clears `fits`, so `truncated.options` co-exists with `fits: true`. In the P10 regime (11–20 options) every call carries `truncated.options` → a "truncation rate" of **100 % by construction** | Define the metric as **`truncated.state` only**; assert that in the high-cardinality regime `truncated.options` present ⇒ `truncated.state` absent; report option compression as a separate variable |
| **17** | **Truncation budget imported across checkpoints** | The 512 clamp is measured on `english` only; `multilingual` and `typed-decisions` configs say `max_len 1024 / head_max_len 256`. If the clamp follows checkpoint config, the P10 curve is computed against a budget 2.3× too small | Measure the clamp **per checkpoint** with the output-freeze probe before any truncation claim; never propagate 512 |
| **18** | **Calibration computed on `confidence`** | `confidence` is `max(p,1−p)` for bare `noul` and `1−H/log k` for a noul-carried-as-choice. The **same p ≈ 0.54** gave **0.5399** and **0.0046** — 117×. Pooling framings yields a plausible reliability curve that is a mixture of two scales | Assert every calibration row's binned field is `noul` (the probability) and that `confidence` appears nowhere in the calibration pipeline; assert one framing and one option count per row |
| **19** | **Pooled "Laya" calibration** | `english` has 6 fitted temperature buckets; `multilingual` has `fitted_temperature_buckets: 0` and `[1.0,1.0,1.0]` (uncalibrated); `english`'s `choice:11+ = 0.1006` deliberately sharpens logits ~10× for k ≥ 11. One pooled ECE averages a calibrated model, an uncalibrated one, and a deliberately miscalibrated regime | Report calibration per checkpoint with `fitted_temperature_buckets` and `temperature_by_options` printed; report ECE **by option count**; refuse to pool |
| **20** | **T90 with censoring scored as 120** | No detection within 120 steps is right-censored. Entering it as 120 biases T90 downward — i.e. it manufactures *earlier* detection, the paper's direction of interest | Assert no undetected run enters a mean as the horizon length; report the censoring fraction per arm; fit the pre-registered discrete-time survival model |
| **21** | **T90 with a truncation covariate dropped** | If a snapshot was truncated before serialization, the judge never saw the deciding evidence and T90 measures the serializer, not the judge | Make the truncation indicator a **pre-registered covariate** in the T90 model, never a silent exclusion; assert `DROPPED: n` appears in the first tokens of every truncated snapshot (R3 §7's newest-first requirement) |
| **22** | **Detection tables without the B0 false-alarm column** | A judge that always answers "fault" has perfect lead time and the lowest latency. The B0 benign-rewrite control exists precisely to kill this | Assert every detection-metric table carries the B0 column and that the primary T90 is computed on the **B0-adjusted** detection rate |
| **23** | **Mock-Jev zeros reaching a results table** | R4 §"推荐执行顺序" runs the whole pipeline on mock Jev — `latencyMs 0`, `costUsd 0`, hash-derived answers. A table generated from that pass reads "0 ms, $0, accuracy 0.6", every cell of which looks like a measurement | Assert every Jev row carries the `provider` field and that **no** Jev number with `provider == "mock"` reaches a result table; gate on R4 §5's eight-item smoke checklist |
| **24** | **Determinism misread as stability** | Laya is bit-identical on repeat (R13 §6.1), so a repeat-variance of 0 looks like perfect robustness, and an A5c self-consistency arm for Laya yields k = 8 identical samples with agreement 1.0 by construction | Assert repeats are never used for Laya variance estimation (R5 §4.3 rule 13); report A5c as LLM-only; propagate the measured criteria-order sensitivity (Δp ≤ 0.052, Δconfidence 0.111) into every calibration CI as a reported sensitivity |

---

## 8. Changes I recommend to R5, in priority order

1. **Split the truncation claim into two populations** (gated + ungated observational) and make the **paired tail-deletion probe** the primary truncation measurement. Without this, the paper's motivating figure is either 0 % or non-compliant. (§4.4)
2. **Delete the Laya side of A5b** and any matched-latency frontier against Laya; replace with exact round-trip counts. (§1.2)
3. **Correct Laya's per-question latency to batch = 1 (37.4 ms wall / 30.0 ms self-report)** everywhere R5 §7 currently says 3.2 ms, and record `usage.questions` on every call as the assertion. (§1.2, §7 row 3)
4. **Price every cost row at that run's measured state token count and plot cost against horizon** — this is the only form in which R3 §5's crossover claim is testable, and at present the budget contradicts the thesis. (§2.4)
5. **Add Brier decomposition, a resolution floor, a constant-predictor negative control, and a τ\*-fit / ECE-report split** to the calibration plan. (§3.2)
6. **Fix the two arithmetic errors** (`$3,802`, `115 h ÷ 8 = 1.4 days`) and add the two assertions that would have caught them. (§7 rows 11–12)
7. **Measure the clamp per checkpoint** before making any truncation claim about the multilingual regime; do not propagate 512. (§4.1)
8. **Measure the one unmeasured arm cost that matters**: an off/low/max `reasoningEffort` sweep on ≥100 judge calls. R2 §A.1 says effort is the dominant cost variable; R5 never sweeps it, so its per-judge cost claim is a guess. (§2.2)

### Things this audit tried to break and could not

- **"Money is not the constraint" survives adversarial re-derivation.** With measured output tokens (2.3× the assumption), a horizon-realistic prompt model, peak pricing throughout, a live Jev arm and zero oracle coverage, the programme is **< $2,000**. R3's conclusion holds with ~20× margin.
- **The dual-plane measurement design (R5 §5.4) is sound** and is the cheapest good decision in the document. Replay over 69,120 frozen snapshots costs **43 minutes** of Laya GPU time. My only criticism is that its multiplicity (how many judges replay how many snapshots) is never fixed, which is why R15's gold-evaluation row could be self-contradictory without anyone noticing.
- **Laya's determinism is a genuine advantage** for a calibration claim: it means every item contributes exactly one sample, so all the statistical work is honestly item-level. The design is right to make this explicit, and it is right that the LLM arm must be sampled repeatedly (in non-thinking mode, R5 §4.4 rule 17) to be compared.
- **R5's rule 6 ("never put load-bearing evidence at the tail") is exactly right** and is the correct engineering mitigation of the phenomenon the paper measures.

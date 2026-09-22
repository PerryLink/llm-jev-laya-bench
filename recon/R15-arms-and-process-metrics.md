# R15 — Experimental Treatment Arms, Schedule Knob, Process Metrics, Fault Injection, Statistics, Budget

**Unit:** R15 (arms + process-level measurement + fault injection).
**Status:** design deliverable. No live judge calls were made; no checkout inspected.
**Scope:** sections 1–6 below. Task families, item battery, task-specific gold references, and
task selection are owned by another unit and are treated here as a given interface
(`TASKS`, `GOLD[T]`, gold reference trajectory `REF[T][t]`). This document does not redesign them.

---

## 0. The constraint that shapes everything (read this before the arm table)

**Only DeepSeek-V41-Flash generates. Jev and Laya are discriminative: they emit a label plus
probabilities, a chosen label, or a score. They cannot produce text, call tools, or act.**
Consequently every arm in this document contains the *same* generator, on the *same* task, with the
*same* prompt, the *same* tool surface, the *same* step budget and the *same* seed. What varies
between arms is **only the judgment layer**: which judge is asked, in what question form, on what
schedule, and what the returned verdict is permitted to do to control flow.

This is a **within-generator judgment-layer comparison, not an agent comparison.** No arm compares
"an LLM agent" to "a Jev agent" — there is no Jev agent and there cannot be one. A reviewer who
reads any result as "Jev beat an LLM at the task" has misread the design, and the paper must say so
in the abstract, not only in the methods.

### 0.1 The judge is a gate, never an actuator

A verdict may do exactly three things, all of them routed back through the same generator:

| Verdict | Control action | Who still does the work |
|---|---|---|
| `accept` | none; continue to next step | generator |
| `revise` | re-prompt the **same generator** with the verdict's label appended as a terse instruction (`"judge=<label>; redo step under this constraint"`) | generator |
| `halt` | mark the checkpoint for escalation; the generator is asked for a revised candidate or the run aborts per a fixed abort rule | generator |

This guarantees "the generator is constant" is literally true at every step: the number and character
of generative calls varies only through the control-flow rule above, which is identical in form for
all judge arms (A1–A5). Generator calls per run are logged and are a covariate, not a hidden
degree of freedom.

### 0.2 Two planes: CONTROL (online, scheduled) and MEASUREMENT (offline, exhaustive)

This is the single most important architectural decision in the design.

* **Control plane (online, closed loop).** The scheduled arm asks its judge at the *scheduled*
  checkpoints only, and only those verdicts may affect control flow. Cheap in calls, causally honest.
* **Measurement plane (offline, open loop).** At **every** checkpoint of **every** run, the harness
  writes an immutable snapshot `SNAP[run][t]` (state JSON + hash + token count in the frozen
  serializer). After the run is terminated and the generator seed is retired, **all five judges are
  replayed against those frozen snapshots** — the four typed/LLM judges plus the free-prose
  self-assessment — and every verdict is stored.

Why this is required rather than nice-to-have: error-detection lead time (§3.2) is the paper's
headline metric, and it must not be confounded by the schedule. If only scheduled verdicts are
recorded, then "judge-never" has no detection latency at all *by construction* and the schedule
effect and the judge effect become unidentifiable. Replaying on frozen snapshots makes the
**measurement** exhaustive and identical across arms while the **intervention** remains the designed
variable. It also makes every verdict deterministic and re-analyzable after pre-registration.

One fairness constraint follows: the snapshot is partitioned into a **STATE payload**
(identical bytes for every judge) and a **QUESTION block** (the same question text, option set and
rubric for every judge asked that question). No judge gets a longer or friendlier state; the
question block is a fixed constant per checkpoint. This is what makes "the same typed question"
in A1/A2/A3 literally the same.

### 0.3 Frozen state serializer `SER`

One serializer, fixed and hashed into the pre-registration:

* newest-first ordering of the last `K` step records (newest at the head);
* per step: `step_index`, the action taken, the typed tool result (deterministic fields only),
  and the generator's one-sentence rationale, truncated at a fixed char budget;
* a `DROPPED` counter appended as the **last** line, recording how many step records the serializer
  itself elided (`DROPPED: n`).

Two properties matter. First, `DROPPED: n` is *inside* the state, so a judge reading strictly
left-to-right can in principle see that material was elided before it reads any of it. Second, because
ordering is newest-first, an end-truncating judge (Laya) loses the OLDEST material first — which is
the least control-relevant material — rather than losing the current step. This is a fairness
decision, not a favour to Laya: it makes all judges drop the same region for the same reason. The
ordering effect (newest-first vs oldest-first) is measured as a calibration-corpus ablation (§6.4)
and reported; newest-first is the pre-registered primary.

### 0.4 Question bank (identical across judges)

The typed question form is one object:

```
Q(ck) = { type: noul | choice | score,
          instruction: <fixed text, <= 90 words>,
          options: {label: <=6-word description},   # noul: {true,false}; choice: exactly 8; score: 5 levels
          rubric: <fixed 40-word anchor text> }
```

Hard limits, imposed so that we are not silently measuring Laya's option budget instead of judge
quality: **`|options| = 8` for `choice`** (well under the ~20-option accuracy cliff), **≤6 words per
option**, **≤48 tokens per option**, **≤160 tokens of option text per question** (under the shared
192/256-token per-question option budget). This means **the Jev `rank` primitive is the only place
options exceed 8**, and there it is used at batch size ≤20 with total batch text ≤3,500 characters
(§2.3).

Question **type** is a designed factor, allocated 33/33/33 by item in a pre-registered randomized
order and recorded as a covariate; it is never selected by looking at an outcome. Nine question
templates are instantiated, three per type (`noul`: self-consistency-of-claim / spec-conformance /
unit-plausibility; `choice`: error-class / source-trust / next-action-legality; `score`: progress /
rubric-consistency / residual-uncertainty).

---

## 1. The arm set

Notation: `N_step` = generator steps per run (120 primary, 60 compressed). A run is one
(task, arm, replicate) triple. `LLM_J` denotes the LLM acting as judge — **always in the constrained
structured format**, never prose, in every arm except A0.

| Arm | Judge | Ask rate | Format | Notes |
|---|---|---|---|---|
| **A0** GEN-ONLY | the LLM, in free prose, fused into the generation step | every step | prose, unconstrained | the agent-as-it-actually-is baseline |
| **A1** SELF-CHECK (non-negotiable) | the same LLM | every step | the same typed question, JSON-constrained | confound control |
| **A2** LLM+JEV | Jev | fixed schedule | the same typed question + Jev `check`/`rank` | remote |
| **A3** LLM+LAYA | Laya | fixed schedule | the same typed question, sidecar as-is | local, misrouting live |
| **A4** ADAPTIVE ESCALATION | Laya/Jev first, LLM on escalation | typed: every step; LLM: conditional | typed question both levels | policy in §1.5 |
| **A5** EQUAL-BUDGET | any of the above, under a matched judgment budget | budget-derived | as per sub-arm | §1.6 |

### 1.1 A0 — pure LLM baseline (free prose self-assessment)

**Implementation.** The step prompt's final two lines are fixed: *"Then, on a new line, state
whether your work so far is correct and whether to continue: begin that line with `VERDICT:`."*
The continuous text after `VERDICT:` up to the end of the completion is captured verbatim as the A0
judgment. A deterministic extractor maps it to `{accept, revise, halt}` by the first matching token in
a frozen keyword list (`ok|correct|continue` → accept; `wrong|error|incorrect|fix|redo` → revise;
`abort|stop|cannot` → halt); extraction failures default to `accept` and are logged, with the
extraction-failure rate reported as a measurement in its own right (prose judges are not free to
operationalize).

**Cost.** Zero extra calls, but the assessment is **output** tokens (~120 per step), and the whole
generation prefix is re-read. This is the tightest possible baseline: no added latency, no added
round-trip, judgment fused into work already being done — which is exactly why agents do it.

**Honest weakness, stated in the paper.** A0 is not a "no-judgment" arm; it is a judgment embedded in
prose. That is the point: it is the incumbent. The paper must not describe A0 as "no self-check."

### 1.2 A1 — LLM self-check, structured (NON-NEGOTIABLE)

**Implementation.** After the generation step completes, the harness issues a **second, separate call
to the same LLM** carrying exactly the same STATE payload and exactly the same QUESTION block `Q(ck)`
that A2/A3 will receive. Output is schema-constrained JSON: `{"label": <one of the 8 options>,
"prob": <float in [0,1]>}` — no free-text field is permitted, no rationale field, no chain-of-thought
field. The label drives control flow exactly as in §0.1. `prob` is recorded and is what §5's
calibration analysis uses.

**What confound it removes, precisely.** Three, and they are separable:

1. **Mere re-asking (test–retest / review effect).** Simply asking "are you sure?" a second time
   changes behaviour, independently of any judge. A2/A3 cannot be credited for a gain that A1 already
   obtains by asking again.
2. **Format effects.** Constraining the answer to a closed label set with a numeric probability
   changes the answer relative to free prose, independently of who is answering. A0→A1 is that
   contrast, cleanly.
3. **Judge identity.** With A1 in hand, A2/A3 differ from it in *exactly one* respect — the identity
   of the network answering `Q(ck)` — because state payload, question text, options, rubric and ask
   rate are held byte-identical (§0.2). The estimand of interest becomes
   `β = P(catch | Q asked of judge X) − P(catch | Q asked of the same LLM)`, with re-asking and format
   differenced out.

**Why omitting it would invalidate the paper.** Without A1, the design cannot distinguish the claim
*"a discriminative judge adds process-quality signal"* from the claim *"asking twice helps"*. If a
third of the typed-judge gain survives in A1, the paper's headline result is a restatement of
test–retest reliability — a real, reproducible, and completely uninteresting finding. Worse, the
error is not detectable post hoc: no amount of analysis recovers the missing counterfactual. A1 is
therefore not an arm among arms; it is the **floor** against which every typed-judge claim is stated,
and every reported typed-judge effect must be a *difference from A1*, not from A0.

**Budget note.** A1 costs one extra LLM judgment call per checkpoint — the same order as A2/A3's typed
calls. It is the most expensive arm that is not A5, and it must be funded before anything else.

### 1.3 A2 — LLM + Jev on a fixed schedule

**Implementation.** At each scheduled checkpoint, the harness sends `Q(ck)` (§0.4) to Jev. Question
type is the pre-registered allocation. Jev's returned label drives §0.1 control flow. Two dedicated
sub-conditions, each on a pre-registered 1/3 of items:

* **`check` sub-arm.** Instead of `Q(ck)`, the checkpoint's central claim is submitted to Jev's
  `check` primitive, returning `supported | contradicted | conflicted | insufficient | undecided |
  unknown`. Control mapping, frozen: `contradicted|conflicted` → `revise`; `insufficient|undecided` →
  escalate per §1.5; `unknown` → log as judge-absent (a *no-verdict*, never imputed as `accept` — this
  matters for lead-time censoring, §3.2); `supported` → `accept`.
* **`rank` sub-arm.** At checkpoints with multiple candidate revisions available, submit up to 20
  candidates in one batch, total batch text ≤3,500 characters. When the cap would be exceeded, the
  harness **chunks** into minimal-call batches, and the number of chunks is recorded. The primary
  measurement from this sub-arm is operational: **cap refusals per run** and the extra calls they cost
  — Jev's batch cap is a real, countable constraint on judgment density, and the paper should report
  its incidence rather than hide it. A "static batch" variant (one call, refuse if over cap, verdict
  lost) is compared to the chunked variant to price the refusal.

**Cost.** Zero marginal dollar per call under current terms (remote, no disclosed per-call price); the
binding constraints are network round-trip and the batch character cap.

### 1.4 A3 — LLM + Laya on a fixed schedule

**Implementation.** Jev is replaced by the local Laya sidecar answering the identical `Q(ck)`.
**Laya's pipeline is used as-is, including the language detector** — misrouting is a measurement, not
a bug to be patched out. Three fields are logged on every call, unconditionally:

1. `detected_lang` as reported by the sidecar;
2. the sidecar's own accounting (`truncated`, `budget_summary`, `warnings`) when the invocation path
   exposes it;
3. `script_check`: a deterministic Unicode-block test for Cyrillic / CJK / Greek / Arabic / Hebrew /
   Thai / Devanagari / Hangul / Kana. `script_check ≠ detected_lang` is `MISROUTE=1`, computed
   deterministically from the bytes and therefore valid even where the sidecar exposes no accounting.

**Mandatory instrumentation (this is the horizon story).** `.NET`-free token counting is impossible;
instead Laya's own reported input-token count when available, plus the serializer's character count,
are both recorded per checkpoint, giving `tokens_L(t)`. From these two sequences the harness computes:

* `integrity(t) = 1[ tokens_L(t) ≤ W ]` where `W = 512` (en) / `1024` (multilingual);
* `blind_frac(t) = 1 − min(1, W / tokens_L(t))` — the fraction of the payload Laya could not see;
* `t_trunc = min{ t : tokens_L(t) > W }` — the **truncation onset step**, right-censored if the run
  never exceeds `W`.

**Confirmation of silent end-truncation, deterministically.** At every 10th checkpoint, evaluate
`Q(ck)` twice: once on the full state, once on the state with the final 20% of characters deleted.
`TRUNC_CONFIRMED=1` if `tokens_L(t) > W` and the two verdicts are identical on ≥90% of such
checkpoint pairs while a third variant, the state with the final 20% *reordered to the head*, yields a
different verdict. This is a cheap, sidecar-independent existence proof that the tail is being
ignored, and it converts "we believe it truncates from the end" into a measured quantity.

**Cost.** ~140 ms/check CPU, ~34 ms/check M1 Max GPU, 25–35 s cold start amortized once per session.
At 120 checks/run this is ~17 s CPU per run of judgment against ~12 min of generation: **judgment is
~2% of wall clock.** The measured wall-clock block at A2/A3 is a result in itself.

**Known-failure arms are kept, not fixed.** The multilingual checkpoint's uncalibrated 100%/0%
reporting is not corrected before the primary analysis; it is analyzed in §5 as a separate,
pre-registered secondary contrast (calibrated vs as-shipped routing), because hiding it would remove
the most decision-relevant finding in the whole study.

### 1.5 A4 — adaptive escalation

**Policy, stated as an algorithm.**

```
at checkpoint t, with state payload bytes B(t), script mismatch M(t), typed judge D:
  e1 = M(t) == 1                                  # language misroute: hard, deterministic
  e2 = tokens_L(t) > W                            # out of window: hard, deterministic
  e3 = (D == Jev) and verdict in {insufficient, undecided, unknown}
  e4 = (D == Laya) and prob_label(label_chosen, D) < tau   # soft routing signal, calibrated
  e5 = qtype == numeric and (abs(scale_mismatch_ratio) > s*)  # ordinal/ratio competence bound
  if e1 or e2 or e3 or e4 or e5: escalate to A1's structured LLM judge (once)
  else: adopt D's verdict
```

* **τ (and s\*) is set on a held-out calibration corpus, never on the test set.** Protocol, run and
  frozen *before* any test run is unblinded, and written into the pre-registration:
  1. Collect a calibration set: 4 task families × 40 runs (2 arms × 20), gold-labeled at every
     checkpoint by the same evaluator used in the test phase. This corpus is generated first and its
     items never enter the test battery.
  2. For each candidate τ in a pre-declared grid `0.50, 0.51, …, 1.00`, compute the precision of
     *accepted* verdicts on calibration: `prec(τ) = P(gold-correct | adopted and not escalated)`.
  3. **Rule:** `τ* = min{ τ : prec(τ) ≥ 0.99 }`. If no τ attains 0.99, `τ* = argmax_τ prec(τ)` and the
     attained precision is reported as a headline negative result ("this judge's confidence does not
     support a 99%-precision routing policy").
  4. Freeze `τ*`. The test set never sees a re-fit. Sensitivity to τ is reported as a secondary curve,
     explicitly labelled exploratory.
* **Why the escalation rate is itself a result.** `esc(t)`, the escalation probability as a function
  of step index, is a **process curve**: early checkpoints are in-competence and cheap; late
  checkpoints have larger states, longer numeric chains and more likely non-English artifacts, so
  `esc(t)` should rise with horizon. `esc(t)` rising is the cleanest possible demonstration that a
  fixed-window judge's competence **decays with horizon** while its cost does not.
* **Hard cap.** ≤5 escalations per run (bounds the arm's cost and keeps generation-call counts inside
  the pre-registered envelope). Escalations are logged as events with checkpoint index.

**Reported routing diagnostic (headline).** For each typed judge, `AUC_route` = the AUC of
`confidence` in discriminating correct from incorrect verdicts on the **calibration** corpus, with a
bootstrap CI. This number is separable from accuracy and is what decides whether a cheap-judge-first
architecture is even coherent.

### 1.6 A5 — the equal-budget arm (matched-cost design)

**Statement of the claim being tested.** The paper's efficiency claim is *"cheap judges buy far more
checks for the same money."* A5 is where that claim either holds or dies, so it is specified as an
explicit matched-budget experiment rather than an afterthought.

**Cost model (all terms explicit; generator terms cancel by construction).**

| Term | Model | 120-step run |
|---|---|---|
| Generation (identical in all arms, excluded from the judgment budget) | 1.8k in @85% cache, 0.9k out/step | ~$0.43/run |
| `LLM_J` judgment call | ~1.5k in @85% cache, ~0.12k out | ~$0.00104/call |
| Laya, CPU, local | 140 ms @ amortized $0.00025/CPU-s | ~$0.000035/call |
| Laya, cloud-equivalent (for the dollar ledger) | 140 ms @ $0.0007/vCPU-s | ~$0.000068/call |
| Jev | no disclosed marginal price | assumed $0, flagged as an unverified assumption |

**Two matched-budget levels, both on the judgment layer only:** `B_lo = $0.10/run`,
`B_hi = $1.00/run`. Max affordable calls at `B_lo`: Laya 2,900 (CPU ledger) / 1,470 (cloud ledger),
Jev unbounded, `LLM_J` 96. At `B_hi`: Laya 29,000 / 14,700, `LLM_J` 961. There are at most
`N_step = 120` checkpoints, so **at both levels the typed judges can afford to judge every step with
2–24× headroom, while `LLM_J` is budget-bound at `B_lo` (0.8 calls/step) and only becomes
check-bound at `B_hi`.** That asymmetry, stated as numbers, *is* the efficiency result.

**Checks per arm at fixed total spend (per 120-step run):**

| Arm | Judgment calls/run | Checks/step | $/run (judgment) | First detection latency floor |
|---|---|---|---|---|
| A0 prose | 0 extra (fused) | 1.0 | ~$0.05 (output tokens) | next step |
| A1 structured | 120 | 1.0 | $0.125 | next step |
| A2 Jev | 120–400 | 1.0–3.3 | ~$0 | next step |
| A3 Laya | 120–400 | 1.0–3.3 | $0.004–0.027 | next step |
| A5·LLM @B_lo | 96 | 0.80 | $0.100 | 1.25 steps |
| A5·LLM @B_hi | 961 (capped at 120 checkpts; remainder → k-sample voting) | 1.0 × k=8 | $1.00 | next step, k-vote |
| A5·typed @B_lo | 2,900 feasible / 120 used | 1.0 (+replay depth) | $0.004 | next step |

**Three A5 sub-arms, because "the LLM could just sample more" is the real threat:**

* **A5a — plain matched cost.** `LLM_J` on a uniform subsample of `f` checkpoints at the same ask
  rate as the typed arm; sweep `f ∈ {0.05, 0.10, 0.25, 1.0}` to trace the curve.
* **A5b — BATCHED matched cost (must be included; it is the fair strong baseline).** The *same* state
  payloads, multiple checkpoints per call: up to 8 checkpoint windows plus their question blocks in
  one request, returning a per-checkpoint label array. This cuts serialized round-trips from 120 to 15
  at identical token cost, i.e. the LLM arm can match the typed arm's *density* if batching is
  allowed. Including A5b is what prevents the paper from being refuted by a reviewer who says
  "you never let the LLM batch."
* **A5c — LLM self-consistency at matched cost.** `k` independent samples of the same `Q(ck)` at
  T=0.7, majority label, mean probability as the confidence for routing. At `B_lo`, `k=1` (96 of 120
  checkpoints); at `B_hi`, `k=8` (8 repeated samples at 120 checkpoints) — a genuine 8-sample
  self-consistency judge, which is a strictly stronger baseline than A1 and the strongest thing the
  LLM can be at this budget.

**Primary direction of the analysis: matched DOLLARS, not matched counts.** Rationale, stated so it
can be argued with rather than assumed:

* Matching *counts* presupposes the conclusion. Equalizing checks equalizes the one resource the
  cheap judge has more of, then measures quality — the typed judge wins trivially and the magnitude
  is uninformative, because it is the magnitude at an arbitrary density that no deployment would
  choose.
* The deployment question is "given a fixed budget, which judgment layer produces a better process?"
  That is a matched-cost question. The frontier is `detection_lead_time` (and `AUC_route`, and
  `cost-per-detection`, §3.7) plotted against **total judgment dollars per run**, with one curve per
  arm, sweep points at `B ∈ {$0.02, $0.05, $0.10, $0.25, $0.50, $1.00, $2.50}`.
* Matched-count is retained as the **secondary** analysis, because it answers the complementary and
  independently interesting question "at equal verification density, is a discriminative judge a
  better verifier than a prompted generative one?" Both are reported; the frontier is primary.

**The reframing the lead should decide on before we build this.** At 2026 prices a structured LLM
judgment call costs ≈$0.001, and a 120-step run's *judgment* budget is ~1/4 of its own *generation*
budget. **Money may not be the binding constraint at all.** The genuinely binding asymmetries are:
(i) **latency and serialization** — a typed check is one forward pass (34–140 ms), an LLM check is a
new sequential round-trip (multi-second) inside the agent loop; (ii) **the fixed state window** —
Laya's per-token marginal cost is zero but its window is 512/1024, so the *competent* state size is
bounded while the LLM's grows to context limit (this is §3.5's horizon story); (iii) **auditability** —
typed verdicts are reproducible and calibratable.
**Recommendation:** make the primary frontier a two-panel figure — *wall-clock latency vs detection
lead time* and *judgment dollars vs detection lead time* — and pre-register an **equivalence test** on
the dollar axis (TOST, equivalence margin = 0.5 steps of lead time). If the dollar difference is
inside the margin while the latency difference is large, the paper's *stated* claim ("cheap judges buy
more checks for the same money") must be rewritten as "**fair-cost judges buy the same number of
checks without spending a sequential round-trip, and with a hard horizon ceiling the generative judge
does not have.**" That is a weaker headline and a much stronger paper.

---

## 2. The schedule knob

Judgment is not free even when cheap, so **dose of judgment is a designed factor, not a nuisance
parameter.** Four levels, crossed with the judge (A1/A2/A3), same generator throughout:

| Schedule | Rule | Judgment calls per 120-step run |
|---|---|---|
| **S0 judge-never** | no verdicts (A0's prose verdicts are recorded but never gate) | 0 |
| **S1 every-step** | all `N_step` checkpoints, depth-1 question each | 120 |
| **S2 checkpoints** | `m` checkpoint indices; at each, **depth-`d`**: the base question plus `d−1` follow-up questions of other types | `m·d`, `m ∈ {6, 12, 24}` |
| **S3 trigger** | base question only when a deterministic trigger fires, plus a mandatory probe every 20th step | trigger-dependent, capped at 60 |
| **S4 (optional) S3+confirm** | S3 **plus** a second independent judge to confirm any `revise` before it takes effect | 2× S3 on triggered steps |

**S3 trigger set (deterministic, logged, identical across judges):**

`tri1` any tool/unit-test failure since last checkpoint; `tri2` generated output's schema/type check
fails; `tri3` numeric result differs >2% from the task's frozen golden reference value (`GOLD[T][t]`);
`tri4` first appearance of a new token in the run's state; `tri5` all of the last 3 steps produced
identical state hashes (loop detection); `tri6` the step's own prose `VERDICT:` (§1.1) is non-`accept`.
`tri6` deliberately makes S3 partially A0-dependent — a real coupling that is *measured* by reporting
the per-trigger firing rates and re-fitting the S3 result with `tri6` ablated.

**Equal-total-budget comparison across schedules.** The item-level budget is **per task family**:
`C(T) = Σ_runs [ gen(β, N_r, effort) + Σ_checks cost(judge, qtype, |state|) ] ≤ C̄(T)`, with `C̄(T)`
fixed at the median of the S1·A2 configuration. Two consequences, both deliberate:

1. **S2/S3 buy depth or extra judges with the calls they save.** "Checkpoints" is not "every-step but
   lazier" — it spends the same money differently, which is the actual design question. (Secondary
   within-schedule comparison: hold `m·d` fixed and vary the split, to separate spacing from depth.)
2. **The generator is untouched.** No schedule change may alter the generator's prompt, seed, tools,
   or context assembly. If an arm's generator call count differs (S0 pays no revise loop), the
   difference is logged as `Δgen` and (a) reported as a distinct cost line and (b) used as a covariate
   in the model (§5.4), never silently absorbed.

**Primary schedule estimand.** For each schedule level: the *best achievable detection lead time* and
the *process-quality-per-dollar* ratio. Prediction to be tested, not assumed: S1 favors low-latency
detection of small errors; S2 favors deep diagnosis of large structural ones; S3 gets most of S1's
benefit at a fraction of the calls; S0 quantifies what the generator does unaided.

---

## 3. Process measurements as functions of horizon

**Evaluator.** The gold evaluator is deterministic wherever a deterministic oracle exists (unit tests,
schema/type checks, golden numeric values, reference-text similarity from the task unit's frozen
`REF[T][t]`). Where no oracle exists, a **held-out grader LLM that is not the generator** is used, and
its own accuracy is reported from a hand-labelled audit of ≥200 cells with a binomial CI; no headline
number rests on an unaudited grader. Every metric below is computed per run on the frozen snapshots.

### 3.1 Drift against the gold reference

* **Definition.** Divergence between the run's state and the task's gold reference trajectory.
* **Formula.** `D(r,t) = 1 − sim(state(r,t), REF[T][t])`, with `sim` the frozen composite
  `0.5·(oracle_pass_rate) + 0.3·(retrieval/lexical overlap) + 0.2·(1 − normalized_numeric_error)`;
  the three components are also reported separately so no conclusion depends on the weights.
  Derived: **absolute drift** `D(r,t)`, **drift velocity** `v(r,t) = D(r,t) − D(r,t−1)`,
  **signed drift** = the pass/fail direction of the first failing oracle at `t`.
* **Unit of analysis.** Step-within-run; `n = N_runs × N_step`.
* **Model.** `D(r,t) = α + β_1 t + β_2 t² + b_{0,task} + b_{1,r} + b_{2,r} t + ε` (random intercept per
  task; random intercept and slope per run; `b` terms grouped by arm). The reported quantity is the
  **arm × t interaction** — does drift *accelerate* under this judge?
* **What it tests.** H1: drift velocity from `t = 40` onward is lower under typed-judge arms than A0.

### 3.2 Error-detection lead time — the paper's most valuable metric

* **Definition.** For each run, the number of steps *before the end* at which a judge first flags the
  fault or failure that the gold evaluator confirms. Large is better.
* **Formula.** With fault-onset step `t_0`, gold failure set `F(r) = {t : state(r,t) fails gold}`,
  `t_E(r) = min{ t : t ≥ t_0, judge verdict at t ∈ {revise, halt} }`:
  `LEAD(r) = t_final(r) − t_E(r)` if `t_E` exists, else **right-censored at 0** (never imputed,
  never dropped). Headline summary: **`T90(m, arm)` = the first step at which the judge's cumulative
  detection probability reaches 0.90**, i.e. the inverse of the detection CDF
  `F_m(t) = P(t_E ≤ t)` computed on **measurement-plane replay verdicts** (§0.2), fully crossed with
  the online schedule. Report both `LEAD` (per run) and `T90` (per arm), plus `AUC_detect` on `[t_0, T]`.
* **Unit of analysis.** Run (one `LEAD` per run, one event/censor per run).
* **Model.** Discrete-time survival: `logit P(detect at t | not yet) = γ_t + δ_arm + u_task + v_run`,
  i.e. a per-step baseline hazard plus an arm shift with task and run random effects; equivalently a
  Cox model with task-level robust variance. Report `1 − HR_arm` as the detection-risk reduction.
* **Why this is the metric to stake the paper on.** Four reasons, in order of weight:
  1. **It is the only metric that is causally upstream of the outcome.** A judge's value is its
     ability to flag a fault *while intervention is still possible*. A judge that catches an error
     with one step left has the same end-state score as one that never caught it, so end-state metrics
     cannot separate them; lead time can.
  2. **It is the cleanest discriminator of process from luck.** Good processes with lucky endings and
     bad processes with lucky endings are indistinguishable in final accuracy and perfectly separated
     in lead time.
  3. **It is directly comparable across all five judges by construction, including the judge that
     cannot speak.** Because the measurement plane replays every judge on the identical frozen
     snapshot and question (§0.2), the "free prose" judge and the 421M-parameter judge are measured on
     the same estimand. Nothing else in the design achieves this.
  4. **It is what practitioners actually buy.** "How many review cycles before the damage is
     irreversible" is the human question behind the paper.
* **Pre-registered primary endpoint: `T90` at matched judgment dollars.** One endpoint, one α.

### 3.3 Compounding-error rate

* **Definition.** Whether errors beget errors, and how fast the error stock grows.
* **Formula.** With `E(r,t) ∈ {0,1}` the gold-error indicator,
  `CER_cond = P(E(r,t)=1 | E(r,t−1)=1) / P(E(r,t)=1 | E(r,t−1)=0)` (conditional recurrence ratio,
  run-clustered); and a growth exponent from `log(1 + Σ_{s≤t} E(r,s)) = a + λ t + u_task + v_run`,
  reporting `λ` per arm in **errors/log-step**.
* **Unit of analysis.** Step-within-run for `CER_cond`; run for `λ`.
* **Model.** Mixed-effects Poisson (log link) with run intercepts; `exp(Δλ)` is the arm rate ratio.
* **Companion metric.** `carry_frac` = fraction of runs in which an error detected at `t` is still
  present at `t + 20` — separates *detection* from *correction*, which are different products sold by
  the same judge and should never be reported as one number.

### 3.4 Per-checkpoint quality trajectory

* **Definition.** Arm-mean gold quality as a function of checkpoint index, i.e. the shape of the
  process rather than its endpoint.
* **Formula.** `Q(r,t) ∈ [0,1]` from the deterministic oracle battery at checkpoint `t`;
  `Q̄(arm, t)` with run-bootstrap CIs; fitted `Q(r,t) = f(t) + δ_arm + δ_arm·t + u_task + v_run`.
* **Unit of analysis.** Checkpoint-within-run.
* **Reported as.** Absolute trajectory plus **time-to-plateau** `t*(arm) = min{t : Q̄(arm,t+10) −
  Q̄(arm,t) < 0.01}` — do cheap judges simply plateau later, or lower?

### 3.5 State growth versus the judge's fixed token budget (Laya's truncation, made plottable)

* **Definition.** How the judge's input payload grows with horizon relative to its hard window.
* **Formula.** `tokens_L(r,t)` (Laya's reported input tokens when available, else char count × the
  calibration-corpus chars-per-token constant); `integrity(t) = 1[tokens_L(t) ≤ W]`;
  `blind_frac(t) = 1 − min(1, W / tokens_L(t))`; `t_trunc(r) = min{t : tokens_L(r,t) > W}`
  (right-censored if never); `TOKEN_ratio(t) = P(t_trunc ≤ t)` — a survival curve for the judge's
  usability over the horizon, reported for `W = 512` and `W = 1024` separately.
* **Unit of analysis.** Step-within-run for `tokens_L(t)`; run for `t_trunc`.
* **The plot that carries the horizon claim.** Four curves on one axis versus step index:
  `tokens_L(t)` (rising), Laya's window `W` (flat), the LLM judge's context limit (flat, high), and
  `detection_prob(t) | integrity(t) = 1` (falling). The claim to be tested: **detection probability
  conditional on being in-window degrades with horizon even before the window is exceeded**, so
  truncation is the *last* symptom of a fixed-window judge's horizon problem, not the first.
* **Secondary quantities.** `(i)` minimum required window `W*(t)` = tokens needed to see the full
  state at step `t`, and the earliest `t` at which `W* > 512` / `> 1024`; `(ii)` `TOKEN_ratio` and
  `detection_prob` also for `check`/`rank` batches — Jev's batch character cap is the *refusing*
  analogue of Laya's *truncating* limit and both belong on the same figure:
  |  | **truncates silently** | **refuses loudly** |
  |---|---|---|
  | **Laya** | state > 512/1024 tokens → tail dropped | option text shortened; >20 options |
  | **Jev** | — | `rank` batch > cap → call refused |
  The asymmetry (silent vs loud failure) is a first-class finding: **a silent failure mode produces
  confident wrong verdicts with no error signal, which is strictly worse than a refusal** and should
  be quantified as `P(wrong | truncated) / P(wrong | in-window)`.

### 3.6 Recovery after a fault

* **Definition.** Whether the process returns to a good trajectory after a fault (§4), and how fast.
* **Formula.** `rec(K) = 1[∃ s ∈ [t_0, t_0+K] : D(r,s) ≤ D(r,t_0) + 0.05]`, `K = 10`;
  **recovery latency** `RL(r) = min{ s − t_0 : D(r,s) ≤ tol }`, right-censored if never, with
  `tol = 0.05` on the frozen composite; `tol` sensitivity at 0.02/0.10 reported as a robustness table.
* **Unit of analysis.** Run (one `RL` and one `rec(K)` per run, per fault instance).
* **Model.** `RL`: AFT survival model, `log RL = a + δ_arm + g_fault + u_task + v_run`; `rec(K)`:
  mixed-effects logistic.
* **Distinguishes.** Detection from correction — a judge can be excellent at `T90` and useless at
  `rec(K)` if its `revise` prompt does not actually steer. Both are reported; neither substitutes.

### 3.7 Cost-to-completion curves

* **Definition.** Cumulative resources as a function of elapsed steps, per arm.
* **Formula.** `cost(r,t) = Σ_{s≤t} [ in_tok·p_in + out_tok·p_out + cache_discount ]` (generation and
  judgment lines kept separate); `wall(r,t)` = cumulative **critical-path** latency (sequential)
  and cumulative **total** latency (parallelizable), reported separately — this is where the typed
  judges' 140 ms/34 ms per check lives; `judge_calls(r,t)`; `token_budget_used(r,t)`.
  Derived process-efficiency measures: `$ per detected error`, `$ per step with drift ≤ tol`,
  `$ to T90`, `wall-clock to T90`.
* **Unit of analysis.** Step-within-run for the curves; run for the scalars.
* **Model.** Curves are reported descriptively with run-bootstrap bands, and scalar derived measures
  get the same mixed-effects treatment as §5.4.
* **Why the parallel/serial split matters.** A typed judge's cost is *parallelizable* (batch 120
  checks across cores at ~35 ms each on GPU), while each LLM judgment is a *serial* round-trip inside
  the control loop. Cost-to-completion in dollars and cost-to-completion in wall clock will therefore
  disagree, and the paper should show both rather than pick the flattering one.

---

## 4. Fault injection

**Design.** A nested factor: **fault class** (5 + 1 benign control) × **onset step**
`t_0 ∈ {10, 30, 60}`, assigned by pre-registered randomization within task family. `t_0 = 60` is the
"late" stratum used to measure *whether late faults are detectable at all* under a fixed-window judge
(they occur after `t_trunc` for many runs — this is the interaction the paper predicts).
**Every injected fault has a deterministic oracle**, so "propagation" is a measurable predicate rather
than a judgment call.

**The benign control is mandatory.** Fault class **B0 ("benign paraphrase")**: restate the correct
material at `t_0` without changing content (wording, ordering of independent clauses, formatting).
A judge that flags everything wins spuriously on lead time. Therefore the headline is never detection
alone but **`AUC_detect` and the detection lead time at the false-alarm rate measured on B0**, with
per-judge false-alarm rate (and its horizon trend) reported in the same table. No arm is compared
without its B0 column.

### 4.1 F1 — wrong assumption planted early, never revisited

* **Reproducible injection.** At `t_0`, **force-overwrite** (not prompt-suggest) a single field of the
  run's structured state — e.g. `assumed_unit` or `assumed_constant` — with a plausible-but-wrong
  value, and append a one-line rationale phrase to the state asserting it as established. The
  generator is never told it was injected; the fault is indistinguishable from its own earlier output.
* **Propagation predicate.** `F1_prop(r,t) = 1` iff any *derived* field later in the run was computed
  using the planted value — decidable because the harness records the full tool-call argument graph
  and can replay the data dependency. `Δ_prop = t_prop − t_0` is the **propagation delay**.
* **Good vs bad response.** Good: the judge flags the assumption, or asks a question whose label is
  "assumption unsupported," *before* `t_prop`. Excellent: it flags at `t_0 + 1`. Bad: it flags after
  `t_prop` (detection without prevention), or never, or flags only at the final answer.

### 4.2 F2 — mislabeled exemplar that biases later steps

* **Reproducible injection.** At `t_0`, insert into the run's exemplar store one exemplar whose
  **input is valid and whose label is flipped** on a binary criterion, then log
  `n_copy(r) = ` count of later steps whose output matches the flipped exemplar's label on inputs the
  gold oracle resolves to the *opposite* label. Injection is a store write performed by harness code
  with a `FAULT:F2` marker in the event log (never in the generator-visible state).
* **Propagation predicate.** `F2_prop` at the first step where `n_copy ≥ 1`; severity =
  `n_copy(t_final)`.
* **Good vs bad response.** Good: flags the exemplar as inconsistent with the run's own earlier
  accepted items, or *abstains* on it (an explicit `choice` option meaning "cannot adjudicate this
  exemplar"). **Abstention is scored as a success and must be, or the design punishes exactly the
  behaviour that prevents contamination.** Bad: silent adoption followed by confident downstream
  reasoning; worst is adoption *plus* a prose statement that the exemplar is authoritative.

### 4.3 F3 — contaminated source

* **Reproducible injection.** At `t_0`, patch one retrieved document: replace one factual sentence
  with a plausible wrong claim asserting the same proposition as the gold reference, with a fabricated
  citation, and add `CONFLICT_ORACLE: contradicts=REF[T][k]` to the harness's source metadata (the
  oracle knows; the generator does not). The wrong sentence is drafted by a pre-registered script from
  a frozen template, so it paraphrases the true claim rather than contradicting it in surface form.
* **Propagation predicate.** `F3_prop` at the first downstream state field containing the wrong
  sentence's distinctive token `Z` (or a paraphrase of it, detected by the frozen composite `sim`).
* **Good vs bad response.** Good: contradiction with the *other* retrieved sources or with the run's
  earlier accepted content. **The interesting failure:** a judge that *summarizes* the document
  correctly, and thereby propagates `Z` verbatim, while scoring well on a "consistency with source"
  question — i.e. fidelity is not truth, and the question template must be able to tell them apart
  (`check` on the claim, not on the summary). This fault is the sharpest test of whether a judge
  checks truth or checks agreement, and should be reported as an explicit good/bad pair of examples.

### 4.4 F4 — mid-run spec change

* **Reproducible injection.** At `t_0`, modify the frozen task spec through the harness's
  `spec_update()` (an append-only spec log with version numbers), changing a required output
  constraint without stating that earlier work is now stale. The generator sees only the new spec
  version; the injected requirement is in its context, so this fault is fair.
* **Propagation predicate.** `F4_prop` = first post-`t_0` step whose output violates the *new* spec
  while satisfying the *old* one — trivially decidable from the two oracle suites.
* **Good vs bad response.** Good: flags stale-conforming outputs *and* the specific fields requiring
  rework; the ideal verdict distinguishes "correct under v_{k−1}, invalid under v_k" from "wrong."
  Bad: re-validates old work as still correct (the classic drift failure), or flags everything
  indiscriminately (caught by B0).

### 4.5 F5 — subtle unit/scale error

* **Reproducible injection.** At `t_0`, change one numeric parameter by a `10^±2` factor with no
  textual hint (e.g. `1000` → `10`), in a field whose *local* context remains self-consistent so no
  in-step plausibility check fires. The error is detectable only by cross-referencing a downstream
  magnitude or the gold reference range.
* **Propagation predicate.** `F5_prop` at the first step whose numeric output deviates from
  `GOLD[T][t]` by >2% (the same deterministic predicate as `tri3`, so the trigger schedule and the
  fault oracle agree by construction — deliberate, and reported as such so S3's advantage on F5 is
  interpreted with that in mind).
* **Good vs bad response.** Good: flags the magnitude as implausible *with respect to an anchor*
  (dimensional analysis, order-of-magnitude check, comparison with a previously accepted value).
  Bad/scored-as-null: flags the number as "unusual" without an anchor — logged as a false-alarm-adjacent
  verdict and excluded from detection credit, because unanchored anomaly-flags are not detection.

### 4.6 Fault-injection log (one row per injected fault, the analysis unit)

`run_id, task_id, fault_class, t_0, t_prop, t_E(judge), LEAD, prop_severity, detected_at_prop,
recovered(K), RL, responded_at_t0+1, false_alarm_rate_from_B0, judge_calls_spent, tokens_spent`

**Claimed-versus-demonstrated, stated explicitly.** The design does **not** claim that injecting a
fault equals a naturally occurring failure. It claims (and can defend) that faults with a known onset
step and a decidable propagation predicate are the only way to measure *lead time* at all, and that the
five classes span the realistic failure taxonomy of long-horizon agent runs (state corruption,
exemplar contamination, source contamination, requirement drift, quantitative error). A
naturally-occurring-failure stratum is retained alongside via `tri1`/`tri2`/`tri3`, and the injected
and natural strata are reported separately — never pooled — with the injected-vs-natural gap as a
limitations number rather than an assumption.

---

## 5. Statistical plan

### 5.1 Unit of analysis, and why nothing is independent

Three levels: **items ⊂ steps ⊂ runs ⊂ tasks.** Within a run, consecutive checkpoints share almost all
of their state; within a task, runs share the prompt, the gold reference and the fault distribution.
Treating judge verdicts as independent observations inflates `n` from ~100 runs to ~40,000
checkpoints and is the single easiest way to produce a false positive in this design.
**Rules:** every hypothesis test is at the **run** level or coarser; checkpoint-level data is used only
for curve estimation, with run-clustered uncertainty; `n` is always reported as the number of runs and
the number of tasks, never as the number of checkpoints.

### 5.2 Models

* **Continuous process endpoints** (drift `D(r,t)`, quality `Q(r,t)`, cost curves): linear mixed models,
  `y = Xβ + Zb + ε`, with random intercept for task, random intercept and random slope for run, and
  fixed effects `arm × t`, `schedule × t`, `fault_class`, `qtype`, plus `log(gen_calls)` as a covariate.
  Fit by REML; Satterthwaite or Kenward–Roger degrees of freedom; the arm effect is reported as the
  `arm × t` interaction at `t = 0.5·T` and `t = T`.
* **Binary endpoints** (`rec(K)`, `detected_before_prop`): GLMM logit with the same random structure,
  Laplace approximation; cluster-robust (CR2) sandwich for the primary arm contrast.
* **Time-to-event endpoints** (`LEAD`, `RL`, `t_trunc`): discrete-time survival with a per-step
  baseline hazard, arm shift, and task/run random effects; equivalently a Cox model with **task-level
  robust variance**. Right-censoring is applied, never dropped and never imputed as zero.
* **Counts** (compounding errors): mixed-effects Poisson with run intercepts and an offset for
  exposure (steps at risk).
* **Primary contrast:** `T90` difference at matched judgment dollars, estimated from the discrete-time
  survival model with **task-level cluster-robust SEs**.

### 5.3 Few clusters, and the fallback that actually works here

With ~24 task families, cluster-robust asymptotics are shaky. Therefore:

* report CR2 with a **wild cluster bootstrap** (`B = 9,999`, Rademacher weights) at the task level;
* **the primary inference is randomization inference.** Arms are randomized **within task family**, so
  the sharp null is literally true under permutation: reassign arm labels within task, recompute the
  statistic, and report the permutation `p` over ≥10,000 draws. This is assumption-light, valid with
  few clusters, and — because the randomization is ours — exactly the right test for a designed
  experiment. Pre-register RI as primary for the single headline endpoint and CR2 as the sensitivity
  check.

### 5.4 Multiplicity across many metrics and arms

Fixed hierarchy, pre-registered, no exceptions:

1. **Gate 1 — primary family:** one endpoint (`T90` lead time, matched judgment dollars) × the five
   planned contrasts (A1 vs A0; A2 vs A1; A3 vs A1; A4 vs A1; A5b/A5c vs A2/A3). Holm–Bonferroni.
   No other endpoint may be reported as "significant" before this family is reported in full.
2. **Gate 2 — secondary family:** the seven remaining metrics of §3 × arms,
   Benjamini–Hochberg at `q = 0.10`, reported as **FDR-adjusted** with the raw `p` alongside.
3. **Gate 3 — exploratory:** the schedule grid, fault classes, question types, calibration variants,
   language/misroute contrasts, and every interaction. Reported as effect sizes with 95% bootstrap CIs
   and **explicitly labelled exploratory with no `p`-values**. Curve figures live here.
4. **Subgroup discipline.** No subgroup claim (e.g. "the typed judge wins on F5") is made unless the
   subgroup × arm interaction survives Gate 2 on its own.
5. **Covariate discipline.** `qtype`, `fault_class` and `t_0` are pre-registered covariates; anything
   else added must be named as a deviation with its own exploratory label.

### 5.5 Missing data, censoring, and power

* **Censoring** (`LEAD`, `RL`, `t_trunc`) is the expected form of missingness and is handled in the
  survival model; **`unknown` from Jev is a censored no-verdict, never an `accept`** (this single
  convention choice will move the Jev numbers more than any model choice — it is pre-registered).
* Runs lost to harness error: multiple imputation at the run level (`m = 20`), with complete-case
  reported as sensitivity. If loss exceeds 5% and is arm-correlated, the arm contrast is reported as
  inconclusive rather than imputed.
* **Power (target).** 24 tasks × 4 runs × 6 arms = 576 runs. Effective clusters ≈ 96 per arm after a
  design effect of ~2.2 from task-level ICC ≈ 0.15. That detects a `T90` shift of ~0.35 SD on the
  latent detection scale at 80% power, α = 0.05 (RI), i.e. roughly **1.5–2.5 steps of lead time** at
  the observed lead-time SD. If the pilot's ICC comes in above 0.25, the pilot's own `T90` difference
  is used to re-size the full design before it is funded rather than after.

### 5.6 Pre-registration contents (frozen before unblinding)

Primary endpoint and its exact estimator; the arm list and n; `τ*` and `s*` with the calibration rule
and the calibration corpus hash; the serializer `SER` and its hash; the question bank with all nine
templates; option counts and character limits; the evaluator battery and `tol = 0.05`; the
multiplicity hierarchy; the RI/CR2 plan; the B0 false-alarm control; and every metric's formula. The
skeleton is written first, `τ*` is inserted from the calibration corpus, and the hash of the completed
file is timestamped **before** the first test run.

---

## 6. Feasibility and budget

### 6.1 Cost model with assumptions marked

**Marked assumptions (must be verified by another unit; each is a line item that can move the budget):**
DeepSeek-V41-Flash pricing ≈ `$0.28/Mtok` in, `$0.42/Mtok` out, `$0.028/Mtok` cached in;
generation ≈ 1,800 in (85% cached) + 900 out per step, ≈6 s/step serial; a structured `LLM_J`
judgment ≈ 1,500 in (85% cached) + 120 out, ≈$0.00104/call, ≈2.5 s serial; Laya 140 ms/check CPU and
34 ms GPU, 30 s cold start once per session; Jev marginal cost ≈ $0 (**unverified — flagged**);
grader-LM eval ≈ 1,600 in + 250 out per checkpoint, ≈$0.00055/call.

### 6.2 Full design: 24 tasks × 4 runs × 6 arms = 576 runs, 120 steps/run

| Line | Per run | ×576 runs |
|---|---|---|
| Generation (`S0`–`S3` averaged; identical across arms by construction) | $0.398 | **$229** |
| A0 prose verdict (output tokens only) | $0.050 | $29 (96 runs) |
| A1 structured self-check | $0.125 | $72 (96 runs) |
| A2 Jev | ~$0 | ~$0 |
| A3 Laya (cloud-equivalent ledger) | $0.008 | $5 (96 runs) |
| A4 adaptive (≈|15%| escalation to `LLM_J` + typed floor) | $0.026 | $15 (96 runs) |
| A5a/A5b/A5c at `B_hi = $1.00/run` | $1.000 | $288 (288 runs) |
| **Gold evaluation pass, 5 judges × 120 checkpoints × 576 runs (69,120 calls)** | **$0.066** | **$3,802** |
| Engineering, harness, calibration corpus, audits | — | $1,500–3,000 |
| **Total** | | **$5,900–7,400 ≈ $6,000–7,500** |

**The dominant cost is measurement, not judgment**: the gold evaluator pass is ~55% of the total and
~17× the entire judgment budget. This is the single most important budget fact in the design, and the
first thing to optimize (see §6.5).

**Wall clock.**

* Generation: 576 runs × 120 steps × ~6 s ≈ **115 h serial**; with 8 parallel streams ≈ **1.4 days**
  of continuous generation, realistically **3–4 working days**.
* Judgment: 576 runs × 120 checks × 140 ms ≈ **2.7 h CPU**, parallelizable to **~25 min** on 8 cores;
  ~40 min on one M1 Max GPU. Laya cold start 6 sessions × 30 s.
* Evaluation: 69,120 grader calls, parallelizable to ~8 streams ≈ **6 h**; deterministic-oracle cells
  are near-free and should cover ≥70% of cells.
* **Total ≈ 4–6 working days of machine time**, comfortably inside a session budget if the harness
  checkpoints and resumes per run.

### 6.3 REDUCED design (recommended default): 12 tasks × 2 runs × 6 arms = 144 runs, 60 steps/run

| Line | Per run | ×144 |
|---|---|---|
| Generation | $0.199 | $29 |
| A1 self-check | $0.063 | $6 (24 runs) |
| A5a/b/c at `B_hi` | $0.500 | $36 (72 runs) |
| A4 escalation | $0.013 | $1 (24 runs) |
| A2/A3 typed | $0.004 | <$1 |
| Gold evaluation, 60 checkpoints × 144 runs | $0.033 | $475 |
| Calibration corpus (4 tasks × 40 runs, 60 steps) | — | $260 |
| Fault-validation pass (5 faults + B0 × 6 arms × 3 onset × 20 runs, detection-only, computed from
  replay verdicts — **zero extra calls**) | — | $0 |
| Engineering + audits | — | $1,200–2,000 |
| **Total** | | **$2,000–2,800 ≈ $2,500** |

### 6.4 What each reduction weakens (exactly)

| Reduction | What it costs the paper |
|---|---|
| 24 → 12 task families | Power for task-level generalization; the task random effect is estimated from half as many clusters, so the RI permutation test loses resolution. The paper can no longer claim breadth across task families, only across *tasks*. |
| 4 → 2 runs/task | Weaker run-level ICC estimate; compounding-error growth (`λ`) and `RL` survival fits lose precision first. `T90` survives; `CER` and recovery claims become directional. |
| 120 → 60 steps | **`t_trunc` is right-censored for more runs**, so the truncation-onset claim (`TOKEN_ratio` crossing 50%) is weakened and may be unobservable for short-state tasks. The `t_0 = 60` late-fault stratum must be dropped to `t_0 ∈ {10, 30}`. Compounding still occurs (drift velocity is measurable by step 30), but the *accelerating* tail of `D(r,t)` is truncated. |
| Drop A4 | Loses the "cheap-judge-first is actually deployable" claim; the paper keeps its measurement results but loses its systems recommendation. |
| Drop A5b (batched LLM) | **Fatal to the efficiency claim's credibility** — the LLM arm is then strawmanned on latency. Never drop A5b. |
| Drop the calibration corpus | `τ*` can no longer be set without test-set leakage. The escalation arm becomes unpublishable; if the corpus is dropped, A4 must be dropped with it. |
| Drop the multilingual/Laya-misroute stratum | Loses the strongest and most decision-relevant finding about Laya (uncalibrated confidence + silent misrouting = confident wrong verdicts). Recoverable later as a cheap add-on (Laya is free per call) once generation is done. |

### 6.5 Cost reduction levers, in order of value

1. **Deterministic-first evaluation.** Replace grader-LM calls with oracle cells wherever a
   deterministic predicate exists; target ≥70% of cells. Saves ~$1,400 at full scale with no loss of
   validity (it *raises* it).
2. **Replay, don't re-generate.** The measurement plane already reuses frozen snapshots; ensure the
   five-judge replay is computed once and cached by `(snapshot_hash, question_hash, judge)` — saves
   30–40% of evaluation calls across arms.
3. **Cached prefix for the evaluator.** The rubric and gold reference are a stable prefix; at 85% cache
   hit the eval call drops ~35%.
4. **Batch the evaluator** across checkpoints, halving round-trips.
5. With 1–4 applied, the **full** design lands near **$3,500–4,500**, which is likely affordable.

### 6.6 One session versus several

**Fits in one long session (4–6 h):**
* The **calibration corpus** (4 tasks × 40 runs × 60 steps) — must run *first*, since `τ*` cannot be
  set without it.
* The **fault-injection validation pass**: injection reproducibility, oracle decidability, and
  propagation-predicate checks on ~100 runs. No judge calls needed; this validates the harness.
* The **serializer ablation** (newest-first vs oldest-first) on the calibration corpus, plus the
  hidden-injection test (inject a synthetic contradiction at a known offset and verify a probe judge
  can recover it while a 512-token reader cannot) — this is what licenses the truncation claim.
* The **pilot** if only A1, A2, A3 and A2/A3 at `B_lo` are run (est. $600–900, 4–6 h).
* The **Laya latency/throughput benchmark** (1,200 checks, ~3 min of compute).

**Needs several scheduled sessions (3–5):**
* The **full 24×4×6 battery** — generation alone is 1.4 days of continuous compute across 8 streams.
* The **A5 budget sweep** (7 spend points × 3 sub-arms) — this is a separate large generation set and
  should be its own session block.
* The **multilingual/misroute stratum** on non-en/fr/de/es/pt/it/nl Latin-script and non-Latin-script
  tasks, with per-language calibration checks.
* The **grader-LM audit** (≥200 hand-labelled cells) and the **recovery/latency re-scoring pass** on
  frozen snapshots.
* The **question-type balance check**, which must be verified *after* generation because qtype was
  randomized at item level.

**Order of operations (locked):** (1) serializer + question bank + hashing → (2) calibration corpus →
(3) `τ*`/`s*` fit and freeze → (4) fault-validation → (5) pilot → (6) re-size the full design from the
pilot ICC → (7) full battery → (8) A5 sweep → (9) analysis per the pre-registered hierarchy.

---

## 7. Blocking questions for the team lead

1. **Is the efficiency claim about dollars or about latency/round-trips?** §1.6 argues dollars may not
   bind at 2026 prices. The answer changes the primary endpoint, the primary figure, and the abstract.
   Everything else in this document is written to survive either answer, but the paper should not.
2. **A1 must be funded before A5.** A1 is the most expensive non-A5 arm and is the floor for every
   typed-judge claim. If the budget forces a cut, cut A5a before A1.
3. **Verify the Jev marginal price assumption** (§6.1). If Jev meters per call, its "unbounded checks"
   advantage disappears and A2's density claim must be re-derived.
4. **`tol`, `B_lo`, `B_hi`, `W`, and the 2% deviation predicate are all frozen constants** in this
   document: `tol = 0.05`, `B_lo = $0.10`, `B_hi = $1.00`, `W ∈ {512, 1024}`, deviation >2%. Changing
   any of them after data collection breaks the pre-registration.

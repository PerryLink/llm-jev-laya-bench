# D2 — Horizon-Scope Decision

**Unit:** D2 (horizon scope).
**Question put to this unit:** fund the horizon slope at ~1,900 items, demote it to a descriptive curve, or something in between.
**Inputs read:** [R9-final-specification.md](../recon/R9-final-specification.md), [V2-stats-audit.md](../recon/V2-stats-audit.md), [V4-battery-audit.md](../recon/V4-battery-audit.md), [R8-clamp-calibration-and-final-adjudication.md](../recon/R8-clamp-calibration-and-final-adjudication.md), [R14-long-horizon-battery.md](../recon/R14-long-horizon-battery.md), plus [V3-feasibility-audit.md](../recon/V3-feasibility-audit.md), [R5-synthesis.md](../recon/R5-synthesis.md) for the feasibility and claim-frame context.
**Status:** decision, not survey. One verdict, one design, one falsifier.

**Standing assumption about the parallel item-supply unit** (stated, not assumed silently — see Q3.4): that unit can plausibly relieve the authoring cost of *accuracy and calibration* items. It cannot relieve the *horizon* battery, because "distance from the planted poison" is defined by a run the authors execute and control. **No part of this decision depends on that unit's output.** If it returns something better than that, the escalation threshold in the design below moves; nothing else does.

---

## Q1 — What does the paper lose if the horizon slope is demoted to descriptive?

### 1.1 Concretely, what changes

| Location | Current wording (R9 §6 skeleton, R5 §0 headline) | After demotion |
|---|---|---|
| **Title / subtitle** | "…成本不是约束，静默退化才是" ("cost is not the constraint; silent degradation is") | **Unchanged.** The silent-degradation evidence is the per-checkpoint clamp + unalerted damaged interval ([R8 §1.5](../recon/R8-clamp-calibration-and-final-adjudication.md)), not the slope. |
| **Abstract, claim 1** (judgment-layer comparison, not agent comparison) | as written | **Unchanged.** |
| **Abstract, claim 2** (cost is not the constraint, qualified by mode) | as written | **Unchanged.** The per-token cost ladder is a synthetic state-length measurement ([V3 §5.5](../recon/V3-feasibility-audit.md)). |
| **Abstract, claim 3** (instrument self-reports untrustworthy) | as written | **Unchanged — and strengthened.** Per-checkpoint clamp (english 512 / multilingual 1024 / typed-decisions 1024) and the 111-character unalerted damaged interval are measured in 3 minutes per checkpoint, no generation battery ([R8 §1](../recon/R8-clamp-calibration-and-final-adjudication.md)). |
| **Abstract, claim 4** (cross-species error complementarity, `Δ_catch` + κ) | as written | **Unchanged.** Does not use the horizon dial. |
| **Abstract / Results — any sentence of the form "judge accuracy degrades with horizon", "typed judges degrade faster as the horizon grows", "capability degrades silently *with horizon* as a causal claim** | must be **deleted** | Replaced by: *"On a fixed-width carrier over a frozen 128-junction run, the carrier's usable signal declines by X points across the dial. This curve is descriptive: the pre-registered minimum detectable divergence was Y points."* |
| **Results A** (cost) | as written | **Unchanged**, except every cost row already must be priced at that run's measured state tokens and drawn against horizon ([R8 §5](../recon/R8-clamp-calibration-and-final-adjudication.md)). |
| **Results B** (instrument honesty) | as written | **Unchanged.** This is the leg that carries the headline. |
| **Results C** (process quality: `P_detect(τ*)`, drift, compound error, recovery, B0) | as written | **Unchanged.** These are the corrected primary endpoint and none of them is the horizon slope. |
| **Results D** (cross-species complementarity) | as written | **Unchanged.** |
| **Discussion §10** ("both judges' economics degrade with horizon: silent truncation vs per-token price") | as written | **Unchanged**, because both halves are measured (truncation curve; per-token cost curve). The sentence that must go is any **attribution** sentence — "Z% of the decline is trace non-survival" — unless the mediation analysis is run (Q4 below makes it mandatory). |
| **Limitations §11** | T3, single device, Jev blocked, batching asymmetry, abstention | **Gains:** the declared MDE on the horizon curve; the non-generalization clause ("conditional on four authored families"); the F3 underdetermination-knob fix. |
| **Pre-registration / three forks (§7 fork 2)** | "fund ~1,910 or demote" | **Resolved** by this document. |

### 1.2 Does the "silent degradation" thesis survive on instrument honesty and truncation alone?

**Yes — with one connecting fact that is already free.**

The thesis has two parts, and only one of them was ever riding on the horizon slope:

1. **The instrument discards state silently.** Proven directly and per checkpoint: english clamps at 3,083 chars / 512 tokens while `truncated` first fires at 3,194 chars — a 111-character interval in which the answer has already flipped and every self-report field still says the state is fine; output then freezes at `noul = 0.3594` across 3,971→7,967 chars ([R8 §1.1](../recon/R8-clamp-calibration-and-final-adjudication.md)); multilingual's window is 2× english's and its warning arrives *with* the clamp, so "silent window" is itself a per-checkpoint measurable. Marginal cost: minutes, no battery, independently reproduced.
2. **Real long-horizon states exceed that clamp.** This is a claim about the *state-size distribution as a function of `t`*, i.e. `token_ratio(t)` on live run states. It is **not** an inferential slope and it is **not** a new experiment: it is a by-product of the generator runs the paper is already paying for.

Both halves survive untouched. What does **not** survive — and what was never in the abstract to begin with — is the *second-order* claim that judge accuracy on a fixed-width carrier declines with distance from a trace. That claim is the only one that needs the dial, and the dial is broken (Q4).

**Conclusion for Q1:** demotion costs the paper one Results subsection's p-value column and two sentences of discussion. It does not touch the title, the abstract's four claims, the corrected primary endpoint, or any of the three evidence legs that need no generation battery ([V3 §5.5](../recon/V3-feasibility-audit.md); [R8 §2.7](../recon/R8-clamp-calibration-and-final-adjudication.md)).

---

## Q2 — Is the ~1,910 figure the right target?

### 2.1 The figure is arithmetically right, and it is the price of a target nobody pre-registered

Recomputing [V2 §3.2](../recon/V2-stats-audit.md) from its own inputs. Currency: `log2 H ∈ {0,2,3,5,7}`, `Σ(x−x̄)² = 29.2` per slot (5 items/slot), `SE(β̂) = √(ψ−Δ²)/√(Σ(x−x̄)²·s)`, `MDE₈₀,α=.05 = 2.8016·SE`, divergence `D` accumulated over the **7 doublings** from the floor to H=128, so `β = D/7`:

```
s (slots) = 7.849·(ψ−Δ²) / (29.2·β²)        N = 5s
N ≈ 66·(ψ−Δ²)/D²                              (with β = D/7)
```

Check: `ψ−Δ² = 0.2987`, `D = 0.10` → `N = 1,966`. V2 prints 1,910; the 3% gap is rounding inside their chain. Same 3% at D = 0.15 (V2: 849; recomputed 874) and D = 0.05 (V2: 7,639; recomputed 7,896). **The figure reproduces.**

I also checked whether the figure is an artifact of including the floor level, which [V2 B5/B6](../recon/V2-stats-audit.md) and [V4 §6.3(a)](../recon/V4-battery-audit.md) both flag as a poison/no-poison contrast rather than a horizon point. Fitting on H1–H4 only: `Σ(x−x̄)² = 14.75` per slot, range 5 doublings → `N ∝ R²/Σ = 25/14.75 = 1.695`, versus 49/29.2 = 1.678 for the five-level fit. **Identical to within 1%.** The floor is a red herring for the *N*; it matters for the *interpretation*, not the sample size.

### 2.2 Where the target comes from — and why 10 points is the wrong purchase

Two different bands are in play and [V2 §3.2](../recon/V2-stats-audit.md) merges them:

- **R14's own pre-registered target:** 0.04–0.05 accuracy per doubling = **28–35 points cumulative** ([R14 line 331](../recon/R14-long-horizon-battery.md)). At ψ = 0.30 this needs **244–252 items**. Both [V2 §3.2](../recon/V2-stats-audit.md) ("300 does support R14's declared target… under ψ ≤ ~0.45") and [V4 §7.4](../recon/V4-battery-audit.md) ("genuinely achievable at 300 items") independently confirm that **the design as pre-registered is already powered**.
- **The audit's re-target:** "the effects the paper is actually about are 5–15 points" → 10 points → 1,910 items.

So the ~1,910 figure is **the right price for a target that was never pre-registered**. It is not a strawman in *magnitude* — 10 points is the midpoint of R14's stated narrative band — but it is a strawman in *provenance*: it prices an effect size the design never committed to, and then reports the design as underpowered against it.

### 2.3 The two corrections that actually move the number

**(a) The 57% inert fraction.** [V4 §1.4](../recon/V4-battery-audit.md): 170 of 300 keys depend only on the local block. Let λ = the live fraction. A pooled fit attenuates the coefficient by λ while carrying all the noise, so `t ∝ λ√N`; a live-only fit has `t ∝ √(λN)`. Live-only is therefore `1/√λ = 1.53×` more efficient, i.e. **equally powered with `1/λ = 2.33×` fewer items.** But the price of a 10-point *live-item* divergence in a *pooled* design is `N_pool = N_live/λ`.

| Target divergence *on live items* | N at λ = 1 | N authored at λ = 0.43 (current dial) | N authored at λ = 0.90 (after Q4's certificate rebuild) |
|---|---|---|---|
| 10 points | 1,970 | **4,580** | 2,190 |
| 15 points | 877 | 2,040 | 974 |
| 20 points | 493 | 1,147 | 548 |
| 28 points (R14's own target) | 252 | 586 | 280 |

The inert items are worse than neutral: [V4 §1.4](../recon/V4-battery-audit.md) says any measured drift on them is a *distractor* effect — the carrier making an answerable question harder. They bias the pooled slope toward zero *and* destroy the placebo. **On the dial as built, the honest price of a 10-point divergence is ~4,600 authored items, not 1,910.**

**(b) Identification costs variance.** The repair that removes the `d ≡ H−4` confound is the within-item `L` vs `L+C` carrier-lift pair ([V4 §1.3](../recon/V4-battery-audit.md), [R8 §3.1](../recon/R8-clamp-calibration-and-final-adjudication.md)). Its per-item variance is `ψ_lift − lift²` with `ψ_lift ≈ 0.45`, `lift ≈ 0.22` → `ψ_eff ≈ 0.40`, against 0.30 for the judge-divergence contrast. Substituting into the same formula:

```
N ≈ 88·(ψ_eff − Δ²)/D²      (identified lift estimand, ψ_eff = 0.40)
```

| Target divergence (identified estimand) | N at λ = 1 | N at λ = 0.90 |
|---|---|---|
| 10 points | 2,630 | 2,920 |
| 15 points | 1,170 | 1,300 |
| 20 points | 658 | **731** |
| 25 points | 421 | 468 |

**The repair buys identification, not power.** Reaching the midpoint of the paper's own 5–15 point band on an *identified* estimand costs ~2,900 items — more than the 1,910 that started this decision. That is the decisive arithmetic finding of this document.

### 2.4 Answer to Q2

- The ~1,910 figure is correct, and it is **not** the right target — but not because 10 points is too small. It is wrong because (i) it prices an effect nobody pre-registered, (ii) it assumes 100% live items when the dial delivers 43%, making the true price ~4,600, and (iii) it prices the *confounded* estimand, so at any N it would buy an uninterpretable number.
- The honest expectation: if a divergence exists, it is somewhere in R14's 5–15 point narrative band *or* its 28–35 point pre-registered band, and **the design as pre-registered can only speak about the upper half of that range**. The correct move is not to fund N for 10 points; it is to **pre-register the MDE you can afford, in the currency of the identified estimand, and print it on the figure.**
- Any N chosen now is provisional: it must be re-derived from the pilot's measured ψ and certified-live fraction ([R9 P7](../recon/R9-final-specification.md) already provides that mechanism).

---

## Q3 — Can the item supply come from somewhere other than hand authoring?

### 3.1 Programmatically generated items with computed ground truth

**This is already the design, not a proposal.** [R14 §6 T1](../recon/R14-long-horizon-battery.md) restricts every label to "an execution, a static predicate, a simulator, or an authoring-time record"; F1's keys are pytest node ids / AST predicates, F2's are a coverage function over annotation records, F3's are row-hash diffs plus 34 SQL assertions, F4's are rule-engine reachability. Programmatic *label* generation is therefore free to scale. What does not scale is the *input*: the documents, claim tuples, and alert records that a human authors, plus the certificates below.

**Can support:** slope/interaction inference on the carrier-lift estimand at arbitrary N; the whole accuracy/calibration population. **Cannot support:** generalization beyond the authored families (governed by the number of families, not the number of items — [V2 §3.2](../recon/V2-stats-audit.md), [V4 §7.4](../recon/V4-battery-audit.md)); and — the killer — **derivability**. A mechanical key does not make the item answerable from the state the judge sees ([R14 T3](../recon/R14-long-horizon-battery.md)). The gap is not closed by scale, and **scale makes it worse, because the artifact is correlated with the treatment**: higher `d` mechanically lowers the probability that the decisive trace is in the carrier, so every unanswerable-at-H4 item biases the slope downward. Automated generation multiplies a *biased* slope; it does not merely add noise. Scale-up is licensed only after the entailment + necessity certificates of [V4 §2.4](../recon/V4-battery-audit.md) are computed for 100% of items, and after G3b (symbolic baseline ≤ 0.80 over printed fields) is run per class — otherwise you scale a class that a hand-written rule solves.

### 3.2 Synthetic long-horizon traces by concatenation with injected faults

**This is the right instrument for the wrong claim — and the right instrument for the headline.** Concatenating short public items and injecting faults makes the terminal oracle a sum/product of per-segment scores. That is exactly [R14 §2](../recon/R14-long-horizon-battery.md)'s definition of "many steps, not long-horizon": LH-1 fails *by construction*, and a judge that catches a fault locally becomes indistinguishable from one that tracks global consistency. So it **cannot** support the horizon claim at any N — and [R14](../recon/R14-long-horizon-battery.md) already reached this verdict, which is why `F4-CTRL` exists as the horizon placebo.

It **can** support, at negligible cost: the M2 instrument-honesty and per-checkpoint clamp curves; the latency and cost ladders against a state-length grid; high-cardinality saturation; format adherence. That is three of the paper's four headline legs ([V3 §5.5](../recon/V3-feasibility-audit.md)). Use it there, label it a placebo in the horizon section, and never pool it.

### 3.3 Reuse of public labelled data

**Can support:** the marginal accuracy contrast and the calibration curve (the ≥1,000-item population), i.e. "is a 421M typed judge competitive on typed questions". **Cannot support the horizon claim**, because `d` is *defined* by a run the authors execute; public data has no planted upstream error and no junction index. Three hazards to state before reuse: (i) **contamination asymmetry** — public items sit in the generative judge's pretraining and largely not in the 421M checkpoint's, biasing *toward the paper's comparator and against its own subject*; [R14](../recon/R14-long-horizon-battery.md) requires an n-gram/embedding contamination search for its fictional corpora and that protection does not exist for public data; (ii) most public process-supervision labels are *human-judged step labels*, which reintroduce the circularity [R14 T1](../recon/R14-long-horizon-battery.md) exists to prevent; (iii) public labels are not typed-question labels (`noul`/`choice`/`check` with a declared boundary), so a mapping layer becomes a new construct that itself needs validation.

One genuinely promising variant: **public runnable repositories with regression suites** (SWE-bench-shaped). These supply an executable oracle *and* accept an author-planted fault at a chosen junction — i.e. programmatic input supply for the horizon battery itself. Contamination still applies, but it biases the judge-gap estimate, not the truncation measurement.

### 3.4 Explicit assumption about the parallel unit

I assume: it will deliver useful labelled items for the **accuracy/calibration** population and will materially cut authoring there; it will **not** deliver `distance-from-poison` labels; and its timeline is unverified. I therefore make no part of the horizon decision depend on it. If it returns a re-runnable long-horizon agent corpus with per-junction executable labels, the escalation threshold below moves down and 1,200 becomes the funded N rather than the conditional one.

---

## Q4 — What is the minimum design that still supports a defensible horizon claim?

### 4.1 The two fixes that must happen at *any* N (and are nearly free)

These are not optional and are not substitutes for each other:

1. **Promote the `L` vs `L+C` carrier-lift pair to the primary horizon estimand, on every item.** [R14 §4.3](../recon/R14-long-horizon-battery.md) already specifies the instrument; [V4 §1.3](../recon/V4-battery-audit.md) and [R8 §3.1](../recon/R8-clamp-calibration-and-final-adjudication.md) both rule it the fix. Trace presence is manipulated **within item**, so the `d ≡ H − 4` collinearity stops being a confound. Cost: one extra judge call per item per judge.
2. **Add the `H4-refreshed` cell** (long position, fresh trace; buildable from F1's own detection-delay knob, [R14 line 111](../recon/R14-long-horizon-battery.md)) to break position-vs-distance directly ([V4 §1.3](../recon/V4-battery-audit.md)).

Plus three mandatory corrections already ruled on: the floor reads off the poisoned run's own J1 ([V4 §6.3(a)](../recon/V4-battery-audit.md)); `d` is declared per family with each family's own injectable junction ([V4 §6.3(b)](../recon/V4-battery-audit.md)); trace survival is analysed as a **mediator, not a filter** — the `survives`-only primary is deleted because it conditions on a post-treatment variable ([V4 §2.3](../recon/V4-battery-audit.md)).

### 4.2 The leverage that is cheaper than N

**Raising the certified-live fraction from 0.43 to ~0.90 is worth 2.1× in effective N — the equivalent of ~1,100 free items** (§2.3 table). The instrument is the build-time **necessity certificate**: delete the decisive carrier line; if ≥2 keys remain consistent with the shipped state, the item was answerable from `LOCAL` alone and is a free item, excluded ([V4 §2.4](../recon/V4-battery-audit.md)). This is *redesign* effort, not *scale* effort, and it is the single highest-return item in this document.

### 4.3 The recommended minimum design

| Element | Specification |
|---|---|
| **Families** | **4** (restore F3 — [R8 §3.5](../recon/R8-clamp-calibration-and-final-adjudication.md) item 12; F3 carries the only true step-irreversibility mechanism) |
| **Slots** | **120** (30 per family) |
| **Horizon levels** | **5** — floor J1 read off the poisoned run, then H1/H2/H3/H4 at the family's own injectable junction; `x = log2 H = {0,2,3,5,7}` |
| **Items** | **600** primary instances (120 slots × 5 levels) |
| **Variants** | **both `L` and `L+C` on all 600** → 1,200 judge-facing states per judge |
| **Extra cell** | **+120** `H4-refreshed` instances (×2 variants) → 1,440 states per judge |
| **Frozen runs** | **120 slot-runs** (one generator run per slot, poison installed at that family's junction, log frozen), H0 read off the same run |
| **Judges** | all on all items, paired by item; one pre-specified LLM reasoning effort primary, others secondary |
| **Primary estimand** | **carrier-lift × log2(H)** on the **certified-live** stratum (pre-register live ≥ 0.85; if the pilot certifies < 0.70, the slope falls back to descriptive — pre-registered, decided before data) |
| **Pre-registered MDE** | **≈0.22 cumulative divergence** (≈22 points) at ψ_eff = 0.40, λ = 0.90 — printed on the figure, in the abstract, and re-derived from the pilot |
| **Inferential secondary** | **carrier-lift main effect**: 540 live pairs × 2 variants → MDE ≈ **8 points** (ψ_lift = 0.45). This is *inside* the paper's declared 5–15 point band and is the paper's real gain from the repair. |
| **Descriptive** | raw accuracy × log2(H), cluster-bootstrap bands, **no p-value**; the inert stratum reported as a distractor placebo |
| **Escalation (pre-registered)** | if the pilot shows ψ_eff ≤ 0.35 **and** certified-live ≥ 0.85, extend **+120 slots → 1,200 items** (MDE ≈ 15 points, the first N whose resolution enters the paper's own band). **Hard cap at 1,200. Do not fund 1,910.** |
| **Required at build** | entailment + necessity certificates on 100% of items; G3b symbolic baseline ≤0.80 per class; F3's difficulty knob re-specified from *underdetermination* to *inference depth* with every item shipping a disambiguating clause |

### 4.4 Cost of the recommended design

- **Machine time:** generation 120 runs × 128 junctions = 15,360 steps at [V3's measured 9.6 s/step](../recon/V3-feasibility-audit.md) → 41 h serial → **≈2.6 h at 16 streams**. Judge calls ≈ 5,760–7,200: Laya 1,440 × 37.4 ms ≈ 1 min; LLM structured replay 1,440 × 3.0 s → 1.2 h serial → minutes parallel; A0 free (inside generation); Jev blocked. **≈3–4 h total**, against V3's ~23 h for the full programme. **Machine time is not the cost of this decision.**
- **Elapsed time:** the cost is the **120 slot specifications** plus certificates, mediation analysis, and the certificate tooling. Against R9's P3.5 (item generation and annotation, previously unclaimed and the largest hidden human cost): **+2 to 3 weeks over the 300-item baseline → ≈7–11 weeks total**, on V3's 5–9 week baseline. This is a 30–50% schedule increase for a claim that is not the headline — which is why the funded N is 600 and not 1,200.
- **Dollars:** negligible; the programme is under $2,000 with a ~20× margin ([V3 §2.3](../recon/V3-feasibility-audit.md)).

### 4.5 Exactly which claim each reduction weakens

| Reduction (from the ~1,900-item ideal) | Claim it weakens |
|---|---|
| 600 instead of 1,900 | The divergence claim drops from "≥12 points detectable" to "**≥22 points detectable**". The paper can no longer say anything about divergences of 5–20 points. **This is the whole cost of the intermediate.** |
| Live-stratum primary instead of pooled | Family- and class-level comparisons lose their already-thin effective n (15 per family) — they were pre-registered as descriptive anyway ([R14 §4.5](../recon/R14-long-horizon-battery.md)). |
| No 1,900-item extension | Nothing at all is lost that the paper's abstract claims. The 1,900-item design would itself need the same certificate rebuild and would still be conditional on four authored families. |
| Demotion to descriptive (the fallback if the pilot certifies live < 0.70) | The second-order claim "judge accuracy declines with trace distance" loses its inferential status entirely. The first-order claim (the instrument discards state silently) is untouched (Q1). |

**Answer to Q4:** 600 items, 5 levels, 120 frozen slot-runs, both variants, plus the `H4-refreshed` cell, with a pre-registered 22-point MDE and a conditional escalation to 1,200. Defensible inferential claim at that N: *"the carrier's usable signal does not decline by less than 22 points across the dial; the measured decline is X (95% CI …), and the carrier-lift main effect of Y points (95% CI …) is itself significant."*

---

## Q5 — The reviewer test

**Honest answer: it depends on whether the curve is *supplementary* or *load-bearing*, and on where the disclosure sits.**

**Case A — the curve is supplementary and the resolution is printed on it: accepted.** A competent reviewer objects to unsupported claims, not to declared resolution. A curve with cluster-bootstrap bands, a pre-registered MDE drawn as a reference line on the figure, and no inferential language reads as a measurement. This is standard in characterization work, and [R5 §6](../recon/R5-synthesis.md) already lists "SAFE = measurement/characterization" as the paper's own defensible fallback.

**Case B — the curve is asked to carry "silent degradation with horizon": reads as underpowered, and worse, as evasive.** The failure mode is not the missing p-value. It is a *causal-sounding title plus a descriptive curve plus an undisclosed confound*. If the paper declines the inferential claim without disclosing that `d = H − 4` was perfectly collinear, the reviewer supplies the confound themselves and reads the omission as concealment. That is the one outcome that damages the paper rather than merely limiting it.

**Three things make the difference, and all three are cheap:**

1. **Put the disclosure in the abstract, not the limitations.** R9 §6's abstract already carries "instrument self-reports are untrustworthy" — which is a *finding*, not an apology. Add one sentence in the same register: "the horizon divergence is reported descriptively; the pre-registered minimum detectable divergence is 22 points." Reviewers forgive a declared limit and punish a discovered one.
2. **Make the demotion look like a design decision, because it is.** The paper is not declining to test the horizon; it is declining to spend 6× the authoring budget on a manipulation whose dose variable was identical to its nuisance variable. That is a *methodological* contribution a reviewer can respect — and [V4](../recon/V4-battery-audit.md) and [R8](../recon/R8-clamp-calibration-and-final-adjudication.md) already rule it the fix.
3. **Keep an inferential horizon-adjacent claim.** The carrier-lift main effect at 540 live pairs (MDE ≈ 8 points) is an *inferential* claim about the paper's mechanism, inside the paper's own 5–15 point band, and it costs one extra judge call per item. A paper with four inferential claims and one descriptive curve does not read as underpowered. A paper with one descriptive curve where its thesis used to be reads exactly that way.

**One foreseeable review question and its answer.** A reviewer who recomputes will ask: "a 10-point divergence needs ~1,900 items; why 600?" The answer must be complete and short: *because 600 was funded for a 22-point target on an identified estimand, the paper never claims a 10-point effect, and funding 1,900 would have bought a 5× larger sample of a confounded manipulation.* That answer holds only if the paper contains no sentence implying it could resolve small divergences. If one such sentence survives into the abstract, the demotion does read as an admission.

---

## RECOMMENDATION

**INTERMEDIATE at N = 600.**

The ~1,910 figure reproduces to within 3% and is the price of the wrong purchase. On the dial as built, 170 of 300 items (57%) cannot respond to the manipulation; [V4 §1.4](../recon/V4-battery-audit.md) shows they are not neutral filler but a distractor biasing the pooled slope toward zero. Correcting for that puts the honest price of a 10-point divergence at ~4,600 items, not 1,910. And `d ≡ H − 4` makes distance-from-poison and run position perfectly collinear, so at *any* N the slope is uninterpretable. **N does not fix a collinear design.** Buying 1,900 items before fixing the dose variable spends 6× the authoring budget — the binding constraint, since machine time is 3–4 hours — on a number a reviewer rejects on sight.

Demotion alone is also wrong: the paper does not need to buy its horizon claim back, because it never sold it. The abstract's four claims (judgment-layer comparison; cost is not the constraint; instrument self-reports untrustworthy; cross-species complementarity) survive untouched — three of the four evidence legs need no generation battery. What demotion costs is the `L`/`L+C` repair, which turns a **within-item, identified** manipulation into an inferential claim for one extra judge call per item.

So: repair the dial, certify items live, and pre-register the resolution you can afford. 600 items buys a 22-point divergence claim on an identified estimand **and** an 8-point carrier-lift main effect — the latter inside the paper's own 5–15 point band. Escalate conditionally to 1,200 (MDE ≈ 15 points) only if the pilot certifies ψ_eff ≤ 0.35 and live ≥ 0.85. Hard cap there: beyond it, 700 more items buy 3 points of resolution and change no sentence the paper can write.

*(≈300 words)*

---

## The concrete design that follows

Adopt §4.3 verbatim as the pre-registration. In execution order:

1. **P3.5a — slot construction (before any judge call).** 120 slots, 30 per family, 4 families. Each slot: one local block, one junction at the family's own injectable junction, one key computed by that family's oracle, two carrier variants (`L` filled with frozen no-op lines, `L+C` carrying the decisive line), one `H4-refreshed` variant.
2. **P3.5b — certificates (blocking gate).** Entailment (does the shipped state entail the key under the family's inference rules?) and necessity (delete the decisive line — does ≥2 keys remain consistent?) on 100% of items. Report certified-live fraction. **Gate: live ≥ 0.85, else escalate the item rebuild, else pre-registered fallback to descriptive.** G3b symbolic baseline ≤ 0.80 per class.
3. **P6 — generation and freezing.** 120 slot-runs with the poison installed; freeze logs; H0 extracted from the same run's J1.
4. **P7 — pilot.** Measure ψ_eff, λ, and the lift main effect on a subset; re-derive N; apply the published escalation rule.
5. **P8 — collection.** All judges on all 1,440 states, paired, byte-identical, forced choice.
6. **P11 — analysis, in this order:** carrier-lift main effect (inferential) → carrier-lift × log2(H) on the certified-live stratum (inferential, MDE printed) → trace survival as a **mediator** → raw accuracy × log2(H) (descriptive, bands, no p) → inert stratum as distractor placebo.
7. **Deletions this decision forces:** the `survives`-only primary analysis; the +375-item escape hatch (superseded by the escalation rule above); the F3 underdetermination knob; any sentence of the form "judge accuracy degrades with horizon" in the abstract, results, or title.

---

## WHAT WOULD CHANGE MY MIND

**Move to FUND 1,900 if** (a) the parallel item-supply unit returns a re-runnable long-horizon corpus with per-junction executable labels and a controllable poison junction, cutting slot authoring by more than 3× — then the 6× authoring argument collapses and only the identification argument remains, which the repair handles; **or** (b) the P7 pilot certifies ψ_eff ≤ 0.25 **and** live ≥ 0.95, in which case 1,900 items buys ~8 points — inside the paper's band — for the first time; **or** (c) a funder or reviewer commits in advance to treating the horizon divergence as the paper's primary contribution, which changes which claim must be inferential.

**Move to DEMOTE TO DESCRIPTIVE if** (a) the certificate gate returns a certified-live fraction below 0.70 on the rebuilt items — then the manipulation is measuring item construction, not judgment, and no N fixes that; **or** (b) the elapsed-time budget tightens below 6 weeks, since 2–3 weeks of slot construction is the entire cost of the intermediate and the horizon curve is not load-bearing; **or** (c) F3's underdetermination knob cannot be re-specified as inference depth with every item shipping a disambiguating clause — then one of four families manufactures unanswerable keys and the pooled slope inherits it.

**Move the funded N within the intermediate if** the pilot's measured ψ_eff lands outside 0.30–0.50, or if the certified-live fraction lands between 0.70 and 0.85, in which case the escalation rule's thresholds must be re-derived before P8 rather than after. The one move I would resist at all three branches: locking 1,900 items now, before the certificates exist. That spends the scarce resource — authoring — on items whose live fraction and derivability are, at this moment, unknown.

# V2 — Adversarial audit of the statistical and causal validity of the merged design

**Unit:** V2 (statistical / causal verification, second round).
**Target of audit:** [R5-synthesis.md](R5-synthesis.md) (the merged design), with [R15-arms-and-process-metrics.md](R15-arms-and-process-metrics.md), [R14-long-horizon-battery.md](R14-long-horizon-battery.md), [R3-corrected-economics.md](R3-corrected-economics.md) as the inputs it merges.
**Method:** every number below was recomputed from the standard formulae at the stated inputs; every verdict is tied to a file and line. I did not modify any other file. Where I agree with a unit, I say so explicitly — agreement is not the deliverable.
**Stance:** the design contains one genuinely excellent decision (the two-plane replay, [R15:40-63](R15-arms-and-process-metrics.md#L40-L63)) and one genuinely broken primary endpoint. The endpoint is broken in *both* directions, which is why it is the lead finding.

---

## 1. Is `T90` well-defined and identifiable?

### 1.1 It is defined three different ways

| Where | Definition | Conditioning clause |
|---|---|---|
| [R15:430-433](R15-arms-and-process-metrics.md#L430-L433) | `T90(m, arm)` = first step at which the judge's cumulative detection probability reaches 0.90 = inverse of `F_m(t) = P(t_E ≤ t)`, computed on **measurement-plane replay verdicts** | "fully crossed with the online schedule" |
| [R15:452](R15-arms-and-process-metrics.md#L452) | "Pre-registered primary endpoint: `T90` at matched judgment dollars." | matched **dollars** |
| [R5:152](R5-synthesis.md#L152) | "主终点：`T90`（检测概率达 0.90 的步数），**在匹配顺序往返下**" | matched **sequential round-trips** |
| [R15:683-684](R15-arms-and-process-metrics.md#L683-L684) | Gate 1: "one endpoint (`T90` lead time, matched judgment dollars)" | dollars, and `T90` is called "lead time" |

The third is not merely a different sentence — it is not realizable. A typed judge's defining property is that it needs **zero** extra round-trips per checkpoint (fused or local), while `A1` needs one and `A5b` needs one per eight ([R15:116-137](R15-arms-and-process-metrics.md#L116-L137), [R15:316-320](R15-arms-and-process-metrics.md#L316-L320)). Round-trip count is a property *constituted* by the arm; it cannot be a matching stratum. "Matched round-trips" either means nothing or collapses to "within arm".

### 1.2 What the treatment contrast actually compares

Write the estimator out. For arm `a`, run `r`, step `t`:

```
S_{a,r}(t)   state at t, written by the harness   (arm-dependent)
j(a)         the judge the arm schedules online
π_a          the arm's control policy: when a verdict ∈ {revise,halt} rewrites the prompt
V_j(·)       judge j's verdict function, replayed offline on frozen snapshots

t_E(a,r) = min{ t ≥ t_0(r) : V_{j(a)}( S_{a,r}(t) ) ∈ {revise, halt} }
F_a(t)   = P_r( t_E(a,r) ≤ t )
T90(a)   = inf{ t : F_a(t) ≥ 0.90 }
```

The Gate-1 contrast `T90(A3) − T90(A1)` is therefore

> [90th-percentile first-flag step of **Laya**, measured on **Laya-governed trajectories**] − [same for the **LLM**, measured on **LLM-governed trajectories**].

Three things move together inside that difference and are not separable in the pre-registered analysis:

1. **Judge identity** (`V_Laya` vs `V_LLM`) — the quantity the paper is about.
2. **Control policy and trajectory** (`π_a`, hence `S_{a,r}(·)`): the online verdicts of the *scheduled* judge cause `revise` re-prompts, so snapshots differ across arms. `t_E` is a functional of the trajectory, not only of the judge.
3. **Fault survival and run length**: `t_final(r)` differs by arm ([R15:33](R15-arms-and-process-metrics.md#L33): `halt` aborts the run), and whether F reaches 0.90 within the horizon is therefore an arm property.

So the estimand of the primary endpoint is an **ITT effect of the arm bundle**, while the claim the paper makes ("typed judges detect failures earlier") is about the **judge**. The design contains the data to separate them — every judge is replayed on every snapshot ([R15:46-50](R15-arms-and-process-metrics.md#L46-L50)) — but the pre-registered endpoint uses the confounded version. The ambiguity is not rhetorical; it is the difference between two numbers.

### 1.3 `T90` is not estimable for the arms of interest

`T90` exists only if the *observed* detection CDF reaches 0.90. With `R15`'s own sample size (96 runs per arm, 576/6), that requires ≥ 87/96 = 90.6% of runs to detect within the horizon. Binomial recomputation:

| true within-horizon detection probability | P(observed CDF reaches 0.90) = P(T90 defined) |
|---|---|
| 0.80 | **0.004** |
| 0.85 | **0.075** |
| 0.88 | 0.271 |
| 0.90 | 0.505 |
| 0.92 | 0.762 |

Any judge whose true detection rate is below ≈0.88 has an undefined `T90` with probability >0.73. The design's own thesis is that some judges *fail* to detect — that is the horizon story ([R15:485-490](R15-arms-and-process-metrics.md#L485-L490)). The primary endpoint is thus undefined precisely in the cells that carry the paper's claim, and its non-existence is not expressible as a value (it is not "T90 = 120"; it is "no such step"). Right-censoring language ([R15:659-661](R15-arms-and-process-metrics.md#L659-L661)) does not fix this: censoring is handled, a censored quantile that never resolves is not.

A second, independent definability bug: `F_m(t) = P(t_E ≤ t)` indexes **absolute step**, but onset `t_0 ∈ {10,30,60}` is randomized ([R15:536-539](R15-arms-and-process-metrics.md#L536-L539)). The CDF is therefore a mixture of three shifted distributions, and `T90` is a property of the onset mixture, not of the judge. The correct index is `τ = t − t_0`.

A third: the reported summary `LEAD(r) = t_final(r) − t_E(r)` ([R15:428-429](R15-arms-and-process-metrics.md#L428-L429)) is **a function of the judge's own halt action**. A judge that halts at detection sets `t_final ≈ t_E` and scores `LEAD ≈ 0`; a judge that detects at the same step and does nothing scores the maximum. `LEAD` is stated "Large is better" ([R15:426](R15-arms-and-process-metrics.md#L426)) while `T90` is better when smaller — the two headline summaries rank halt-happy judges in opposite directions, and neither is a monotone function of the other.

### 1.4 Minimal re-specification

1. Anchor detection on `τ = t_E − t_0`, never on absolute `t`; report the onset strata separately.
2. Split the estimand in two, pre-registered as such:
   - **JUDGE (primary for judge claims, and paired):** on a **single frozen snapshot population** (the `S0`/`A1` trajectory set), compute each judge's cumulative detection probability at a fixed pre-specified `τ*` (e.g. `τ* = 10`). All judges see the same states, so this is a within-snapshot contrast and it is schedule-free.
   - **ARM ITT (primary for schedule/policy claims):** the same statistic computed on each arm's own snapshots with its own judge.
3. Replace the 0.90 quantile with the fixed-`τ*` cumulative probability (or restricted mean detection time). Add a pre-registered rule for prevention: a fault removed by an earlier `revise` must be credited by a stated rule, not by the absence of a detectable fault.
4. Replace `LEAD` with `τ` or with `min(t_final, T) − t_E` at a fixed horizon `T`, so the judge cannot destroy its own lead time by halting.
5. Reinstate the schedule factor in the arm table. [R15:362-364](R15-arms-and-process-metrics.md#L362-L364) correctly declares the schedule *crossed* with the judge; [R5:136-144](R5-synthesis.md#L136-L144) collapses that crossing into one arm per judge, which is exactly what makes judge and policy inseparable.

**VERDICT: unsound.** The endpoint as pre-registered cannot be the primary. Minimal fix: the two-estimand split in §1.4 items 1–3 above, with `τ`-anchored, fixed-`τ*` detection probability replacing the 0.90 quantile.

---

## 2. Fault injection manufactures the very signal being measured

### 2.1 The overlap is real and structural

[R15:534-620](R15-arms-and-process-metrics.md#L534-L620) injects five fault classes plus `B0`. [R14](R14-long-horizon-battery.md) plants poisons in the same four families, and the **horizon knob is the distance to that poison** ([R14:396-405](R14-long-horizon-battery.md#L396-L405)). The mapping is nearly one-to-one:

| `R15` fault class | `R14` planted poison |
|---|---|
| F1 wrong assumption planted early | F1 §7.2 residual reading at J4 ([R14:101-105](R14-long-horizon-battery.md#L101-L105)) |
| F3 contaminated source | F2 `C-11 = SUPPORTED` from a tier-1 span at J8 ([R14:128-129](R14-long-horizon-battery.md#L128-L129)) |
| F5 subtle unit/scale error / F4 spec change | F3 `+00:00` stored as-is at J12 ([R14:147-149](R14-long-horizon-battery.md#L147-L149)) |
| — | F4 early false negative pruning an audit subtree at J6 ([R14:167-169](R14-long-horizon-battery.md#L167-L169)) |

And the *items* are authored from the same records that define the injected fault: F2's ground-truth label is "a deterministic function of the annotation table" ([R14:129-131](R14-long-horizon-battery.md#L129-L131)) — the same annotation records that create the planted contradiction; Q1's `CLAUSE` slot is the §7.2 clause that is itself the poison ([R14:243](R14-long-horizon-battery.md#L243) vs [R14:102-104](R14-long-horizon-battery.md#L102-L104)). Detectability is authored in by rule: "Same primary-span position: always inside the first 40% of the state" ([R14:417](R14-long-horizon-battery.md#L417)).

### 2.2 Is the *endpoint* circular? Yes, in the strict sense — but not the way `R14` guards against

`R14`'s anti-circularity rules (R0/R1, [R14:65-69](R14-long-horizon-battery.md#L65-L69); T1, [R14:442](R14-long-horizon-battery.md#L442)) genuinely close the *label* channel: no model supplies a label. That is sound.

The primary endpoint is circular through a different door. `t_E` is defined as

```
t_E = min{ t ≥ t_0 : verdict at t ∈ {revise, halt} }
```

with **no requirement that the flag identify the injected fault** ([R15:428](R15-arms-and-process-metrics.md#L428)). Since the fault *is* injected at `t_0` by the harness, and the state changes discontinuously there, and the serializer puts the newest material at the head ([R15:69-70](R15-arms-and-process-metrics.md#L69-L70)), the degenerate strategy "flag the newest thing at every checkpoint" attains `t_E = t_0 + 1` — the minimum possible `T90` and the maximum possible `LEAD`. The endpoint therefore measures *the harness's edit* at least as much as the judge. (This is the same defect that makes `B0` inoperative; see §6.)

### 2.3 A second, admitted circularity in the schedule dimension

[R15:614-616](R15-arms-and-process-metrics.md#L614-L616): F5's propagation predicate is "the same deterministic predicate as `tri3`, so **the trigger schedule and the fault oracle agree by construction** — deliberate". An `S3` arm fires a mandatory probe exactly when the oracle says the fault is detectable, and the primary endpoint is "fully crossed with the online schedule". `S3`'s advantage on F5 is manufactured by construction. R15's mitigation is to say it will be "interpreted with that in mind" — that is not a control.

### 2.4 What would break the circularity

1. **Require oracle-matched detection.** A hit counts only if the verdict at `t_E` names/entails the injected fault's class or target (the `choice` question templates, [R15:104-105](R15-arms-and-process-metrics.md#L104-L105), can carry this). Without it, `T90` is satisfiable by an undirected flag.
2. **Hold out the fault templates from the item bank.** Freeze and hash the question bank and item states *first*; then generate fault instances with a script that has no access to them. The horizon knob then varies distance to a poison the item author never saw. R14's `T3` ([R14:446](R14-long-horizon-battery.md#L446)) is the same complaint from the other side; this is its constructive form.
3. **Make `B0` byte-identical in form to a fault.** Same field, same length, same appended rationale line, so "the harness edited something at `t_0`" carries no signal.
4. **Promote the natural-fault stratum** (`tri1`–`tri3`) and the `absent`-trace subset ([R14:427-432](R14-long-horizon-battery.md#L427-L432)) to co-primary: the thesis must replicate on faults the design did not author. R15 currently promises they will never be pooled with the injected stratum ([R15:627-634](R15-arms-and-process-metrics.md#L627-L634)) — which means the headline rests entirely on authored faults.
5. **Exclude or ablate trigger-aligned faults.** For `S3`, report endpoints with F5 removed and with `tri6` ablated (the latter is already promised, [R15:380](R15-arms-and-process-metrics.md#L380); the former is not).

**VERDICT: unsound.** The endpoint is satisfiable without identifying the injected fault and is partly manufactured by the trigger schedule. Minimal fix: fix (1) plus (3).

---

## 3. Sample size and power

### 3.1 Are the two derivations in conflict? Mostly not — they answer four different questions

| Claim | N | Question it actually answers | Re-verified |
|---|---|---|---|
| [R13:405](R13-laya-probe.md#L405) | 385 | one judge's accuracy to ±0.05, worst case p=0.5, **unpaired** | `1.96²·0.25/0.05² = 384.2` ✓ |
| [R13:405](R13-laya-probe.md#L405) | ≥500 | a within-judge reliability/ECE curve (10 bins × 50) | rule of thumb, no derivation given |
| [R13:405](R13-laya-probe.md#L405) | ≥1000 | comparing **two judges'** ECE | **no derivation anywhere**; assertion |
| [R13:405](R13-laya-probe.md#L405) | ≈390/arm | a 0.10 two-judge accuracy difference, **unpaired**, p≈0.5 | `(1.96+0.8416)²·0.49/0.01 = 384.6` ✓ |
| [R14:315-323](R14-long-horizon-battery.md#L315-L323) | 234 (floor), 300 (design) | the same 0.10 two-judge difference, **paired** McNemar, ψ=0.30 | recomputed exactly: 234 ✓ (77 / 155 / 312 / 391 / 469 at ψ = 0.10 / 0.20 / 0.40 / 0.50 / 0.60) |

So the only genuine head-to-head conflict is **390 vs 234**, and it is fully explained by pairing: the same items judged by every judge. R14's derivation is correct, its CI claim is correct (`1.96·√(0.29/270) = ±6.4pt` ✓), and power at n=270 is 0.862 (not the nominal 80%) ✓. There is no conflict to reconcile — but R5's reconciliation is nevertheless wrong in four ways:

**(a) A unit error that assigns R14's N to the wrong endpoint.** [R5:73-76](R5-synthesis.md#L73-L76) assigns R14's 300 to "horizon 斜率 / **检测提前量**" (detection lead time) and states "总条目 1000，其中 R14 的 300 条构成 horizon 子设计". R14's 300 are **decision-point items** (60 slots × 5 levels) powering a paired **accuracy** contrast. `T90` is a **run**-level survival quantile with its own N (576 runs, [R15:704](R15-arms-and-process-metrics.md#L704)). Items and runs are not one currency; R14 never mentions lead time and never powers it.

**(b) The calibration headline contradicts the design's own measurement rules.** [R5:74](R5-synthesis.md#L74) makes calibration a headline deployment conclusion at ≥1000 items. But [R14:450](R14-long-horizon-battery.md#L450) (T5) pre-registers "raw probabilities are **never** compared across judges" and computes ECE within-judge only; [R5:110](R5-synthesis.md#L110) rule 10 freezes "`confidence` 永不用于门控/阈值/路由"; and R13's own fact 8 ([R5:52](R5-synthesis.md#L52)) is that confidence 0.9981 appeared on the only wrong answer. R13's ≥1000 was specifically for the cross-judge ECE comparison that T5 forbids. Further, `A0` emits **no probability at all** ([R15:128-133](R15-arms-and-process-metrics.md#L128-L133) — a 3-way keyword map), so no five-judge calibration analysis exists.

**(c) The 1000 items do not exist.** R14's total inventory is 300 primary + 100 carrier-lift instances + 48 Jev-only = **448**. R5's 1000 requires 552 unspecified items with no classes, no ground truth, no gates and no power statement.

**(d) The cluster structure undoes the ≥1000.** ECE items are not independent: 5 levels per slot, shared lineage. Effective n ≈ 1000/(1+4ρ) = 625 at ρ=0.15, 455 at ρ=0.30 — below the ≥500 curve requirement at the design's own upper ICC.

### 3.2 Does 300 support a judge × log2(H) slope? Computed, not accepted

Levels are J ∈ {1,4,8,32,128} → predictor `log2(H) ∈ {0,2,3,5,7}`, h̄ = 3.4, and **Σ(h−h̄)² = 29.2 per slot** (over 5 levels). For a paired per-item correctness difference with variance `ψ − Δ²`:

```
SE(β̂) = √(ψ−Δ²) / √(29.2 · s)          s = number of slots
MDE₈₀,α=.05(β) = 2.8016 · SE(β̂)
```

| ψ | MDE per doubling, 60 slots (300 items) | required slots/items for R14's 0.04–0.05 target |
|---|---|---|
| 0.20 | 0.0292 | 31 slots / 156 items (for 0.050) |
| **0.30** | **0.0360** | **49 slots / 244 items (for 0.040)** |
| 0.40 | 0.0418 | — |
| 0.50 | 0.0469 | — |

**So 300 does support R14's declared target** — but only under ψ ≤ ~0.45 and only if the judge × horizon slope is homogeneous across families (no lineage random slope is pre-registered, and R14's own families predict heterogeneity: F1's poison surfaces at J96, F2's at J70, F4's at J6 — [R14:105](R14-long-horizon-battery.md#L105), [R14:129](R14-long-horizon-battery.md#L129), [R14:169](R14-long-horizon-battery.md#L169) — with 3–4 family clusters the between-family slope variance is unestimable). With 3 families ([R5:126](R5-synthesis.md#L126)), the interaction's SE is dominated by a variance component the model does not contain.

**The decisive point is that the target itself is enormous.** 0.04/doubling over a 7-doubling range is a **28-point** change in the judge gap. The effects the paper is actually about are 5–15 points — R14 says so itself ([R14:327](R14-long-horizon-battery.md#L327)). Required items for a judge gap that reaches `X` at H=128 and 0 at the floor:

| gap at H=128 | β/doubling | required items |
|---|---|---|
| 0.05 | 0.0071 | 7,639 |
| **0.10** | **0.0143** | **1,910** |
| 0.15 | 0.0214 | 849 |
| 0.20 | 0.0286 | 477 |
| 0.28 | 0.0400 | 244 |

So 300 items can only detect a horizon-dependent judge divergence of **≥25 points** across the whole range — 2–5× larger than any effect the paper claims to be about. The pre-registered extension rule (+75 slots = 375 items, [R14:331](R14-long-horizon-battery.md#L331)) reaches MDE 0.032/doubling = 0.23 cumulative, still nowhere near the regime of interest. **The horizon-slope test needs ≈1,900 items for a 10-point divergence; the pre-registered escape hatch is 5× too small.** Also, the slope as fitted mixes the floor level — which is read off a **clean run with no poison** ([R14:420](R14-long-horizon-battery.md#L420)) — into the same linear term, so the first interval (log2H = 0 vs 2) carries a poison/no-poison contrast, not a horizon contrast. Fit the slope on H1–H4 only.

### 3.3 `R15`'s own `T90` power statement is wrong

[R15:704-708](R15-arms-and-process-metrics.md#L704-L708): "Effective clusters ≈ 96 per arm **after a design effect of ~2.2** from task-level ICC ≈ 0.15. That detects a `T90` shift of ~0.35 SD … α = 0.05 (RI)".

Recomputed:

| Step | Claimed | Correct |
|---|---|---|
| runs per arm | 96 | 96 (576/6) ✓ |
| design effect, m=4, ρ=0.15 | 2.2 | **1.45** (DE=2.2 requires ρ=0.40) |
| effective n per arm | "96 after DE 2.2" | **66.2** |
| MDE at α=0.05 | 0.35 SD | **0.487 SD** |
| MDE at the pre-registered Gate-1 level (Holm: 0.05/5 = 0.01) | — | **0.594 SD** |
| runs needed for 0.35 SD at α=0.01 | 576 | **1,659** (2.9×) |
| MDE expressed in steps (SD 4.3–7.1 from R15's own 1.5–2.5 ↔ 0.35) | 1.5–2.5 | **2.1–4.2** |

The α is the load-bearing part: Gate 1 is Holm over five contrasts ([R15:683-684](R15-arms-and-process-metrics.md#L683-L684)), so the first test is judged at 0.01, and planning at 0.05 for any member of that family is anti-conservative. Under the corrected numbers the design is powered for a ~2–4-step lead-time difference, not 1.5–2.5, and needs ~1,660 runs to reach the claimed 0.35 SD.

**VERDICT: sound-with-fix.**
Minimal fix: (i) restate the four Ns against their four distinct endpoints and delete R14's 300 from every `T90` sentence in [R5 §3](R5-synthesis.md#L68-L76); (ii) either fund ≈1,900 items for the accuracy slope or demote it to a descriptive curve with a pre-declared MDE; (iii) correct the DE/n_eff/MDE/α arithmetic in [R15 §5.5](R15-arms-and-process-metrics.md#L704-L708) and re-size to ≈1,660 runs if 0.35 SD is the target; (iv) either drop the calibration headline or reconcile it with R14 T5 and R5 rule 10.

---

## 4. Clustering, the unit of analysis, and whether RI is licensed

### 4.1 The cluster count is undefined, and stated four different ways

| Source | Cluster count |
|---|---|
| [R15:669](R15-arms-and-process-metrics.md#L669) | "~24 task **families**" |
| [R15:732](R15-arms-and-process-metrics.md#L732) | "24 **tasks**" |
| [R5:126](R5-synthesis.md#L126) | "取 **3 族**" (3 families kept) |
| [R5:181](R5-synthesis.md#L181) | "**24 族** × 4 run × 臂" |
| [R14](R14-long-horizon-battery.md) | **4** families defined |

Every piece of few-cluster machinery hangs on this number: CR2 with a wild cluster bootstrap at the task level ([R15:671](R15-arms-and-process-metrics.md#L671)), task-level RI, and the "effective clusters ≈ 96 per arm" power claim. If R5's scope (3 families) governs, the cluster count is **3**, cluster-robust asymptotics are meaningless at 3 clusters, and "≥10,000 permutation draws" ([R15:675](R15-arms-and-process-metrics.md#L675)) is arithmetically impossible at the family level (3 families admit 3! = 6 label arrangements). If 24 tasks govern, R5 §5.1's 3-family scope is wrong.

### 4.2 The permutation does not mirror the randomization

[R15:673-675](R15-arms-and-process-metrics.md#L673-L675) states both "Arms are randomized **within task family**" and "reassign arm labels **within task**" in consecutive sentences. A permutation test is valid only if the permutation distribution is generated by the actual assignment mechanism; a finer permutation than the design used does not test the design's null. **Fix:** pre-register the exact randomization (block = task, 4 runs per arm per task, the realized assignment and its seed stored), and permute exactly that.

### 4.3 The randomization does not license RI for the **judge** contrast

The measurement plane replays **all five judges on every snapshot** ([R15:46-50](R15-arms-and-process-metrics.md#L46-L50)). The judge factor is therefore a *within-unit* factor — every judge is measured on every unit — and permuting arm labels cannot move it. What arm randomization licenses is the ITT effect of the **arm bundle** on that arm's own trajectories. The pre-registered endpoint is the bundle (see §1.2), while the paper's claim is about the judge. RI is the right tool for the ITT and the wrong tool for the judge; using it for both, as [R15 §5.3](R15-arms-and-process-metrics.md#L669-L677) does, tests a null that is partly true by construction for the replayed verdicts. **Fix:** RI for the arm/ITT and schedule contrasts; a paired within-snapshot contrast (paired model, CR2 by task) for the judge contrast.

### 4.4 Ways the design's own replay/batching breaks exchangeability

1. **Shared generator state.** [R15:15-18](R15-arms-and-process-metrics.md#L15-L18) holds prompt, seed, tools and step budget identical across arms and [R14:436](R14-long-horizon-battery.md#L436) says the long-run generation is executed once and frozen because "re-running the generator for a second arm destroys the pairing". Consequences: (i) every prefix before the first judgment-driven `revise` is **byte-identical across arms** — the same material is counted in several arm groups, so units are not distinct, the permutation distribution is too narrow and p-values are anti-conservative; (ii) arms also differ in exposure (generator calls, state size, hence `t_trunc`), so the survival model compares unequal exposure. R15 logs `Δgen` as a covariate ([R15:390-392](R15-arms-and-process-metrics.md#L390-L392)) — correct — but a covariate does not restore unit exchangeability.
2. **Batching breaks snapshot parity, and therefore the replay.** `A5b` sends up to 8 checkpoint windows in one call ([R15:316-320](R15-arms-and-process-metrics.md#L316-L320)). (i) The "byte-identical state and question block" guarantee ([R15:59-63](R15-arms-and-process-metrics.md#L59-L63)) no longer holds: the effective state is an 8-checkpoint union that Laya cannot receive inside its 512-token window, so batching is available to the LLM and Jev but not to Laya — the `A5b` vs `A3` contrast is then a **state-content** difference, not a round-trip-density difference. (ii) Verdicts within a batch are mutually dependent, so the verdict at checkpoint `t` is not reproducible from `SNAP[run][t]` and checkpoint-level verdicts are not exchangeable across `t`. **Fix:** batch only in the control plane; always record the measurement verdict from the single-checkpoint snapshot; report `Δ_ctx = P(verdict | batched) − P(verdict | single)` as a pre-registered quantity.
3. **Step-level hypothesis test inside a run-level rule.** [R15:646-648](R15-arms-and-process-metrics.md#L646-L648) says "every hypothesis test is at the run level or coarser", but [R15:417-421](R15-arms-and-process-metrics.md#L417-L421) gives drift a step-within-run unit (`n = N_runs × N_step` ≈ 40,000) and states hypothesis H1 on it — and drift is in Gate 2's FDR family.

**VERDICT: unsound.** Minimal fix: fix the cluster definition in writing (task = cluster; family = 3-level fixed effect, reported descriptively), pre-register and store the exact within-task assignment, use RI only for the ITT/schedule contrasts, and make the batched-context effect an explicit measured quantity rather than an unmodelled difference.

---

## 5. Multiplicity and the three-gate hierarchy

**Is the hierarchy correctly specified?**

1. **Gate 2's family size is wrong.** [R15:686](R15-arms-and-process-metrics.md#L686): "the **seven remaining** metrics of §3". §3 has exactly seven subsections (§3.1–§3.7), and §3.2 *is* the primary family. **Six** remain. The BH family is therefore of unspecified size, and every adjusted q depends on it.
2. **The primary endpoint appears in more than one gate — yes.** §3.7 defines derived scalars `$ to T90` and `wall-clock to T90` ([R15:522-523](R15-arms-and-process-metrics.md#L522-L523)) and says scalar derived measures "get the same mixed-effects treatment as §5.4" ([R15:525-526](R15-arms-and-process-metrics.md#L525-L526)) — i.e. p-values, inside Gate 2 — while being functions of the Gate-1 endpoint. Additionally §3.2's `LEAD` and `AUC_detect` ([R15:433](R15-arms-and-process-metrics.md#L433)) are reported "plus" `T90` but assigned to no gate: if they fall into Gate 2, the same data are tested twice under two different corrections.
3. **Reporting order is not gatekeeping.** [R15:684-685](R15-arms-and-process-metrics.md#L684-L685) says no other endpoint may be reported as significant "before this family is reported in full". Hierarchical FWER control requires Gate 2 to be *conditional* on a Gate-1 rejection (or a closed/gatekeeper procedure). As written, FWER is not controlled across gates.
4. **`A4`'s contrast mixes estimands inside one Holm family.** Gate 1's five contrasts are A1-vs-A0 (a re-asking + format contrast), A2/A3-vs-A1 (judge identity), A4-vs-A1 (a *policy* effect, since A4 is adaptive escalation, [R15:236-249](R15-arms-and-process-metrics.md#L236-L249)) and "A5b/A5c vs A2/A3", which is a 2×2 of sub-arms, not one contrast. Holm requires a fixed, enumerated family; a 2×2 written as a slash is not one.
5. **The paper's most important claim is pre-registered as non-inferential.** [R5:22-25](R5-synthesis.md#L22-L25) fixes the honest headline as silent degradation with horizon. That claim's evidence is the `token_ratio(t)` curve and "detection probability **conditional on integrity(t)=1** degrades with horizon" ([R15:485-490](R15-arms-and-process-metrics.md#L485-L490)). Gate 3 puts curve figures and calibration variants in exploratory with **no p-values** ([R15:688-690](R15-arms-and-process-metrics.md#L688-L690)), and no power analysis anywhere targets that conditional contrast. The design therefore cannot reject or fail to reject its own headline.
6. **`τ*` is a maximally-selected statistic evaluated in-sample.** [R15:256-259](R15-arms-and-process-metrics.md#L256-L259) selects `τ* = min{τ : prec(τ) ≥ 0.99}` by scanning a 51-point grid on the calibration corpus and then reports the attained precision **on that same corpus**. No inner split exists. **Fix:** fit on one half, report attained precision on the other.
7. **`e4` gates on probability, which the design freezes as forbidden.** [R15:245](R15-arms-and-process-metrics.md#L245): `e4 = (D == Laya) and prob_label(label_chosen, D) < tau`. [R5:110](R5-synthesis.md#L110) rule 10 freezes "`confidence` 永不用于门控/阈值/路由". These are the same signal.

**Is anything reporting a p-value outside Gate 1 that should not be?** Yes: the `T90`-derived cost scalars in §3.7 (item 2), and `LEAD`/`AUC_detect` if they are silently absorbed into Gate 2. `AUC_route` is called a "headline" diagnostic with a bootstrap CI ([R15:271-274](R15-arms-and-process-metrics.md#L271-L274)) on the corpus used to fit `τ*` — in-sample, and outside every gate.

**VERDICT: sound-with-fix.** Minimal fix: enumerate the Gate-2 family explicitly and correct "seven" to six; remove every functional of `T90` from Gate 2 (report them descriptively in Gate 3); make Gate 2 conditional on a Gate-1 rejection; promote the conditional-on-integrity degradation contrast into Gate 2 with a pre-registered MDE; split the `τ*` corpus; delete `e4` or delete rule 10.

---

## 6. The benign-paraphrase control `B0`

**What statistic does it enter?** [R15:543-548](R15-arms-and-process-metrics.md#L543-L548) defines `B0` as a fault class (benign paraphrase at `t_0`) and states the headline "is never detection alone but `AUC_detect` and the detection lead time **at the false-alarm rate measured on B0**, with per-judge false-alarm rate … reported **in the same table**. No arm is compared without its B0 column." [R5:154](R5-synthesis.md#L154) restates this as a reporting requirement ("必须与 B0 假警报率**同表报告**"). So: `B0` enters as a **reported companion column**. It is not a covariate (no model in [R15:650-665](R15-arms-and-process-metrics.md#L650-L665) contains FAR), not a gate (no rule adjusts or rejects when FAR is high), and not an endpoint (no hypothesis, no power, no multiplicity slot).

**Can a high-false-alarm judge still win the primary endpoint? Yes — by construction.** `t_E = min{ t ≥ t_0 : verdict ∈ {revise, halt} }` counts *any* revise/halt after onset, with no requirement that the flag identify the injected fault. `B0` runs carry no fault onset, so they contribute no `t_E` and are excluded from `F_m(t)` by definition. A judge that flags every checkpoint therefore attains `t_E = t_0 + 1` in every fault run → the **minimum possible `T90`** and the **maximum possible `LEAD`**. Gate 1 contains no FAR test, so the always-flag judge passes the entire primary family. `B0` cannot stop it, because `B0` is only printed next to the result. Note also that `A0`'s extractor is a keyword scan ([R15:128-133](R15-arms-and-process-metrics.md#L128-L133)), so an undirected keyword hit is enough to score.

**Two further weaknesses.** (i) `B0` is 1 of 6 fault classes, so at 96 runs/arm only ~16 runs are benign — the FAR is estimated with roughly ±0.12 uncertainty at FAR ≈ 0.5, and the between-arm FAR difference must exceed ~0.35 to be distinguishable. The control therefore cannot rule out "wins by flagging everything" for moderate FAR differences. (ii) FAR is measured **between** runs (B0 runs) while detection is measured **within** fault runs, so FAR and detection are never measured on matched units.

**Minimal fix.** (a) Inject `B0` as a **sham onset in the same runs** as faults, so FAR and detection are within-run matched quantities. (b) Require **oracle-matched detection** (§2.4 item 1) so an undirected flag scores zero. (c) Run `B0` at a **higher allocation** than fault classes (it is cheap — nothing propagates) and pre-register the FAR margin. (d) Make FAR a pre-registered **covariate** in the survival model with an exclusion rule (no process-quality claim if a judge's FAR exceeds `A1`'s by more than a stated margin), and pre-register the FAR-matched comparison (equalize FAR, then compare detection).

**VERDICT: unsound.** A reporting column cannot neutralize an endpoint that an always-flagging judge wins. Minimal fix: (a) + (b).

---

## 7. What result would falsify the thesis?

State it in advance, before data:

**Thesis H.** At least one typed judge (`A2` Jev / `A3` Laya) detects injected faults earlier than the same LLM answering the same typed question (`A1`), and produces lower drift over the horizon, at a B0 false-alarm rate within the pre-registered margin of `A1`'s.

**Pre-registered falsifiers.**

| # | Observation that would show H false | Computable in the design as written? |
|---|---|---|
| F1 | `A1 ≥ A2` **and** `A1 ≥ A3` on the Gate-1 primary endpoint: the typed *substrate* (a closed label set + a second pass), not the judge's identity, produced every gain. Gate 1 contains exactly these two contrasts ([R15:683-684](R15-arms-and-process-metrics.md#L683-L684)), and [R15:165-171](R15-arms-and-process-metrics.md#L165-L171) itself declares A1 the floor. | **Yes** |
| F2 | The `S0` (judge-never) arm's drift trajectory is within the pre-registered equivalence margin of the best judge arm: judgment does not affect process quality at all, and the whole judgment-layer comparison is moot. `S0` exists in [R15:366](R15-arms-and-process-metrics.md#L366) but is **absent from [R5 §5.3](R5-synthesis.md#L136-L144)** — R5's arm table starts at `A0`. | **No — the control was dropped in the synthesis** |
| F3 | B0 false-alarm rate ≥ detection rate − δ, or the oracle-matched flag-correctness rate is at chance: the endpoint measures the injection procedure, not the judge. | **No — no correctness-matched detection and no FAR matching exist** (§6) |
| F4 | The `absent`-trace subset ([R14:427-432](R14-long-horizon-battery.md#L427-L432)) shows the same accuracy drop as `survives`: the horizon effect is not carrier-mediated, so the mechanism claim fails. | Yes — pre-registered |
| F5 | The `F4-CTRL` horizon placebo ([R14:187](R14-long-horizon-battery.md#L187)) slopes as steeply as the poisoned families: the knob measures long context, not long horizon. | Yes — pre-registered |

So the comparative thesis **is** falsifiable — F1 can go against the typed judges and the design would return it. That is the design's real strength. But two things blunt it:

1. **R5 has pre-absorbed the failure.** [R5:14-25](R5-synthesis.md#L14-L25) records that two of the three original claims already fail and that if the fine-tuning branch is cancelled "**准确率主张整体删除**，论文退守为测量/刻画论文（仍成立）". The surviving headline — "成本不是约束，静默退化才是" — rests on two statements that are not hypotheses about this experiment at all: money is not the binding constraint (derived from a price list, [R3:48-63](R3-corrected-economics.md#L48-L63); R5 says as much at [R5:16](R5-synthesis.md#L16)) and Laya's window silently truncates at 512 tokens (measured in R13; an implementation constant of the deployed checkpoint, [R5:49-51](R5-synthesis.md#L49-L51)). **No outcome of the battery can falsify either.** A design whose stated fallback cannot be refuted by its own data has an unfalsifiability problem, even when its primary contrast can fail.
2. **The one falsifiable part of the surviving headline is pre-registered as exploratory.** The claim "detection probability conditional on being in-window degrades with horizon even before the window is exceeded" ([R15:488-490](R15-arms-and-process-metrics.md#L488-L490)) is a hypothesis; it lives in Gate 3 with no p-values, no MDE, and no power analysis (R14's slope simulation targets an *accuracy* interaction, not a conditional-on-integrity degradation). In practice it cannot be rejected.

**What I would state in advance, verbatim, as the falsification clause:** if `A1 ≥ A2` and `A1 ≥ A3` on the corrected primary endpoint, the claim "typed judges improve long-horizon process quality" is false and is reported as the paper's headline result — not as a "measurement paper". If the `S0` equivalence test passes, the claim that judgment affects process quality at all is false. If F3 obtains, the primary endpoint is withdrawn. If F4 or F5 obtains, the mechanism claim is withdrawn.

**VERDICT: sound-with-fix.** Minimal fix: add `S0` to [R5 §5.3](R5-synthesis.md#L136-L144) with a pre-registered equivalence test against the best judge arm; add correctness-matched detection so F3 is computable; promote the conditional-on-integrity degradation contrast into a tested gate with a pre-registered MDE; and pre-commit in writing that F1 terminates the process-quality thesis rather than triggering the characterization reframe.

---

## ERRORS FOUND

### A. Arithmetic and power

| # | Where | Error | Corrected value |
|---|---|---|---|
| A1 | [R15:704-706](R15-arms-and-process-metrics.md#L704-L706) | "design effect of ~2.2 from task-level ICC ≈ 0.15", "effective clusters ≈ 96 per arm" | DE = 1+(4−1)(0.15) = **1.45**; n_eff = 96/1.45 = **66.2**. DE = 2.2 requires ρ = 0.40. "96 after DE 2.2" is impossible under any reading (raw is 96) |
| A2 | [R15:706-707](R15-arms-and-process-metrics.md#L706-L707) | MDE "~0.35 SD at 80% power, α = 0.05" | **0.487 SD** at α=0.05; **0.594 SD** at the pre-registered Gate-1 level (Holm, 0.05/5 = 0.01) |
| A3 | [R15:707-708](R15-arms-and-process-metrics.md#L707-L708) | "roughly 1.5–2.5 steps of lead time" | **2.1–4.2 steps** at the corrected MDE (SD 4.3–7.1 implied by R15's own conversion) |
| A4 | [R15:704](R15-arms-and-process-metrics.md#L704) | 576 runs suffice for 0.35 SD | **1,659 runs** needed (191 effective runs/arm × DE 1.45 × 6 arms) = 2.9× the plan |
| A5 | [R15:743](R15-arms-and-process-metrics.md#L743) | "Gold evaluation … (5 judges × 120 checkpoints × 576 runs = 69,120 calls)" | 5 × 120 × 576 = **345,600**; 69,120 is the one-judge figure |
| A6 | [R15:743](R15-arms-and-process-metrics.md#L743) | gold-eval total **$3,802** | **$38.0** by R15's own $0.066/run × 576 (a 100× decimal error); **$13** at R3's corrected prices; **$14.5** by R15's own token × price product. R3's identification of this as an arithmetic error is correct |
| A7 | [R15:736-742](R15-arms-and-process-metrics.md#L736-L742) | arm-run accounting: A0/A1/A3/A4 rows labelled "(96 runs)" but priced at 576 runs ($0.05×576=$29; $0.125×576=$72; $0.008×576≈$5; $0.026×576=$15), while the A5 row is priced at 288 runs | the matrix needs 5 arms × 96 + 3 sub-arms × 96 = **768 runs**, not 576. Either 576 runs and one A5 variant, or 768 runs |
| A8 | [R15:286-297](R15-arms-and-process-metrics.md#L286-L297) | unit costs are 2.6–7× their own token × price products: generation $0.398/run (own value: **$0.0596/run** = 802 steps at $0.00049644); LLM judgment $0.00104/call (own value: **$0.0001491**); grader $0.00055/call (own value: **$0.00021**) | **consequence for R3**: [R3:5](R3-corrected-economics.md#L5) claims the $229→$40 generation change is purely a price effect. False — R15's own prices give $34.3, so most of the $229 is a pre-existing arithmetic error, not a price error. R3's corrected *values* are right; its *attribution* is not |
| A9 | [R15:292-297](R15-arms-and-process-metrics.md#L292-L297) | "at `B_lo`… `LLM_J` 96 [calls]" i.e. the LLM arm is budget-bound at 0.8 calls/step | 96 only under the erroneous $0.00104/call. R15's own assumptions give **670**; R3's corrected prices give **912** (85% cache) / **336** (0% cache) — all ≥ 120 checkpoints. The headline "asymmetry" does not exist |
| A10 | [R14:321-323](R14-long-horizon-battery.md#L321-L323) | ψ=0.30 called "conservative" | required n is **monotone increasing in ψ**: 234 / 312 / 391 / 469 at ψ = 0.30 / 0.40 / 0.50 / 0.60. 234 is a *floor conditional on ψ ≤ 0.30*, not a conservative floor. (The table's own 77/155/234 are correct ✓; the ±6.4pt CI at n=270 is correct ✓; power at n=270 is 0.862 ✓) |
| A11 | [R14:300](R14-long-horizon-battery.md#L300) | "paired McNemar at n=100 detects ≈15 points at ψ=0.20" | the probe is 50 items × 2 variants = 100 **observations** = **50 pairs**. At 50 pairs: MDE **0.174** (ψ=0.20) / **0.212** (ψ=0.30); power at Δ=0.15, ψ=0.20 is **0.37**. 67 pairs are needed for 80% power at Δ=0.15 |
| A12 | [R14:331](R14-long-horizon-battery.md#L331) | extension rule "+75 slots (375)" | MDE at 375 items = 0.032/doubling = 0.23 cumulative — still 2–5× coarser than the 5–15pt effects the paper is about (≈1,900 items needed for a 10pt divergence) |
| A13 | [R15:686](R15-arms-and-process-metrics.md#L686) | "the **seven remaining** metrics of §3" | §3 has seven subsections total and §3.2 is the primary ⇒ **six** remain |

### B. Definitional / estimand errors

| # | Where | Error | Corrected specification |
|---|---|---|---|
| B1 | [R15:430-433](R15-arms-and-process-metrics.md#L430-L433), [R15:452](R15-arms-and-process-metrics.md#L452), [R5:152](R5-synthesis.md#L152) | the primary endpoint carries three different conditioning clauses (schedule-crossed / matched dollars / matched round-trips) | one clause; "matched round-trips" is not a realizable stratum, since round-trip count is constituted by the arm |
| B2 | [R15:430-433](R15-arms-and-process-metrics.md#L430-L433) | `F_m(t) = P(t_E ≤ t)` indexes absolute step while `t_0 ∈ {10,30,60}` is randomized | index `τ = t − t_0`; the current form makes `T90` a property of the onset mixture |
| B3 | [R15:428-429](R15-arms-and-process-metrics.md#L428-L429) | `LEAD = t_final(r) − t_E(r)` | confounded by the judge's own `halt` ([R15:33](R15-arms-and-process-metrics.md#L33)): halting at detection yields LEAD ≈ 0, i.e. the judge destroys its own score; `LEAD` (large better) and `T90` (small better) rank halt-happy judges oppositely |
| B4 | [R15:430-433](R15-arms-and-process-metrics.md#L430-L433) | `t_E` requires only that the verdict ∈ {revise, halt} | add the requirement that the flag match the injection oracle; otherwise `T90` is won by flagging everything |
| B5 | [R14:420](R14-long-horizon-battery.md#L420) | "Same run lineage… The manipulation is therefore **position, not instance**" | false for H0, which is "read off a **clean run**" with no poison. The fitted `judge × log2(H)` slope carries a poison/no-poison contrast in its first interval (log2H = 0 vs 2); fit the slope on H1–H4 only |
| B6 | [R5:133](R5-synthesis.md#L133) | "judge × log2(H) 斜率" over levels whose log2(H) = {0,2,3,5,7} | not equally spaced, and the floor level's distance-from-poison is undefined (`d = —`); the floor is a different condition, not a horizon point |
| B7 | [R5:144](R5-synthesis.md#L144) | `B0` is listed in the **arm** table, whose own rule ([R15:15-18](R15-arms-and-process-metrics.md#L15-L18)) is that only the judgment layer varies | `B0` is a fault/item class, not a judgment layer; the arm table is malformed |

### C. Internal contradictions

| # | Contradiction | Resolution required |
|---|---|---|
| C1 | [R5:75](R5-synthesis.md#L75) "类型化判定器是确定性的，因此可以对全部 1000 条只跑一次" vs [R5:113](R5-synthesis.md#L113) rule 13 "重复调用…不用于方差估计", and [R14:450](R14-long-horizon-battery.md#L450) T5 "raw probabilities are never compared across judges" vs [R5:74](R5-synthesis.md#L74) making cross-judge calibration a headline at ≥1000 | determinism removes within-item sampling variance and says nothing about the between-item/cluster variance that dominates; `A0` emits no probability at all, so no five-judge calibration exists |
| C2 | [R5:110](R5-synthesis.md#L110) rule 10 ("confidence 永不用于门控/阈值/路由") vs [R15:245](R15-arms-and-process-metrics.md#L245) `e4 = prob_label(...) < tau` | delete `e4` or delete rule 10 |
| C3 | [R15:646-648](R15-arms-and-process-metrics.md#L646-L648) "every hypothesis test is at the run level or coarser" vs [R15:417-421](R15-arms-and-process-metrics.md#L417-L421) drift unit = step-within-run with hypothesis H1 and `n = N_runs × N_step` | state drift's test level explicitly, or move H1 to a run-level functional |
| C4 | [R15:669](R15-arms-and-process-metrics.md#L669) "24 task families" / [R15:732](R15-arms-and-process-metrics.md#L732) "24 tasks" / [R5:126](R5-synthesis.md#L126) "3 族" / [R5:181](R5-synthesis.md#L181) "24 族" / [R14](R14-long-horizon-battery.md) 4 families | one definition, written into the pre-registration, with the cluster count printed in every table |
| C5 | [R5:76](R5-synthesis.md#L76) total 1000 items vs R14's inventory of 300 + 100 + 48 = 448 | 552 items are unspecified: no classes, no ground truth, no gates, no power statement |
| C6 | [R15:673-675](R15-arms-and-process-metrics.md#L673-L675) "randomized within task **family**" vs "reassign arm labels within **task**" | the permutation must mirror the actual randomization |

---

## TOP 3 THREATS TO VALIDITY

**1. The primary endpoint is not a valid test in either direction.** `T90` is won by a judge that flags everything (`t_E` never checks *what* was flagged, [R15:428](R15-arms-and-process-metrics.md#L428)), and is undefined unless ≥87/96 runs detect (P(defined) = 0.004 at a true rate of 0.80). A positive result is therefore uninterpretable and a null result is uninformative — and the paper's headline rests on it.
*Mitigation:* replace `T90` with the `τ`-anchored, oracle-matched, FAR-matched cumulative detection probability at a pre-specified `τ*`, computed on one frozen snapshot population (§1.4, §2.4, §6).

**2. The judge effect is not identified.** The arm bundles judge identity with control policy, trajectory, run length and state size; the replay plane that would separate them is used only descriptively, while the pre-registered endpoint is the bundle, and RI over arm labels cannot test a factor that every judge receives on every unit (§1.2, §4.3).
*Mitigation:* pre-register two estimands — a paired within-snapshot judge contrast (primary for judge claims) and an arm ITT (primary for schedule claims) — and restore the schedule factor to R5's arm table.

**3. The power scaffold is arithmetically wrong and its cluster count is undefined.** A 0.35 SD lead-time effect needs ≈1,660 runs, not 576; the horizon slope resolves only a ≥25-point divergence where the paper claims 5–15 points; and CR2 / the wild bootstrap / RI all depend on a cluster count stated as 3, 4, 24 families and 24 tasks in four different places (§3.2, §3.3, §4.1).
*Mitigation:* fix the cluster definition and the randomization in the pre-registration, correct the DE/α/MDE arithmetic, and either fund ≈1,900 items for the slope or pre-register it as a descriptive curve with a declared MDE.

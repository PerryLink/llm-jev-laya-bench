# §7 Results D — cross-species complementarity: a negative result

*(English translation of `paper/08-results-D-draft.md` (§7 Results D, which sits at §8 in the assembled
manuscript: `paper/_assemble.py` remaps this draft's `§7` → `§8`). Faithful, not abridged: every hedge,
every ⚠️ marker, every blockquote, every n and every decimal place is carried across. Terminology
follows `paper/TRANSLATION-GLOSSARY.md`; field names, verdict vocabulary, artifact IDs, paths, statistics
and model IDs are left untranslated. Cross-references `§N.M` and the heading numbers are reproduced
exactly as the Chinese draft writes them, so that the assembler remaps them identically in both builds.
The draft's own audit annotations and their round numbers are retained.)*

> **Principle of the writing**: the value of a negative result lies in **what it refutes**, not in "we did not find it". So this section first states the architectural claim being refuted, then gives the **paired** evidence from **three regimes**, and finally explains **how far it can be extrapolated, and how far it cannot**.

---

## 7.0 The claim being refuted

**Claim**: in long-horizon tasks, using a **cheap, different-species** judge as the first tier, and escalating to a frontier model only when it is uncertain, can obtain **equal or better** judgment quality at lower cost.

**The single premise that claim depends on**: **a heterogeneous judge and the LLM will make errors on different items** (complementarity). If the two err in the same place, the first tier is merely "a worse second tier".

**In the existing work, the first tier is mostly an LLM judging an LLM** ([FrugalGPT](https://arxiv.org/abs/2305.05176), [RouteLLM](https://arxiv.org/abs/2406.18665), [AutoMix](https://arxiv.org/abs/2310.12963), [Cascaded LMs](https://arxiv.org/abs/2506.11887)). **But a non-generative discriminator is not without precedent** — RouteLLM itself comments on Hybrid-LLM's **BERT-based router** and Zooter's **BERT-style router**; so **the question "does heterogeneous mean complementary" is not "nobody has used a heterogeneous first tier before", but "nobody has treated it as a controlled first tier and run a paired complementarity test against a frontier generator".**

**This section's answer: on the three regimes measured, no complementarity was found in any of them.**

---

## 7.1 The metric

On **the same item**, let the two judges each answer once, making a **paired comparison**:

```
Δ_catch = P(typed judge correct | LLM wrong) − P(typed judge correct | LLM right)
```

- The **paired** design makes item difficulty **cancel within the item**, so Δ_catch **is not confounded by a difference in accuracy level** — the problem every "A is more accurate than B" comparison cannot avoid;
- We also report the **confusion matrix** (both correct / only the typed one correct / only the LLM correct / both wrong) and **Cohen's κ**;
- **The criterion is the sign of Δ_catch**, not whether the "only the typed one correct" count is non-zero (see one correction in §7.4).

---

## 7.2 Regime one: authority location (template-matching kind)

**Items**: `DECOY + filler + CORRECTION`, in which the authority-marked statement must be found among several statements; **all options are numerically plausible** (avoiding the shortcut of "eliminating by plausibility"). 48 paired items.

| metric | value |
|---|---|
| **LLM accuracy** | **1.0000 (48/48)** |
| **Laya accuracy** | **0.4583** |
| Only the LLM correct | **26** |
| **Only Laya correct** | **0** |
| Both correct | 22 |
| κ | **0.0** |

→ **The LLM did not err once**, so `P(Laya correct | LLM wrong)` and **Δ_catch are both undefined**.
→ All that can be said is: **on this regime Laya caught no item the LLM missed (only Laya correct 0 / only LLM correct 26)**, but instead failed alone on 26 items.

**⚠️ But the reading above is the forced-choice arm. The same artifact also records a second arm, and its Δ_catch is POSITIVE (ninth-round addition, ERRATA §10.1 item 3).**
`results\P14-llm-arm-full.json`'s `complementarity_prose_arm` records the paired result on **the same 48 items** with the LLM answering **in prose** (the label recovered by an extractor):

| metric | value (P14 prose arm, n=48) |
|---|---|
| **LLM accuracy** | **0.9583 (46/48)** |
| judge accuracy (the same judge readings) | **0.4583** |
| both correct / only LLM / **only judge** / neither | 21 / 25 / **1** / 1 |
| **`P(judge correct \| LLM wrong)`** | **0.5 (1/2)** |
| `P(judge correct \| LLM right)` | 0.4565 (21/46) |
| **Δ_catch** | **+0.0435** |
| Δ_catch 95% CI (unpaired Wald / Newcombe) | **[−0.664, +0.751] / [−0.386, +0.471]** |
| Fisher exact p (2×2) | 1.0000 |

→ **This is the only measurable Δ_catch in regime one, and its sign is positive.** This section previously reported only the forced-choice arm and therefore wrote the whole regime off as "unmeasurable" — **that judgement holds for the forced-choice arm and does not hold for the prose arm.**
→ **The denominator must be given with the point estimate, or +0.0435 will be read as stronger than it is**: the LLM errs on only **2** of the 48 prose items, so `P(judge correct | LLM wrong)` is **1/2**; both 95% intervals are wide and both contain 0, and the Fisher p is 1.0000. **It is not established complementarity; but it is also not zero** — reading +0.0435 as "no complementarity" and reading it as "complementarity" are equally unsupported.
→ **The two arms are two answer formats of ONE 48-item battery** (this artifact's `_provenance.consumes` is `P9b`; the judge reads 0.4583 on both arms), **not two independent pieces of evidence**; in the capability profile each occupies one row and the pairing must be stated (§6.1).
→ Every number above is recomputed by `src\analysis\p28_recompute_all_stats.py` and written into the `regime1` block of `results\P28-recomputed-statistics.json`; that block also records that **the forced-choice arm's Δ_catch is undefined because `n_wrong_arm = 0`** (it must not be printed as 0).
→ **⚠️ This artifact's `_provenance.published_figures_at_risk` already listed "prose arm 0.958"** — this arm has been on the "if this moves, the paper's numbers are at risk" list since it was recorded, yet it never appeared in the body text.


**The strength of this regime's evidence**: the **ceiling effect applies only to the forced-choice arm** (LLM 48/48). **The prose arm is measurable**, with a Δ_catch point estimate of **+0.0435**, an interval containing 0, resting on only **2** items where the LLM errs. **⚠️ The accurate statement for this regime is therefore: not measurable in one answer format, measurable in the other with a positive point estimate and insufficient precision to decide** — not "this battery cannot measure complementarity" (ninth-round correction: the original sentence rested on the forced-choice arm alone; see the table above).

---

## 7.3 Regime two: 77-class intent classification (Laya's relative strength)

**Why this one was chosen**: after P14's negative result, I originally assumed complementarity ought to appear in **Laya's regime of relative strength**. P7 had measured the second level (≤3 candidates, **conditional on the ancestor being correct**) at **0.867**, so it was chosen as the "strength".

**But that assumption was itself wrong**: 0.867 is an **artefact of conditioning**. In a real deployment the ancestor does not know it is wrong, and **group selection is only 0.275, and an error there is final**.

**Design (an honest deployment comparison)**: the same batch of 40 **real Banking77 test-set sentences** —
- **Laya**: walks the full hierarchy (self-selects the group → selects the intent within the group); an error in group selection is final;
- **LLM**: faces **all 77 real intent labels** at once (a **harder** task).

**⚠️ This section has been changed to report 4 independent draws**: the recorded round did not pass `temperature`, so the LLM arm is a **single draw** from the API's default sampler. On review we reran **3 times** with `temperature=0` (the same 40 sentences, the same seed), making **4** in total together with the recorded round.

| metric | recorded round | reproduction r1 | reproduction r2 | reproduction r3 |
|---|---|---|---|---|
| **LLM flat 77-class** | 0.7500 | **0.9000** | 0.8750 | 0.8750 |
| **Laya full hierarchy (end-to-end)** | **0.2250** | **0.2250** | **0.2250** | **0.2250** |
| Laya group selection | 0.2750 | 0.2750 | 0.2750 | 0.2750 |
| Only the LLM correct | 23 | **27** | 27 | 26 |
| **Only Laya correct** | **2** | **0** | **1** | **0** |
| **Δ_catch** | **−0.033** | **−0.250** | **−0.029** | **−0.257** |
| Δ_catch 95% CI (**unpaired Wald; see note below**) | [−0.324, +0.257] | [−0.391, −0.109] | [−0.406, +0.349] | [−0.402, −0.112] |
| Δ_catch 95% CI (**Newcombe**, trustworthy with a zero cell) | [−0.260, +0.297] | [−0.411, +0.253] | [−0.259, +0.409] | [−0.421, +0.192] |

> **⚠️ Two cells of this row were once misprinted (found and corrected in the fifth review round).** One cell of the recorded round originally printed **[−0.324, +0.257]** — that is a **digit-for-digit copy** of the Wald value in the same column, mistakenly taken as a Newcombe value; the r2 cell originally printed **[−0.410, +0.184]**, which is **not** any Newcombe interval for this data (enumerating all tuples with `n₁≤14, n₂≤41`, the only combination giving that interval is `(5,13,13,25)`, which matches no cell of this regime). Both cells are now recomputed by **Newcombe method 10 (the MOVER of the Wilson score)**. The r1 and r3 cells, on recomputation, **were correct as printed**.
> **This correction runs in favour of the conclusion's direction**: after the correction, **all four draws' Newcombe intervals contain 0** (the original table pointed this out explicitly for only two of them).
> All intervals and exact tests are now recomputed uniformly by `src\analysis\p28_recompute_all_stats.py`, output `results\P28-recomputed-statistics.json` — previously these numbers had **no script at all** that could reproduce them (no Wald/Newcombe/Fisher code anywhere in the tree), and it is precisely that gap that let one Wald value masquerade as a Newcombe value for a long time.

**Four readings**:
1. **Laya is fully deterministic**: across the 4 draws, end-to-end and group selection are **bit-identical** (0.2250 / 0.2750) — Laya does not sample, and the item set is fixed.
2. **The recorded round's 0.7500 is the lowest of the 4.** The reproduced values cluster at **0.875–0.900** (empirical centre ≈0.875, mean 0.850). **So the abstract must no longer treat 0.7500 as the LLM's capability value**; it should write "0.750–0.900 (4 draws), centre ≈0.875".
   → This also **weakens** one premise of the contamination argument: if the LLM is relying on memory, its true level is more likely to be near 0.875.
3. **Δ_catch is ≤ 0 in all 4 draws, never positive** — and the recorded round (−0.033) is the one **most favourable** to the complementarity hypothesis. **The sign is stable, the magnitude is not** (span 0.229).
   **⚠️ But "the CI excludes 0" is a statistical artefact on this regime and must not be cited**: in 2 of the 4, the "only Laya correct" count is **exactly 0** (r1 is 0/4, r3 is 0/5), and **the zero cell makes the Wald interval lose all of that arm's variance**, so the interval is spuriously narrowed. After switching to the Newcombe method, **all four draws' intervals contain 0**: [−0.260, +0.297] / **[−0.411, +0.253]** / [−0.259, +0.409] / **[−0.421, +0.192]** — and it is precisely the r1 and r3 whose counts are 0 whose **Wald** intervals ([−0.391,−0.109], [−0.402,−0.112]) **exclude 0 while Newcombe does not**, which is the exact source of the artefact. The **95% one-sided exact upper bound for 0/4 is 0.527** and for 0/5 is **0.451** (`P28-recomputed-statistics.json`; the 0.602 / 0.522 printed in an early version are **97.5% one-sided** bounds, corresponding to a two-sided 95%). **⚠️ But one cannot therefore say "the data is compatible with a Δ_catch as high as +0.35"** — that statement is not any interval: **the Newcombe upper bounds are +0.253 (r1) and +0.192 (r3)**, and those are the limits compatible with the data.
   ⇒ **The only robust statement about this regime is "the sign is negative in 4/4"**, not "2 of them are significant". The Fisher exact p for the same 2×2 is **0.557 / 1.000 / 0.570** (1.0000 for the recorded round before the fix) — **not one of them is anywhere near significant**.
4. **"Only Laya correct" is 0 / 1 / 0 across the 3 reproductions** (2 for the recorded round), while "only LLM correct" is 26–27. **Laya almost never catches an item the LLM missed.**

→ **Ruling**: **across 4 independent draws, not one shows complementarity**; the recorded round is the most favourable one and is still negative. So this regime's conclusion is **stronger** than before: it is no longer "n=40 is not significant, so it cannot be decided", but "**the direction is consistent in 4/4 draws, and is still negative in the most favourable one**".

### 7.3.1 An incidental finding: the hierarchy is a **net gain** for Laya

**P7 (n=30, paired within the same batch of items)**:

| level | accuracy | chance |
|---|---|---|
| **Flat 77-class (same batch of items)** | **0.0333** (1/30) | 0.013 |
| Group selection (10 groups) | **0.200** (6/30) | 0.10 |
| Within-group selection (≤3, conditional on the **true** ancestor being correct) | **0.867** (26/30) | 0.333 |
| **End-to-end** | **0.200** (6/30) | — |

→ **The hierarchy (0.200) beats flat (0.0333), by about 6×**; `results\P7-…json` itself has `hierarchy_beats_flat = true`.
→ The bottleneck is **group selection** (0.200, chance 0.10), not within-group (0.867, chance 0.333).
→ **Independent reproduction**: on **40 real Banking77 sentences** P15 gives end-to-end **0.225** (9/40) and group selection **0.275** (11/40), the same direction as P7.
→ And **the LLM gets 0.750–0.900 flat on the same task (4 draws, centre ≈0.875)** (P15, n=40) ⇒ the hierarchy is unnecessary for a **large model**, but genuinely effective for a **small judge**.
→ **⚠️ Correction**: an early version of this section wrote "the hierarchy (0.225) is below single-level flat Laya performance" and concluded from it that "the hierarchical decomposition is **harmful** to a small judge" — **the direction was the opposite of the artifact** (0.200 > 0.0333), and that table had also laid out rows from two batches of items, P7 (n=30) and P15 (n=40), mixed together without annotation. Both places have been corrected against the artifacts.

---

## 7.4 A criterion defect I fixed in this section

On its first run the script **announced "COMPLEMENTARITY EXISTS"**, on the grounds that "only Laya correct" was non-zero (=2).
**That was wrong**: at the time "only LLM correct" was **23**, and **Δ_catch was negative**.

**Fix**: the criterion was changed to **the sign of Δ_catch** (only a threshold of +0.10 counts as support).
→ **Lesson**: a non-zero "only A correct" count **does not constitute complementarity**, unless A is at the same time more reliable where B fails. **A count and a sign are two different things.**

---

## 7.5 Conclusion and the boundary of extrapolation

**Conclusion**:
> On the **three** task regimes measured, **a heterogeneous judge provides no incremental coverage**. On one of them the LLM is strictly dominant (forced-choice arm: only LLM correct 26 / only judge correct 0; **⚠️ the same 48-item battery's prose arm is 25 / 1, Δ_catch = +0.0435 — the regime's only measurable Δ_catch, and it is positive, see §7.2**); on another the LLM hits the ceiling, making its error structure **unmeasurable**; on the third the ceiling has been broken and, **re-judged after the ground-truth fix**, Δ_catch is consistently negative (3/3; under an unpaired Wald interval 2 exclude zero, **but the reason this interval is narrower differs from regime 2's: this regime's cells are 17/29/3/19 and none is zero -- the zero cell belongs to regime 2, and an earlier version misattributed that explanation here**; after switching to Newcombe **only 1 robustly excludes and 1 sits at the boundary**), and the failure correlation is **positive in 3/3 draws** — i.e. the evidence is **consistent with "shared failure"**, rather than being complementarity.
> **⚠️ Strength qualification**: the Fisher exact p for that correlation is **0.086 / 0.049 / 0.163** (r1/r2/r3). **Uncorrected, only 1 of 3 is significant at α=0.05 (r2, p=0.0487, just 0.0013 from the threshold); and under this paper's own Holm rule (§4) none of the three survive** (the first threshold is 0.0167). The one-sided test of "conditional accuracy vs marginal" has a 95% CI **containing 0 in 3/3 draws**.
> **The MDE (0.28–0.30) is still larger than the pre-declared gate (+0.10), so this is "the direction is consistent in 3/3, with 2 excluding zero under Wald (1 robust under Newcombe, 1 at the boundary)", not a precise effect size.**
> **The architecture of "a cheap heterogeneous judge as the first tier" finds no support on the tasks this project measured.**

**How far it can be extrapolated**:

| can | cannot |
|---|---|
| "Heterogeneous ≠ automatically complementary" — **an architectural choice needs positive complementarity evidence; it cannot be assumed from a difference of species** | **Cannot** say "there is no complementarity under any circumstances" |
| On tasks that are **single-text, have explicit labels, and are decidable in a single hop**, the LLM's accuracy advantage is enough to drown out any gain from a heterogeneous first tier | **Cannot** extrapolate to open-ended tasks, tasks requiring multi-hop retrieval, or tasks with an extremely large label space requiring external knowledge |
| On a battery where **either judge hits the ceiling**, complementarity is **not measurable** (rather than "does not exist") | **Cannot** treat "not measurable" as "does not exist" |

**What must go into the limitations**: this project measured **three regimes**, of which **the first two both put the LLM at or near the ceiling** (and therefore made it **unmeasurable**), while the third has broken the ceiling but is **underpowered** (MDE = 0.311, far larger than the pre-declared threshold +0.10). **This is therefore a methodological result about "how to decide an architectural claim", not a universal conclusion that "a heterogeneous judge is useless".**

---

## 7.6 Regime three: multi-hop chained verification (**the ceiling is ruled out; after the ground-truth fix Δ_catch is consistently negative, and the failure correlation runs the same way**)

**Why a third regime was mandatory**: neither of the first two can decide the claim — because **one side does not fail**. In regime one the LLM was correct 48/48; in regime two it was 0.750–0.900 and the gap was dominated by task difficulty. **When one side does not fail, "whether the two fail in different places" is not measurable.**

**Changing items would be useless**: the existing items are all "template matching + single-hop verification", entirely coinciding with the LLM's strengths. **The structure has to change.**

**CHAIN-AUDIT's structure**: the audit trail contains K operation lines (`+d / −d / ×2 / ÷2`), some of which are marked **`SUPERSEDED — DO NOT APPLY`**; the question asks for **the value after the last non-superseded step**. The ground truth is given by a program simulation.
**Certificate**: the generator computes `simulate(ignore superseded lines)` and the ground truth, and **only those that are not equal enter the pool** (reusing §4.3's mechanism).
**⚠️ Wording correction**: an early version of the paper wrote "the generator **asserts** … those that do not satisfy it are rejected at build time", but the code is `if alt == truth: continue` — a **silent filter** (96 → 68), **not an assertion**; and measurement shows that on 8/96 chains `simulate(ignore_superseded=True)` **is not equal to** "reading out every rendered line literally" (because the parity adjustment has already changed the active value), so `alt` is an **approximation** to "ignoring the superseded marker", not a literal reading.

**Results — the pre-fix battery (96 items designed, K∈{2,4,8,16}×24, paired n=69; this table is the round with the **disclosed defect**, kept for the record)**:

| chain length K | n | **LLM** | **Laya** | chance |
|---|---|---|---|---|
| 2 | 12 | 0.833 | 0.417 | 0.25 |
| 4 | 12 | **1.000** | 0.250 | 0.25 |
| 8 | 21 | **0.429** | 0.286 | 0.25 |
| 16 | 24 | **0.417** | 0.250 | 0.25 |
| **Total** | **69** | **0.5942** | **0.2899** | 0.25 |

**Results — the fixed battery (n=68, 3 draws, `temperature=0`; this section's conclusions take this as authoritative)**:

| chain length K | n | LLM r1 | LLM r2 | LLM r3 | **Laya (identical in all 3)** | chance |
|---|---|---|---|---|---|---|
| 2 | 12 | 0.917 | 0.917 | 0.917 | **0.417** | 0.25 |
| 4 | 12 | 1.000 | 1.000 | 1.000 | **0.250** | 0.25 |
| 8 | 21 | 0.571 | 0.476 | 0.476 | **0.286** | 0.25 |
| 16 | 23 | 0.478 | 0.522 | 0.522 | **0.261** | 0.25 |
| **Total** | **68** | **0.6765** | **0.6618** | **0.6618** | **0.2941** | 0.25 |

→ **LLM overall 0.662–0.677 < 0.95: the ceiling has been broken, and complementarity is measurable.**
→ **The LLM's failure structure (already corrected to the answerable denominator)**: on items that **actually offered** the option "ignore `SUPERSEDED`", the rate at which the LLM selected it is **11.5% / 13.1% / 13.1%** (7/61, 8/61, 8/61; 10/62 = 16.1% for the recorded round). **That rate is only meaningful read conditionally**: among the items the LLM **got wrong**, **31.8–34.8%** of the errors **are exactly** "carrying out the superseded line as well" (r1 7/22, r2 8/23, r3 8/23); on the deep chains with **K≥8** it is **29.4–32.3%** (K=8 10/31, K=16 10/34).
   ⇒ **"Not noticing that a line was superseded" is a real and stable failure mode of the LLM, accounting for about one third of its errors, but it is not its main failure mode** — the remaining errors are landing on an approximate decoy after **getting one step wrong**.
→ **The evidence on Laya's side is much stronger, and it is this section's most direct evidence on the central hypothesis**: its rate (answerable denominator) is **34.4%**, and among the items it **got wrong** it accounts for **43.8%**; while on the **shallowest K=2**, it **gives the result of "carrying out the superseded line as well" outright on half the items (18/36)**, which is **85.7%** of all its errors (21 items).
   ⇒ **In the simplest form of the chain battery, Laya's dominant behaviour is "do not supersede, execute everything"** — before depth has even become an issue, it is already not carrying out the instruction "skip superseded lines". This is precisely an instance, in the **non-inferential** sense, of §6.3's "no channel for detecting absence", and it corroborates §7.6.2's "capability absence vs error compounding" in both directions.
   ⇒ Note that **two readings pointing in opposite directions** must be placed side by side: **Laya makes this particular error of "ignoring supersession" more often than the LLM (34.4% vs 11.5–13.1%)**, while its **overall** accuracy is also lower (0.294 vs 0.662–0.677).

### 7.6.1 ⚠️ This battery's ground-truth defect and the **re-judgment after the fix** (this section's conclusions have been rewritten against the fixed version)

**Defect**: `make_chain` silently adjusts parity when `div` meets an odd number, and `simulate()` (whose source calls itself *"Authoritative truth"*) does not reproduce it; and **the documented certificate was never implemented**. Consequence: **11/69 items (15.9%) have a scored ground truth that cannot be derived from the rendered question** (of which 10 have a "faithful reading" answer that is not even among the options).

**Fix**: the parity adjustment is now recorded step by step, and `simulate()` replays it **before the superseded determination** (the generator has already rewritten the active value at the **evaluation** step, even if that step is superseded afterwards), and the certificate **has been implemented as an assertion**. After the fix, **96 items generated → 0 non-derivable → 68 entered the pool**.

**Re-judgment**: rerun with the fixed generator, `temperature=0`, and **3 independent draws** (68 items each, about $0.0027 each):

| reading | pre-fix (recorded) | fixed r1 | fixed r2 | fixed r3 |
|---|---|---|---|---|
| n | 69 | 68 | 68 | 68 |
| **LLM overall** | 0.5942 | **0.6765** | 0.6618 | 0.6618 |
| **Laya overall** | 0.2899 | **0.2941** | 0.2941 | 0.2941 |
| K=2 / K=4 / K=8 / K=16 (LLM)| .833/.1000/.429/.417 | .917/1.000/.571/.478 | .917/1.000/.476/.522 | .917/1.000/.476/.522 |
| `P(Laya correct \| LLM wrong)` | 0.2857 (n=28) | **0.1364** (n=22) | 0.1304 (n=23) | 0.1739 (n=23) |
| `P(Laya correct \| LLM correct)` | 0.2927 (n=41) | **0.3696** (n=46) | 0.3778 (n=45) | 0.3556 (n=45) |
| **Δ_catch** | **−0.0070** | **−0.2332** | **−0.2473** | **−0.1816** |
| Δ_catch 95% CI (**unpaired Wald**, see note below) | [−0.225, +0.211] | [−0.433, −0.033] | [−0.445, −0.050] | [−0.390, +0.027] |
| φ (failure correlation)| +0.0075 | **+0.239** | **+0.257** | +0.189 |

**Four key readings**:

1. **⚠️ The difference between the two batteries [cannot] be attributed to the ground-truth fix — this item overturns the causal assertion of this section's first draft.**
   **And the strength of "the CI excludes 0" must also be downgraded**: the intervals in the table are **unpaired Wald** (an early version of the paper called them "Westfall-type", but that is a **label with no implementation** — there is no interval code for Δ_catch anywhere in the tree, and the 8 numbers are digit-for-digit equal to the Wald formula). After switching to the score/Newcombe method, **r1's upper bound is −0.0003 (a bare exclusion), r2 robustly excludes, and r3 does not exclude** ⇒ the honest statement is "**1 of 3 robustly excludes, 1 at the boundary**", not 2/3.
   On review we decomposed the 68 **shared** items one by one:

   | check | result |
   |---|---|
   | Did the scored **ground truth** change | **68/68 bit-identical** (the ground truth comes from `make_chain`, and the fix only made `simulate()` agree with it) |
   | `state_tokens_laya` | identical for 68/68 |
   | Laya label changed | **only 1 item** (CH-K16-018) |
   | LLM label changed | **28/68 = 41.2%** |
   | item set | 69 → 68 (CH-K16-009 dropped); and **exactly 7 items' option sets changed**: `CH-K8-011/012/023`, `CH-K16-001/004/007/018` (see the confusion note at the end of §7.6.1) |

   **Counterfactual decomposition** (Δ_catch recomputed on the 68 shared items):

   | combination | Δ_catch |
   |---|---|
   | pre-fix battery | −0.0143 |
   | fixed battery | −0.2332 |
   | **fixed Laya + pre-fix LLM** | **−0.0143** ⇐ **the contribution of the ground-truth/judge side is exactly 0** |
   | pre-fix Laya + fixed LLM | −0.1660 |

   ⇒ **Almost all of the shift comes from resampling the LLM arm** (the recorded round **did not pin `temperature`**, the fixed version pins it at 0), **not** from the ground-truth fix.
   ⇒ **The paper must not claim "the ground-truth defect depressed the effect".** The counter-evidence is in this project's own records: rerunning the same 69-item battery **without any fix at all** twice already gives Δ_catch of **−0.0328 / −0.2071** — **the same magnitude is reachable without doing the ground-truth fix**.
   ⇒ The role of the ground-truth fix is to make the battery **well-posed** (the scored ground truth is derivable from the question, the certificate is implemented, 1 item is dropped), **not** to change the effect size. **These two facts must be stated separately.**
   ⇒ **What actually raises the strength of the evidence is "repeated draws with temperature pinned"**, and that has nothing to do with the ground-truth fix.
2. **It is not "no complementarity", but "consistent with shared failure".** After the fix, `P(Laya correct | LLM wrong)` = 0.13–0.17 (3/22, 3/23, 4/23), while Laya's **marginal** accuracy is 0.2941; `P(Laya correct | LLM correct)` = 0.36–0.38, **above** the marginal. φ is positive in 3/3 draws (+0.19…+0.26).
   **⚠️ The strength must be qualified (in three places)**:
   (a) The Fisher exact p for the 2×2 is **0.086 / 0.049 / 0.163** (in the order r1/r2/r3; an early version of the paper printed them in **ascending numerical order** as 0.049 / 0.086 / 0.163, inconsistent with the r1/r2/r3 order of the adjacent rows and easily misread as "r1 is the most significant" — **it is in fact r2**). **⚠️ And under this paper's own pre-declared multiple-comparison rule (§4, Holm for the primary endpoint family), not one of the three draws survives**: Holm's first threshold is 0.05/3 = **0.0167**, and the smallest value, 0.0487 > 0.0167. So the correct statement is "**1 of 3 is significant at the uncorrected α=0.05; under this paper's own Holm correction, 0/3**" — **not "1/3 draws significant"**;
   (b) Comparing `P(Laya correct | LLM wrong)` with the **independence baseline 0.2941**, all three **Wilson 95% CIs contain the baseline** ([0.047,0.333] / [0.045,0.321] / [0.070,0.371]), with one-sided p = **0.052 / 0.043 / 0.103 (normal approximation, no continuity correction)** ⇒ **"below the marginal" is a point estimate, not an established inequality**; **⚠️ The convention must be named (ninth-round correction, ERRATA §10.1 item 2)**: these three numbers were printed without a stated test, so the reader could not tell which one produced them. **The exact binomial lower tails for the same `(x, n, baseline 0.2941)` are 0.076 / 0.061 / 0.149** — **nothing is significant under either convention**. Both conventions are recomputed from the artifacts by `src\analysis\p28_recompute_all_stats.py` and written into `results\P28-recomputed-statistics.json` under `regime3[*].vs_marginal_one_sided`, which carries both `exact_binomial_lower_tail` and `normal_approximation`; **⚠️ do not conflate them with the Fisher exact p printed in the same place (0.086 / 0.049 / 0.163) — that is a different test on the 2×2 table**;
   (c) **The three draws are not three independent pieces of evidence**: the Laya arm is bit-identical across 3×68, only the LLM arm is being resampled, and the numerator is only **3–4 items**; doing a 68-item permutation test at the correct clustering level gives a correlation of **+0.243**, **p = 0.057**;
   (d) **After stratifying by difficulty K, the positive φ disappears**: K is the difficulty knob **this battery manipulates itself**, and almost all of the pooled φ's positive value comes from the K=16 stratum. Recomputed stratum by stratum: **K=2 stratum φ = −0.357 (negative in 3/3)**; K=8 stratum +0.122/+0.241/+0.030; K=16 stratum +0.621/+0.569/+0.569; **the K-stratified CMH permutation test gives p = 0.059 / 0.055 / 0.201 — not one of the three reaches α=0.05**.
   ⇒ So the statement "**φ is significantly positive**" **does not hold**, and both this section and the abstract have deleted the word "significant"; the correct statement is "**the pooled correlation is positive, but is not significant after stratification**".
   ⇒ So all that can be said is "**consistent with shared failure**". For a "backup judge", if that pattern holds it is **worse than independent** — but **this is an inference, not an established effect**.
   **⚠️ There is also one confound not ruled out**: **difficulty heterogeneity by itself can mechanically produce Δ_catch < 0** (for two conditionally independent judges, so long as item difficulty varies, conditioning on the LLM being right or wrong induces a negative association). This project's empirical anchor: on the pre-fix battery, **deleting only 11 items, with no code change and no ground-truth change**, Δ_catch moves from −0.0070 to **−0.0969** (n=58) — so the contribution of difficulty/item composition **has not been separated**.
3. **The LLM arm's reproducibility improves greatly after temperature is pinned**: the item-level label agreement **between** the three **pinned** draws is **86.8% / 86.8% / 89.7%**; while between the unpinned recorded draw and any one of the pinned draws it is only **58.8% / 63.2% / 60.3%** (40/68, 43/68, 41/68). **⚠️ These two numbers are not the same conventions and must not be compared side by side**: the former is an agreement rate **within a condition** (pinned vs pinned), the latter is an agreement rate **across conditions** (unpinned vs pinned); **and for an arm sampled only once, there is no "between repeated draws" agreement rate at all**. After dropping the 7 items whose option sets changed, the cross-condition agreement rates are **60.7% / 63.9% / 62.3%**, and **the direction of the conclusion is unchanged**. **This is the main gain from this re-judgment.**
   ⇒ **And the Laya arm gives this project's single strongest piece of evidence about a judgment arm**: its disagreements with the recorded round **total only 1 item** (`CH-K16-018`), **all three draws are this same one item**, and it **falls within those 7 items whose option sets changed**; after dropping them it is **61/61 = 100.0% (3/3 draws)**, with the overall accuracy identical in all three (0.2941). **The judgment arm is not merely "reproducible in practice" — when the question is fixed it is completely invariant to sampling**: it is a deterministic function of (state, options).
4. **The denominator of the "chose ignore SUPERSEDED" rate was structurally depressed (now corrected on both the code and the artifact sides)**: of the 68 items, **7** have `alt_ignore_superseded` **not among the four options at all** — **two** (`CH-K16-000`, `CH-K16-008`) are filtered out by `v > 0` because `alt ≤ 0`, and **five** (`CH-K4-005/015/018`, `CH-K8-021`, `CH-K16-012`) are cut off by `sorted(...)[:4]` because `alt` is always the largest candidate; **it kept the `truth × 2` "approximate" decoy, but lost the "exact" ignore-superseded value**. So the rate's ceiling is only **61/68 = 0.897**.
   ⇒ **How it was corrected**: the generator now **preferentially inserts `alt` and forbids it from being cut off** (the new battery has **66/68** answerable, with only the 2 remaining `alt ≤ 0` ones **explicitly marked `alt_in_options=False`**, rather than silently thinning the denominator); `run()` now computes on the **answerable denominator** and **retains the old denominator as well**; the 4 published artifacts were **backfilled with `alt_in_options` and recomputed** by `src\items\p22f_repair_denominator.py` — **nothing was re-measured and no verdict was changed** (the item set is generated from a fixed seed, the option sets can be reconstructed exactly, and the per-item assertions against `truth` all pass, 68/68 and 69/69 all hit).
   ⇒ **The corrected readings**: **LLM 11.5% / 13.1% / 13.1%** (7/61, 8/61, 8/61; the recorded round 10/62 = **16.1%**), **Laya 34.4%** (21/61; recorded round 33.9%). The old numbers (14.5% and 10.3–11.8%) are **values on the depressed denominator**.
   ⇒ The paper **still must not** read this rate as "the proportion of times the LLM noticed the superseded marker"; but after the correction **Laya's rate (34.4%) is nearly three times the LLM's (11.5–13.1%)** — **this one runs opposite to the rest of this section's readings and must be stated side by side** (see the body of §7.6).

**The treatment of κ**: κ is not a suitable criterion on this battery (a low κ proves only "independent", whereas after the fix φ is an **edge-positive correlation** — see the stratified test in §8.6.1). The paper **no longer uses κ for any conclusion**; and it states plainly that the recorded round's κ = 0.0062 has a bootstrap 95% CI of **[−0.185, +0.206]** — reading a point estimate ±0.2 wide to four decimal places.

**⚠️ The still-unresolved power problem**: this battery (**three pinned draws**) has MDE (80% power) = **0.28–0.30** (**⚠️ not the same quantity as the pre-fix battery's 0.311 in §7.6** — the latter is a single draw at n=69), which is **still larger than the pre-declared +0.10 gate**. So although the point estimates are consistently negative, **the precision is still limited**; the conclusion should be stated as "**the direction is consistently negative in 3/3 draws; after switching to the score/Newcombe method, only 1 of the 3 robustly excludes zero and 1 sits at the boundary** (under an unpaired Wald 2 exclude, but that is the interval narrowing caused by the zero cell, see the note above); the **pooled** failure correlation is positive in 3/3 draws, but **after stratifying by K none of the three is significant** (CMH permutation p = 0.059 / 0.055 / 0.201)", rather than giving a precise effect size, and rather than "significantly shared failure".

**Protocol clause (new)**: **wherever a judgment arm is sampled through an API, it is mandatory to (a) pin `temperature` explicitly, (b) report the item-level label agreement between repeated draws, and (c) not use a point estimate at the four-decimal level as the basis of a conclusion.**
→ **But Δ_catch is negative (pre-fix −0.007; fixed version −0.18…−0.25): Laya is not more reliable where the LLM fails.** Its 8 successes are **scattered across both sides**.
→ **Conclusion: the two failing independently ≠ complementary.** The fact that one judge's errors are **uncorrelated** with the other's does not make it a useful backup — **what complementarity requires is a "conditional advantage", not "independence".**

**The ruling on the pre-declared reading** (the reading was written before the run):
> "If the ceiling is broken but Δ_catch is not > +0.10 → even where the LLM fails, the typed judge does not cover its errors."

**Measured: pre-fix battery Δ_catch = −0.007 (n=69), fixed version's three draws Δ_catch = −0.233 / −0.247 / −0.182 (n=68) → all three fall short of the threshold, and the direction is opposite to the threshold.**

**⚠️ But the power of this test must be reported alongside**:
- Δ_catch's SE = **0.1111** ⇒ 95% CI = **[−0.225, +0.211]**; **MDE (80% power) = 2.80 × 0.1111 = 0.311**.
- **The pre-declared threshold +0.10 is far below the MDE of 0.311** ⇒ at n=69, **this test is almost incapable of detecting the support threshold it set for itself**.
- Per-K breakdown (the paper previously reported only the pooled value; filled in here):

| K | n | `P(Laya correct \| LLM wrong)` | `P(Laya correct \| LLM correct)` | Δ_catch |
|---|---|---|---|---|
| 2 | 12 | 0.500 | 0.400 | **+0.100** |
| 4 | 12 | —(LLM 12/12) | — | undefined |
| 8 | 21 | 0.333 | 0.222 | **+0.111** |
| 16 | 24 | 0.214 | 0.300 | **−0.086** |

→ K=8's +0.111 **crosses** the +0.10 gate in the code at a single point, but K=2 is +0.100 and K=16 is −0.086, **with no consistent trend**; and the pre-declaration (`protocol\HARDER-BATTERY-DESIGN.md`) pre-declared only the **regime-level** reading, and **did not** pre-declare a per-K gate, so this is a **post-hoc subgroup** and can be interpreted only after multiple-comparison correction. **It does not constitute complementarity evidence.**
- **Oracle union control (pre-fix battery)**: 49/69 = 0.7101 vs LLM 0.5942 (+0.1159); only Laya correct 8/69, Wilson95 **[0.060, 0.212]**. **The union gain must be compared with the expectation under independence**: if the judge and the generator are independent with accuracy 0.2899, then among the generator's 28 failures one expects **8.1** hits, and **8 are measured** ⇒ **that gain is exactly the value expected under independence, not complementarity**. After the fix φ is positive, but **after stratifying by K it is not significant** (see §8.6.1 for detail) — the argument **remains at "independent"**, and has not been upgraded to "shared failure".
- **Independence test (pre-fix battery)**: the 2×2 χ²(1) = 0.0039, Fisher exact two-sided **p = 1.0000** ⇒ the recorded round's Δ_catch = −0.007 is entirely compatible with "the two judges are independent". **After the fix the same test gives p = 0.086 / 0.049 / 0.163** — no longer compatible with independence.

→ **Ruling (rewritten against the fixed version)**: **the architectural claim is not supported, and the evidence is stronger than before the fix.** The ceiling effect can no longer be used as an excuse — **the ceiling has been broken, the LLM really is failing (about 33%), and the cheap judge not only fails to cover its errors, but its failures run in the same direction as the generator's (φ > 0 in 3/3 draws; but Fisher p < 0.05 in only 1/3, see above).**
→ The pre-fix recorded round (69 items, Δ_catch = −0.007) is retained as **a measurement with a disclosed defect**, whose ground-truth defect has been explained above.

### 7.6.2 An incidental result: two fundamentally different failure modes

**⚠️ The shape must be corrected (fifth round): it is not "monotonic collapse with depth", but "one drop between K=4→8, completely flat thereafter".**
Per-K recomputation (the three pinned draws merged, LLM judgments / total judgments at that K):

| K | LLM accuracy (3 draws merged) | Laya | Fisher exact p for the adjacent contrast |
|---|---|---|---|
| 2 | 33/36 = **0.917** | 0.417 | — |
| 4 | 36/36 = **1.000** | 0.250 | K=2 vs K=4: **p = 0.239** (not significant, and the direction is **upward**) |
| 8 | 32/63 = **0.508** | 0.286 | K=4 vs K=8: **p = 3.6×10⁻⁸** |
| 16 | 35/69 = **0.507** | 0.261 | K=8 vs K=16: **p = 1.000** (**completely flat**) |

⇒ The pooled contrast of shallow (K∈{2,4}) against deep (K∈{8,16}): **23/24 = 0.958 vs 45/88 = 0.511, Fisher p = 1.4×10⁻⁴ (all 3 draws at the 10⁻⁴ order of magnitude)**.
⇒ So **the "collapse" happens at a single crossing only**: for K≤4 it is near the ceiling, and for K≥8 it drops to about half and **no longer worsens with depth**.
⇒ **The original text's "collapses with depth" and "K=2 → K=16, 0.917 → 0.478" describe only r1, that single draw**; r2/r3 **rise** from K=8 to K=16 (0.476 → 0.522), and **not one** of the three draws is monotonic (K=2→K=4 rises in **3/3**).
⇒ **The mechanism is not yet determined**: the deep-chain errors **are not** "getting one step wrong and compounding" — if it were error compounding, K=16 should be significantly worse than K=8, and the measured difference is zero. **Item by item, almost all of the LLM's errors at K≥8 land on an approximate decoy in the neighbourhood of the ground truth** (rather than "exactly equal to the value after ignoring supersession", which at K≥8 accounts for only 16.7% / 29–32% of its errors, see §7.6). The more likely explanation is **a switch, at some depth, from "executing" to "choosing one among near-neighbour candidates"**; **this battery has no design** that distinguishes the two mechanisms, so only the phenomenon is recorded here, and no claim about mechanism is made.

| | LLM | Laya |
|---|---|---|
| K=2 → K=16 (pre-fix battery) | 0.833 → **0.417** | 0.417 → 0.250 |
| K=2 → K=16 (fixed version, three draws) | 0.917 → **0.507** (1.000 at K=4) | 0.417 → 0.261 |
| **Shape** | **one drop (K=4→8), then flat** | **flat, always near chance** |

→ **Laya is already only 0.417 at K=2 (the simplest form of this battery), and does not change with depth** → **it is not "degrading with depth", it is simply not performing chain-style computation at all.**
→ This is consistent with §6.3: it **collapses on tasks where "something's absence must be noticed"**, and **every line of this battery requires it to notice the `SUPERSEDED` marker**.

| judge | failure mode | does it worsen with load |
|---|---|---|
| **LLM** | **a single drop**: falls between K=4→K=8, flat thereafter (**not error compounding** — p = 1.000 for K=8 vs K=16, mechanism undetermined, see §7.6.2) | ⚠️ **No** |
| **Laya** | **capability absence**: constant near chance | ❌ No |

→ **The implication for "long-horizon tasks"**: **using a constantly-failing component to backstop a cumulatively-failing component cannot work in principle** — and this is the structural background to Δ_catch being negative (**⚠️ Eighth-round correction: the original printed "Δ_catch ≈ 0", which is the pre-fix −0.007; the fixed version's three draws are −0.182…−0.247**).

---

## 7.7 The evidence on truncation (P24 + P26)

§5.3.1–5.3.2 report window erosion and truncation harm in cumulative runs. Here we record only what they mean for **this section's claim**.

**The part that can serve as evidence is "truncation occurs"**: P24 shows that of 60 steps only 14 fit into the window, with a final-state 3.4× clamp; P26's 20 calls all record `in_pad = 512`, `truncated = true`.

**⚠️ But P26's original design is insufficient to prove "truncation changed the answer"** (see §5.3.2 for detail); it has two defects:
(a) **The two arms' visible prefixes are bit-identical** — the dropped arm still has a ~4× clamp, and the correction sits at tokens 1,943–1,952, **beyond the 512 window the two share**, so "the two arms give the same answer" is a **construction necessity**;
(b) The option order is collinear with the answer (the decoy is always in first position, the ground truth always in last position), and Laya picks the first position 10/10 times.
**On review the missing control was filled in**: **⚠️ that quantitative assertion has been withdrawn (seventh round)**: that set of numbers (6/10, 4/10, p = 0.011, state 79–92 tokens) **has no artifact anywhere in the whole tree**, and its state size is exactly that of P26's **discarded first prototype**. **Withdrawn**; this section keeps only the artifact-backed part, "truncation occurs".

→ So this section's "unified shape" has **two artifact-backed instances, and the third is under-supported**: the truncation cell **can only be established as far as "truncation occurs"** — the early version's printed "explains about 6/10 of them, with the other 4/10 occurring when the evidence was fully visible" **rested on a control arm that has no artifact, and has been withdrawn (eighth round)**.

| task | what must be "noticed" | Laya | LLM |
|---|---|---|---|
| chained verification (K=2…16) | that a line is marked superseded | **0.25–0.42 (constant)** | **0.917 → 1.000 → 0.508 → 0.507** (fixed version, three draws merged; flat after K≥8, **non-monotonic**)|
| `no_support` stratum (n=220) | that the candidate value **never appeared at all** | **acc 0.3091, mean P(true)=0.5643** | ~1.00 |
| over-window state (control arm, n=10) | the correction is **fully visible** yet not adopted | **⚠️ that control has no artifact, the numbers are withdrawn** | — |

→ **Neither of the first two is "insufficient compute"; both are "no channel for detecting absence".**
→ **The third is different in kind and must be stated separately**: (that decomposition has been withdrawn: the control arm it rested on has no artifact), it is "seeing but not adopting", and **not** detection of absence. So "no channel for detecting absence" **cannot** cover it.

---

## 7.8 An experiment not yet executed: **autonomous** runs with cross-session accumulation

**This section's horizon evidence is a reduced version**: P24's 3×20-step accumulation is **within a single process**, with **no tool use**, **no cross-process recovery**, and the judge is invoked as a **judgment device**, not as an autonomous agent.
→ **What it measures is "whether accumulated state erodes the window, and whether truncation changes the answer", not "the reliability of autonomous long-horizon runs".**
→ **The paper must not upgrade it to the latter.** See §10.1 item 1.

---

## 7.9 Limitations

1. **Regime one's ceiling effect occurs only in the forced-choice arm** (LLM 48/48); **on the prose arm the LLM is 46/48 with 1 judge-only item, Δ_catch = +0.0435 (Newcombe 95% CI [−0.386, +0.471]) — a positive point estimate resting on only 2 items where the LLM errs** ⇒ that arm likewise **cannot prove the absence of complementarity**, and it **can** produce an (imprecise) **positive** point estimate; the rest of this section's conclusions rest on the **forced-choice** arm's "only judge correct 0", which this correction does not touch;
2. **Regime two is n=40**, and one item moves it by 0.025; **the magnitude of Δ_catch goes from −0.029 to −0.257 across the 4 draws** ⇒ what can be said is **"the direction is negative in 4/4, and the recorded round is the most favourable one"**, not "the effect size is −0.033";
3. **Contamination**: Banking77 is Laya's **prior set**, while **exposure on the LLM side is more direct** — `D3` itself records that the model was trained on 45T tokens including Common Crawl, and writes explicitly that "the LLM may have memorised the labels".
   **⚠️ The argument that "contamination is conservative" therefore covers only one side and must be corrected**: Banking77's test sentences and its 77 label names are all public plain text, and the LLM's 0.75 would be hard to reach without memory; while **the negative Δ_catch is held up precisely by the "23 items only the LLM got right"** — **contamination on the LLM side runs in the same direction as this paper's negative conclusion, not in the conservative direction**.
   ⇒ This regime's negative result is therefore **stronger** (if contamination raises the LLM, it only makes complementarity look worse), but **the universal extrapolation "a heterogeneous judge is useless" cannot be built on this regime**. The genuinely clean regime is **regime three** (the ground truth is generated by program simulation, not taken from any public corpus).
4. **Laya's hierarchy uses programmatic grouping** (agglomerative, by token similarity of label names), and **the quality of the top-level grouping is itself the bottleneck** (group selection 0.275). **Switching to a semantically better grouping might improve end-to-end**; this round did not test it — this is the most important unexplained factor in this section;
5. **The LLM was measured in only one configuration** (`deepseek-flash`, non-thinking, single draw).

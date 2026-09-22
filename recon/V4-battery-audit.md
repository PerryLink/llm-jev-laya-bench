# V4 — Adversarial audit of the task battery and the horizon manipulation

**Unit:** V4 (verification, adversarial)
**Targets:** `R5-synthesis.md` §5 (the merged design) and `R14-long-horizon-battery.md` (the battery, dial, N, T3)
**Checked against:** `R13-laya-probe.md` (measured Laya limits), `R2-verified-externals.md` §A/§B, plus cross-reads of `R15-arms-and-process-metrics.md` §5 and `V5-reproducibility-audit.md` §0.
**Method:** document analysis only. I made **no live judge, Laya, Jev or LLM calls**. Every number below is either quoted from the files or is arithmetic I show in place. Where I recompute a design quantity I say so and give the formula.

**Scope note on overlap.** V5 §0 BLOCKER-1 already establishes that the paper's stated headline (silent truncation vs horizon) has no instrument, because R14's gate G1 rejects any state that would truncate. I reach the same conclusion from a different direction in Q3 and do not re-claim it as new; I extend it with the fairness/estimand argument and a quantified envelope-waste computation. V5 §0 items 5 and 6 (missing 1000-item corpus; two dials called "horizon") also stand and are not repeated.

**Headline of this audit.** The families are largely fine; **the dial is not.** R14's four families do contain real accumulate-error structure and pass LH-1/LH-2. But the instrument that is supposed to turn that structure into a dose-response measurement does not manipulate horizon: `d` is a deterministic relabelling of junction index, the local block is byte-identical across levels so all within-item variation lives in a ≤55-token carrier, and raising `d` mechanically lowers the probability that the decisive trace is present at all. The measured "slope" is therefore a mixture of position, trace recency and trace presence that the design cannot separate — and the pre-registered remedy (`survives`-only analysis) is a post-treatment selection that cannot fix it.

---

## 0. Verdict summary

| # | Question | Verdict |
|---|---|---|
| 1 | Does the battery test HORIZON or many steps? | **sound-with-fix** — families pass LH-1/LH-2; the dial fails. 57% of the primary 300 have keys that cannot respond to the manipulation. |
| 2 | T3 poison survival | **sound-with-fix** — resolvable, but the fix changes the estimand. As written it is a limitation that forbids the causal wording. |
| 3 | Fixed-width carrier vs Laya's window | **sound-with-fix** — equal-information protocol is a valid *estimand*, invalid as a *claim*. Handicaps exist in both directions; one is unquantified. |
| 4 | Equal footing of item classes | **sound-with-fix** — two classes unfair (Q2-F4, Q5-F3), one structurally degenerate (Q4), one requires a symbolic baseline gate (Q4), one metric choice is wrong (Q6). |
| 5 | Ground truth | **sound-with-fix** — anti-circularity holds for all four families; F2's "no model labels anything" is verified. Two oracles are author-relative, and one difficulty knob manufactures unanswerable keys. |
| 6 | The horizon dial as dose-response | **unsound-with-repair** — `d ≡ H−4` exactly (no independent variation), fixed width confounds distance with presence, floor reads off a different run, family poison junctions contradict the common dial. |
| 7 | N = 300 for the horizon claim | **sound-with-fix** — the *slope* is genuinely well powered (R14 under-sells why); the *marginal contrast* is not (n_eff ≈ 77–106 vs 234 required); the inferential unit for the headline claim is contradictory across units. |

---

## Q1 — Does the battery actually test HORIZON, or merely MANY STEPS?

### 1.1 What R14 claims, and what it is entitled to

R14 §2 line 79: *"The phrase is empty unless it is operational. A family qualifies only if all three hold, and each must be demonstrated with a witness at design time, before any judge is called."* The three tests are LH-1 (non-separability, line 83), LH-2 (history-dependent optimal policy, line 85) and LH-3 (lossy carrier, line 87).

**The families pass.** This deserves to be said flatly before the criticism:

- **F1 SPECSHIFT** has a genuine propagation chain at R14 lines 101–105: the J≈4 reading `legs[0] += residual` "is a defensible reading, and the §7.2 test passes because in the test fixture leg 0 *has* the largest remainder"; at J32 the v2 change to banker's rounding produces no failure "because `sum(legs) == total` holds under both rules and no test inspects *which* leg received the residual"; at J64 the ingest rewrite "reuses the (now wrong) residual helper"; at J96 "Exactly 12 rows differ, all of them rows written before J32." That is a real 90-junction invisibility window with an executable oracle. Not "many steps".
- **F2 EVIDENCE-BRIEF** propagates through a claim dependency graph of depth 1–5 (line 125) and an oracle that is *global*: line 139, *"Correctness of the terminal artifact is a *global* property — closure of the trace — and no single section exhibits it; an early over-claim makes later sections look *better*, not worse."* That last clause is the correct statement of LH-1: the local signal is anti-correlated with the global one.
- **F3 SCHEMA-EPOCH** has the cleanest irreversibility: line 149, *"The rows are already written; recovery requires re-reading `evt_raw` — and **the harness revokes source access at J64**... each epoch was locally correct."* LH-2 witness at line 159 is concrete and falsifiable.
- **F4 AUDIT-CASCADE** has the only genuinely path-dependent *metric*: line 179, *"the same per-item classifier with 92% accuracy yields 55% or 78% recall depending on where the budget went."*

F4's negative control is also the right instrument: line 187 retains uniform triage as *"the horizon placebo: if drift-vs-horizon is flat there and slopes in F1–F4, the knob is doing what the paper claims and the effect is not 'long contexts are hard in general'."* That is exactly the control a reviewer would ask for.

### 1.2 Family-by-family: the propagation mechanism, and whether the design can separate horizon from difficulty

| Family | Mechanism by which an early error *must* propagate | Early error | First visible surface | Can the design separate "horizon grew" from "task got harder / state got longer"? |
|---|---|---|---|---|
| **F1 SPECSHIFT** | A stale helper survives two spec epochs and one file rewrite; the deciding fact (which stored rows obey which rounding rule) exists only in the code's history, not in any failing test before J96 | J4 residual allocation | J96 replay: 12 pre-J32 rows differ | **State length: controlled** (§5.2 item 5, "Same total token count within ±8 tokens"). **Task difficulty: controlled** (§5.2 item 1, local block byte-identical across the 5 levels). **Information content: NOT controlled** — the trace must be in the ≤55-token carrier to be answerable at all, so `d` and `trace present` move together. |
| **F2 EVIDENCE-BRIEF** | A wrong claim status (C-11 at J≈8) is inherited by sections 3 and 7 and by C-24 (derived at J≈70 from C-11 + C-19); the memo's conclusion chain is unsound at J128 | J8 status call | J128 traceability closure | Same as F1, **plus** a structural problem: the F2 *items* do not depend on the run at all (see §1.4). |
| **F3 SCHEMA-EPOCH** | Epoch-local-correct choices compose into a jointly-wrong store; source revocation at J64 makes it irreversible | J12 `+00:00` stored verbatim | J96/J128 `session_key` mismatch | Irreversibility is a **step function**, not a gradient: every junction ≥J64 is equally unrecoverable. Fitting a linear-in-`log2(H)` slope to a step is model misspecification, and F3's key for underdetermined columns is the authors' private reference transform (§5.3 below). |
| **F4 AUDIT-CASCADE** | An early false negative prunes a subtree permanently; the recall ceiling drops and no later diligence recovers it | J6 first stratum call | `recall@400` at termination | **Partly yes** — F4's key is a genuine counterfactual rollout. But the worked example (R14 lines 373–377) puts the stratum statistics *in the options*, so the carrier is decorative and the item reduces to an argmax over numbers printed in the stem. |

### 1.3 The defect is in the dial, not the families

R14 §5.1 line 396 states the operationalization: *"Horizon is **position in one frozen run**, and it is operationalized as **distance from the planted upstream error** `d`, which is the mechanism the paper is about."* The dial table (lines 398–404) is:

| Level | H | d |
|---|---|---|
| H0 | J1 | — |
| H1 | J4 | 0 |
| H2 | J8 | 4 |
| H3 | J32 | 28 |
| H4 | J128 | 124 |

**d = H − 4 exactly, for every level at which d is defined.** There is no cell in the design where position is long and the trace is fresh, or position is short and the trace is old. The two variables are perfectly collinear, so the design *cannot* distinguish "distance from the poison" from "position in the run" — which is precisely the distinction R14 §1.2 (line 41) says the paper exists to make: *"the paper can claim horizon effects on Class G directly... and on Class D only *through the carrier*"*.

Combined with §5.2 item 1 — *"The local block is byte-identical across the five levels of a slot (same claim, same span, same hunk, same record)"* — every item in a slot is **the same question** with a different ≤55-token decoration. So the *only* thing the manipulation varies is which five ledger lines are shipped. R14 §5.2 item 3 says horizon *"changes the content of the tail, never its size."* That is honest, but it means the manipulated variable is *carrier content*, and the name "horizon" is doing rhetorical work that the manipulation does not do.

### 1.4 57% of the primary 300 have keys that cannot respond to the manipulation

This is the most damaging concrete finding in Q1. R14 §4.2 defines the ground-truth source of each item class (lines 228–238 and the class sections). Cross-tabulating the key's dependency against the manipulation:

| Class | /level | Key | Depends on the carrier? |
|---|---|---|---|
| Q1 clause-consistency | 8 | *"the clause's pytest node id or its AST predicate, evaluated on the artifact"* (line 244) — the artifact is in `LOCAL` | **No** |
| Q3 rubric-score | 8 | levels are *"a conjunction prefix over statically decidable predicates"* on the shipped hunk (line 257) | **No** |
| Q4 evidence-verdict | 12 | the coverage function over `(claim, span A, span B, tiers, scopes)` (lines 263–264) | **No** |
| Q5 shortlist-rank | 6 | *"F1 — number of currently failing acceptance tests blocked by the clause; F2 — planted source tier and dependency out-degree; F3 — number of downstream assertions affected; F4 — simulator terminal recall"* (line 272) | No for F1–F3; marginal for F4 |
| Q2 next-action | 12 | exhaustive rollout of the remaining run under a scripted reference policy (line 250) | **Yes** |
| Q6 halt/escalate | 8 | reachability rollout; R14 line 279: *"the local block alone yields the *wrong* answer; only the carrier flips it"* | **Yes** |
| Q7 summary-faithfulness | 6 | fit of S to the run log through J_n | **Yes** |

**Horizon-live: 26 of 60 items per level (Q2+Q6+Q7) = 130 of 300 = 43%. Horizon-inert: 170 of 300 = 57%.**

Two of R14's own sentences confirm this reading. Line 279 names Q6 as the class where *"only the carrier flips it"* — if that were true of Q2, Q4 and Q5 as well, R14 would not have needed to single out Q6. And line 265 describes Q4 as *"where a 421M encoder can plausibly beat a large generative model on cost-adjusted accuracy, because the decision is **local, short, and shape-based**"* — R14 states outright that Q4's decision is local, i.e. the carrier contributes nothing to the key.

The consequence for the estimand: a judge that ignores the carrier entirely gets 57% of the battery right *for the right reason*. Any measured drift on those 170 items is a **distractor effect** — the carrier making an otherwise answerable question harder — not horizon-dependent judgment. Pooling them into a single `judge × log2(H)` slope attenuates the coefficient of interest by roughly the live fraction and adds variance without signal.

### 1.5 What is genuinely fine here

- LH-2's witness requirement (line 85: two path-divergence witnesses per family, *"a written pair `(prefix_A, prefix_B, a*_j(A), a*_j(B))` computed by the oracle, with a one-line causal account"*) is the right demand and F1/F3/F4 satisfy it.
- §5.2 item 6 (*"Same primary-span position: always inside the first 40% of the state, so Laya's end-truncation can never be the explanation"*) correctly removes the one alternative explanation R13 makes salient.
- §5.2 item 7 (Latin-square option position) and item 8 (family mix) are the right nuisance controls and are correctly specified.

**One further defect in the qualification tests themselves.** R14 §2 line 81 says *"each must be demonstrated with a witness at design time."* LH-1 has a stated test (line 83), LH-2 has a stated witness procedure (line 85), and **LH-3 has neither** — line 87 states a *requirement* ("the information needed at `j` must survive a bounded-width carrier") and then concedes it cannot be verified ("see §6, T3 — the threat I could not fully close"). So the one gate that would certify the item is answerable is the one gate with no procedure. §5.3's mention-flag is per-item and post-hoc, not a design-time witness.

**VERDICT: sound-with-fix.** The families are not "merely many steps" — F1–F4 each ship a real accumulate-error mechanism and a computable oracle, and F4-CTRL is the correct placebo. The dial is the defect.

**Minimal fix (three parts, all cheap):**
1. **Promote the carrier-lift manipulation to primary.** §4.3 already builds exactly the right instrument: two variants with identical token counts, `L` (neutral filler in the carrier slot) and `L+C` (the real carrier). Run **both variants of all 300 items** — 600 observations at the cost of one extra judge call per item per judge. The estimand becomes `acc(L+C) − acc(L)` per level, i.e. **carrier-lift × log2(H)**, which is the mechanism claim and is free of the trace-presence confound (it is manipulated *within* item). Demote the raw accuracy × log2(H) slope to secondary.
2. **Add a recency cell at H4.** Build one extra H4 condition in which the decisive carrier line is re-injected as the *most recent* ledger line ("H4-refreshed"): long position, fresh trace. If accuracy returns to H1 levels, the effect is trace distance and the horizon wording survives; if it does not, the effect is position/context and the paper must say so. R14's own F1 difficulty knob (c), *"detection delay between clause and catching test 0→90 junctions"* (line 111), is the material for constructing it.
3. **Report the two item populations separately.** Pre-register a horizon-live stratum (130 items: Q2/Q6/Q7) as the primary horizon estimand and the 170 inert items as the accuracy/calibration population plus a **distractor placebo** (expected lift ≈ 0; a nonzero lift there is pure distraction and is itself reportable). Never pool them into one slope without naming the mixture.

---

## Q2 — R14's admitted unsolved threat T3 (poison survival)

### 2.1 What R14 concedes

R14 §6 T3, line 446, verbatim:

> *"If, at `d = 124`, the shipped 5-line carrier under-determines the correct answer, the item is unanswerable by construction and any measured 'drift' is an artifact of item construction, not judge degradation. The §5.3 mechanical flag is a *proxy* for a counterfactual about inference, not the counterfactual itself... None of these fully closes it: whether a judge 'could have' recovered the poison from a fixed-width string is not decidable from the string alone."*

And the design's own framing at line 19: *"The one thing to read if you read nothing else: §1.4 (state parity) and §5.3 (poison-survival classification). Without them the paper's central claim is unfalsifiable."*

### 2.2 There is a prior problem: the design is constructible in two mutually exclusive ways, and both kill the dose-response reading

R14 never states whether the 5-line carrier is a **rolling tail of the frozen run log** or a **curated ledger that retains the decisive line**. §5.2 item 3 (*"Horizon changes the content of the tail"*) and the ledger-line format at §4.1 (*"`J{n} {decision} -> {consequence}`"*) both point to a rolling tail. §5.3 (*"Report the flag... and the survival rate **per level**"*) presumes survival *declines* with level, which only happens if the carrier rolls. So take the rolling reading:

- **Horn A (rolling tail).** At H3 and H4 the J4 line has long since rolled out. §5.3 classifies those items `absent`, and §5.3's pre-registered rule is: *"the primary drift-vs-horizon analysis is run on `survives` items only."* The primary analysis therefore has **approximately zero items at H3 and H4**, and gate G7 (*"per-level rates reported; on failure: block the drift analysis"*, line 489) fires. The headline experiment cannot be run as pre-registered.
- **Horn B (curated ledger).** The poison line is retained at every level. Then `survives` ≈ 100% everywhere, the `absent` lower-bound control (§5.3: *"if accuracy also falls on `absent` items, the effect is not carrier-mediated"*) is empty, and the only thing that varies with `d` is the number of intervening no-op lines — a primacy/recency manipulation, not a horizon manipulation.

There is no third reading in the document. This is a **constructibility contradiction**, not merely an unresolved threat, and it should be resolved before anything else in Q2 matters.

### 2.3 The §5.3 flag is one-sided, and the `survives`-only rule is post-treatment selection

The flag as specified (line 427): *"does any shipped carrier line or summary sentence mention the entity/module/column affected by the planted error, or a consequence of it?"*

- **False positives**: a line can name the module without entailing anything ("J04 touched the residual helper"). The flag says `survives`; the item may still be unanswerable.
- **False negatives**: a line can entail the trace without naming the entity ("J04 rounding follows the largest fractional part"). The flag says `absent`; the item may be perfectly answerable, and it is then *excluded* from the primary analysis.
- Neither error rate is measured or bounded anywhere in R14.

Worse, §5.3's remedy is: *"Pre-register that the primary drift-vs-horizon analysis is run on `survives` items only."* Under Horn A, survival is a **deterministic consequence of the treatment** (`d` ↑ ⇒ trace rolled out ⇒ `survives` = false). Conditioning on it is conditioning on a post-treatment variable: the `survives`-only slope does not estimate the effect of `d`; it estimates the effect of `d` within a subpopulation whose membership was caused by `d`. R14 §4.5's T8 correctly worries about pseudo-replication and cluster bootstrap, but this selection problem is not in the threat list at all.

### 2.4 T3 is resolvable — the concrete design change

T3's own framing ("whether a judge *could have* recovered the poison... is not decidable from the string alone") is too pessimistic. Three additions close it operationally:

1. **Build-time entailment + necessity certificates (replaces the mention flag).** For each item, the harness holds the family's oracle language (F1 AST predicates, F2 coverage function, F3 SQL assertions, F4 rule engine). Then compute mechanically:
   - *Entailment*: does `shipped_state ⊢ key` hold under the oracle's inference rules? (In F1, does some shipped line fix the rounding rule?)
   - *Necessity*: does deleting the decisive line leave ≥2 keys consistent with the shipped state? If not, the item is answerable from `LOCAL` alone and is a **free item** that dilutes the slope (this is the mechanical detector for the 170 inert items of §1.4).
   Both are properties of the shipped strings plus the oracle, i.e. inside the experiment's own formal system. This does not require solving the general "could a judge have inferred it" question; it requires only that the authors fix the inference rules, which they already have. This also fixes LH-3's missing witness procedure (§1.5).
2. **Derivability ceiling check (DCC) for the residual human question.** Run a fourth judge-visible configuration **outside the primary N**: the same LLM given the item *plus the full frozen run log*. If the full-context LLM succeeds where the fixed-carrier judges fail, the deficit is carrier-mediated; if the full-context LLM also fails, the item is broken and is dropped. Pair it with R14's own mitigation (b), the human 60-second audit, but note that R14's *"must derive the key within 60 seconds"* conflates derivability with reading speed — report the derivation time as a covariate or drop the limit.
3. **Analyse survival as a mediator, not a filter.** Replace the `survives`-only primary with a mediation model on all items: total effect of `d` on accuracy, plus the indirect path through the (now certified) trace-presence indicator. R14's mitigation (c), *"the two-width carrier-lift probe (5 lines vs 5 lines + summary) to see whether added carrier resolves the item"*, is the same idea done at n=50; the §1.3 fix above scales it to n=300 and folds T3(c) into the primary design.

### 2.5 If the team will not do this: exactly what must be weakened

- **Must be deleted from the abstract and results:** "judgment quality degrades as the horizon grows"; "the judge degraded because the horizon grew"; R5 §0's *"能力随 horizon 静默退化"* ("capability degrades silently with horizon") as a causal statement.
- **May be claimed instead, verbatim-worthy:** *"On a fixed-width (5-line, ≤55-token) carrier over a frozen 128-junction run, accuracy on items whose key requires an upstream trace declines by X points per doubling of trace distance (95% CI ...). Between Y% and Z% of that decline is attributable to the measured decline in trace survival and cannot be separated from item unanswerability at d = 124."*
- **Mandatory reporting:** per-level survival rate, the entailment/necessity certificate outcomes, the DCC pass rate, the human-audit exclusion rate, and the `absent`-subset accuracy as a lower bound. R14 already commits to all of these except the certificates and DCC.
- **Separable and unaffected:** R13's silent-truncation measurement is a *state-width* effect and stands on its own (see Q3).

**VERDICT: sound-with-fix.** T3 is not fatal and not merely a limitation — it is resolvable by certificates + DCC + mediation. But the fix changes the headline from a causal horizon claim to a mediated carrier-distance claim, and R14's current mitigation set (mention-flag, 30-item human audit, n=50 two-width probe) is too weak to support the causal wording.

---

## Q3 — The fixed-width carrier versus Laya's fixed window: is the comparison rigged?

### 3.1 The equal-information argument is sound as an estimand and unsound as a claim

R14 §1.3 R-LAYA-1 (line 62): *"every item shipped must fit Laya's English 512-token window with margin."* R1 (line 69): *"Every judge receives the **byte-identical** state string, the same option strings in the same order, the same label set, single-shot, no tools, forced choice."* R3 (line 73): *"A judge that wants more context has failed the item. 'LLM-as-judge with retrieval/tools' is a *different arm* `[→ARMS]` and a different estimand."*

The within-item comparison is genuinely fair, and R1's hash-and-freeze is the strongest single piece of design in the battery. **But byte-identical inputs make the comparison fair; they do not make the construct neutral.** The state width is set to the maximum the weakest instrument can read (R5 §4.2 rule 5: *"硬上限 450 state token/问"* — hard cap 450 state tokens per question) rather than to the width at which the task's decisions naturally occur. R5 §5.5 lists `token_ratio(t)` — *"Laya 可用性随 horizon"* ("Laya availability as a function of horizon") — as a process metric precisely because natural states exceed the window. So the design already concedes that the deployable state often does not fit, and then builds the entire head-to-head inside the fit.

### 3.2 Both instruments are handicapped, in opposite directions — the fairness argument is not one-sided

- **Against the LLM:** DeepSeek-V4.1-Flash has a 1M context (R2 §A). The design removes that entire capability and then measures whether the LLM degrades on a 55-token carrier. R14 §1.2 line 43 is explicit that this is the intended mechanism: *"Horizon degrades the **carrier**. A judge that must rely on the carrier degrades with it. A generative model partially escapes this because, as generator, it can *rebuild* context by acting — which is exactly the ability it does not have in the judge role."* The design therefore constructs a situation in which one contestant's principal advantage is forbidden, and calls the result a property of judgment layers.
- **In Laya's favour, on cardinality:** R14 §4.2 line 253: *"4 candidates is the ceiling, and the ceiling is Laya's, not ours."* R13 §3.2 measured Laya's collapse at 20 options (`mobile_app 0.9993, confidence 0.9981` on the only wrong answer) with compression beginning at 11 options on Path A. Pinning every item to ≤4 options excludes the regime where Laya is **worst** while including the regime where it is best.
- **In Laya's favour, on determinism:** R5 §3 conflict 2 (line 75) notes that typed judges are bit-identical on repeat (R13 §6.1) while the LLM arm must sample. R5 says this asymmetry *"对类型化判定器有利，应在论文中明说"* ("favours the typed judge and should be stated in the paper"). Stated, yes — but R14 R4 (line 75) scores the LLM as *"first valid label token"*, a **single sample**, against Laya's deterministic call. The primary contrast is therefore a deterministic estimator versus a noisy one, which understates the LLM. R5's k=8 self-consistency arm (A5c) exists but lives *outside* the primary N.

So the design is a compromise, not a handicap aimed at one side. What is *unfair* is not the equality of inputs — it is the **unquantified** narrowing of the LLM's evidence budget while Laya is run inside its comfortable envelope.

### 3.3 The battery cannot exercise the failure mode the paper headlines

R5 §0 line 18 makes the headline: *"优势在**并行检查 + 无顺序往返 + 自带升级语义**；但**能力随 horizon 静默退化**（R13 实测静默窗口 ≈300 字符）"* ("the advantage is parallel checking + no sequential round-trips + built-in escalation semantics; but capability degrades silently with horizon (R13 measured a silent window of ≈300 characters)").

The parenthetical is the whole evidential basis, and it is a **state-width** finding, not a horizon finding: R13 §2.5 (line 287) — *"Real truncation begins at `state_tokens > 512 − head_tokens − 1`. For this question (`head_tokens = 61`) that is **> 450 tokens ≈ 2850 chars**"*; R13 §2.4 shows the flip at 2836 chars with `truncated` absent and `fits: true`. Meanwhile:

- R14 G1 rejects every item that would truncate (line 483: *"state ≤512 tok (target ≤497)... reject item, report drop rate"*).
- R14 §5.2 item 5 holds total token count *"within ±8 tokens"* across levels.
- R5 §4.2 rule 5 caps state at 450 tokens; rule 6 (*"决定性证据永不放 state 尾部"*) prevents the tail position that R13 proved fatal.

**The battery is designed so that the motivating failure cannot occur.** This is V5 §0 BLOCKER-1, reached independently; I add the mechanism: the truncation result is a function of state *width*, and the dial deliberately fixes width, so no manipulation in R14 can vary it. The only instrument that could measure it is `token_ratio(t)` on live run states (R5 §5.5), which has no design, no N, and no power analysis in any unit's plan. If the paper's headline is silent degradation, the battery cannot support it and the support must come from elsewhere.

### 3.4 A quantified, reclaimable waste in the envelope

R14 §4.1 (lines 204–220) budgets the assembled question as: scaffold 35 + carrier 55 + local 190 + stem 25 + boundary 40 + options 152 = **≤497** against Laya's 512-token window. That puts the "head" (scaffold + stem + options) at **212 tokens**. R13 measured head costs of **113** tokens (bare noul, `head_tokens_estimated`) and **106** (noul carried as a 2-option choice), with a real built-sequence overhead of ~61 tokens (`input_tokens_padded = state_tokens + 61`, R13 §2.3). Even allowing generously for 4-option questions, R14 is over-budgeting the head by roughly 100–150 tokens, i.e. the state is capped near 285 tokens where R13's measurements permit ~450.

The consequence is exactly the Q3 fairness problem in miniature: **a third of Laya's usable window is left unused, and it is evidence the LLM judge is also denied.** Fix: derive the envelope from the checkpoint tokenizer (`_models/laya/tokenizer/tokenizer.json`, as R5 §4.2 rule 4 and R13 §10 rule 1 require) with the *measured* head cost per question shape, and report the achieved state size per item. Expect to reclaim ≥150 tokens of `LOCAL`/`CARRIER` capacity per item — a >50% increase in the evidence any judge sees.

**A related gate defect.** R14 R2 (line 71) gates on `laya_plan(..., strict=true)`. R13 §1.2 shows the plugin `laya_plan` is broken (`"value.fits" must be a boolean`); R13 §2.5–2.6 show the two hosts' planners err in **opposite directions** — Path A optimistic by ~300 chars, Path B pessimistic from 1399 chars where `input_tokens_padded: 265` proves no truncation occurred. R5 §4.2 rule 7 says *"不使用插件 `laya_plan`（已损坏），改用 `mcp__laya__laya_plan` 或直接 `POST /plan`"*. But `mcp__laya__laya_plan` **is Path B** (`max_len 512 / head_max_len 192`, `state_room_estimated: 405`) — using it to gate Path A items (room 917) over-rejects systematically. R13 §10 rule 12 already gives the correct rule: *"Gate on your own arithmetic; use Laya's numbers as corroboration only."* R14's G1 should say so explicitly.

### 3.5 The honest interpretation of the result

If Laya matches or beats the LLM judge on 300 items at ≤497 tokens:

> **Licensed:** "Within a fixed evidence budget of ≤450 tokens and ≤4 options — the regime in which a local non-autoregressive judge is deployable — a 421M typed judge is/ is not competitive with a frontier generative judge on the same typed questions, at X% of the per-decision latency (R13 §8.2: 3.2–37.4 ms) and no output tokens."
>
> **Not licensed:** "typed judges fail at long horizons"; "generative judges degrade over long tasks"; "judgment quality degrades with horizon". Every judge in the battery was denied the run, and R14 says so itself (line 41: Class D claims hold *"only through the carrier"*).

The one strengthening move available is the **LLM-only evidence-budget extension**: run the same 300 slots at ≥2 widths (450 tokens and the full frozen log) with the LLM judge only, and report Δ accuracy and Δ lift. That converts "the design handicaps the LLM" from an objection into a measured quantity, and it is the same run as Q2's derivability ceiling check. One artifact, two defects closed.

**VERDICT: sound-with-fix.** Neither "biased against the LLM" nor "fair" is the right description: the design is a valid, narrow estimand (fixed shared evidence budget) whose *name* overclaims. Fixes: (i) rename the estimand in the abstract to the fixed-budget reading; (ii) re-derive the envelope with the checkpoint tokenizer and reclaim ~150 tokens; (iii) gate G1 on own-tokenizer arithmetic, `laya_plan` as corroboration only; (iv) add the LLM-only evidence-budget extension; (v) either declare single-sample as the deployable LLM regime on purpose, or promote a k-sample marginal variant into the primary N.

---

## Q4 — Are the decision items answerable by all three judges on equal footing?

R14 §1.3's capability matrix (lines 49–59) is honest about *form*: it excludes Laya from `rank` and reduces it to a `choice`, and it caps options at Laya's ceiling. The question is whether the *content* of each class matches. Class by class:

| Class | Genuinely discriminative text-only work? | Structural bias found |
|---|---|---|
| **Q1 clause-consistency** | **Yes.** `CLAUSE` + `ARTIFACT` + boundary, single-hop, the interesting half being the "undetermined" arm (line 246: *"40% of Q1 items have artifacts that neither satisfy nor violate the clause, and a yes-biased judge fails them"*). | None material. |
| **Q2 next-action** | **No for F4, arguably for F1.** | **F4 is unfair toward Laya by construction.** The worked example (lines 373–377) prints the stratum statistics *in the options*: `A S4 size 610 cur 0.8% implicating R2 | B S2 size 880 cur 0.0% implicating R1 | C S5 size 240 cur 1.2% implicating R3 | D S3 size 1,300 cur 0.7% implicating R1`, key C, *"margin 3.1 pts > ε"*. The naive expected-yield argmax is D (1300×0.7% = 9.1 vs 240×1.2% = 2.88). Getting C requires combining size × base rate × coupling strength and then optimizing over a 400-inspection budget — arithmetic and search that a 2-layer head over ModernBERT-large cannot perform and that a generative model can. **The inputs are equal; the required competences are not.** F1's Q2 has the same shape one level down: the key is *"the one whose clause test passes without breaking the regression suite (execution)"* (line 250) — the judge must predict the behaviour of an 84-test suite that is not in the state. |
| **Q3 rubric-score** | Partly. | Two problems. (a) **Cross-unit conflict:** R5 §3 conflict 4 (line 90) rules *"主分析以 `noul` 为主... `score` 作为**独立的小型重测实验**"* — score is demoted out of the main analysis pending R13 rule 25 (*"re-test the `score`-vs-`choice` claim on ≥200 items"*). R14 keeps **40 score items (8/level) inside the primary 300**. If Laya's `score` primitive behaves differently, 13% of the primary N carries a primitive-specific artefact that R5 explicitly ruled out of the main analysis. (b) Not unfair, but capability-loaded: evaluating a 3-predicate conjunction (`argmax` remainder, `utcnow()` in the write path, empty-input handling) over a ≤130-token hunk favours a model that can track three variable names at once. |
| **Q4 evidence-verdict** | **Only weakly.** R14 calls it *"the most scientifically interesting class... the decision is local, short, and shape-based"* (line 265). | **The metadata header gives the answer away.** The stem format is `SPAN A [doc, tier, scope]` and `SPAN B [doc, tier, scope]` (line 263), and the coverage function is defined on exactly those fields: *"`SUPPORTED` iff a covering span with matching polarity at tier ≤2 exists... `INSUFFICIENT` iff no span covers the tuple (scope/modal mismatch ⇒ no coverage)"*. A judge that reads `tier 1 / scope 2024` off span A and `tier 3 / scope 2026` off span B and compares the claim's stated scope can produce the key without any evidence judgment. That is rule application over three printed fields, not evidence assessment. The trap controls at line 266 address *lexical* overlap only; **no gate tests whether a symbolic rule over `(tier, scope, polarity)` reproduces the key.** |
| **Q5 shortlist-rank** | Yes, honestly reduced. R14 declares Laya cannot rank (line 56) and reduces all judges to `choice(4)`, with Jev's `rank` in a separate stratum outside the primary N (lines 271–273). That is the right call. | F3's key is *"number of downstream assertions affected by the column (from the dependency graph)"* (line 272) — the graph is not in the 497-token state, so the judge must infer out-degree from the carrier. Underdetermined unless the carrier is certified (§Q2 fix). |
| **Q6 halt/escalate** | Yes — this is the one class where the carrier is load-bearing by design (line 279). | **Two construction hazards.** (a) The label is one-sided: `TRUE = the run cannot reach the terminal oracle without an action the harness has made unavailable` (line 277). Fault-injection gate G6 caps any label at 70% of a class (line 488) — so an always-halt strategy scores up to **0.69**, and Q6's primary metric is plain *"accuracy"* (line 235) whereas Q1 uses *"balanced accuracy"*. The core instrument is the one class where a degenerate constant strategy scores best. (b) The answer reduces to "is the revocation line in the carrier?" — a retrieval check, not a judgment. Combined with §1.4, that makes the paper's central instrument a one-fact lookup. |
| **Q7 summary-faithfulness** | Yes — scripted corruption with a known target is an exact label (line 284). | **Under-specified and a possible R0 breach.** Line 284: *"Fluency is varied by a **frozen paraphraser** (a configuration not under test)."* The paraphraser is a model producing judge-visible strings. R0 (line 67) requires *"Every judge-visible string is authored or selected by L0. No judge ever judges a state it produced."* If the paraphraser is the same family as the LLM judge (DeepSeek-V41-Flash under a frozen config), the LLM judge reads prose its sibling wrote, and T7's self-preference probe (line 454) is listed as an *addition*, not a requirement. R14 must name the paraphraser and require it to be a different family, or move it into the reported diagnostics. |

**A cheap general fix for Q4: add a symbolic baseline to the gate set.** T9/G3 (lines 458, 485) tests only a *lexical* baseline (*"TF-IDF/logistic baseline ≤0.80 accuracy for every item class... and cannot separate filler from real ledger lines"*). Add **G3b**: for every class whose key is a function of labelled fields (Q4 especially, and Q1/F2), fit a hand-written rule over `(tier, scope, polarity, modality)` and reject the class if it exceeds ~0.80. Q4 as specified would very likely fail this gate, and it is better to learn that before authoring 60 items than after.

**A related measurement asymmetry R5 already spotted but did not fix:** R5 §3 conflict 2 (line 75) states that deterministic typed judges need one call while the LLM arm needs repeats. R14 R4 scores the LLM single-shot. Either the paper declares single-shot as the deployable regime (defensible: it is what a real in-loop judge costs) or it moves k-sample marginal accuracy into the primary N. Doing neither leaves the headline contrast between a deterministic estimator and a noisy one.

**VERDICT: sound-with-fix.** Unfair toward Laya: Q2-F4 (and arguably Q2-F1) — key requires global optimization/execution prediction. Degenerate rather than unfair: Q4 (metadata-header rule application) and Q6 (one-sided label + 70% balance cap + plain accuracy). Cross-unit conflict: Q3's 40 `score` items. Under-specified: Q7's paraphraser. Minimal fix: report Q2-F4 separately as a capability item excluded from the "typed judge is competitive" claim; add gate G3b (symbolic baseline); switch Q6's primary metric to balanced accuracy and cap the TRUE rate at 50 ± 5 for the primary analysis; remove or re-cast the 40 score items per R5's ruling; name and freeze the paraphraser with a family constraint.

---

## Q5 — Ground truth: who supplies it, can it be gamed, is it independent of the models under test?

### 5.1 Per-family verification

| Family | Oracle as stated | Is a model in the loop? | Independent of the judges? | Gameable / weak point |
|---|---|---|---|---|
| **F1 SPECSHIFT** | Line 107: *"Every spec clause carries either a pytest node id or a *statically decidable* predicate over the source (`AST` queries...). The terminal oracle is the frozen acceptance suite plus the replay equality check. Per-clause pass/fail per junction is computed by the harness."* | **No** | **Yes** | T11 (flaky suite) is handled (*"run each clause test 3× at build time and drop any clause whose result is not stable"*, line 462). Residual: the replay oracle is a single author-written reference implementation; the 12 differing rows have no second implementation or hand-computed check. |
| **F2 EVIDENCE-BRIEF** | Line 131: status is *"a deterministic function of the annotation table"*, with the four-way rule spelled out; closed by *"No model labels anything, ever."* | **No** | **Yes** | **Clean.** See §5.2. |
| **F3 SCHEMA-EPOCH** | Line 151: *"Expected destination built by a frozen reference transform; oracle = row-hash diff plus 34 SQL assertions."* | **No** | **Yes** | Two weak points: (i) the reference transform is a *single* implementation presented as the truth; (ii) it is the **hidden** oracle for exactly the columns the design deliberately leaves underdetermined — see §5.3. |
| **F4 AUDIT-CASCADE** | Line 171: *"Labels are authored; reachability is computed by the harness's rule engine. No model labels anything. Every planted critical item must be *decidable from its own record under the written policy* — verified by two authors independently, disagreement kills the item."* | **No** | **Yes** | The Q2/Q6 keys are *"exhaustive rollout in the L0 simulator under a scripted reference policy"* (line 250) — the key is the argmax **under that policy**, not the true optimum. The policy is authored code, and its quality is never reported. |

**The anti-circularity claim is verified for all four families.** R14 T1 (line 442) restricts labels to *"an execution, a static predicate, a simulator, or an authoring-time record"*, and every family's stated oracle is one of those. The specific concern in the audit brief — that F2's labels might be judge-produced — is **not** borne out: F2's status function is closed over `(entity, predicate, value, polarity, scope_period, modality, source_tier)` tuples, all authoring-time fields. Credit where due.

### 5.2 F2 deserves explicit clearance

R14 lines 129–131 and 141 define the anti-gaming rules and they hold up: the generator *"must never see the records, only the documents"* (line 141), entities are fictional with an n-gram/embedding contamination search required, and the trap subset is *"reviewed by **two human annotators**; kept only if both agree with the computed label"* (line 267). Annotators **validate** a computed label rather than supplying one; where they disagree the item is dropped, which introduces a mild bias toward human-intuitive labels but no model circularity. The claim in the brief is confirmed.

### 5.3 Where the oracle is not a model but is not independent either

**F3's underdetermination knob manufactures unanswerable items.** The difficulty knob at line 155 is: *"(b) fraction of columns whose source semantics are underdetermined 0.10→0.60"*. The key for such a column is the **frozen reference transform's** choice, which is visible to no judge. At the top of that knob, up to 60% of items have a key that is not derivable from any shipped string — not because the carrier is too narrow (T3), but because the task is underdetermined by construction and the oracle is private. **This is strictly worse than T3**, because no amount of carrier widening fixes it. It is also a difficulty knob that *is* an unanswerability knob, which is the one thing a difficulty knob must never be.

**Fix:** (i) re-specify knob (b) as *inference depth* — how many clauses must be composed to determine the semantics — rather than *underdetermination*; every item must ship a disambiguating clause; (ii) run the entailment certificate of §2.4 on 100% of items and report the derivable fraction per level; (iii) require two independent implementations of the reference transform, or a hand-computed table for the boundary rows.

**F4's keys are policy-relative.** Q2 for F4 is *"simulator terminal recall if that stratum is opened next"* under *"a scripted reference policy"* (lines 250, 272). The key is therefore "best action under policy P". Fix: for a planted 5-stratum instance the optimal ordering is computable by exhaustive search over a small action space; report the reference policy's recall@400 against the optimum, and either close the gap or restate the stem as "best under the published policy".

### 5.4 The one place a model may be in the loop, and it is unspecified

R14 §1.4 R0 (line 67) allows judge-visible strings to be *"generated by the harness (templated, or **frozen once by a non-judged configuration**)"*. F2 requires 60 authored documents and F4 requires **12,000 authored alert records** with notes ≤120 tokens (line 167). R14 §7 S0 (line 471) lists these under "Authoring" without saying whether a model produced them. If they were produced by DeepSeek-V41-Flash under a frozen config, then: (a) T7's self-preference risk applies to the **corpus**, not only to Q7's summary variants (line 454 mentions only summaries); (b) F2's contamination search (line 141) is required precisely because such corpora are generated, not written. **Fix:** state the corpus provenance in the methods section, hash the generator config, require a family different from the judge if a model was used, and extend the T7 self-preference probe to corpus items.

**VERDICT: sound-with-fix.** No family's oracle is a model — the circularity concern the brief raises does not apply anywhere. Defects: F3's underdetermination knob directly manufactures non-derivable keys; F4's keys are relative to an unreported reference policy; corpus provenance is unspecified and could put the judge's own family into the state.

---

## Q6 — The horizon dial as a dose-response design

### 6.1 `d` is not a measure of horizon; it is the junction index minus four

Verified from the dial table (lines 398–404): for every level where `d` is defined, `d = H − 4`. `H ∈ {1,4,8,32,128}` → `d ∈ {—,0,4,28,124}`. The correlation between position and distance is exactly 1. R14 asserts the operationalization at line 396 (*"Horizon is **position in one frozen run**, and it is operationalized as **distance from the planted upstream error** `d`, which is the mechanism the paper is about"*) but the design provides no condition that separates them. A reviewer will read this as: the authors renamed position to distance and then claimed the rename was a mechanism.

**The dose is also not credible as a continuous measure.** R14 §5.1 line 406 claims the levels are *"geometrically spaced"*. They are not: the ratios are 4, 2, 4, 4. `log2(H)` values are 0, 2, 3, 5, 7 — unequal steps, with H1→H2 a single doubling and the rest double doublings. A linear-in-`log2(H)` term can absorb unequal spacing only if the true relationship is linear in log-horizon, which F3 (a step at the J64 revocation) and F4 (a ceiling set by a single early branch) both violate.

### 6.2 Yes — fixing carrier width while raising `d` creates a confound, and it is the central one

If the carrier is a rolling tail (§Q2 Horn A), then raising `d` mechanically removes the decisive line from the shipped state. The manipulation therefore moves **two** things at once: distance, and the probability that the item is answerable at all. R14 §5.3 treats this as a manipulation check to be reported per level, and then converts it into an analysis filter (*"the primary drift-vs-horizon analysis is run on `survives` items only"*, line 432). Filtering on a variable caused by the treatment cannot identify the treatment effect (Q2 §2.3).

**This is the confound I would expect a reviewer to name, and it should be named in the paper before it is named against them:**

> *"Distance from the poison is perfectly collinear with position in the run (`d = H − 4`), the carrier is fixed at five lines, and trace survival necessarily declines with distance, so the reported horizon slope is a mixture of run position, trace recency and trace presence that the design cannot separate."*

The second-most-likely confound: *"the carrier is not the run's memory but an authored five-line summary, so its fidelity is under the authors' control at every level."* Both are answered by the same fix.

### 6.3 Two further dial defects

**(a) The floor reads off a different run.** §5.2 item 9 (line 420): *"H0 is read off a clean run of the same instance. The manipulation is therefore position, not instance."* But if the poison is installed at J4, then J1 is **pre-divergence** — the poisoned and clean runs are identical at J1 by construction. Reading H0 from a separate clean run adds instance variance for no benefit and gives the floor two simultaneous differences (no poison *and* a different lineage). **Fix: read H0 off the poisoned run's J1 state; keep the clean-run reading only as a robustness check.**

**(b) The common dial contradicts the families' own poison junctions.** The dial fixes the poison at J4 for all families: §5.2 item 9 says *"the prefix is run once with the poison installed at J4"*. But the families place their poison elsewhere:
- F1: *"J≈4: ... the generator implements `legs[0] += residual`"* (line 102) → J4 ✓
- F2: *"At J≈8 the generator records C-11 as `SUPPORTED`"* (line 129) → J8, not J4
- F3: *"J≈12: the generator decides that `source.ts` values with a `+00:00` offset are 'already UTC'"* (line 149) → J12
- F4: *"Injectable junction. J6 (first stratum call)"* (line 173) → J6

So either the poison is forced to J4 for all families (contradicting three families' timelines) or the actual `d` differs by family within a level: at H1 (J4), F2/F3/F4 items are *pre-poison*, i.e. the poisoned condition does not exist for three of four families; at H3 (J32), the true `d` is 28 for F1, 24 for F2, 20 for F3, 26 for F4. Since §5.2 item 8 holds *"15 items per family at every level"*, the regressor labelled `d` is heterogeneous within every level. **Fix: declare `d` per family and either (i) use a single family for the dose-response claim while the others support the accuracy/calibration claim, or (ii) move every family's injectable junction to J4 and re-audit the timelines.**

### 6.4 Does a 5-level dial support the planned `judge × log2(H)` slope analysis?

Arithmetically yes, and better than R14 claims — see Q7 §7.4: because every slot carries the **identical** `x`-profile `{0,2,3,5,7}`, the slot random intercept contributes exactly zero variance to the slope, so the slope is identified purely within slots. Five levels suffice for a linear contrast and for distinguishing a linear-in-log from a step (with 5 points and 3 residual df). What five levels do **not** support is the threshold-vs-linear discrimination R14 promises at line 406 (*"so drift can be plotted against `log2(H)` and a threshold or a linear-in-log slope can be distinguished"*) once the true shape is a step (F3) inside a mixture of four families with different poison junctions. **Fix: pre-register per-level fixed effects with a linear contrast as the primary and a monotone/isotonic alternative as secondary; report both.**

### 6.5 R14's item 10 overstates an invariance R13 measured to be false

§5.2 item 10 (line 421): *"Same Laya cost: constant state width ⇒ constant re-encoding cost per item ⇒ **latency is structurally not confounded with horizon**."* The width claim is true. The latency claim is not usable: R13 §6.1 measured 266 ms vs 33 ms for **byte-identical** requests and R13 §10 rule 20 says *"Never use `latency_ms` as a stable measurement of the model."* R5 §5.5 nevertheless wants latency-vs-lead-time panels. Net: the width invariance is fine; any per-item latency endpoint must be re-specified as a distribution over warm calls (R13 rule 20) or dropped.

**VERDICT: unsound-with-repair.** The dial's *intent* is right and §5.2's held-fixed list is thorough, but the instrument as specified is not a dose-response manipulation of horizon: `d ≡ H − 4`, trace presence moves with `d`, the floor uses a second run, and the common J4 poison contradicts three families' timelines.

**Minimal repair, in order:**
1. Define the primary manipulation as `L` vs `L+C` at each of the five levels (the §4.3 variant pair already exists) and make **carrier-lift × log2(H)** the estimand. This removes the survival confound, uses all 300 slots, and keeps the fixed-width property.
2. Add the **H4-refreshed** cell (long position, fresh trace) to break the `d`/position collinearity.
3. Read H0 off the poisoned run.
4. Declare `d` per family, or move every injectable junction to J4.
5. Replace the single linear-in-`log2(H)` term with per-level fixed effects + a pre-registered linear contrast, and an isotonic alternative as secondary.

---

## Q7 — Is N = 300 sufficient for the horizon claim specifically?

### 7.1 R14's arithmetic is correct — verify it and move on

The McNemar formula at line 312, `n = [z(1−α/2)·√ψ + z(1−β)·√(ψ − Δ²)]² / Δ²`, is the standard Connor-style paired formula, and the table at lines 317–321 recomputes exactly:

- ψ = 0.10: `(1.96·0.3162 + 0.8416·0.3000)² / 0.01 = 76.1` → 77 ✓
- ψ = 0.20: `(1.96·0.4472 + 0.8416·0.4359)² / 0.01 = 154.6` → 155 ✓
- ψ = 0.30: `(1.96·0.5477 + 0.8416·0.5385)² / 0.01 = 233.1` → 234 ✓
- CI half-width at n = 270, ψ = 0.30: `1.96·√(0.29/270) = 0.064` → ±6.4 pts ✓

No arithmetic error. The defect is in the assumption.

### 7.2 The independence assumption that R14 denies elsewhere — and that R15 explicitly forbids

Two independent internal contradictions:

**(a) R14's own T8.** Line 456: *"300 items over 60 slots, 4 families, and shared lineages are not independent; naive CIs are too narrow."* The mitigation offered is *"slot-level pairing, random intercepts for slot and run lineage, cluster bootstrap."* A cluster bootstrap repairs the **CI**; it does not repair the **power calculation**, which was run at n = 234 *before* any design effect. R14 deflates the interval and leaves the sample size alone — the two must be consistent.

**(b) R15 §5.5 uses a design effect of 2.2 in the same design.** *"24 tasks × 4 runs × 6 arms = 576 runs. Effective clusters ≈ 96 per arm after a design effect of ~2.2 from task-level ICC ≈ 0.15."* If a DEFF of 2.2 applies to the arms experiment, it applies with at least equal force to a battery whose 5 items per slot share a **byte-identical local block, stem, options and key** (R14 §5.2 items 1–2).

**(c) R15 §5.1 forbids exactly R14's test.** *"Treating judge verdicts as independent observations inflates `n` from ~100 runs to ~40,000 checkpoints and is the single easiest way to produce a false positive in this design. **Rules:** every hypothesis test is at the **run** level or coarser; checkpoint-level data is used only for curve estimation, with run-clustered uncertainty."* R14's primary contrast is a paired McNemar over **300 item instances** with slot-level pairing. An item is a junction, and a junction is a checkpoint. The two units are in direct conflict about the headline test.

### 7.3 Recomputing the effective sample size

R14 §5.2 item 1 makes the five items of a slot **the same question**; §5.2 items 2 and 5 make stem, options and key identical too. So a slot is a five-fold repetition of one item with a different ≤55-token decoration. Combined with §1.4's finding that 170 of 300 items have keys invariant to that decoration, and with Laya's measured bit-determinism (R13 §6.1: identical requests are bit-identical), a judge that ignores the carrier returns the **same answer five times per inert slot** → ICC ≈ 1 for those slots.

- Inert: 34 of 60 slots entirely inert (34 inert items per level × 5 levels = 170). With ICC = 1, information ≈ 34 independent observations.
- Live: 26 slots. With ICC = 0.5 → DEFF = 1 + 4(0.5) = 3 → 130/3 ≈ 43. With ICC = 0.3 → DEFF = 2.2 → 59. With ICC = 0.2 → DEFF = 1.8 → 72.

**n_eff ≈ 34 + 43 … 34 + 72 = 77 … 106**, central ≈ 90, against a required **234**. Shortfall **2.2–3.0×**. On R15's own DEFF = 2.2 with no inertness assumption at all: `300 / 2.2 = 136`, still short of 234.

Rearranged: the raw N required is `234 × DEFF` = **515** at DEFF = 2.2 and **700** at DEFF = 3 — i.e. ~103–140 slots, or 515–700 items. **This converges with R13's independent derivation** (R2 §B.9: *"单判定器准确率 ±0.05（95%）：n ≈ 385... 两判定器准确率差 0.10、80% 功效：≈390/臂"*; R13 rule 24: *"≥400 items per judge per condition... ≈390 per arm"*). Two units, two methods, same answer: **400–700, not 300.**

### 7.4 The slope test is better powered than R14 claims — for a reason R14 never states

This is the part of R14 that is *stronger* than its own argument. Because every slot carries the identical `x`-profile, a slot-level random intercept contributes **zero** variance to the slope: in `Var(β̂) = σ²_ε/Σ(x−x̄)² + τ²·Σ_s(x̄_s − x̄)²/(Σ(x−x̄)²)²`, the second term vanishes when every `x̄_s = x̄`.

With `x = {0,2,3,5,7}`, `x̄ = 3.4`, `Σ(x−x̄)² = 29.2` per slot and **1752** over 60 slots. Take `ψ = 0.30` (R14's conservative value), within-slot residual `σ²_ε ≈ 0.21`, and a per-slot slope SD of `τ` log-odds per doubling:

| τ (between-slot slope heterogeneity) | SE(interaction) log-odds/doubling | MDE, accuracy/doubling, 80% power |
|---|---|---|
| 0.25 | 0.034 | **0.024** |
| 0.50 | 0.066 | **0.046** |
| 0.75 | 0.097 | **0.068** |

(Accuracy scale = log-odds × 0.25 at p ≈ 0.5; MDE = 2.80 × SE. OLS-on-differences approximation, stated as such.)

**Conclusion: R14's pre-registered target — *"80% power for an interaction of 0.04–0.05 accuracy per doubling of horizon"* (line 331) — is genuinely achievable at 300 items, provided between-slot slope heterogeneity stays at or below τ ≈ 0.5.** So the answer to "does 300 suffice for the slope?" is **yes, conditionally** — the prompt's premise that 300 is plainly insufficient does not hold for this estimator, and the reason is a design property R14 never claims.

But the margin is consumed by two things R14 does not price in:

- **Inert dilution.** If the interaction is estimated on the pooled battery and only 43% of items can respond, the pooled coefficient is attenuated toward zero by roughly the live fraction. The target 0.04–0.05/doubling pooled then requires **0.09–0.12/doubling on live items**, and the MDE expressed on the live-item effect rises to **0.055–0.107**. Under Q6's recommendation (live stratum primary), n = 130 with 26 per level re-intersects §4.5's own admission: *"Per-cell n = 60 has an MDE of 16–20 points — so *no per-cell claim is supportable*"* (line 327).
- **Between-family generalization.** If the true interaction differs by family (F3 a step, F2 a gradient), generalizing beyond the four authored families is governed by the number of families, not the number of items. R14 §4.5 already concedes this for family contrasts (*"the between-slot quantities (e.g. 'F3 drifts more than F2') have an effective n of 15 per family and are reported as descriptive"*), but the same logic applies to the pooled interaction and is not carried through.

### 7.5 The pre-registered inferential unit for the headline claim is contradictory across units

R5 §5.5 (line 152) names the primary analysis as *"离散时间生存模型 + **任务层随机化推断**（簇数少时的正确选择）"* — task-level randomization inference, described as the correct choice when clusters are few — and R15 §5.3 line 672 makes it explicit: *"**the primary inference is randomization inference.** Arms are randomized **within task family**... report the permutation `p` over ≥10,000 draws."*

The horizon claim, however, is R5 §3 conflict 2's ruling (line 73): *"**horizon 斜率 / 检测提前量**：R14 的 **300**"* — i.e. the slope lives in R14's battery, which has **4 families** (or 3, if R5 §5.1's *"取 3 族以控制规模"* — "take 3 families to control scale" — is taken literally; R5 §5.1 keeps F2, F1, F4 and drops F3 entirely without stating why, while R14's 60-items-per-level arithmetic requires 4 × 15).

Under a task-level permutation test, the minimum attainable two-sided p-value is `2/2^S`: **S = 4 → p ≥ 0.125; S = 3 → p ≥ 0.25.** With three or four families, **p < 0.05 is arithmetically unreachable**, regardless of how many items are nested inside. So if the horizon slope inherits R5/R15's randomization-inference plan, the headline test cannot reject at α = 0.05 by construction. If instead R14's mixed model is primary, the claim is conditional on four authored families and must be worded that way.

**Fix:** declare, in the pre-registration, which inferential unit governs the horizon slope. Either (i) RI at the **run-lineage** level with S ≥ 8 (which R15's 24 families × 4 runs supports, if the battery is nested inside it), or (ii) a mixed model with an explicit *"conditional on these four authored families"* limitation and cluster-robust SEs, with the generalization claim withdrawn. Do not leave the slope attached to a family-level RI plan it cannot satisfy.

### 7.6 Checkable arithmetic and cross-unit inconsistencies found while testing N

| # | Location | Problem |
|---|---|---|
| 1 | R14 §4.2 vs §4.3 | Q4 = 12/level and Q6 = 8/level, i.e. **20** Q4+Q6 items per level. §4.3 line 293 specifies the carrier-lift probe as *"50 designated items (Q4 and Q6, at horizon levels d=28 and d=124, **25 per level**)"*. 25 > 20 — the probe draws from a pool that does not exist. |
| 2 | R14 §4.5 vs T8 | Design effect acknowledged (T8) but not applied to the n = 234 derivation. |
| 3 | R15 §5.1 vs R14 §4.5 | R15: *"every hypothesis test is at the run level or coarser"*; R14: item-level paired McNemar. Direct conflict on the unit of analysis for the headline claim. |
| 4 | R5 §5.1 vs R14 §4.2 | R5 keeps **3** families (*"取 3 族以控制规模"*); R14's 60 items/level requires **4** (4 × 15). With 3 families the battery is 225 items, not 300. F3 is dropped by R5 with no stated reason, removing the strongest irreversibility mechanism in the design. |
| 5 | R5 §7 P8 vs R14 §5.2 | R5 plans *"24 族 × 4 run × 臂，120 步"*; R14's families are 128 junctions (F1/F2/F3). "120 steps" and "128 junctions" are different lengths in the same design. |
| 6 | R14 §4.3 vs §4.3 | *"paired McNemar at n=100 detects ≈15 points at ψ=0.20"*. Check: n = 68 required at Δ = 0.15, so the claim is conservative as stated — but the 100 pairs are 50 items × 2 levels whose two levels share a byte-identical local block, so n_eff ≈ 50–75 and the real MDE is ≈ **0.17–0.18**, not 0.15. |
| 7 | R14 §4.1 vs R13 §2.3 | The ≤497-token envelope budgets 212 tokens for scaffold+stem+options against measured head costs of 61–113, capping the state near 285 where ~450 is available. See Q3 §3.4. |
| 8 | R14 R2 vs R5 §4.2 rule 8 | R14 permits **4** options; R5 pins the ceilings at *"10（Path A）/ 3（Path B）"*. Four options compress on Path B (R13 §1.4: compression begins at **4** on Path B; `tightest_option_tokens_each` becomes 45 < 49, which R13 rule 8 calls *"a design failure, not a warning"*). R5's Path B robustness arm therefore cannot run the primary battery as designed. |

### 7.7 Recommended N, stated as a decision rather than a number

1. **Marginal accuracy contrasts (Laya vs Jev, LLM vs Jev):** re-power at **≥515** (DEFF 2.2) and preferably **≥700** if the inert fraction stays at 57%. Re-estimate from the pilot ICC — R5 §7 P7 already plans this (*"从试点 ICC **重估**全量规模"*), so the mechanism exists; only the pre-registered default of 300 is wrong. Move the default to ~600 before the pilot.
2. **Slope/interaction:** keep 300 slots, but (a) run **both** the `L` and `L+C` variants of every item → 600 paired observations from the same 300 slots, which powers the lift main effect and the lift × horizon interaction without new authoring; (b) pre-register the interaction target with an explicit τ assumption and a live-item dilution factor; (c) retire the *"+75 slots (375)"* escape hatch (line 331) or restate it in **effective** n — 375 raw with DEFF 2.2 is 170 n_eff, still below 234.
3. **Calibration/ECE:** unchanged — R5 §3 conflict 2's ≥1000 stands, and V5 §0 item 5 correctly notes that the other 700 items have no collection procedure anywhere in the design.

**VERDICT: sound-with-fix.** R14's McNemar arithmetic is correct and its slope target is genuinely attainable at n = 300 — but only for the within-slot slope, a property R14 does not identify, and not for the marginal contrasts (n_eff ≈ 77–106 vs 234 required), which are the contrasts the paper's comparative claim rests on. The pre-registered inferential unit for the headline claim is contradictory across units, and at S = 3–4 the randomization-inference plan cannot reach p < 0.05 at all.

---

## TOP 3 THREATS TO THE HORIZON CLAIM

### 1. The dial does not manipulate horizon — and the pre-registered fix for the resulting confound cannot work

**Why it is first.** Everything downstream is uninterpretable if this stands. `d = H − 4` exactly (R14 lines 398–404), so distance-from-poison and position-in-run are perfectly collinear. §5.2 item 1 makes the local block byte-identical across a slot's five levels, so the *only* varying quantity is which five ≤55-token ledger lines are shipped. If the carrier is a rolling tail — the natural reading of §5.2 item 3 and of §5.3's expectation of a *per-level* survival rate — then raising `d` mechanically removes the decisive line, so the manipulation moves distance and answerability together, and the pre-registered remedy (*"the primary drift-vs-horizon analysis is run on `survives` items only"*, line 432) conditions on a post-treatment variable caused by the treatment. If instead the poison line is retained at every level, then `survives` ≈ 100%, the `absent` control is empty, and the only thing varying with `d` is recency. **There is no reading of R14 on which the dial isolates horizon.** On top of that, 170 of the 300 primary items (57%) have keys that are functions of the local block alone — R14 says so itself when it calls Q4 *"local, short, and shape-based"* (line 265) and reserves *"only the carrier flips it"* for Q6 (line 279) — so a majority of the battery cannot respond to the manipulation.

**Mitigation (cheap, uses material R14 already specifies).** Promote §4.3's `L`/`L+C` variant pair to primary: run both variants of **all 300 items**, making the estimand `carrier-lift × log2(H)`. This manipulates trace presence *within* item, at fixed distance, and is therefore free of the survival confound. Add the **H4-refreshed** cell (long position, fresh trace; buildable from F1's own detection-delay knob, line 111) to break the `d`/position collinearity. Report the 170 inert items as a distractor placebo with an expected lift of ≈ 0.
**If refused, the concession is:** delete the causal horizon wording from the abstract and results; claim only *"accuracy on a fixed-width carrier declines with distance from the trace it must carry"*, with the survival-mediation band stated (see Q2 §2.5).

### 2. Drift at large `d` is not identifiable as degradation: T3 unresolved, plus an unanswerability knob and policy-relative oracles

**Why it is second.** Even with a repaired dial, the top of the curve is not evidence of degradation. R14 concedes T3 honestly (line 446: *"any measured 'drift' is an artifact of item construction, not judge degradation"*) but its mitigations are too weak: the §5.3 flag is a one-sided *mention* check with unmeasured false-positive and false-negative rates, the human audit covers ~30 of 300 items (≈6 per level, CIs of ±30 points), and the two-width probe is n = 50. Two further oracle defects compound it: F3's difficulty knob *"(b) fraction of columns whose source semantics are underdetermined 0.10→0.60"* (line 155) raises the share of items whose key is the authors' private reference transform and derivable from no shipped string — unanswerability dressed as difficulty; and F4's Q2/Q6 keys are argmax *"under a scripted reference policy"* (line 250) whose optimality gap is never reported.

**Mitigation.** (i) Replace the mention flag with build-time **entailment and necessity certificates** in each family's oracle language — entailment proves the key is derivable from the shipped state; necessity proves the item is not answerable from `LOCAL` alone (and mechanically detects the 170 inert items). (ii) Add a **derivability ceiling check**: the LLM with the full frozen log, run outside the primary N — if it succeeds where fixed-carrier judges fail, the deficit is carrier-mediated; if it fails too, the item is broken. (iii) Analyse trace survival as a **mediator, not a filter**. (iv) Re-specify F3's knob as inference depth, and report F4's reference-policy optimality gap. This also supplies the missing design-time witness for LH-3, which at present is the only one of R14's three qualification tests with no test (lines 83, 85, 87).
**If refused, the concession is:** the d = 124 point may not be reported as a degradation estimate, and the horizon claim cannot exceed *"between Y% and Z% of the decline is attributable to trace non-survival and cannot be separated from unanswerability."*

### 3. The horizon claim has no powered inferential home: wrong unit of analysis, wrong sample size, and an unreachable significance floor

**Why it is third — and why it still matters.** Three independent failures converge on the headline:
- **Unit of analysis.** R14's primary contrast is an item-level paired McNemar (line 309). R15 §5.1 forbids exactly that: *"every hypothesis test is at the **run** level or coarser... n is always reported as the number of runs and the number of tasks, never as the number of checkpoints."*
- **Sample size.** With 5 items per slot sharing a byte-identical local block and key, and 57% of them key-invariant, n_eff ≈ **77–106** against the required 234 — a 2.2–3.0× shortfall. R15 §5.5's own DEFF of 2.2 gives 136, still short. The required raw N is 515–700, which is exactly where R13 landed independently (≈385 for ±0.05; ≈390/arm for Δ = 0.10; ≥400 per judge per condition). R5 §3 conflict 2 blessed 300 for the slope on the grounds that *"其配对设计针对该主张，power 论证成立"* — the power argument does **not** hold once its own T8 design effect is applied.
- **Unreachable floor.** R5 §5.5 makes *"任务层随机化推断"* (task-level randomization inference) the primary inference, and R15 §5.3 makes it explicit. Under a permutation test the minimum two-sided p is `2/2^S`: with R14's **4** families p ≥ 0.125; with R5 §5.1's **3** p ≥ 0.25. **p < 0.05 is arithmetically impossible** for a family-level RI test at this S, whatever N is spent inside.

One genuine credit: the slope itself is better powered than R14 argues, because every slot carries the identical `x`-profile, which zeroes the slot-intercept contribution to the slope variance (MDE ≈ 0.024–0.046 accuracy/doubling at n = 300 for τ = 0.25–0.5). That is a real and unclaimed strength — but it applies to the *within-slot* slope only, and it evaporates once the interaction is expressed on the 130 live items or generalized past four authored families.

**Mitigation.** (i) Declare the inferential unit for the slope in the pre-registration: RI at the **run-lineage** level with S ≥ 8, or a mixed model with an explicit *"conditional on these four authored families"* limitation and the generalization claim withdrawn. (ii) Re-power the marginal contrasts at **≥515**, default **600**, with re-estimation from the pilot ICC (R5 §7 P7 already provides the mechanism). (iii) Retire or restate the *"+75 slots (375)"* extension rule in effective n. (iv) Reconcile whether the battery has 3 families (R5 §5.1) or 4 (R14 §4.2) — the item count, the family mix and the RI plan all depend on the answer.
**If refused, the concession is:** the horizon claim is reported as a *descriptive* within-battery curve with cluster-bootstrap CIs, explicitly non-generalizable beyond the authored families, and no p-value attaches to it. That is a publishable measurement paper — R5 §6 already lists *"SAFE = 测量/刻画"* (measurement/characterization) as the defensible fallback — but it is not the horizon claim the current framing advertises.

---

## Appendix — files and locations this audit relies on

| Claim | Source |
|---|---|
| LH-1/LH-2/LH-3 tests and the absent LH-3 procedure | R14 §2, lines 79–89 |
| Family poison junctions (F1 J4, F2 J8, F3 J12, F4 J6) | R14 lines 102, 129, 149, 173 |
| Dial table and geometric-spacing claim | R14 lines 396–406 |
| Ten held-fixed items, including byte-identical local block and ±8-token equality | R14 §5.2, lines 410–421 |
| Poison-survival flag and `survives`-only primary analysis | R14 §5.3, lines 425–432 |
| Item-class ground-truth sources and metrics | R14 §4.2, lines 228–238, 242–287 |
| Carrier-lift probe (50 items, 25 per level) | R14 §4.3, lines 289–301 |
| N derivation, slope model, extension rule | R14 §4.5, lines 307–333 |
| T3, T8, T9, T12 | R14 §6, lines 446, 456, 458, 464 |
| Gates G1–G8 | R14 §7, lines 483–490 |
| Laya 512 clamp, 450-token real budget, ~300-char silent window | R13 §2.3–2.5, lines 251–289 |
| Option compression at 11 (Path A) / 4 (Path B); 20-option failure | R13 §1.4, §3.2–3.3, lines 190–214, 320–359 |
| Determinism, latency unreliability, per-item cost | R13 §6.1, §8.2, lines 466–482, 596–605 |
| R13's constraints 1–25 and sample-size rules | R13 §10, lines 673–725 |
| R13's sample-size paragraph (n ≈ 385 / ≥500 / ≈390) | R13 §4.2, lines 401–405; R2 §B.9, lines 155–160 |
| Laya checkpoint facts, confidence decoupling, silent-state acceptance | R2 §B.2, §B.3, §B.5, §B.6 |
| Three-family cut, N ruling, protocol rules, headline claim | R5 §0 (lines 10–25), §3 (lines 58–90), §4.2 (lines 101–120), §5.1–5.5 (lines 126–154) |
| DEFF 2.2, checkpoint-level prohibition, RI plan | R15 §5.1, §5.3, §5.5, lines 640–708 |
| Silent-truncation-has-no-instrument finding (independent concurrence) | V5 §0 BLOCKER-1, line 26 |

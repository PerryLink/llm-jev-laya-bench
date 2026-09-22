# R14 — Long-Horizon Task Families and the Decision-Point Item Battery

**Design unit:** R14 (task families + decision-point item battery)
**Consumers:** team lead (paper design), task-implementation unit, [→ARMS], [→METRICS], [→INJECT]
**Status:** design proposal, pre-registration-ready. No live judge calls were made in producing this document; every token/Laya/Jev limit used below is taken from the measured facts supplied in the remit.

---

## 0. Scope of this unit

**Owned here.**
(A) Task families: objectives, accumulate-error structure, ground truth, injectable junctions, difficulty knobs, decision units.
(B) The decision-point item battery: state envelope, item classes, ground-truth procedures, anti-circularity rules, sample size.
(C) The horizon knob as a controlled instrument (levels + held-fixed list + manipulation check).
(D) Validity gates local to the battery.

**Not owned here.** Treatment arms (LLM reasoning effort, tool access, self-judging arms), process metrics and term-level instrumentation, fault injection into judge inputs, latency/throughput reporting charts. Where a design decision here creates a *requirement* on those units, it is tagged `[→ARMS]`, `[→METRICS]`, `[→INJECT]`.

**The one thing to read if you read nothing else:** §1.4 (state parity) and §5.3 (poison-survival classification). Without them the paper's central claim is unfalsifiable.

---

## 1. The decomposition

### 1.1 Three layers, exactly one of which is generative

| Layer | Who | What it does | Can it be a "judge"? |
|---|---|---|---|
| **L0 — Environment / Oracle** | Harness code. No model. | Owns world state, applies transitions, computes the terminal oracle, writes the structured decision log, authors/selects every judge-visible string. | No — it is the ground truth |
| **L1 — Generator / Executor** | **DeepSeek-V41-Flash only.** | The only layer that emits free text or takes actions: code edits, prose, plans, checkpoint notes, tool calls. Its output *is* the trajectory. | Its output is the object being judged |
| **L2 — Judgment** | All three (LLM, Jev, Laya) | Answers a typed question about a bounded state handed to it. No tools, no re-reading, no side effects. | Yes — the comparison lives here |

Consequence, stated flatly: **a "Jev-only long-horizon run" does not exist and must never appear in the paper as a treatment.** Jev and Laya are discriminative; there is no agent. Every long-horizon run in this design is executed by the LLM, and all three systems are compared at *junctions inside* that run.

### 1.2 The two sub-task classes

**Class G — generative.** Produce an artifact, a next action, a summary, a repair. Attemptable by: **LLM only.** Class G is *not* a head-to-head comparison. It is the spine that manufactures the states, and its quality is a context variable. `[→METRICS]` owns its instrumentation; R14 owns only the requirement that **the generator emit a structured decision record at every junction** (`{junction_id, chosen_action, rationale_span, artifacts_touched, assumptions[]}`) so that items can be extracted and carrier-lift can be measured.

**Class D — discriminative.** Answer a typed question about a fixed, bounded state. Attemptable by: **all three.** The entire battery in §4 is Class D. Class D is where the paper's comparative claim is made.

**The load-bearing consequence:** the paper can claim horizon effects on Class G directly (does the long run succeed?) and on Class D only *through the carrier* — the bounded residue of earlier decisions that the judge is shown. The interesting scientific claim is therefore:

> Horizon degrades the **carrier**. A judge that must rely on the carrier degrades with it. A generative model partially escapes this because, as generator, it can *rebuild* context by acting — which is exactly the ability it does not have in the judge role.

This is why the carrier-lift probe (§4.3) and the horizon knob (§5) are the two instruments the paper actually needs.

### 1.3 Capability matrix — who may attempt what

| Item form | LLM (as judge) | Jev | Laya |
|---|---|---|---|
| Class G: produce artifact / action / prose | **yes (only)** | no | no |
| noul (yes / no) | yes | yes | yes |
| choice, ≤4 options | yes | yes | yes |
| score, ≤5 ordered levels | yes | yes | yes |
| check (evidence vs claim) | yes, collapsed 4-way | yes, full 6-way | yes, 4-way, **English only in practice** |
| rank, ≥3 candidates | yes (list order) | yes (`rank`) | **no** → reduced to a `choice` ("which is worst?") |
| multi-span state > ~480 tokens | yes | yes | **no** — tail silently dropped |
| State in a Latin-script language outside en/fr/de/es/pt/it/nl | yes | yes | **no** — silently routed to the English checkpoint, answers confidently and wrongly |
| State re-read / tool use / second look | **forbidden in Class D** | n/a | n/a |

Two rules follow and are non-negotiable:
- **R-LAYA-1 (window):** every item shipped must fit Laya's English 512-token window with margin. This shapes the *corpus* (§3, F2's span-length invariant) rather than being patched at the end.
- **R-LABEL-1 (common label set):** the head-to-head is scored only on labels all three can emit. Jev's `undecided` and `unknown` are mapped to `insufficient` for the primary metric; the raw 6-way output is a pre-registered secondary analysis, and Jev's `unknown` *rate* is reported as a service-reliability diagnostic (a remote `unknown` may be an outage, not a judgment — do not interpret it as epistemic caution without checking).

### 1.4 State parity protocol — the master rule

**R0.** *Every judge-visible string is authored or selected by L0. No judge ever judges a state it produced.* Checkpoint summaries, carrier ledger lines, and candidate option sets are generated by the harness (templated, or frozen once by a non-judged configuration) and are then **frozen and hashed**. The generator's *live* output is never the state of an item it is judged on. This is the single rule that keeps the comparison from being self-graded.

**R1.** Every judge receives the **byte-identical** state string, the same option strings in the same order, the same label set, single-shot, no tools, forced choice. The state string is hashed (`sha256`) at freeze time and re-verified at collection time; a hash mismatch voids the item.

**R2.** For every item, `laya_plan(..., strict=true)` is run at build time. Any item whose state would be truncated, or whose option block exceeds 4 options / 192 tokens / 48 tokens per option, is **rejected, not trimmed**. Rejections are counted and reported (gate G1, §7).

**R3.** A judge that wants more context has failed the item. "LLM-as-judge with retrieval/tools" is a *different arm* `[→ARMS]` and a different estimand; if it is run, it must be reported as such and excluded from the primary N.

**R4.** Decision rules are fixed in advance so that all three judges produce a hard label: Laya noul → `p > 0.5`; Jev noul → `p > 0.5`; Jev rank/check → argmax; Laya score → nearest level, `.5` rounds down; LLM → first valid label token, anything unparseable counted **incorrect** with the unparseable rate reported.

---

## 2. What "long-horizon" must mean here — three tests a family must pass

The phrase is empty unless it is operational. A family qualifies only if all three hold, and each must be demonstrated with a **witness** at design time, before any judge is called.

**LH-1 (non-separability).** The terminal oracle score `S` is not a sum of per-junction local scores: there exist junctions `i < j` such that `S` depends on the action `a_i`, and no bounded view at `j` (≤512 tokens) entails whether `a_i` was correct. *Test:* fit a local-only predictor (logistic regression on the junction's own bounded view + junction metadata) to predict `S`; if it reaches ≥0.95 of the full-carrier predictor's performance, `S` is separable and the family is **"many steps", not long-horizon** → reject.

**LH-2 (history-dependent optimal policy).** There exist `i < j` and two valid prefixes differing only in `a_i` such that the oracle-optimal action at `j` differs. Each family must ship **two path-divergence witnesses**: a written pair `(prefix_A, prefix_B, a*_j(A), a*_j(B))` computed by the oracle, with a one-line causal account. This is the concrete meaning of "an early wrong decision poisons later steps".

**LH-3 (lossy carrier).** The information needed at `j` must survive a **bounded-width** carrier (we fix it at 5 ledger lines + optional ≤120-token checkpoint summary, §5.2). If the required information fits in an unbounded context, the task tests context length, not horizon; if it fits in nothing the judge can see, the item is unanswerable by construction (see §6, T3 — the threat I could not fully close).

**Rejected framing.** "128 steps" is not horizon. A 128-step task whose per-step score decomposes is *many steps* and must be labelled that way in the paper. F4's negative control exists precisely to demonstrate that the knob does nothing when LH-1 fails.

---

## 3. Task families

Four families. Each entry gives: objective, accumulate-error chain, ground truth, injectable junction, difficulty knob, 512-token decision unit, the long-horizon argument, and invalidation conditions.

### F1 — `SPECSHIFT`: maintain a service against a spec that moves, across resumable checkpoints

**Objective (128 junctions).** Keep `ledgerd` — a 9-module Python service (HTTP ingest → SQLite ledger → nightly reconciliation job → CLI) — passing a frozen 84-test acceptance suite while `SPEC.md` is revised four times (v1 at J0, v2 at J32, v3 at J64, v4 at J96). The run is cut into four segments by context resets at J32/J64/J96: after each reset the generator sees only the code, the current spec, and the ≤120-token checkpoint note it wrote immediately before the reset.

**Accumulate-error chain (the poison).**
1. J≈4: from v1 §7.2 ("residual shall be allocated to the leg with the largest fractional remainder; ties by lower leg index"), the generator implements `legs[0] += residual` — a defensible reading, and the §7.2 test passes because in the test fixture leg 0 *has* the largest remainder.
2. J32: v2 §7 changes the rule to banker's rounding at the ledger level. Nothing fails, because `sum(legs) == total` holds under both rules and no test inspects *which* leg received the residual.
3. J64: v3's idempotency-key requirement forces a rewrite of the ingest path; the rewrite reuses the (now wrong) residual helper.
4. J96: v4 §9 requires a replay test — 100 stored rows recomputed under the current rule and compared. Exactly 12 rows differ, all of them rows written before J32. The failure is invisible for **~90 junctions**, and the terminal oracle (suite + 100-row replay equality) is the first place it surfaces.

**Ground truth (executable, not judged).** Every spec clause carries either a pytest node id or a *statically decidable* predicate over the source (`AST` queries, e.g. "the residual assignment target is `argmax(fractional_remainders)`"). The terminal oracle is the frozen acceptance suite plus the replay equality check. Per-clause pass/fail per junction is computed by the harness.

**Injectable junction.** J4 (the residual reading) and each epoch boundary ("re-derive the rule, or reuse the stored helper?"). `[→INJECT]` can substitute a pre-authored wrong candidate at either.

**Difficulty knob.** (a) revisions 1→4; (b) fraction of clauses with *executable* tests 1.00→0.60 (forcing reliance on judgment over testing); (c) detection delay between clause and catching test 0→90 junctions; (d) codebase size 3→12 modules.

**Decision unit (≤512 tokens).** One clause verbatim (≤80 tokens) + one diff hunk (≤130) → Q1. Hunk + two failing test lines → Q3. Ledger tail (55) + hunk + pending-epoch note → Q6.

**Why long-horizon, not many steps.** The deciding fact — *which rounding rule the 12 stored rows obey* — is in no local view and in no failing test until J96; the only carriers are the code's history and the checkpoint notes. LH-2 witnesses: at J64, if `a_J4` = "largest remainder", the optimal action is "re-derive rounding and backfill before adding idempotency"; if `a_J4` = "§7.2 literal", the optimal action is "add idempotency only". The two prefixes are identical in all other respects.

**What would invalidate F1.** (i) Each spec revision's repair set confined to files not yet touched → local views suffice, it is a codegen benchmark; (ii) the acceptance suite satisfiable clause-by-clause with no coupling → LH-1 fails; (iii) checkpoint resets removed → the LLM's context carries everything, and the *judge* comparison loses its object (the task survives, the experiment does not); (iv) any judge able to read the repo → R0/R1 violated.

---

### F2 — `EVIDENCE-BRIEF`: a living claim table over a planted corpus, ending in a traceable decision memo

**Objective (128 junctions).** From 60 authored documents (6 fictional agencies: *National Grid Siting Board*, *Battery Safety Council*, *Northmoor District Council*, *Interconnect Standards Office*, *Fire Risk Inspectorate*, *Ratepayers' Federation*), build a **claim table** of 40 claims, resolve planted contradictions, track provenance and source tier, then write a 12-section decision memo whose every assertion maps to a claim-table row.

**Planted structure (authored, machine-readable).** Each document span carries an annotation record: `(doc_id, span_offsets, entity, predicate, value, polarity, scope_period, modality, source_tier ∈ {1,2,3})`. Planted: 18 claim tuples with 2–3 conflicting spans; 7 where exactly one side is tier-3 (authority control); 9 "insufficient" tuples where the only available span has a mismatched scope or is modal (an *expectation*, not a fact); 40 tuples overall; a claim dependency graph of depth 1–5 (e.g. C-24 is derivable only from C-11 + C-19).

**Corpus invariant (this is what makes the battery possible).** **Every decisive evidence span is authored at ≤130 tokens and every supporting span at ≤60 tokens.** Spans are excerpts, not documents. This is a real cost to realism, accepted deliberately: it is the reason every F2 item fits a 512-token judge.

**Accumulate-error chain.** At J≈8 the generator records C-11 as `SUPPORTED` after reading only the tier-1 span. Sections 3 and 7 are then written on C-11; C-24 is derived from C-11 + C-19 at J≈70 and is therefore wrong in a way that is internally consistent; the memo's conclusion chain is unsound at J128. The terminal oracle is **traceability closure**: every memo assertion must map to a claim-table row, and every row's status must equal the status computed from the annotation records.

**Ground truth (authoring-time records).** Status is a deterministic function of the annotation table: `SUPPORTED` iff ≥1 span covers the claim's full `(entity, predicate, scope)` tuple with the claim's polarity and tier ≤2; `CONTRADICTED` iff a covering span has opposite polarity at tier ≤2 and no covering same-polarity span at tier ≤2; `CONFLICTED` iff covering spans of opposite polarity at equal tier; `INSUFFICIENT` iff no span covers the tuple (scope/modality mismatch ⇒ no coverage). No model labels anything, ever.

**Injectable junction.** J8's status call; and any junction where a *tempting but non-covering* tier-3 span is handed to the generator.

**Difficulty knob.** (a) contradiction density 0.05→0.45 of tuples; (b) scope-mismatch rate 0.10→0.50; (c) dependency-graph depth 1→5; (d) citation forcing: fraction of sections required to cite ≥3 claims 0.25→1.0.

**Decision unit.** Claim (≤60 tokens) + span A (≤130) + span B (≤60) + 4 verdict options (≤38 each) ≈ 480. ✓

**Why long-horizon, not many steps.** Correctness of the terminal artifact is a *global* property — closure of the trace — and no single section exhibits it; an early over-claim makes later sections look *better*, not worse. Twelve independent sections with no claim table would be "many steps" and would fail LH-1 by construction.

**Invalidations.** (i) Real entity names, or any corpus text found by n-gram/embedding search in a public corpus (contamination) → keep entities fictional and run the search; (ii) the traceability oracle satisfiable by copying the annotation table → the generator must never see the records, only the documents; (iii) span invariant relaxed → items exceed the window and the family becomes Laya-incompatible; (iv) a bag-of-words model ≥0.80 on the check items → the items test lexical overlap, not judgment → regenerate (gate G3).

---

### F3 — `SCHEMA-EPOCH`: a migration whose schema changes three times mid-run, with a row-level oracle

**Objective (128 junctions).** Migrate `evt_raw` (2.1M rows; schema v3: 14 columns, epoch-seconds, nullable strings) to v6 (19 columns, tz-aware ISO-8601, typed enums, plus derived `session_key`), with revisions at J32 (v4: `tenant` becomes NOT NULL with a derivation rule), J64 (v5: `amount` float → integer minor units), J96 (v6: `session_key` derivation changes to include `channel`).

**Accumulate-error chain.** J≈12: the generator decides that `source.ts` values with a `+00:00` offset are "already UTC" and stores them verbatim — defensible under v3, which is silent. v4 and v5 pass cleanly. At v6 the `session_key` derivation over the *stored* timestamps produces keys that disagree with expectation for the 6.3% of rows with non-UTC offsets. The rows are already written; recovery requires re-reading `evt_raw` — and **the harness revokes source access at J64**. The error is silent for ~80 junctions and is *jointly* wrong: each epoch was locally correct.

**Ground truth (deterministic oracle).** Expected destination built by a frozen reference transform; oracle = row-hash diff plus 34 SQL assertions (`sum(amount_minor) = round(sum(source.amount)*100)`, per-tenant cardinality, `session_key = sha1(tenant||date||channel||seq)`, non-null rates, no dropped columns).

**Injectable junction.** J12's normalization decision; and every epoch boundary's "re-derive vs reuse" choice.

**Difficulty knob.** (a) epochs 1→4; (b) fraction of columns whose source semantics are underdetermined 0.10→0.60; (c) irreversibility (source revoked at J64 vs retained); (d) detection delay 1→96 junctions.

**Decision unit.** One schema clause (≤80) + one `(source row → stored row)` pair (≤130) → Q1/Q3. Ledger tail + v6 note + a 6-row stored-vs-expected sample → Q6. Four candidate mapping rules + a 6-row sample → Q2.

**Why long-horizon, not many steps.** The failure is a *consistency* property across epochs: a per-epoch-correct answer can be jointly wrong, and the joint oracle is the only thing that sees it. Irreversibility makes the horizon load-bearing rather than decorative. LH-2 witness: after J64, if `a_J12` was "store as-is", the optimal action at J96 is `halt + human review` (no recovery path); if `a_J12` was "normalize to UTC", the optimal action is `backfill session_key`.

**Invalidations.** (i) The migration can be re-run idempotently at the end → one final re-migration fixes everything → remove by revoking source access; (ii) the reference transform matches a public tool's default (dbt/Airbyte) → authored, non-standard derivation rules + a defaults baseline diff; (iii) the oracle gameable by nulling rows → add non-null and cardinality assertions; (iv) the ambiguity resolvable from schema comments → strip provenance hints from DDL.

---

### F4 — `AUDIT-CASCADE`: budget-constrained adaptive audit over a planted corpus

**Objective (≤400 junctions).** Over 12,000 authored alert records with authored fields (channel, amount band, counterparty-country tier, velocity, note ≤120 tokens), find as many of the **168 planted critical items** (1.4% prevalence, distributed across 5 hidden strata) as possible within **400 inspections**. The sampling rule is a *tree*: an inspection returns its label, and a stratum is only expanded if an already-confirmed critical item implicates it. The generator must decide, at each junction, which stratum to expand and when to stop.

**Accumulate-error chain.** An early false negative on a critical item in stratum S2 prunes S2's subtree permanently; the recall ceiling drops and no later diligence recovers it. Terminal metrics: `recall@400` and `precision of the critical set`, both against the planted labels, plus a harness-computed counterfactual: **reachable-critical count** given the generator's confirmed set under the reference policy.

**Ground truth (planted labels + deterministic reachability).** Labels are authored; reachability is computed by the harness's rule engine. No model labels anything. Every planted critical item must be *decidable from its own record under the written policy* — verified by two authors independently, disagreement kills the item.

**Injectable junction.** J6 (first stratum call), and every "expand or stop".

**Difficulty knob.** (a) prevalence 1.4%→0.3%; (b) hidden strata 2→7; (c) budget 800→200; (d) label noise on 0/5/15% of records; (e) coupling strength of the sampling rule (independent → strict tree).

**Decision unit.** One record (≤130 tokens) + the policy rule (≤60) → Q1/Q4. Ledger tail (55) + stratum statistics (≤120) → Q6. Four candidate next strata with their stats (≤38 each) → Q2.

**Why long-horizon, not many steps.** The metric is budget-constrained coverage, a function of the whole path: the same per-item classifier with 92% accuracy yields 55% or 78% recall depending on where the budget went. Early errors permanently lower the ceiling. LH-2 witness: after a J6 false negative on S2, the optimal J40 action is "expand S4 by rule R2 instead"; after a true positive, "deepen S2".

**Invalidations.** (i) The generator can inspect arbitrary items → coupling vanishes → the harness must *mechanically* enforce the rule (the agent submits a stratum request; the harness returns records from it); (ii) the free-text note leaks the label → strip label-correlated tokens and validate with the G3 lexical baseline; (iii) some critical items undecidable from their record → two-author decidability check.

---

### Rejected candidates

**Reject (iv)-as-stated — uniform triage/audit with measurable drift.** Ground truth is fine (planted labels), but **LH-1 fails**: with independent per-item labels, terminal accuracy decomposes into per-item accuracy; the "drift" is a property of the rubric text, a single generative artifact, not of the horizon. It measures many steps. **Retained deliberately as `F4-CTRL`**, a budget-unconstrained uniform triage loop, as the *horizon placebo*: if drift-vs-horizon is flat there and slopes in F1–F4, the knob is doing what the paper claims and the effect is not "long contexts are hard in general".

**Reject anything whose ground truth would need an LLM grader.** That includes free-form "quality of this research plan", holistic prose scores, and "is this a good summary" without a proposition list. If a label cannot be computed by a mechanical predicate, an execution, a simulator, or an authoring-time record, **the item does not ship**.

### Reserve family (if `[→INJECT]` does not claim the incident surface)

**`ONCALL-HORIZON`** — fault-graph incident response: a deterministic service simulator with planted faults, where the *world state changes as a consequence of the agent's own earlier mitigations* (endogenous state). This has the strongest of all the long-horizon mechanisms — active interference — but its planted faults sit close to the fault-injection unit's surface, so it is offered as F5 only if that unit confirms no overlap. Decision units: one alert + one log excerpt (Q4), four diagnostic actions (Q2), ranked hypotheses (Q5).

---

## 4. The decision-point item battery

### 4.1 State envelope and the token budget

Every item is one string with five slots. The scaffold is **byte-identical across all items and all judges** (it carries no item information).

```
[R0] <SCAFFOLD>     ≤35 tok   constant: role line + output format + "answer with exactly one label"
[R1] <CARRIER>      ≤55 tok   ≤5 ledger lines, each ≤11 tok: "J{n} {decision} -> {consequence}"
[R2] <LOCAL>        ≤190 tok  primary span ≤130 + optional secondary span ≤60
[R2'] <SUMMARY>     ≤120 tok  only for Q7; then LOCAL shrinks to ≤90
[R3] <STEM>         ≤25 tok   the typed question
[R3'] <BOUNDARY>    ≤40 tok   required on every noul: what TRUE and FALSE mean
[R4] <OPTIONS>      ≤152 tok  ≤4 options × ≤38 tok
```

| Slot | Cap | Why this cap |
|---|---|---|
| Scaffold | 35 | constant, so it cannot correlate with the label |
| Carrier | 55 | fixed width — see §5.2; horizon must vary *content*, not size |
| Local | 190 | primary span authored ≤130 (F2 corpus invariant) |
| Stem + boundary | 65 | Jev requires an explicit boundary on noul; an unstated boundary makes 0.5 uninterpretable |
| Options | 4 × 38 = 152 | Laya: 48 tok/option hard cap, 192 tok/question budget (English). 4 × 38 leaves headroom; 5 score levels at ≤36 tok = 180 ≤ 192 |
| **Total** | **≤497** | vs. Laya's 512-token English window; gate rejects at >512 with `laya_plan(strict=true)` |

**Two accountings apply to option text simultaneously**: it consumes Laya's state window *and* its per-question option budget. Both are respected by the caps above. Score items cap at **5 levels** for the same reason; rank items never exceed 6 candidates because Jev's `rank` question budget is 4,000 chars and each candidate costs `126 + len(criterion)` chars — so the criterion must be terse (≤120 chars) and the detail must live in the state.

### 4.2 The seven item classes

Per horizon level, 60 items; five levels; **N = 300** (§4.5).

| ID | Class | Type | /level | Total | Ground truth source | Primary metric |
|---|---|---|---|---|---|---|
| Q1 | clause-consistency | noul | 8 | 40 | executable test or static predicate (harness) | balanced accuracy |
| Q2 | next-action | choice(4) | 12 | 60 | exhaustive simulator rollout / execution | accuracy |
| Q3 | rubric-score | score(5) | 8 | 40 | static predicate vector, mechanically composed | exact-level accuracy + ordinal MAE |
| Q4 | evidence-verdict | choice(4) | 12 | 60 | annotation records (coverage + polarity + tier) | accuracy + macro-F1 over 4 labels |
| Q5 | shortlist-rank | rank + choice(4) | 6 | 30 | simulator scores / dependency counts / planted tiers | Kendall τ (Jev-only) + top-1 accuracy (all) |
| Q6 | halt / escalate / continue | noul + boundary | 8 | 40 | reachability rollout + pre-registered safety predicates | accuracy; escalation-recall reported separately |
| Q7 | summary-faithfulness | noul or choice(4) | 6 | 30 | harness decision log + scripted corruption labels | accuracy |

Families contribute 15 items per level each (4 × 15 = 60).

---

**Q1 — clause-consistency (noul).**
*Shape:* `CLAUSE: <verbatim constraint, ≤80 tok>` + `ARTIFACT: <hunk / span / row-pair, ≤130 tok>` + `BOUNDARY: TRUE = the artifact satisfies CL01 as written; FALSE = it violates CL01, or CL01 is left undetermined by the artifact.` + `Does this artifact satisfy CL01?`
*Ground truth:* F1 — the clause's pytest node id or its AST predicate, evaluated on the artifact; F2 — the annotation records (does the artifact's proposition match the clause tuple exactly?); F3 — an oracle SQL assertion on the transformed sample; F4 — the policy rule applied to the record's fields.
*512-fit:* 80 + 130 + 40 + stem + 2 options ≈ 300. Comfortable; the cheapest class to keep in-window.
*Why it is not trivial:* the "undetermined" arm of the boundary is the interesting half — 40% of Q1 items have artifacts that neither satisfy nor violate the clause, and a yes-biased judge fails them.

**Q2 — next-action (choice ×4).**
*Shape:* carrier + `LOCAL: <current junction's observable state, ≤190 tok>` + `Which next action should be taken at J{n}? A/B/C/D` (each option ≤38 tok).
*Ground truth:* **exhaustive rollout in the L0 simulator under a scripted reference policy** — for each of the 4 candidates, roll the remaining run forward deterministically and take the candidate maximizing the terminal oracle. Ties (or a margin below a pre-registered ε) ⇒ strip discarded, and the discard rate is reported. For F1, the candidates are 4 scripted repairs and the winner is the one whose clause test passes without breaking the regression suite (execution). For F2, the winner is computed from the claim dependency graph (which claims are now blocked).
*Anti-circularity:* the reference policy is *scripted code*, not an LLM; ground truth is a computed argmax, not an opinion.
*512-fit:* 55 + 190 + 25 + 152 = 422. ✓
*Note:* 4 candidates is the ceiling, and the ceiling is Laya's, not ours.

**Q3 — rubric-score (score, 5 levels).**
*Shape:* `RUBRIC: L0..L4` (each ≤36 tok) + `ARTIFACT: <hunk, ≤130 tok>` + `Score the artifact against RUBRIC. 0/1/2/3/4.`
*Ground truth — the key move:* **levels are defined as a conjunction prefix over statically decidable predicates**, so the level is *computed*, not judged. F1 example: L0 = hunk does not parse/apply; L1 = parses but P1 (residual assigned to `argmax` remainder) false; L2 = P1 ∧ ¬P2 (`utcnow()` still called); L3 = P1 ∧ P2 ∧ ¬P3 (no empty-input handling); L4 = P1 ∧ P2 ∧ P3. Level = the satisfied prefix, evaluated by AST queries on the shipped artifact.
*Why this is legitimate:* the judge is asked to **predict a mechanical function of an artifact it can see** — a real inference (it cannot run the analyser), with an exact label. Construct-validity cost, declared: taste/architecture dimensions are excluded (see §6, T4).
*512-fit:* rubric block ≤180 + artifact ≤130 + stem ≈ 340. ✓
*Decision rule:* nearest level, `.5` rounds down; Laya/Jev expected values reported as a secondary ordinal metric.

**Q4 — evidence-verdict (choice ×4: supported / contradicted / conflicted / insufficient).**
*Shape:* carrier + `CLAIM: <≤60 tok>` + `SPAN A [doc, tier, scope]` (≤130) + `SPAN B [doc, tier, scope]` (≤60) + verdict options (≤38 each).
*Ground truth:* the coverage function over annotation records — `SUPPORTED` iff a covering span with matching polarity at tier ≤2 exists; `CONTRADICTED` iff a covering opposite-polarity tier-≤2 span exists and no covering same-polarity tier-≤2 span does; `CONFLICTED` iff covering opposite-polarity spans at *equal* tier; `INSUFFICIENT` iff no span covers the tuple (scope/modal mismatch ⇒ no coverage). Computed from authoring-time records (F2), or from harness-generated structured events (F1 logs, F3 samples, F4 records, where each event carries its own annotation record so coverage is computable).
*This is the most scientifically interesting class:* it is where a 421M encoder can plausibly beat a large generative model on cost-adjusted accuracy, because the decision is local, short, and shape-based — and where the LLM's usual escape (re-reading, world knowledge, verbosity) is removed.
*Anti-lexical-overlap controls (required):* (a) *trap* items: span and claim share ≥70% content-word overlap but the span is negated / scope-swapped ⇒ label `contradicted` or `insufficient`; (b) *paraphrase* items: ≤10% overlap, label `supported`; (c) *two-span* items where the naive answer is `conflicted` but the tier/scope analysis makes it `supported` (worked example in §4.6).
*Trap fairness:* every trap item is reviewed by **two human annotators**; kept only if both agree with the computed label *and* rate the wrong answer as "tempting but wrong". This is the single best use of the human-annotation budget in the design, and it is not circular — annotators validate a computed label, they do not supply it.
*512-fit:* 55 + 60 + 130 + 60 + 25 + 152 = 482. ✓ Tight; the secondary span is capped at 60 for this reason.

**Q5 — shortlist-rank.**
*Shape (all judges):* `Which of these is the WORST candidate by CRIT? A/B/C/D` (4 candidates ≤38 tok each). *Shape (Jev-only stratum):* `rank` with a criterion ≤120 chars and ≤6 candidates ≤180 chars each.
*Ground truth:* candidate quality is *computed*, never rated: F1 — number of currently failing acceptance tests blocked by the clause; F2 — planted source tier and dependency out-degree; F3 — number of downstream assertions affected by the column (from the dependency graph); F4 — simulator terminal recall if that stratum is opened next.
*Why reduced:* Laya cannot rank a list, and its accuracy degrades above ~20 options — a 4-candidate "worst" choice is inside its competence. Comparing Jev's `rank` output against the same item's choice form measures whether `rank` adds anything over `choice`; that comparison is a **pre-registered secondary analysis** and the ~48 Jev-only rank items live in a **separate stratum outside the primary N**.
*512-fit:* 55 + 190 + 25 + 152 = 422. ✓

**Q6 — halt / escalate / continue (noul + boundary).** *The core long-horizon instrument.*
*Shape:* carrier + `LOCAL: <the current state, which is deliberately locally consistent and looks fine, ≤190 tok>` + `BOUNDARY: TRUE = the run cannot reach the terminal oracle without an action the harness has made unavailable (e.g. re-reading revoked source, re-reading a superseded spec revision); FALSE = a legal action sequence still reaches the oracle.` + `Should the run halt for human review before J{n}?`
*Ground truth:* reachability rollout in L0 — the simulator enumerates whether any legal action sequence from the current state reaches the oracle threshold; plus pre-registered one-way safety predicates (F3: "a column was dropped whose values a future revision requires" fires halt unconditionally).
*Why it is the core instrument:* the local block alone yields the *wrong* answer; only the carrier flips it. These items are the designated subjects of the carrier-lift probe (§4.3).
*512-fit:* 55 + 190 + 25 + 40 + 2 options ≈ 330. ✓

**Q7 — summary-faithfulness.** *The carrier's own audit.*
*Shape:* carriage + `SUMMARY S (≤120 tok)` + `Is S faithful to the run log through J{n}? yes/no`, or a 4-option variant `Which sentence of S is not supported by the log?` (4 sentences ≤38 tok each).
*Ground truth — exact by construction:* S is generated from a **machine-readable proposition list** built from the structured decision log (each proposition references a log event id). *Unfaithful* variants are produced by a scripted corruption with a known target proposition: swap the affected module, drop a load-bearing decision, promote a conditional to an assertion. The corrupting edit is known, so the label is exact. Fluency is varied by a **frozen paraphraser** (a configuration not under test), so "templated" and "fluent" summary variants are reported **separately** — this isolates *detecting drift in fluent prose* from *checking a template*, which is the difference between a hard item and a formatting exercise.
*Anti-circularity:* no judged model ever writes a summary that is judged; the R0 freeze applies.
*512-fit:* 55 + 90 (local) + 120 (summary) + 25 + 152 = 442. ✓
*Three sub-variants per family:* faithful, one-proposition-corrupted, and *omission* (S omits a decision the log flags `load_bearing: true`). The omission variant is the one that catches a judge that only checks local consistency.

### 4.3 The carrier-lift probe (secondary, n=100 pairs)

The instrument that makes the "bounded view" constraint a *measurement* rather than an excuse.

For each of 50 designated items (Q4 and Q6, at horizon levels d=28 and d=124, 25 per level), build **two variants with identical token counts**:
- `L`: local block only; the carrier slot is padded with *neutral filler* — ledger lines drawn from a frozen pool of no-op lines ("J{n} ran the linter -> clean"), verified at authoring time to carry no decision content.
- `L+C`: the real carrier.

The difference in accuracy `acc(L+C) − acc(L)`, per judge, is **carrier use**. That is the direct measurement of the paper's central mechanism, and it is a within-item manipulation.

- These 100 instances are a **separate analysis stratum**, never merged into the primary 300 (no double-dipping).
- Power: paired McNemar at n=100 detects ≈15 points at ψ=0.20 — adequate, because carrier lift is expected to be large (it is the difference between having and not having the decisive fact).
- Filler neutrality is an authoring claim that must be stated: the filler is frozen, contains no decision content, and is not separable from real ledger lines by the G3 lexical baseline.

### 4.4 The Jev-only extension stratum (outside the primary N)

~48 items (24 `rank`, 24 full 6-way `check`) where Jev's richer primitives have no Laya analogue. Pre-registered as secondary. Two questions it answers: (a) does `rank` beat `choice` on the same shortlist? (b) do Jev's `undecided`/`unknown` labels carry information (i.e., is Jev's abstention better than chance)? Neither may enter the head-to-head N.

### 4.5 N and power — why 300, not 150 and not 600

**Design.** The primary contrast is a **paired** judge difference in decision accuracy on identical items ⇒ McNemar. With discordance proportion ψ and true difference Δ, the required n is

```
n = [ z(1−α/2)·√ψ  +  z(1−β)·√(ψ − Δ²) ]² / Δ²
```

At α = 0.05 two-sided, power 0.80, Δ = 0.10:

| ψ (discordance) | required n |
|---|---|
| 0.10 | 77 |
| 0.20 | 155 |
| **0.30 (conservative)** | **234** |

ψ is not known before collection, so the design is powered at the **conservative ψ = 0.30 → n = 234**.

**Collection.** 5 horizon levels × 60 matched slots = **300 item instances**, all judges answer all 300. Gate G1 (§7) is expected to reject 5–10% for window/option violations ⇒ **≥270 analysed ≥ 234** with margin. Precision at n = 270, ψ = 0.30: 95% CI half-width on the paired difference = `1.96·√((ψ−Δ²)/n)` ≈ **±6.4 points** for the main effect.

**Why not fewer.** Below ~234 the study cannot resolve a 10-point paired difference at the conservative discordance, and the headline effects of interest (Laya vs Jev on 512-token items; LLM judge vs Jev) are plausibly in the 5–15 point band. Per-cell n = 60 has an MDE of **16–20 points** — so *no per-cell claim is supportable*: family-level (n = 15 slots) and class-level comparisons are explicitly **exploratory and descriptive only**, reported with cluster-bootstrap CIs, and pre-registered as such.

**Why not more.** 300→600 costs double for a CI narrowing of √2 (±6.4 → ±4.5 points), which changes no decision in the paper at the expected effect sizes; the marginal money is far better spent on the trap-item audit (§4.2 Q4), which is the binding credibility cost, and on the two secondary strata (carrier-lift, multilingual) that are otherwise unpowered.

**The horizon analysis is a slope, not a set of cell contrasts.** The pre-registered primary model is a mixed-effects logistic regression of item correctness on `judge × log2(H)` with random intercepts for slot and run lineage. This uses all 300 items, so the judge × horizon interaction is far better powered than any single-level contrast; the design analysis (10,000 Monte-Carlo replications of that model under the pre-registered effect grid, run before collection) targets 80% power for an interaction of **0.04–0.05 accuracy per doubling of horizon**. If the simulation says 300 is insufficient for that target, the pre-registered extension rule is **+75 slots (75 × 5 = 375)** — declared now, not after seeing results.

**Cluster structure.** Items are not independent: 60 slots × 5 levels, 4 families, and shared run lineages. Slot-level pairing handles the within-slot dependence by design; all CIs are cluster-bootstrapped by slot and by run lineage; the between-slot quantities (e.g. "F3 drifts more than F2") have an effective n of 15 per family and are reported as descriptive.

### 4.6 Worked examples (real strings, compressed to fit)

**Q4 trap item (F2).**
```
CARRIER: J04 claimed C-11 SUPPORTED | J05 cited D-07 in S3.1 | J06 opened C-24 | J07 status C-24 pending
CLAIM:   The 2024 siting cap for the Northmoor district is 240 MW.
SPAN A [D-07 | tier 1 | scope 2024]: "Northmoor's permitted capacity was raised to 240 MW
        effective January 2024; the earlier 180 MW ceiling applies only to the 2021–2023 programme."
SPAN B [D-31 | tier 3 | scope 2026]: "District caps in Northmoor have historically been set at
        180 MW, and no upward revision is expected before 2026."
OPTIONS: A supported | B contradicted | C conflicted | D insufficient
KEY:     A
```
*Computed label:* Span A covers `(entity=Northmoor cap, predicate=limit, value=240MW, scope=2024)` with matching polarity at tier 1 ⇒ `SUPPORTED`. Span B covers a *different* tuple (scope 2026, modality = expectation) ⇒ no coverage, so it cannot create a conflict. The tempting answer is C. Two-anthropic... two-**annotator** review required.

**Q1 item (F1).**
```
CLAUSE §7.2 (v1): "When a total does not divide evenly, the residual cent shall be allocated to
                  the leg with the largest fractional remainder; ties broken by lower leg index."
ARTIFACT: residual = total - sum(legs)
          legs[0] += residual            # deterministic
BOUNDARY: TRUE = the artifact satisfies §7.2 as written; FALSE = it violates §7.2, or §7.2 is
          left undetermined by the artifact.
KEY: FALSE   (AST predicate: assignment target must be argmax(fractional_remainders))
```

**Q6 carrier-only item (F3).**
```
CARRIER: J10 tz '+00:00' stored as-is | J31 v4 tenant default applied | J63 v5 minor units |
         J64 source evt_raw access REVOKED | J95 v6 session_key now includes channel
LOCAL:   v6 §4.1 + a 6-row stored-vs-expected key sample; 2 rows mismatch, both tz-offset rows.
BOUNDARY: TRUE = the run cannot reach the acceptance oracle without re-reading a source the
         harness has revoked; FALSE = a legal action sequence still reaches the oracle.
KEY: TRUE    (reachability rollout: mismatch rows require source re-read; no legal path)
```
The local block alone suggests "fix forward". Only the carrier (J64 revocation + J10) forces the halt. This item is a designated carrier-lift subject.

**Q2 item (F4).**
```
CARRIER: J02 expanded S1 | J05 S1 0/240 critical | J06 opened S2 | J07 budget 388 inspections left
LOCAL:   A S4 size 610 cur 0.8% implicating R2 | B S2 size 880 cur 0.0% implicating R1
         C S5 size 240 cur 1.2% implicating R3 | D S3 size 1,300 cur 0.7% implicating R1
KEY: C    (rollout: C maximizes terminal recall@400; margin 3.1 pts > ε)
```

**Q3 rubric (F1), mechanically composed.**
```
RUBRIC: L0 hunk does not parse or does not apply
        L1 parses; residual is not assigned to the largest-remainder leg
        L2 L1 ok; utcnow() still called in the ledger write path
        L3 L2 ok; empty-input list is not handled
        L4 L3 ok
KEY: computed by AST predicates P1, P2, P3 on the shipped hunk
```

---

## 5. The horizon knob

### 5.1 Levels

Horizon is **position in one frozen run**, and it is operationalized as **distance from the planted upstream error** `d`, which is the mechanism the paper is about.

| Level | Junction index H | Distance from poison d | What it tests |
|---|---|---|---|
| **H0 — floor** | J1 | — (before any decision) | item answerable from the local block alone; calibration anchor |
| **H1** | J4 | 0 | the item *is* the poisoned junction (error adjacent) |
| **H2** | J8 | 4 | trace fresh in the carrier |
| **H3** | J32 | 28 | trace survived one checkpoint compression |
| **H4** | J128 | 124 | trace survived three checkpoint compressions |

Five levels (four `d` levels plus the floor), geometrically spaced so drift can be plotted against `log2(H)` and a threshold or a linear-in-log slope can be distinguished. `[→METRICS]` plots drift-vs-horizon; R14 only guarantees the knob is clean.

### 5.2 How to step *only* the horizon

All ten of the following are held fixed; any deviation reopens gate G1.

1. **Same slot.** The local block is byte-identical across the five levels of a slot (same claim, same span, same hunk, same record).
2. **Same stem and same option strings**, same label set, same key.
3. **Same carrier width:** 5 ledger lines × ≤11 tokens, at every level. Horizon changes the *content* of the tail, never its size.
4. **Same summary presence and length:** ≤120 tokens when present.
5. **Same total token count within ±8 tokens**, equalized with frozen neutral filler (§4.3).
6. **Same primary-span position:** always inside the first 40% of the state, so Laya's end-truncation can never be the explanation for a wrong answer (R2 also rejects truncated items outright).
7. **Same correct-option position:** balanced Latin square across slots so option position is orthogonal to horizon. Gate G5 checks the distribution is within ±5% of uniform per cell.
8. **Same family mix:** 15 items per family at every level.
9. **Same run lineage:** for a given slot, levels H1–H4 are all read off the **same executed run** (the prefix is run once with the poison installed at J4, and the log is frozen); H0 is read off a clean run of the same instance. The manipulation is therefore position, not instance.
10. **Same Laya cost:** constant state width ⇒ constant re-encoding cost per item ⇒ **latency is structurally not confounded with horizon**. (Cold start 25–35 s and per-question latency are `[→METRICS]`; the design merely ensures their invariance across levels.)

**Prefix realism.** Prefixes are produced by a real generator run, not authored. Control comes from **selection**: the harness installs the wrong candidate at J4 (via the injectable junction) and includes a run only if the automated checks confirm (a) no *other* upstream error before the item in the poisoned arm, (b) no upstream error at all in the clean arm. The acceptance rate is reported as a design statistic; a low rate is itself a finding about run reproducibility.

### 5.3 Manipulation check — poison-survival classification (pre-registered, per item)

For every item at `d > 0`, the harness computes a **mechanical poison-survival flag** from the *shipped strings*: does any shipped carrier line or summary sentence mention the entity/module/column affected by the planted error, or a consequence of it?

- `survives` — the trace is present in the shipped state.
- `absent` — the trace is not present.

Report the flag for 100% of items and the survival rate **per level**. Items whose trace is `absent` are **not drift items**; a wrong answer there measures memory of nothing. Pre-register that the primary drift-vs-horizon analysis is run on `survives` items only, with the `absent` subset reported separately as a **lower bound control**: if accuracy also falls on `absent` items, the effect is not carrier-mediated and the paper's mechanism claim fails. This single classification is what makes a null result at H4 interpretable.

### 5.4 Collection matrix

300 primary items = 60 slots × 5 levels. Each judge answers all 300 (paired by item). `[→ARMS]` decides whether the LLM judge is run at one or several reasoning efforts; the design requires that if several efforts are run, the **same 300 states, same order, same forced-choice protocol** are used, and that the primary contrast is declared in advance for one pre-specified effort, with the others as secondary. Long-run generation is executed once and frozen; re-running the generator for a second arm destroys the pairing.

---

## 6. Threats to validity, and the cheapest credible mitigation for each

**T1 — Circular ground truth (judges producing the labels they are graded against).** *Mitigation:* R0 (no judge authors a judge-visible string) + the rule that every label comes from an execution, a static predicate, a simulator, or an authoring-time record. If a class cannot meet this, it is dropped, not approximated. Residual human use is limited to *validating* computed labels on the trap subset (~40 items, 2 annotators, ~2 hours), with agreement reported.

**T2 — Window/parity violation or silent truncation.** *Mitigation:* freeze and hash state strings; `laya_plan(strict=true)` at build time; decisive span always in the first 40%; gate rejects rather than trims; the drop rate is reported. Cost: one pre-flight call per item, no model run.

**T3 — Poison invisibility at long horizon (the threat I could not fully solve).** If, at `d = 124`, the shipped 5-line carrier under-determines the correct answer, the item is unanswerable by construction and any measured "drift" is an artifact of item construction, not judge degradation. The §5.3 mechanical flag is a *proxy* for a counterfactual about inference, not the counterfactual itself. *Partial mitigations:* (a) the flag, with the `absent` subset as a lower-bound control; (b) a **solvability floor**: a 10% audit sample (~30 items) where a human annotator, given only the shipped state, must derive the key within 60 seconds — items failing this are excluded and the excluded fraction reported; (c) the two-width carrier-lift probe (5 lines vs 5 lines + summary) to see whether added carrier resolves the item. None of these fully closes it: whether a judge "could have" recovered the poison from a fixed-width string is not decidable from the string alone. **Report the flag, the audit, and the exclusion rate together, and state the residual ambiguity in the limitations section.**

**T4 — Construct validity of score items.** Only *statically decidable* rubric predicates are ground-truthable, so Q3 measures inspection-based prediction of mechanical properties, not artifact quality or taste. *Mitigation:* declare it; run a 20-item side-study with 3 human raters scoring holistic quality, and report the rank correlation between the static-predicate level and holistic rating. If ρ < 0.5, drop the claim that Q3 measures quality and rename the class "rubric-prediction".

**T5 — Non-comparable probability scales (Laya multilingual ships uncalibrated, T = 1.0, emits 0% and 100% readily).** *Mitigation:* the primary metric is **argmax accuracy**, not probability. Probability metrics (ECE, Brier) are computed **within-judge** only, after temperature scaling fitted on a disjoint 20% calibration split, and **raw probabilities are never compared across judges**. Report the calibration split's composition.

**T6 — Language routing hazard.** Any Latin-script language outside en/fr/de/es/pt/it/nl is silently routed to the English checkpoint and answered confidently and wrongly. *Mitigation:* primary battery is **English-only**, asserted by a language-ID check on every state string; `lang` is pinned on every Laya call; the multilingual extension is limited to es/de/fr/pt/it/nl with pinned languages and translated by a frozen pipeline, and — because the annotation records are language-independent tuples — **ground truth is invariant under translation**, which makes that extension nearly free.

**T7 — Self-preference / same-family judging.** If the generator is DeepSeek-V41-Flash and the LLM judge is the same family, it is shown text its sibling wrote. *Mitigation:* all carrier strings are harness-authored or frozen; live generator output is never judged by itself; add a self-preference probe (own-family vs other-family summary variants) as a reported diagnostic. `[→ARMS]`: any "judge its own output" arm stays out of the primary N.

**T8 — Pseudo-replication.** 300 items over 60 slots, 4 families, and shared lineages are not independent; naive CIs are too narrow. *Mitigation:* slot-level pairing, random intercepts for slot and run lineage, cluster bootstrap by slot and lineage, and the explicit pre-registration that family- and class-level comparisons are descriptive (effective n = 15 per family).

**T9 — Lexical-baseline saturability.** A TF-IDF/logistic baseline that reaches high accuracy means the item class tests word overlap, not judgment. *Mitigation:* gate G3 — compute the baseline for every item class before freezing; **regenerate any class above 0.80**. This is the cheapest single validity gate in the design and it should run on day one, because it can invalidate a whole class before any judge is called.

**T10 — Filler contamination in the carrier-lift probe.** Neutral filler might accidentally carry decision content, which would invalidate the `L` variant. *Mitigation:* filler drawn from a frozen pool of no-op lines; authoring attestation; the G3 baseline must not separate filler from real ledger lines; report the pool.

**T11 — Repository-oracle thrash (F1).** A flaky acceptance suite makes ground truth non-deterministic. *Mitigation:* freeze the suite; run each clause test 3× at build time and drop any clause whose result is not stable across the 3 runs; report the drop rate.

**T12 — Irreversibility bugs making families unplayable (F3/F4).** A revoked source or a pruned subtree can make *every* continuation fail, so all items become "halt" and the battery loses variance. *Mitigation:* label-balance gate G6 (no label > 70% of any item class); if violated, re-tune the difficulty knob, not the label distribution.

---

## 7. Generation pipeline and acceptance gates

**Pipeline.**
- **S0 Authoring.** Build the machine-readable oracles: F1 clause→predicate/test map; F2 60 documents + annotation records + dependency graph; F3 reference transform + 34 assertions + simulator; F4 12,000 records + planted labels + rule engine. Author `F4-CTRL` (uniform triage, no budget) as the horizon placebo.
- **S1 Instance generation.** 60 slots × 5 levels. Execute each instance's prefix **once** with the generator, with the wrong candidate installed at the injectable junction; freeze the log. Record acceptance/rejection of runs per §5.2.
- **S2 Item extraction.** At each level's junction, emit the item state from the frozen log (local block + carrier tail [+ summary]); compute the label from the oracle; compute the poison-survival flag; compute the filler-neutrality attestation.
- **S3 Gates.** Run G1–G8 below. Reject, never trim.
- **S4 Freeze.** Hash every state; store the key separately (the key is never in the same artifact as the state); record the option-position Latin square.
- **S5 Collection.** Every judge answers every item, byte-identical states, forced choice, single shot. `[→ARMS]` for efforts and `[→METRICS]` for instrumentation; unparseable answers are incorrect and their rate is reported.
- **S6 Analysis.** Pre-registered mixed model on `judge × log2(H)` with random intercepts for slot and lineage; cluster bootstrap; the `survives`-only primary drift analysis; the carrier-lift stratum; the Jev-only stratum; the multilingual stratum.

**Gates.**

| Gate | Requirement | On failure |
|---|---|---|
| **G1** | every item: `laya_plan(strict=true)` clean; state ≤512 tok (target ≤497); ≤4 options; ≤48 tok/option; option block ≤192 tok; score ≤5 levels at ≤36 tok | reject item, report drop rate |
| **G2** | every rubric level computed by a mechanical predicate; 100% coverage | drop the rubric, redesign the class |
| **G3** | TF-IDF/logistic baseline ≤0.80 accuracy for every item class, and cannot separate filler from real ledger lines | regenerate the class, not the model |
| **G4** | 100% of trap items pass two-annotator unanimous review (target ≥90% acceptance) | discard the trap |
| **G5** | correct-option distribution within ±5% of uniform per cell | rebalance the Latin square |
| **G6** | no label exceeds 70% of any item class | re-tune the difficulty knob |
| **G7** | poison-survival flag computed for 100% of items at `d > 0`; per-level rates reported | block the drift analysis |
| **G8** | state hashes frozen; no post-freeze edit (any edit reopens G1–G3) | re-gate the item |

---

## 8. One-paragraph summary for the paper's method section

Every long-horizon run is executed by the LLM alone, because the other two judges are discriminative and cannot act; the comparison between all three therefore lives at *junctions*, on typed questions over bounded states. Four families provide those junctions — a service maintained against a shifting spec, a claim table over a planted corpus, a migration whose schema changes mid-run, and a budget-constrained adaptive audit — each with an executable or computed oracle, an injectable junction, a difficulty knob, and a decision unit that fits a 512-token window by construction. Horizon is manipulated as distance from a planted upstream error inside a single frozen run, with carrier width and token count held constant, so that drift can be plotted rather than asserted; and every item is pre-classified for whether the poison's trace actually survives into the shipped window, which is what makes the resulting curve interpretable.

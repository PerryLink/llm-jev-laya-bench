# D1 — Should the Jev arm go live, or be dropped?

**Decision unit:** D1 · **Date:** 2026-09-22 · **Status:** recommendation to the lead
**Question put:** enable `provider: live` for TypeSafe Jev, or drop Jev from the study?
**Evidence base:** `../recon/R4-blockers-and-activation.md`, `../recon/R6-jev-interface-verdicts.md`, `../recon/R12-jev-probe.md`, `../recon/R9-final-specification.md`, plus `../recon/R3-corrected-economics.md`, `../recon/R7-v5-adjudication.md`, `../recon/R8-clamp-calibration-and-final-adjudication.md`, `../recon/R2-verified-externals.md`, and the five adversarial audits V1–V5.
All paths in this file are relative to `D:\Projects\llm-jev-laya-bench\`.

**State of the project as of this decision:** `probes/` and `protocol/` are empty; the frozen corpus does not exist (V5 §S1, item 5); the credential does not exist (R6 §1, R12 §3.1). Nothing has been built that a Jev decision would invalidate, and nothing has been built that a Jev decision would require.

---

## Q1 — What is actually lost if Jev is dropped?

### 1.1 The two theses do not need Jev

**Thesis (i), "cost is not the binding constraint" — not merely independent of Jev, but safer without it.**

- The thesis is *derived from a price list*, not from the battery. V2:282 states it plainly: the surviving headline "rests on two statements that are not hypotheses about this experiment at all: money is not the binding constraint (derived from a price list, R3 §4) and Laya's window silently truncates at 512 tokens (measured in R13). **No outcome of the battery can falsify either.**"
- R3 §4 gives the number from the LLM side alone: at $0.10/run, 337 judgments at the *pessimistic* 0% cache-hit rate — 2.8× the 120 designed checkpoints. Jev contributes nothing to that arithmetic.
- Jev's own price makes the thesis *harder* to defend, not easier. On the TypeSafe route `costUsd` is not reported at all, and R6 §4 records that even the token count is unconfirmed on that route; R9 §3.7 already **deleted** the Jev/LLM crossover claim because its sign flips with the cache-hit assumption. A Jev row would therefore add an unverifiable, or at best registry-inferred, number to exactly the table whose credibility thesis (i) depends on.
- Consequence: the paper's cost chapter loses one row and one figure series. Its conclusion is unchanged.

**Thesis (ii), "the instrument's self-reported fields cannot be trusted" — instrumented entirely by Laya, first-party, local.**

The evidence that carries it is already measured on this machine and needs no remote judge:

| Evidence | Source | What it establishes |
|---|---|---|
| Per-checkpoint clamp vs `truncated` onset: english clamps at 512 with a **111-character unwarned window**; multilingual clamps at 1024 with a **~0-character unwarned window** | R8 §1, R9 §2 | Self-report lags real damage — *and* the multilingual checkpoint is a **built-in negative control** where report and reality coincide. This makes the claim falsifiable from within Laya alone. |
| `confidence` 0.9981 on a wrong answer, 0.9989 on noise; `choice:11+ = 0.1006` sharpening logits ~10× | R13, R3 §3.2 | Confidence is decoupled from correctness, and miscalibrated by design at high cardinality. |
| `laya_plan` returns `"value.fits" must be a boolean`; `truncated`/`warnings` fields do not reliably appear; `fits: true` across the whole silent window | R4 P0-2, V3 FN1 | The instrument's own pre-check is broken and its clean verdict is wrong. |
| The mock calibration battery (**14 items**, of which **10 carry binary ground truth**): Brier **0.359** on those 10, worse than a constant 0.5, with a plausible-looking confidence spread; boundary delta exactly 0.0000 by construction; hard-coded `confidence` 0.5 | R12 §1.5, §1.1, R6 §8 | A judge with **no judgment at all** produces a results table that does not read as broken. |

That last row is the single strongest demonstration the project owns, and R9 §6 already places it in Results B ("mock 的 Brier 0.359"). Going live does **not** destroy it — the data are recorded — but it changes its role from *the paper's central exhibit* to *a methods-section control*, and it invites the review question "you had a hash function, you knew it, and you had a key priced at $0.042/1M — why is this in Results?"

**Both theses survive intact.** Thesis (ii) in fact gets cleaner, because the paper can then say of every number in it: *this was measured, here, at this build.*

### 1.2 What is genuinely unavailable

| # | Loss | Magnitude |
|---|---|---|
| 1 | **Arm A2** — the same frozen state and the same typed question `Q(ck)` sent to a third judge (R15 §1.3). The direct three-way byte-identical comparison. | Real but bounded: the primary contrast `P_detect(τ*)` is snapshot-paired and survives with two judges. |
| 2 | **A2's `check` and `rank` sub-arms** (R15 §1.3). The only instrumented test of a five-way verdict vocabulary (`supported / contradicted / conflicted / insufficient / undecided`) and of per-candidate relevance scoring. | Partly recoverable locally — see Q2. |
| 3 | **A4's Jev escalation branch**, triggered by `insufficient`/`undecided`. | Already weakened: R9 §3.8 deletes abstention as a comparison dimension because the question bank gives A0/A1 no abstain option, and V1 requires an `A4′` LLM self-escalation control anyway. Net effect: the study loses its only *externally supplied* abstention signal, and gains the symmetry V1 demanded. |
| 4 | **First-party Jev latency and first-party Jev cost.** | Replaced by citation, clearly labelled: R2 §153 records third-party published figures (p50 236–276 ms, $0.042/1M, ECE 0.246, Banking77 0.870 vs Laya 0.425, 16% zero-probability-on-true-label rate), and the upstream's own README says *"Jev figures are third-party published, never measured here."* R3's registry-priced row ($0.000063 per 1500-token call) survives with that label. |
| 5 | **Three-species complementarity** (`Δ_catch`, κ over three judges) → two-species. | R9 §7.1 rules on this directly: with no credential, delete A2 and the A4-Jev branch, retitle as a two-judge study — "中心主张仍成立，且 §9 的跨物种互补性只需 LLM vs Laya" (the central claims still hold, and cross-species complementarity needs only LLM vs Laya). V5 §331 reaches the same conclusion: "The cheapest route to a real contribution is the cross-species error-diversity experiment." |
| 6 | Generality over typed-decision **implementations** (n=2 → n=1). | This is the only genuinely weaker claim, and the three-judge version would not have licensed it either: R16 §568 forbids "typed judges are better calibrated than LLMs" as a general law at n=1 per family, R16 N1 requires a backend-agnostic replication study, V5 §203 says one implementation cannot carry a class claim, and V1 §224 requires the title be scoped to the artifact regardless. |

**Not lost — these are provider-independent facts already confirmed and they remain publishable as interface-contract findings** (R6 §3, R12 Part 1): the `probability` ≠ P(true) inversion trap; silent coercion of an unknown `type` into `score`; `score` direction fixed by `criteria` writing order; redaction firing on option keys that merely *look* like credentials; the degenerate `rank` envelope that carries no warning, no usage and an empty `model`; `state` truncated-not-refused at 16,000 characters **and inside `state` for `rank`, where every candidate still returns a score describing the fragment**; `questions` refused-not-truncated with retries useless; `check` performing no input validation at all; and `costUsd: 0` meaning *not reported*, not *free*.

### 1.3 Bottom line for Q1

The paper loses **one arm, two sub-arms, one escalation branch, one figure series, and one row of a cost table**. It keeps both central theses, its best single exhibit, its primary endpoint, its primary contrast, and its best contribution. **The study becomes narrower, not weaker.**

---

## Q2 — What does Jev uniquely provide?

### 2.1 `check` is not a primitive; it is an orchestration layer

R6 §3.3 recovered its full semantics from the plugin source: the vocabulary is five values (`unknown` is **not** among them, despite the tool description listing it); the precedence is `conflicted > insufficient > supported/contradicted > undecided`; and it applies exactly two rewrites (`supported` with no sufficiency answer → `insufficient`; `insufficient` with sufficiency ≥ threshold → `undecided`). The thresholds are bracketed: support ∈ (0.5714, 0.7021], contradiction ∈ (0.6245, 0.8103], sufficiency ∈ (0.4108, 0.5044].

That is **three noul questions plus a decision rule**. A local equivalent is therefore constructible: ask Laya the same three sub-questions on the same state and apply the recovered rule, sweeping the thresholds across their bracketed intervals as a sensitivity analysis. This is not a degraded substitute — it is a *better-controlled* experiment, because it separates "does the three-probability decomposition carry the verdict?" from "does the vendor's threshold choice matter?", which the Jev arm cannot separate. R6 §3.3 also notes the mapping is plugin logic, not model output, so it would apply identically live; the only thing live would add is the model probabilities feeding it.

### 2.2 `rank` has a local counterpart

V3 §70 records that `laya_rank` exists: "`laya_rank` takes one query plus candidates." Jev's `rank` is therefore mirrored by a local entry point. **Caveat, stated as a limitation of this recommendation:** no probe has exercised `laya_rank` — R13 used `laya_ask`, `laya_noul`, `laya_plan` and the MCP variants, and its DO-NOT-CLAIM list covers `typed-decisions` behaviour generally. Treat the local rank arm as **conditional on a 30-minute verification probe**, not as an established capability.

### 2.3 The 16,000-character state cap does not matter for this design

At the project's own measured constant (6.33 chars/token for English prose, R13 §679), **16,000 characters ≈ 2,530 tokens** — about **5× the english checkpoint's 512-token clamp** and **2.5× the multilingual/typed-decisions 1024-token clamp**. It is a larger window, not a qualitatively different one.

Three facts make it non-load-bearing:

1. **M1 is gated to ≤400 tokens by construction** (R9 §2, R5 §4.2 #5), and R14's corpus invariant authors every decisive span at ≤130 tokens and every supporting span at ≤60 tokens *precisely so that the battery fits a 512-token judge*. Jev would never truncate in M1 because M1 was designed for a judge five times smaller.
2. **M2 grows only to ≈1,500 tokens** (R9 §2) and **by rule does not cross-compare judges** — it compares the instrument's behaviour against its own self-report. Jev cannot enter that comparison without violating the plane's design.
3. **The entire designed state range sits inside Jev's cap.** So the window advantage would be real but *never exercised*: no measured quantity in the paper would change if Jev's cap were 3,000 characters instead of 16,000.

Worse, Jev has **the same class of silent-truncation defect as Laya**, just higher up: R6 §3.1 and R12 §1.2 record that an over-long candidate list is truncated *inside* `state` while **every candidate still returns a score describing the fragment**, so "the ranking looks complete while having judged part of the input." Jev is not the truncation-free reference judge the design might hope for; it is the same failure mode with a 5× window and a per-token bill. That *strengthens* thesis (ii) as a general observation and removes the last reason to treat Jev as the trustworthy anchor.

**The one place the window could become load-bearing is worth naming**, because it is cheap, on-thesis, and currently unclaimed: extend the M2 growth probe *to Jev*, and measure where Jev's own judgment degrades relative to where its own `truncated` flag fires. That would give thesis (ii) a **second instrument and a remote one**, turning "self-report cannot be trusted" from a local defect into a cross-instrument finding. But note the trade honestly: **that is precisely the experiment that maximises egress volume** — a growing state, up to the full 16,000 characters, sent on every call. It is the one Jev experiment worth paying egress for, and it should be a deliberate, separately justified decision rather than a by-product of enabling the provider.

### 2.4 Is a two-judge study genuinely weaker?

**Narrower on everything the theses touch; genuinely weaker on exactly one axis — generality over typed-decision implementations — and that axis is already closed by the project's own rules** (R16 §568, R16 N1, V5 §203, V1 §224). Consequently:

- If the team wants a second typed-decision *implementation*, the cheapest path is **not** a remote credential. R2 §240 and R2 §599 record a local, non-autoregressive, sub-15 ms, self-described "drop-in alternative to TypeSafe Jev" (`wfzyx/von`), and R7 §84 / V5 §231 already name it as the replication target for the class-level claim. It costs zero egress. **Caveat:** only its repository page title was retrieved; the README fetch failed (R2 §599). It is a lead, not a fact.
- Combining `von` (if verified) with a third Laya checkpoint gives a *narrow* class claim with no egress at all — which is strictly more than Jev could give without the credential anyway.

---

## Q3 — The egress cost

### 3.1 The premise needs one correction before the ethics can be assessed

The brief says "the task corpus itself would be uploaded on every call." Three corrections:

1. **The corpus does not exist yet.** V5 §S1 lists the frozen corpus as **ABSENT** (`protocol/` and `probes/` are empty, verified). The fleet has been deciding what to upload before authoring what would be uploaded. This is the most important fact in Q3, because it means the egress question is still **closable by construction**.
2. **The corpus is designed to be synthetic.** R14 F2 authors 60 documents across six *fictional* agencies (National Grid Siting Board, Battery Safety Council, Northmoor District Council, Interconnect Standards Office, Fire Risk Inspectorate, Ratepayers' Federation), with an explicit invalidation rule: real entity names, or any corpus text found by n-gram/embedding search in a public corpus, invalidates the family (R14 §F2). F1/F3/F4 are similarly authored, with executable or computed oracles.
3. **The state has already left the machine.** The design's generator and LLM judge are `DeepSeek-V4.1-Flash` reached through the one registered credential (`DEEPSEEK_API_KEY`, R6 §1); the entire cost model and the `usage`/cache-hit accounting depend on it (R9 §3.6, R15 §6). The correct framing is therefore **"one processor versus two"**, not "no egress versus egress". The marginal risk of TypeSafe is *incremental*, and it must be assessed as such — not dismissed, and not inflated.
4. **The state is partly model-authored free text.** R14 R0 permits judge-visible strings that are "templated, or frozen once by a non-judged configuration"; checkpoint summaries and ledger lines are generator-produced. R4 §255 flags that corpus provenance is unspecified and could put the judge's own family into the state. A harness cannot fully audit model-authored text for secrets, and R6 §3.4 / R12 §3.3 record that redaction is **best-effort** — "a secret that sits under an unrecognised key name *and* does not match a known shape will pass through." So "the corpus is synthetic" does **not by itself** guarantee the absence of sensitive strings.

### 3.2 The practical assessment

For an academic study, the risk decomposes into three separable items, only one of which is a real problem:

| Item | Severity | Why |
|---|---|---|
| **Third-party research artefacts** — the question bank, serializer output, prompt design, and pre-publication results visible in the state | **Real and the main cost** | This is the team's intellectual contribution leaking to a commercial third party before publication, with no retention control. It is not a privacy harm but it is a genuine priority and confidentiality issue, and it is the item a disclosure must be most explicit about. |
| **Personal data / human subjects** | **Low if the corpus is authored as designed** | Fictional entities, no human subjects, no real incidents. Likely IRB-exempt. Must still be asserted, not assumed — because item 3 above means the harness cannot prove the absence of a stray real fragment. |
| **Confidential or proprietary third-party content** | **Currently zero; becomes non-zero the moment any real corpus enters** | This is what the deferral buys: the chance to make the answer "none" *and prove it*, via the contamination search and a pre-egress scanner, before any call is made. |

### 3.3 What a disclosure would have to say

A defensible disclosure paragraph must contain all eight of these, and the study artifact must make them checkable:

1. **Destination(s), named:** `https://api.typesafe.ai` for `provider: live`, or OpenRouter's endpoint for `provider: openrouter`, plus `DeepSeek` for generation and LLM judging. The plugin prints the resolved endpoint at startup (R6 §6.2), which is what makes this assertable rather than inferred.
2. **What is sent, per tool:** the model-supplied arguments after best-effort redaction — `state` ≤16,000 characters, `questions` ≤4,000 characters — for `jev_ask` / `jev_check` / `jev_rank` only (R6 §6.3).
3. **What is not sent:** the two gates (`safety`, `context`) remain **disabled**, so tool calls and tool results do **not** leave the machine. State this explicitly and record the actual gate values per run, because "we did not enable the larger egress" is the strongest single sentence available here.
4. **Volume and granularity:** number of calls, states per call, and the fact that the *same* state is resent on each logical call (up to three wire attempts per call, R6 §3.1).
5. **That redaction is best-effort and not a guarantee**, quoting the vendor's own wording, plus the study's own pre-egress assertion (no credential-shaped option keys; R6 §10 rule 12).
6. **That the destination's retention, logging and training-use terms were not independently audited by the authors**, and that the choice was made for the reasons in §3.4.
7. **Corpus provenance:** authored, synthetic, fictional entities, English-only, contamination-searched, with the SHA256 of the frozen corpus and the search result published; and that no human-subjects or client data is included.
8. **Mitigation and reversibility:** the credential is revocable and `provider` is read per call, so a revert is one line (R6 §6.2); the discriminators are run head and tail of every run to prove the provider did not change mid-experiment (R6 §7); and the full `egress` block is stored with every response so a reader can recompute exactly what left the machine (R6 §10 rule 5).

### 3.4 TypeSafe vs OpenRouter for a paper

| Criterion | TypeSafe (`live`) | OpenRouter |
|---|---|---|
| Destinations to disclose | **One**, named, printed at startup | **Two** (OpenRouter *and* whatever it hosts onward) |
| `usage.costUsd` | Not reported — `0` means "not reported", not "free" (R6 §4) | **Populated** — a real measured cost |
| Token counts | **Unconfirmed** (R6 §4) — so the registry fallback may not be computable either | Implied by the cost report |
| Model id | Accepts `jev-latest`, whose resolution can drift; the response's `model` field is **not** a mock marker (it read `jev-latest` under the mock too, R12 §1.1) | Constrained to a bare `jev-*` or a versioned `typesafe/jev-1.13` — **forces the pinning the reproducibility plan requires** |
| Key required | `TYPESAFE_API_KEY` | `OPENROUTER_API_KEY` (different vendor, different sign-up) |

**Verdict: TypeSafe is better for this paper, and the reason is that the cost number is decorative.** Thesis (i) is derived from the LLM side's verified prices (V2:282, R3 §4) and does not need Jev's cost; the project's own reproducibility exemplar recomputes cost **from a registry** rather than reading `costUsd` (V5 §5), which is exactly R4 §5's prescribed fallback; and the Jev arm's total marginal spend is under $3 in any case (Q4). Paying a **second** third party, and adding a second destination to the disclosure, to obtain a number the paper does not need is a bad trade. **Switch to OpenRouter only if** the first live smoke shows `usage.inputTokens` absent on the TypeSafe route **and** the team decides a first-party Jev cost is required — and if so, both destinations go in the disclosure.

---

## Q4 — Irreversibility and option value

### 4.1 What is actually irreversible

**The configuration is not irreversible; the data are.** R6 §6.2: `provider` is read per call, so reverting is deleting one line, and an unknown config value fails loudly at load rather than silently changing the privacy posture. The only act that cannot be taken back is sending state text.

This asymmetry is decisive, and it means the decision decomposes:

| Action | Reversible? | Novel egress | Information gained |
|---|---|---|---|
| Register the credential in DSH's credential service | **Yes** (delete it) | **None** — no call is made | Removes the blocking unknown |
| Run discriminators A/B on the two fixture states **already published verbatim in R12 Appendix A** | **Yes** (2–4 calls) | **None** — these exact strings are in the repo | Whether live Jev works at all, and whether live behaviour differs from the mock |
| Upload the frozen corpus on every judgment call | **No** | The corpus, ≤16,000 characters per call, thousands of times | The paper's first-party Jev numbers |

The first two rows are cheap, safe, and answer the question the lead actually lacks. The third is the real decision — and it is **not the same decision**, which is why "enable live or drop Jev" is a false binary as posed.

### 4.2 Cost of re-running the Jev arms later

The design is **snapshot-replay based**: judges are replayed offline on frozen snapshots (R9 §3.2, V1 §134, R3 §7 calls this "全文最好的设计决策"). Therefore:

- **Generation, item authoring, annotation, fault injection and the gold oracle are judge-independent and are not repeated.** R9 §7.2 identifies annotation as the project's largest non-API cost (300 vs 1,910 items of human labelling) — and adding Jev does not add a single annotated item, because Jev judges the *same junctions*.
- **The Jev calls themselves are near-free.** Assume the core replay: ≈600 paired main-battery items (R9 §3.1's `L` vs `L+C` variants) plus the ≥1,000-item calibration corpus = ≈1,600 calls, plus A4 escalation events and the head/tail discriminators, call it 2,000–5,000. At the registry price ($0.042/1M input, $0 output) and ≈500 tokens per M1 state: **≈$0.04–$0.11**. Even at 10× for long states and three wire attempts each: **≈$1–3.** The entire arm costs less than one hour of engineer time.
- **What deferral does cost:** (a) one integration pass for the Jev serializer and the 14 mandatory protocol rules (R6 §10) — but that pass is *already required* by the interface findings the paper keeps, so it is largely not a new cost; (b) the A4-Jev threshold τ\* **cannot be fitted until live** (V5 §135: "Do not build a Jev threshold at all until live"), so if Jev is in, P4 must precede P5 — which R7 §159 and V5 §135 already require on independent grounds; (c) schedule.

### 4.3 Option value of deferring the corpus decision

Deferring the corpus upload is worth more than it costs, for one reason: **it converts an open ethical question into a null one at zero marginal cost, because the corpus has to be authored anyway.** The deferral window is exactly the window in which the team can:

- author the corpus as designed (synthetic, fictional entities, English-only) and thus make Q3's egress answer "no sensitive content, provably";
- run the contamination search R14 F2 already requires and pair it with a pre-egress scanner (credential-shaped keys, non-English strings, entity checks);
- freeze and hash the corpus, the serializer and the question bank (P1), so that whatever Jev sees is a *published* artefact rather than an in-progress one — which also removes the "pre-publication leakage of the team's own contribution" item from §3.2 by making the state text public at submission time anyway;
- certify corpus provenance (V4: currently unspecified) so the state cannot contain the judge's own family.

The counter-argument — "deferring costs a second collection episode" — does not hold, because the replay design makes the second episode free (§4.2). The only genuine schedule risk is that the Jev arm must be added **before P5** if it is to share the calibration corpus and the τ\* fit rather than needing its own.

**Net: deferring the corpus decision has high option value and near-zero re-run cost, provided the pre-registration names the Jev arm and its analysis plan now, and provided the snapshot corpus and question bank are frozen before it lands.**

### 4.4 Is the "public dataset instead of a proprietary corpus" variant worth taking?

**No — and it is a trap.** The task battery's value rests on four properties that a public dataset does not have: (i) the span invariant (decisive ≤130 tokens, supporting ≤60) that makes every item Laya-compatible by construction; (ii) executable or computed oracles per family; (iii) an injectable junction with a known carrier width; (iv) the contamination invalidation rule, which a *public* corpus fails by definition. Swapping to a public dataset would:

- break the Laya-fits-by-construction property and with it the M1/M2 plane split (R9 §2);
- invalidate the contamination defence (R14 F2 invalidation i);
- reopen the "the judge's own family is in the state" self-preference risk (V4 §255);
- discard the ~300–1,910 items of authored annotation that R9 §7.2 identifies as the largest hidden cost.

It reduces egress sensitivity by replacing the study's instrument with a weaker one. **The correct mitigation is the opposite and it is already in the design: author the corpus so the question does not arise.** If part of the corpus must be real, hold the real portion out of the Jev path entirely and report the Jev arm as covering the synthetic strata only — a scope statement, not a redesign.

---

## Q5 — If the credential cannot be obtained at all

Write this down now, before it is needed, so that the fallback is a decision rather than a scramble. V5 §313 already specifies most of it; the following is the executable version.

### 5.1 Retitling

The working title is 《长线任务中判别式判定器的真实代价：成本不是约束，静默退化才是》 — "The real cost of discriminative judges on long-horizon tasks: cost is not the constraint, silent degradation is" (R5 §0).

**The fallback retitle is a narrowing, not a rewrite, because the subtitle already names exactly two models** and never mentions Jev:

- **Keep:** the title, including both clause-halves.
- **Replace the subtitle with:** *"A process-level, snapshot-paired comparison of one local non-autoregressive decision model and one frontier generative model on identical items, with a documented third-party typed-decision interface reported as a non-measured reference."*
- **Strike "three judgment layers" / "three judges" / "三方" from the title, the abstract, every figure caption, and the arm table** (V5 §139, §313). This is the only textual claim that becomes false.
- **Apply the two scoping fixes that the audits require regardless** (they are not caused by dropping Jev, and the paper is unpublishable at a main conference without them): scope the claim to *this build, this host, this checkpoint* rather than to "discriminative judges" as a class, because the measured mechanism is the planner constant `_CHARS_PER_TOKEN = 4.0` × `_SAFETY = 1.15` in `planning.py` plus an unexplained runtime clamp — a **software defect**, not a property of the class (V5 §184, V1 §224); and cite the parameter count with its derivation (421,293,830 across 206 F16 tensors, V5 §11) rather than asserting "~421M" bare (R2 §B.2 forbade the bare figure; V5 supplied the measurement that makes it citable).
- **Add the funding sentence the audits require:** state the engineering and human-review terms alongside the marginal API terms, because at study level the corrected budget is dominated by engineering (~70–85%), and a title saying "cost is not the constraint" without that distinction is the paper's most exposed sentence (V1 §§2.3, d; R9 §3.6.5).

### 5.2 Arm deletions

**Delete:**

- **A2** — Jev, same typed question `Q(ck)` (R15 §1.3). Deleted entirely, not degraded.
- **The A4-Jev escalation branch.** A4's trigger becomes Laya's low probability only.
- **A2's `check` sub-arm and `rank` sub-arm** as *Jev* arms.
- Every figure, table row and abstract sentence carrying a Jev series, including the equal-budget frontier, which R2 §C.5 already prohibits drawing while Jev is unmeasured.
- **Abstention as a comparison dimension** — R9 §3.8 recommends this deletion independently, and dropping Jev makes it forced rather than chosen.
- **The R3 §5 crossover assertion** — already deleted by R9 §3.7 because its sign flips with the cache-hit assumption.

**Add back, so that the deletions narrow rather than hollow the design:**

- **`check`-equivalent arm (Laya).** Three noul sub-questions (`supports` / `contradicts` / `sufficient`) on the same state, reconciled with the recovered precedence `conflicted > insufficient > supported/contradicted > undecided` (R6 §3.3), with the three thresholds swept across their bracketed intervals (support ∈ (0.5714, 0.7021], contradiction ∈ (0.6245, 0.8103], sufficiency ∈ (0.4108, 0.5044]) as a pre-registered sensitivity analysis. Cost: zero egress, zero new annotation; the sub-questions are new question-bank entries, so this must land before the P1 hash freeze.
- **`laya_rank` relevance arm — conditional.** Verify the entry point exists and behaves (V3 §70 names it; no probe has run it). If it works, the rank primitive is covered locally; if not, delete the rank analysis from the paper rather than inferring it.
- **`A3b` (Laya, ≤20 questions per call) — keep, mandatory.** V1 §182 requires it; dropping A2 removes the need for `A2b` but **not** for `A3b`. The batching asymmetry is currently typed-side-disadvantaged and must be fixed on the side that remains.
- **`A4′` (LLM self-escalation) — keep, mandatory.** V1 §186 requires it; with A4-Jev deleted, `A4′` becomes the *only* escalation contrast in the paper, which raises rather than lowers its priority.
- **`S0` (true-silence arm)** — R9 §3.9 requires it restored; unaffected by this decision.
- **Second typed-decision implementation — investigate `von`** (R2 §240, §599; R7 §84; V5 §231) as the egress-free route to a narrow class claim. Verification first: only the repository page title was retrieved and the README fetch failed.

**Keep and cite, clearly labelled as not measured here:**

- **Jev as a documented interface contract** — R6 §3's twelve confirmed facts, all of which survive the mock and are genuine contributions.
- **Jev economics as third-party figures** — R2 §153 (p50 236–276 ms; $0.042/1M; ECE 0.246; Banking77 0.870 vs Laya 0.425; 16% zero-probability-on-true-label rate) plus R3's registry-priced row, under the upstream's own label: *"Jev figures are third-party published, never measured here."*
- **The mock as a synthetic-provider control** — Brier 0.359, hard-coded `confidence` 0.5, boundary delta exactly 0.0000 by construction, one response with no `warning` field, `model` reported as `jev-latest` and therefore useless as a mock marker. **Publish no Jev number as a Jev measurement** (R4's own rule: 不得用模拟数据顶替), state the `provider: "mock"` tag with every such number, and state the FNV-1a construction so a reader can reproduce the hash. File it under Results B as a methodological hazard, which is where R9 §6 already puts it.

### 5.3 The limitations paragraph (verbatim, ready to paste)

> **Scope: two measured judgment layers, one interface contract.** This study measures two judgment layers on identical frozen states: a frontier generative model judging in free prose and through constrained structured questions, and a local non-autoregressive decision model answering the same typed questions. A third layer — TypeSafe Jev, a remote typed-decision service — is described here as a **documented interface contract and a third-party economic reference, and is not measured.** No credential for that service was available to this study, and enabling it would have transmitted the task corpus to a third-party processor on every judgment call; that egress decision was not taken for a study whose corpus, while authored and synthetic, had not been certified at the time. Readers should therefore treat every statement about Jev in this paper as falling into one of exactly three evidence classes, each labelled at its point of use: (i) **interface facts**, confirmed against the shipped plugin and reproducible without a credential — its budget envelope (16,000-character `state`, truncate-not-refuse; 4,000-character `questions`, refuse-not-truncate), its pre-provider validation behaviour, its response-schema semantics (including that `probability` is the probability of the *answered* option, not of `true`, and that `score` is Σ(index × probability) over the `criteria` order as written), and its failure modes (silent coercion of an unrecognised question `type` into `score`; no input validation in `check`; key-name redaction firing inside the instrument); (ii) **synthetic-provider evidence**, collected under the plugin's offline mock provider and reported only as a control: that provider derives every answer from a hash of the question id and state, and therefore produced a full calibration battery scoring **Brier 0.359 — worse than a constant 0.5 — with a plausible confidence spread that would not read as broken in a results table**, alongside a hard-coded `confidence` of 0.5, a boundary-sensitivity delta of exactly 0.0000 by construction, and one response carrying no warning field at all. These are properties of the fixture, not of the service, and they are reported because they are the sharpest available demonstration of this paper's second thesis; and (iii) **third-party published figures** for cost, latency and benchmark accuracy, cited as such and never presented as our measurement. Three consequences follow, and we state them plainly. First, the cross-judge comparison covers two species, not three; the typed-decision class is represented by a single implementation, and we claim nothing about that class in general. Second, the economic comparison contains no first-party measurement of the remote service's cost or latency, and its per-call price is a registry entry on a route that does not report cost — so the cost thesis in this paper is established from the generative side's verified pricing, and the remote judge's row is illustrative rather than measured. Third, the substantive gap is remediable and cheap: the design replays every judge offline on frozen, hashed snapshots, so adding the remote layer later requires no regeneration and no re-annotation, only its own calls and the two activation discriminators (a decisive state must score at least 0.9, and a declared boundary must move the answer). We publish the frozen corpus, serializer, question bank and their hashes precisely so that a reader with a credential can close this gap on our artifacts.

### 5.4 What the fallback costs the paper

One arm, one sub-arm pair, one escalation branch, one cost row, one figure series, and the phrase "three judgment layers." It keeps both central theses, the primary endpoint, the primary contrast, the interface-contract findings, the synthetic-provider control, and the project's best contribution. **It does not become a worse paper; it becomes a narrower one with a better-defended scope** — which is what V1 §224, V5 §184 and R16 §568 require of it in any case.

---

## RECOMMENDATION

### VERDICT: **REHEARSE ON MOCK NOW AND DEFER**

Not "enable live" and not "drop Jev", because **the decision as posed is a false binary**: activating the provider and uploading the corpus are two different decisions with different reversibility, and the instrument itself is built that way (`provider: live` is one line and reverts in one line; the two `gates` are separately opt-in; R6 §6.2–6.3). The study should take the reversible half now and gate the irreversible half on the corpus's certification.

**Deferral deadline — three checkpoints, in order:**

1. **P4a — credential requested today; discriminators A and B run on the two fixture states already published verbatim in `R12` Appendix A, within 5 working days (target 2026-09-29).** Two to four calls, ≈$0.0003, **zero novel egress** — those exact strings are already in the repository. This answers the only question the lead actually lacks: does live Jev work, and does it behave differently from the mock?
2. **P4b — the go/no-go on uploading the frozen corpus: before the first call that generates the P5 calibration corpus (target 2026-10-20), and it may not slip past the snapshot freeze that precedes P8.** Required at P4b: credential present in the DSH credential service; P4a passed; corpus certified (authored, synthetic, fictional entities, English-only, no credential-shaped option keys, contamination search run, provenance recorded per V4 §255); and the pre-registration already containing the Jev arm's analysis plan and the discriminators' exact form.
3. **Trigger condition for going live:** credential registered **and** discriminator A returns `noul ≥ 0.9` on a decisive state (the mock returned 0.0317) **and** discriminator B returns a non-zero boundary delta (the mock returns exactly 0.0000) **and** `provider != "mock"`, `latencyMs > 0`, `inputTokens > 0`, with the startup line reading `provider=live egress=ON`. Any one failing → **execute the Q5 package, do not iterate on it.**
4. **If no credential exists in the DSH credential service by 2026-10-13** — one week of slack before the P4b gate — **execute the Q5 fallback without further debate and stop spending on the Jev arm.**

### Reasoning (≤300 words)

Neither thesis needs Jev, and thesis (i) is safer without it. "Cost is not the binding constraint" is derived from a price list, not the battery (V2:282: no outcome of the experiment can falsify it); the LLM side's verified prices already buy 337–913 judgments per $0.10 against 120 checkpoints; and Jev's own price sits on a route that reports neither cost nor confirmed token counts, so a Jev row would add an unverifiable number to the table the thesis rests on. Thesis (ii) is carried entirely by local, first-party measurements — Laya's per-checkpoint clamp with its 111-character unwarned window and multilingual's zero-length one as a built-in negative control, confidence decoupling, high-cardinality saturation, the broken pre-check — and its single best exhibit, a judgment-free judge producing a credible results table, is the mock itself.

What Jev uniquely provides is not a primitive: `laya_rank` mirrors `rank`, and `check` is three nouls plus a precedence rule already recovered. Its 16,000-character cap is ≈2,530 tokens at the project's own constant — about 5× english, 2.5× multilingual — and the entire designed state range (300–1,500 tokens) sits inside it, so the window never binds. Dropping Jev makes the study narrower, not weaker; the only genuinely weaker claim, generality over typed-decision implementations, is already forbidden at n=1 per family.

So the real question is when the irreversible half happens. Activation is reversible in one line, the smoke test costs two calls on already-published strings, and egress is not. Meanwhile the corpus does not exist and its provenance is unaudited. Deferring the corpus decision is nearly free — the design replays judges on frozen snapshots, so a Jev arm added later costs under $3 in calls, with no regeneration and no re-annotation — and it buys the chance to author the corpus so that the egress question disappears by construction.

### Concrete next actions, in order

1. **Request the TypeSafe credential today** and register it through **DSH's credential service** under the ref `TYPESAFE_API_KEY` — **not** a shell export, which DSH strips silently and which would leave the experiment on the mock with no error (R6 §6.1, R12 §3.5).
2. **Add only `provider: live` to the profile patch** (`C:\Users\zzhdz\.dsh\profiles\web\cordis.patch.yml`), leaving **both gates disabled**. Confirm the startup line `[jevcore] provider=live endpoint=https://api.typesafe.ai egress=ON`. This bounds the egress to explicitly invoked judgments.
3. **Run discriminators A and B on the R12 Appendix A fixture states**; assert `provider != "mock"`, `latencyMs > 0`, `inputTokens > 0`, absence of the `SYNTHETIC` warning, and `confidence != 0.5` on choice/score. **Record whether `usage.inputTokens` is populated on the TypeSafe route** — that single field decides the route question in Q3.4.
4. **Pre-register now, before any live corpus call:** the discriminators' exact form, thresholds and their *mechanical* justification (0.0317 and 0.0000 are known signatures of the hash construction, so the thresholds are derived from the mock's mechanism, not tuned to results — this is the answer to R6 §11's post-hoc-selection worry); the Jev arm's analysis plan; and a fail-closed rule that any Jev row with a null provenance tag is dropped, not imputed (V5 G12).
5. **Proceed with P1–P3 on the mock, unchanged.** Rehearsal is free and nothing about it depends on this decision.
6. **While P3.5 runs, certify the corpus for egress:** author synthetic/fictional/English-only per R14 F2, run the contamination search, add a pre-egress scanner (credential-shaped keys, non-English strings, entity checks), and freeze and hash corpus, serializer and question bank.
7. **Build the Jev serializer path and the 14 mandatory protocol rules now** (R6 §10) — this work is required by the interface findings the paper keeps whether or not Jev goes live, so it is not wasted either way.
8. **Split P4 explicitly** into P4a (fixtures, immediately) and P4b (corpus, before P5), and move P5 after P4 — which R7 §159 and V5 §135 already require, since a τ\* fitted on mock output is a threshold encoding nothing.
9. **Verify `laya_rank` and investigate `von`** (30–60 minutes each, zero egress). If `laya_rank` works, the rank primitive is covered locally. If `von` is a genuine local drop-in, the paper can support a narrow typed-decision class claim without any credential — which would make the Jev question largely moot on the merits.
10. **Write the Q5 fallback package into the pre-registration document now**, so the fallback is a pre-committed branch rather than a rescue.

### IF THIS RECOMMENDATION IS WRONG

**First symptom: discriminator A fails on a call that is provably live.** That is, the response reports `provider` other than `mock`, a non-zero `latencyMs`, `inputTokens > 0`, and a **non-zero** boundary delta in discriminator B — so the credential took and the provider is real — **yet `noul` on a state that asserts the claim three times comes back below 0.9** (the mock's signature value was 0.0317). This is the one outcome that would show both halves of the recommendation to be mispriced at once: it would confirm that deferring was right, because a team that had built and annotated the corpus before probing would have discovered an unusable judge with the annotation already spent; and it would show that the study must **drop** Jev rather than enable it, because the design's decisive-state assumption (a judge shown a decisive state returns a decisive probability) would be false about the live service, and no amount of corpus certification would repair it. The correct response is to execute the Q5 package immediately and record the probe as a first-party finding about Jev, which would be a *better* result for the paper than the arm it replaces.

Two secondary symptoms, each pointing a different way:

- **If no credential can be obtained at all** — the request stalls, requires a paid or legal sign-up, or the deadline of 2026-10-13 passes with no `TYPESAFE_API_KEY` in the credential service — then the recommendation's *prioritisation* was wrong: the Jev work should have been dropped at the outset rather than deferred, and every hour spent on its serializer should be written off. Execute Q5 and do not extend the deadline.
- **If P4a passes cleanly and live Jev disagrees sharply with both the mock and Laya on the complementary-error items** — for instance if Jev catches items that Laya misses and the LLM misses, in the direction R2 §153's third-party figures suggest (Jev 0.870 vs Laya 0.425 at >20 options) — then the deferral cost a collection episode that would have been worth having, and the answer is to accelerate P4b rather than to revisit the structure of the decision. Expected cost of being wrong in this direction: one replay pass, under $3 in calls, and 2–5 days of schedule.

**The asymmetry is the point.** Being wrong toward "should have dropped" costs a few hours and a few dollars. Being wrong toward "should have enabled" costs an irreversible transfer of the corpus to an unaudited processor. The recommendation is deliberately priced to fail in the cheap direction.

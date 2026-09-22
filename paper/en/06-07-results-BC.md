# §3 Results B — the judge's self-reported fields are not trustworthy

*(English translation of `paper/06-results-B-draft.md` (§3 Results B) and `paper/07-results-C-draft.md`
(§6 Results C), carried in one file: §3 first, then §6. Faithful, not abridged: every hedge, every ⚠️
marker, every blockquote, every n and every decimal place is carried across. Terminology follows
`paper/TRANSLATION-GLOSSARY.md`; field names, verdict vocabulary, artifact IDs, paths, statistics and
model IDs are left untranslated. Cross-references `§N.M` and the heading numbers are reproduced exactly
as the Chinese drafts write them, so that `paper/_assemble.py` remaps them identically in both builds
(the two drafts were authored as §3 and §6, and sit at §6 and §7 in the assembled manuscript). The
drafts' own audit annotations and their round numbers are retained. Neither source contains citation
keys `[@key]`.)*

> This section is the one with the **strongest evidence** in the whole paper: seven independent phenomena, of which **six come from real calls** (the other comes from a deliberately designed synthetic backend, as a methodological warning), and it **does not depend on any generator battery**.

---

## 3.0 How this section is organised

The seven phenomena are not seven isolated defects, but **one and the same failure mode showing up in seven places**:

> **This judge fails on the occasions where it "must notice that something is absent, or notice that the input does not match itself"; and it is near-perfect on the occasions where "the answer is explicitly stated".**
> **In both cases, the confidence it self-reports is not low.**

So this section is organised not by "component" but by **failure location**: the input layer (3.1), the field layer (3.2–3.4), the semantic layer (3.5–3.7). Each item gives its **measured numbers**, **why it is dangerous**, and **the mandatory protocol clause it produces**.

---

## 3.1 Input layer: a judge with no judgment capability can produce a completely credible results table

**Phenomenon (R12, n=14-item calibration battery)**: Jev's mock provider returns `undecided` for evidence that **verbatim supports the claim**; and returns `conflicted` for an **empty claim + empty evidence**. **(⚠️ Eighth-round correction: the original printed `insufficient`, but the cited source records precisely the opposite — the verbatim fixture at `recon\R12-jev-probe.md:307` returns `undecided`; `insufficient` is recorded only on another fixture. One fixture records each side, so the generalised wording is not supported by the cited source)**

**But what is really dangerous is not these obvious errors, but its results table**:

| P(true) bin | items (all) | **of which binary-ground-truth items** | observed accuracy |
|---|---|---|---|
| 0.0–0.2 | 3 | **2** | 0.67 |
| 0.2–0.4 | 2 | **2** | 0.00 |
| 0.4–0.6 | 5 | **2** | 0.50 |
| 0.6–0.8 | 2 | **2** | 0.50 |
| 0.8–1.0 | 2 | **1** | 0.00 |
| **Total** | **14** | **9** | — |

**⚠️ The denominators must be spelled out (seventh-round correction, completed in the ninth)**: the **items** column has all 14 items as its denominator, while the **accuracy** column has the **binary-ground-truth subset** as its denominator — so "5 items × 0.50" is arithmetically impossible. The original set the two columns side by side without marking that the denominators differ, and the reader cannot reproduce it. **The middle column is now filled in per bin from the source** (`recon\R12-jev-probe.md:181-185` records 2 / 2 / 2 / 2 / 1), so the total **9** **can be obtained by adding up this table** (**⚠️ ninth-round correction, ERRATA §10.1 item 6**: four rows previously printed an em-dash, leaving the reader unable to reproduce the total they were reading).
**⚠️ And the source contradicts itself in two places; this table can only set the two side by side, not adjudicate them**:
- **the binary-item total**: R12's **table** gives **9** (2+2+2+2+1, addable bin by bin); R12's **prose** says **10** in two places (`:187`, `:388`), and the Brier 0.359 is recorded on "10 items". **9 ≠ 10, and there is no per-item record in the tree that could decide it.** This table therefore prints the **per-bin counts** and the **prose total** separately: at the Brier we keep the prose's **n=10** (next bullet) and mark the one-item discrepancy there.
- **"binary items at threshold 0.5 → 5/10 = chance" cannot be derived from this table**: the (hits, total) combinations compatible with the rate column are **not unique** — **5/10 = 0.50** (what R12's prose records verbatim) and **4/10 = 0.40** are both compatible (0.67 requires that bin's n to be a multiple of 3, 0.50 requires it to be even, and both solutions satisfy this). The original printed "the unique solution is 4/10 = 0.40"; **"unique" is wrong** (**⚠️ ninth-round correction, ERRATA §10.1 item 5**). **This table no longer "corrects" that summary**; it **keeps the source's 5/10 verbatim** and marks it as **not reproducible from this table** — by this paper's own rule, **an unverifiable summary must not be replaced by another unverifiable summary**.
- **Brier 0.359**, while **a constant predictor at 0.5 has Brier 0.25** → on **these 10 items that carry binary ground truth** (14 items in the whole battery), the mock's probabilities are **worse than the constant predictor** (**⚠️ that n=10 comes from the source's prose; the per-bin counts in the table above sum to 9 — a discrepancy of one that the tree cannot adjudicate, see above**);
- **The original wrote "anti-information" — that wording is too strong and has been downgraded**: at n=10 the standard error of a Brier difference of 0.109 is about 0.10 (t ≈ 1.1, **not significant**). The correct statement is "**shows no information on this sample**" **【NOT TRACEABLE ⚠️ ERRATA §10.2】**: this number has **no `results\` artifact**; it exists only in the lab record `probes\P13-jev-remaining-measurements.md` (the t value is a hand computation from 0.109/0.10; no script and no artifact anywhere in the tree). By this paper's own standard (§11.5) **it cannot serve as evidence**; it is kept here as a record only.;
- **But it has a plausible confidence distribution, and in the results table it will not read as "broken".**
- **R12 itself judges this sample to be far from enough**: its own text reads *"This session's 14-item battery is **two orders of magnitude short**"*, and it gives the threshold "about 100 binary items per bin, ≥500 in total (≥1,000 if ECE ±0.05 is to be reported)". **This paper cites that table only to display the shape "the results table looks normal", and draws no calibration conclusion about live Jev from it.**

**Why it is dangerous**: this is the most important methodological argument in the whole paper — **a component with no judgment capability can produce a results table that looks mediocre but is completely credible**. A reviewer will not raise an alarm on account of it.

**Mechanism (localised to the source code)**: the mock's answer = `FNV-1a(questionId + "\0" + JSON.stringify(state))`, and **instructions, criteria, option descriptions and boundary all take no part in the hash**.
→ **Rewrite the question into the opposite meaning and the numbers will not move.**

**Protocol clauses**:
1. **Always use `provider == "mock"` to discriminate live from mock, never the absence of a warning** — R12 measured that when `jev_rank` is passed empty candidates, the response it returns has **no warning, no usage, no egress**, and is "cleaner" than a normal response;
2. **Run the live/mock discriminator once at the start and once at the end of every run**, to prove the provider did not change mid-run.

---

## 3.2 Field layer (i): the `truncated` flag is wrong in both directions

**Method**: `DECOY + filler + CORRECTION`, with the **decisive correction placed at the very end**, scanned character by character, reading two observables (whether `input_tokens_padded` reaches the clamp, and whether `truncated` appears). **It does not depend on any tokenizer estimate.**

| checkpoint | measured clamp | **actual corruption onset** | **`truncated` first fires** | **flag error** |
|---|---|---|---|---|
| english | 512 tok | **3,082 characters** | **3,193 characters** | **+111** (lag = the silent window) |
| multilingual | 1024 tok | **7,966 characters** | **3,193 characters** | **−4,773** (false-reports early) |
| typed-decisions | 1024 tok | **6,967 characters** | **3,193 characters** | **−3,774** (false-reports early) |

**The sharpest one**: **all three checkpoints' flags fire at the same point, 3,193 characters**, while their **real clamps differ by a factor of 2** (512 vs 1024 token).
→ **The flag is driven by a character-based estimate, and that estimate does not scale with the checkpoint's token budget.**

**Independent proof (sidecar-independent)**: keep adding thousands of characters after the clamp takes effect, and **the scores are bit-identical** —

| checkpoint | constant score after the clamp | character span covered |
|---|---|---|
| english | 0.3383 | 3,193 → 15,958 |
| multilingual | 0.0764 | 7,966 → 15,958 |
| typed-decisions | 0.4939 | 6,967 → 15,958 |

→ **The point at which the output freezes aligns exactly with the real clamp onset** → the tail really is discarded.

**Protocol clauses**:
3. **Never gate on `truncated`/`fits`**; always compute the tokenizer count yourself; the flag serves only for **descriptive reporting**;
4. **`W` per checkpoint**; a single constant must not be used;
5. **Report the new "flag error" metric** (the last column of this table); it is a direct quantification of instrument honesty.

---

## 3.3 Field layer (ii): `fits: true` holds at the same time as input that has already been truncated

**Phenomenon (R13 + P3)**: the decisive evidence is placed in the tail — **it is discarded and the answer flips wrong**, while the same response has `fits: true`, no `truncated`, and no warning.
On english, this **interval of damage with no warning is 111 characters**; and `truncated` only begins to appear in the new option-count region (from N≥15 onward).

**Why it is dangerous**: **"passed" and "has already been truncated" can be true at the same time**, so any pipeline that uses `fits` as an admission gate **will silently let through exactly the inputs it should trust least**.

**Protocol clauses**:
6. **`tightest_option_tokens_each < 49` is to be treated as a design failure**, not a warning;
7. **`truncated`/`fits` are only corroborating evidence**; admission uses arithmetic we compute ourselves.

---

## 3.4 Field layer (iii): `probability` is P(the selected option), and will flip the sign of **every item answered `false`**

**Measured on live** (P12/P13, the same response; reproduced in both directions in the third round by the independent direct route `P27`):

```json
{"answer": "false", "noul": 0.02, "probability": 0.98, "band": "no"}
```

- **`probability` is "the probability of the selected option", not P(true)** — recording `probability` as P(true) **flips the sign of every item answered `false`** (**⚠️ ninth-round correction, ERRATA §10.1 item 7**: the original printed "its half of the items", and this section's summary and the abstract printed "about half". **Measured, it is not half**: on the 1,100 items of `P19-calibration.json`, the **LLM answers `false` on 60.0% (660/1100)** and the **judge's `noul < 0.5` on 29.8% (328/1100)** — both obtained by adding up that artifact's per-bin `bins`, **neither anywhere near 0.5**);
- **In the same response `band` points toward true** (0.02 → `"no"`), **while `probability` points toward the selected option** (0.98) → **the two "confidence-like" fields point in opposite directions**;
- Measured to satisfy `answer=="true" ⇒ probability==noul` and `answer=="false" ⇒ probability==1−noul`; **the third round confirmed this in both directions on live** (`true`→0.98/0.98; `false`→0.02/0.98).
  **⚠️ But this identity rules out less than it appears to, and must be qualified**: (a) the machine-readable evidence is only **7 rows** (`P27b`'s plugin route, and **hand-transcribed**), of which **only 1 row** (`answer=="false"`, noul 0.02 vs probability 0.98) actually does any discriminating work — the other 6 rows have `noul = 0.98` and `answer=="true"`, and the four candidate hypotheses are all equal to 0.98 on those rows, zero information;
  (b) **"P(the answered option)" and "the maximum of `probabilities`" are identical under this access layer and cannot be told apart** — for a 2-option `noul`, the access layer defines `answer` as `noul ≥ 0.5`, i.e. the **argmax**, so "the selected is the maximum" is **constructive** and holds at any value of noul; the same goes for `choice`/`score` (the selected level is always the argmax in `legend`). **So an access layer whose `answer` is always the argmax cannot, in principle, produce a row that tells the two hypotheses apart**;
  (c) hence this section **really establishes only one thing**: `probability` is **not** `P(true)` (ruled out by that 1 row). **The stronger reading "= P(the answered option)" is not established, and does not affect any conclusion** — the two are numerically identical, and either reading leaves every number in the paper unchanged.

### 3.4.1 ⭐ These three fields are **not supplied by the provider** (three primitives, 1 direct-route measurement each) — direct evidence from the direct route

The third round built an independent HTTP direct route (`POST /api/v1/systemone`, `src\instrument\jev_client.py`) which takes **the same path** as the DSH plugin (same `noul`, same `input_tokens`, same `cost`, bit-identical). **The provider's raw response has only** `{model, provider, id, answers, usage}` **at the top level**, while **the keys inside the answer object change with the primitive** (1 measurement per primitive, three primitives):

| primitive requested | answer keys returned by the provider |
|---|---|
| `noul` | `type`, `noul` |
| `choice` | `type`, `choice`, **`probabilities`** (distribution), **`confidence`** |
| `score` | `type`, `score`, `legend`, **`probabilities`** (distribution), **`confidence`** |

**⚠️ Therefore this section's attribution conclusions must be qualified by primitive and must not be generalised** (the first draft wrote, from the single `noul` case, "the answer object has only `noul` and `type`", **and this was corrected after the three primitives were measured**):

| field | source |
|---|---|
| `type`, `noul`, `choice`, `score`, `legend`, `probabilities`, `confidence` | **provider** |
| `probability` (**singular**, = the probability of the option the access layer **selected**), `answer` (the true/false label derived from `noul` and a threshold), `band` | **derived by the access layer** |
| `truncated`, `stateChars`, `questionsChars`, `redactions`, **`warnings`** | **the access layer's egress accounting** |
| `latencyMs` | **the access layer's own measured clock** |

⇒ **⚠️ This table must match the artifact's key list key by key (ninth-round correction, ERRATA §10.1 item 11)**: `P27d-primitive-fields.json`'s `never_returned_by_provider` lists **9** keys — `band`, `probability`, `answer`, `truncated`, `stateChars`, `questionsChars`, `redactions`, `latencyMs`, **`warnings`** — while this table previously listed only **8** of them, **omitting `warnings`**. `warnings` in particular cannot be omitted: the whole basis of this section's first protocol clause is that **the absence of a warning must not be used to judge live vs mock**. With it added, the table covers the 7 keys the provider does return and the 9 it does not, 16 in all, matching the artifact.
⇒ **These three kinds of field (the singular `probability`, `band`, `answer`) and all the egress/latency fields are, under the three primitives measured (1 call each), not supplied by the provider**; so **within the range observed** they are indeed synthesised by the access layer. **⚠️ The two primitives `check` and `rank` were never measured (n=0) and cannot be extrapolated** — this section's attribution table is split by primitive precisely because attribution changes with the primitive.
⇒ But **`confidence` and `probabilities` (plural) are indeed returned by the provider in the 1 call each of `choice`/`score`**, and must not be mixed into the "self-reports are untrustworthy" list — **that distinction is itself this section's lesson: attribution must be measured field by field and cannot be extrapolated from one primitive.**
⇒ **⚠️ The amount of evidence must be reported alongside**: `choice` and `score` have **only n=1 each** in the whole `results\` tree (`P27d-primitive-fields.json` has 1 per primitive; `P27`'s provider-field list added only 1 `noul`; `P27b`'s 7 rows are **plugin-route `noul` rows, hand-transcribed by the AI**, and the artifact carries its own `transcription_risk` declaration). So this section's conclusion is "**not seen in these 3+1 observations**", not "the provider never returns them" — **a single observation is enough to establish "these keys do exist", and is not enough to establish "those keys never appear".**

⇒ **This is direct, on-line evidence for the paper's claim that "self-reported fields are untrustworthy"**: these fields are **not reported by the party under test**, but **synthesised by an intermediate layer**.
⇒ Hence the accurate statement of Result B is **about the access layer**, not about any engine's own protocol — consistent with the attribution statement in section 3.1.1, and now with a mechanism-level proof.
⇒ **One flag awaiting verification attached**: the plugin's `latencyMs` (n=7, p50 **1,851 ms**) is about **1.94×** the independent wall clock (the **size-matched** 126-character / 347-token class, n=5, p50 956 ms; switching to the unmatched current n=20 run reads it as **1.55×** — the ratio itself depends on whether the state is matched, so both numbers must be given); the two groups were not collected in the same batch, so this is recorded as a flag rather than a conclusion (§5.2).

**The same trap also appears on the LLM side (the fourth instance in this project)**: the LLM's `prob` is **the confidence of the answered label**. The first version took it as P(true), **reversed the sign of every `false` answer**, and reported 0.0 accuracy on the `explicit_contra` stratum — while the model **answered every item correctly**.
→ **After correcting to `P(true) = prob` (if it answers true) or `1 − prob` (if it answers false), the accuracy is 1.00** (n=1100).

**Why it is dangerous**: this is a **specification-level defect**, not a rounding error — **it flips the sign of the conclusion**, and it appears **independently** on two different systems.

**Protocol clauses**:
8. **The semantics of `probability` must be confirmed by measurement system by system, and must not be assumed**;
9. **Record only the field that points toward true** (for Jev, `noul`; for the LLM, the P(true) derived from the label);
10. **Types/keys must be asserted per response** — an unknown `type` in Jev is **silently turned into `score`**.

---

## 3.5 Semantic layer (i): `conflicted` and `undecided` are unreachable under real inputs

**Design**: the **7 rows** of live `jev_check` readings (all 7 rows of the table below), covering support / negation / **explicit conflict** / **symmetric conflict** / irrelevant / weakly relevant and hearsay (one row) / a single unattributed note. **⚠️ Ninth-round correction (ERRATA §10.1 item 13)**: this sentence printed "eight" and listed eight categories, while **this section's own table has 7 rows** — in the source, "weakly relevant" and "hearsay" are **two rows**, merged into one here. **⚠️ And the source contradicts itself, with no artifact to adjudicate**: `probes\P13-jev-remaining-measurements.md:45` says "**seven**" in its design line, while its table (`:47-56`) lists **8 rows** (one extra: "prescriptive support 0.98 / 0.02 / 0.89 `supported`", not carried into this table); that probe has **no `results\` JSON artifact at all**, so 7-vs-8 **cannot be decided from the tree**. This table reports the **7 rows that are actually visible** and records the discrepancy here.

| nature of the evidence | supports | contradicts | **sufficient** | verdict |
|---|---|---|---|---|
| verbatim support | 0.99 | 0.02 | 0.88 | `supported` |
| clear contradiction | 0.02 | 0.98 | 0.92 | `contradicted` |
| **explicit conflict** | 0.43 | 0.67 | **0.07** | **`insufficient`** |
| **symmetric conflict** | 0.55 | 0.67 | **0.14** | **`insufficient`** |
| completely irrelevant | 0.01 | 0.03 | 0.02 | `insufficient` |
| weak / hearsay | 0.22 | 0.10 | 0.08 | `insufficient` |
| a single unattributed note | 0.06 | 0.04 | 0.03 | `insufficient` |

**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: **all 7 rows of this table** (and the `sufficient` readings quoted from it) have **no `results\` artifact** — **no JSON under `results\` contains a `sufficient` field at all**; these readings exist only in the lab record `probes\P13-jev-remaining-measurements.md:47-56` (see also `protocol\AUDIT-FINDINGS.md`). **So this table can only be read as a record, not as a re-checkable measurement**; the qualitative conclusion drawn from it (the five-value vocabulary degenerating to three) is internally consistent **within that record**, but **external verification needs a rerun** — and a rerun produces new numbers (`temperature` was not pinned), which is a cost this project has already documented.

**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: **all 7 rows of this table** (and the `sufficient` readings quoted from it) have **no `results\` artifact** — **no JSON under `results\` contains a `sufficient` field at all**; these readings exist only in the lab record `probes\P13-jev-remaining-measurements.md:47-56` (see also `protocol\AUDIT-FINDINGS.md`). **So this table can only be read as a record, not as a re-checkable measurement**; the qualitative conclusion drawn from it (the five-value vocabulary degenerating to three) is internally consistent **within that record**, but **external verification needs a rerun** — and a rerun produces new numbers (`temperature` was not pinned), which is a cost this project has already documented.

**`sufficient` does not exceed 0.14 in any of the**5 `insufficient` calls** (**⚠️ Eighth-round correction**: the original printed "all 7" — but in this section's own table only **5** rows are `insufficient`, and the other two rows' `sufficient` values are **0.88** and **0.92**, **both greater than 0.14**. The error was inherited verbatim from `probes\P13-jev-remaining-measurements.md:60`, and has been recorded as audit finding m-8 in `protocol\AUDIT-FINDINGS.md:225`; the first draft was not synchronised)**, while the parser needs sufficiency ≥ a threshold (≈0.5) before it will give `undecided` / `conflicted`. **⚠️ And this has been re-checked everywhere (ninth round, ERRATA §10.1 item 4)**: no second "all 7 calls" quantifier exists in the paper; and **the count is robust to the 7-vs-8 row question above** — in the source's 8 rows only 5 are `insufficient` as well (rows 1, 2 and 3 are `supported` / `contradicted` / `supported`), so "5 calls" holds under either row count.

→ **The five-value verdict vocabulary effectively degenerates into three values.**
→ **When the evidence genuinely contradicts itself, what the system reports is "insufficient evidence".**
→ **Why it is dangerous**: "insufficient evidence" sounds like **just give it a bit more material**; the actual situation is **the material contradicts itself, and giving more is useless**. This is a misdiagnosis that will misdirect the next action.

**Incidentally**: the tool description lists six verdicts (including `unknown`), while **the plugin's actual vocabulary has only five** — **the tool description is itself untrustworthy documentation**.

**Protocol clauses**:
11. **Do not assume that the full verdict vocabulary is available**; **measure, on the target corpus, which verdicts are actually reachable, before evaluating**;
12. **Items of the evidence-conflict class must be reviewed under the prediction that they will be reported as `insufficient`** (with a direct impact on the FEVER-gold adopted by D3).

---

## 3.6 Semantic layer (ii): `no_support` — reading "not stated" as support

**Design**: 1100 binary items (5 difficulty × 220), with **ground truth computed by construction** (no human annotation, no model annotation), the two judges **run paired**. The **sole purpose** of the `no_support` stratum among them is to test the rule R12 wrote into the protocol:

> "Something is supported only when the STATE actually says it. **A non-statement does not constitute evidence for it.**"

| judge | `no_support` accuracy (n=220) | **mean claimed P(true)** | ground truth |
|---|---|---|---|
| **Laya** | **0.3091** | **0.5643** | all FALSE |
| LLM | **1.0000** | 0.0012 | all FALSE |

→ **Faced with items where "the candidate value does not appear at all", Laya gives a mean P(true) = 0.564, i.e. it tends to assert that that value is the current value.**
→ **It reads "not stated" as support for the claim.**

**Another severe asymmetry**: `explicit_support` **0.991** vs `explicit_contra` **0.273** (n=220 each).
→ When the state **explicitly declares that another value is the current one**, it is instead **more likely** to judge the candidate value to be the current value — **it is looking for "the candidate value appeared", not for "it is the current value"**.
→ **This explains why Laya scored 1.00 on this project's early simple items**: that is precisely the only shape it is good at.

**Protocol clauses**:
13. **The evaluation corpus must contain items where "the candidate value does not appear"**, otherwise the judge's performance on verification-style tasks will be systematically overestimated.

---

## 3.7 Semantic layer (iii): cross-language discrimination collapses

**Premise correction**: this script originally set out to measure a routing defect, but a probe proved that **the HTTP sidecar never routes** — for every kind of input (including Cyrillic and Devanagari) it reports `routing.reason = "explicit model selection"`, **and likewise when started without `--model`**. So this item is **not** a routing measurement; it is **the behaviour of the english checkpoint when faced with non-English text**.

| writing-system group | n | accuracy | mean P(true) on true items | **mean P(true) on false items** | always-answers-true baseline |
|---|---|---|---|---|---|
| **native English** | 2 | **1.000** | 0.975 | **0.407** (correctly negated) | 0.5 |
| other Latin scripts | 12 | **0.500** | 0.917 | **0.747** | 0.5 |
| non-Latin scripts | 2 | **0.500** | 0.968 | **0.912** | 0.5 |

→ **On English it separates true from false perfectly; once the text is not English it stops separating, and instead tends to affirm the claim**, and **the false items' P(true) reaches 0.912**.

**Limitation**: English and Russian have only 2 items each, other Latin scripts 12 in total → **only the qualitative shape can be reported**.
**And**: **we must not** make any statement about the Python `Router` used by the DSH plugin — **that is a component this project never reached**.

---

## 3.8 Summary of this section

**Seven phenomena, one shape**:

| # | failure location | in one sentence |
|---|---|---|
| 1 | input layer (mock) | no judgment capability, yet it produces a credible results table |
| 2 | field layer | `truncated` is wrong in both directions |
| 3 | field layer | `fits: true` holds at the same time as input that has already been truncated |
| 4 | field layer | `probability` is P(the selected option); it flips the sign of **every item answered `false`** (measured shares **60.0%** (LLM) / **29.8%** (judge), **not "about half"**), and points opposite to `band` |
| 5 | semantic layer | `conflicted`/`undecided` are in practice unreachable; conflict is reported as "insufficient evidence" |
| 6 | semantic layer | "not stated" is read as support (n=220) |
| 7 | semantic layer | under non-English text it does not separate true from false (n small, qualitative) |

> **Unified shape**: **this judge fails on the occasions where it "must notice an absence or a mismatch", and is near-perfect on the occasions where "the answer is explicitly stated"; in both cases the confidence it self-reports is not low.**

**These seven depend on no generator battery**, and on no long-horizon task either — they **all fall in the access layer** (see the attribution statement in section 3.1.1 and §6.4.1). This section is therefore the **most robust and most reproducible** section in the whole paper.

---

## 3.9 Limitations

1. **Item 7's n is tiny** (2/12/2); only the qualitative shape;
2. **Item 1 is the behaviour of the mock provider**, not the behaviour of live Jev — its value lies in the **methodological warning**, not in an assessment of Jev;
3. **Items 2 and 3 were obtained under three loadouts, english/multilingual/typed-decisions**, and **all are three-checkpoint loadouts** — the window figures must be reported together with the launch loadout (see §4.8);
4. **Item 4's live verification is n=7 rows in machine-readable artifacts (plugin route, hand-transcribed), and only 1 of those rows has discriminating power**; the semantic rule (`probability` ≠ `P(true)`) is established by that row. **"= P(the answered option)" and "= the maximum of `probabilities`" are identical and indistinguishable under this access layer** (the selected is the argmax), so the paper claims only the weaker of the two. The 8/8 and the n=13 come from P12/P13's **report text, with no JSON artifact**, and are not used as a basis;
5. **Item 6 is n=220 per stratum, but the corpus is templated** — the absolute accuracy is not a capability estimate; what is usable is the **relative differences between difficulties and the shape of the calibration**;
6. **Not measured**: the exact truncation point of Jev's **plugin-side** 16,000-character constant (proved only up to 15,002; the vendor documentation's `state` limit of 32k token was not measured); the live behaviour of `rank`'s over-limit refusal.

---

# §6 Results C — capability collapse: the judge fails when it "must notice an absence"

> This section is the paper's **organising core**: it gathers the scattered findings outside §3 (the instrument's self-reports are untrustworthy) and §5 (window/latency) into **one unified shape**.

---

## 6.0 The unified shape

> **The same judge is near-perfect on tasks where "the answer is explicitly stated" (`explicit_support` 0.9909, n=220), and collapses on tasks where it "must notice that something is absent or that something somewhere does not match" (`explicit_contra` 0.2727 / `no_support` 0.3091 / `partial_contra` 0.5818 / `partial_support` 0.6818, each n=220); and in both cases, the confidence it self-reports is not low.**

This shape is supported by **three independent instances**, corresponding to three kinds of "absence":

| instance | what is absent | evidence |
|---|---|---|
| **silent truncation** | part of the input (discarded while the instrument says "passed") | §3.2–3.3 |
| **`no_support`** | the evidence (the candidate value never appears at all) | §6.3, n=220 |
| **cross-language** | the language match (what is being read is not English) | §6.4, n small |

---

## 6.1 Capability profile (all n≥20, and verified with decorrelated option order)

| task type | judge | accuracy | n | source |
|---|---|---|---|---|
| the state **explicitly states** the answer | **LLM** | **1.0000** | 48 | P14 |
| the state **explicitly states** the answer | **Laya** | **1.0000** | 40 | P8 |
| the state **explicitly states** the answer (templated, with a `(current)` marker) | Laya | **0.9909** | 220 | P19 |
| authority location (find the authoritative source among several statements, all options plausible) | LLM | **1.0000** | 48 | P14 |
| authority location (**the other arm of the same 48 items**) | **Laya** | **0.4583** | 48 | P9b |
| 77-class intent classification (flat) | LLM | **0.750–0.900** (**4 draws**; **median 0.875, mean 0.850**) | 40 | P15 + P15b r1–r3 |
| 77-class intent classification (flat) | Laya | **0.0333** | 30 | P7 |
| intent classification (Laya's full hierarchy, **the deployed setting**) | Laya | **0.2250** | 40 | P15 |
| ~~20-candidate relevance judgment~~ (**withdrawn**, see below) | Laya | ~~0.0000~~ | ~~18~~ (actually **3**) | P1 |
| binary verification (5 difficulty levels mixed) | Laya | **0.5673** | 1100 | P19 |
| binary verification (5 difficulty levels mixed) | LLM | **1.0000** | 1100 | P19 |

**⚠️ The pairing must be stated (ninth-round correction, ERRATA §10.1 item 9)**: the two "authority location" rows above are **the two arms of one 48-item battery** — `P14-llm-arm-full.json`'s `_provenance.consumes` is `P9b-template-validation-separated-n48.json`, and its `complementarity.detail` is **paired item by item** with P9b's 48 rows. So these two rows are **not two further independent measurements but the two sides of one paired comparison**; this profile counts the same 48 items **twice** (one LLM row, one Laya row) and **should be counted as 1 battery of 48 items** in any evidence count. **The numbers themselves do not move** (1.0000 and 0.4583 are the measured values on their own arms), but **the reading must change**: they are not two independent pieces of capability evidence.
**⚠️ The word "centre" must be split here (ninth-round correction, ERRATA §10.1 item 10)**: the four draws are **0.750 / 0.900 / 0.875 / 0.875**, so the **median is 0.875 and the mean is 0.850** — the original "centre ≈0.875" holds only for the median. **And the source column previously read `P15` only**: **3 of the 4 draws are `P15b-rep-r1..r3.json`** (`temperature=0`), and only the recorded round is `P15-complementarity-strong-regime.json`; it now names the artifacts. (§7.3 and the abstract already gave "empirical centre ≈0.875, mean 0.850" in full and are unaffected.)

**Three readings**:

1. **Laya's interval is 0.00–1.00**, an enormous span, **determined by the shape of the task rather than by difficulty**;
2. **the LLM hits the ceiling on verification-style tasks** (1.0000, n=1100), so **such tasks cannot measure its error structure** (see §7, a harder battery design);
3. **the only strength the two share is the same thing**: the answer is explicitly stated.

**⚠️ One row that has been withdrawn**: the table above originally had the row "20-candidate relevance judgment / Laya / 0.0000 / n=18", and **that row does not hold and has been withdrawn**, because it violates three rules this paper set for itself at the same time (see the n<20 clause in §4.6 and §10):
- **the n is wrong**: that cell's `n_calls` is actually **3** (it is the whole P1 battery that has 18 items), while §4.6 states explicitly that "**classification cells with n<20 cannot support a conclusion**";
- **that 0.0000 comes from truncated calls**: all three N=20 rows' responses carry `truncated.options.note = "options were re-cut below the 48-token ceiling to fit head_max_len, so labels may no longer be distinguishable from one another"`, with the warning "20 options sharing 512 tokens, ~25 tokens per label";
- **a rule the protocol set for itself**: `laya_client`'s docstring requires "**check `truncated` before any data enters the analysis**" — this was not done for this row.
(The same row was once used by §6.2 as evidence that "maximum confidence can also be wrong"; that use is **withdrawn along with it**; "confidence is decoupled from correctness" is supported independently by §6.2's n=1100 result and does not depend on this row.)

### 6.1.1 A number that must not be cited

**Laya's 0.867 (P7's second level) must not be cited as a capability number.** It is **within-layer skill conditional on the ancestor being correct**; **the same system's end-to-end deployment accuracy is 0.225** (P15).
→ **And the hierarchy is a net gain for Laya**: flat 77-class is only **0.0333** (1/30), hierarchical end-to-end **0.200** (6/30); the artifact's own `hierarchy_beats_flat = true`. The bottleneck is **group selection** (0.200, chance 0.10) rather than within-group (0.867, chance 0.333). (An early version of this section wrote the direction as "net loss"; corrected against the P7 artifact, see §8.3.1.)

---

## 6.2 The relation between `confidence` and correctness (n=1100)

**Main result** (P19, 1100 binary items, ground truth computed by construction, the two judges run paired):

| | Laya | LLM |
|---|---|---|
| accuracy | 0.5673 | 1.0000 |
| **ECE** | **0.2259** | 0.0028 |
| **Brier** | **0.2571** | 0.0000 |
| constant-predictor Brier (base rate 0.4) | **0.240** | 0.240 |
| **Better than the constant predictor?** | ❌ **worse** | ✅ |

→ **Laya's Brier is higher than "always predicting the base rate"** ⇒ its probabilities are **worse than the constant predictor**.
→ **But this is not "no information".** A **Murphy decomposition** on the same 1100 items (10 equal-frequency bins) gives **REL = 0.0556 / RES = 0.0397 / UNC = 0.2400**; and **AUC(`noul`; truth) = 0.7136, 95% CI [0.682, 0.745]** (n_pos=440 / n_neg=660).
→ **Resolution really is present (AUC ≈ 0.71); the failure is in "calibration", not in "information".** So the correct statement is **poorly calibrated**, **not** "negative information" — an early version of this section used the latter wording, and it has been corrected.
→ **But its ECE does not look catastrophic**, because the errors on the two sides cancel each other out → **protocol clause: a calibration report must give all three of Brier, the constant baseline and AUC**.

**Reliability curve shape** (Laya, **10 equal-width bins, [0,1], last bin right-closed**, **all 10 bins carry mass** — smallest n=1): **the overconfidence is concentrated in the middle, and the low end runs the other way**.
(The binning scheme was not stated in the body text before; the measured conclusion is robust to that choice — switching to 5/15/20 bins gives an ECE of 0.2220 / 0.2316 / 0.2323.)

**gap = measured frequency − claimed P(true)** (the same direction as the `gap` field of `results/P19-calibration.json`).

| bin | n | claimed P(true) | measured frequency | **gap** |
|---|---|---|---|---|
| **0.0–0.1** | **1** | 0.061 | 1.000 | **+0.939** |
| **0.1–0.2** | **22** | 0.157 | 0.500 | **+0.343** |
| 0.2–0.3 | 51 | 0.252 | 0.294 | +0.042 |
| 0.3–0.4 | 85 | 0.351 | 0.235 | −0.116 |
| 0.4–0.5 | 169 | 0.453 | 0.148 | **−0.305** |
| 0.5–0.6 | 199 | 0.547 | 0.261 | **−0.286** |
| 0.6–0.7 | 184 | 0.651 | 0.370 | **−0.281** |
| 0.7–0.8 | 176 | 0.749 | 0.540 | **−0.210** |
| 0.8–0.9 | 166 | 0.847 | 0.687 | −0.160 |
| 0.9–1.0 | 47 | 0.922 | 0.830 | −0.093 |
| **Total** | **1,100** | — | — | — |

→ **The middle (0.4–0.8, n=169/199/184/176) systematically exceeds the measured rate by 21–31 percentage points.**
→ **But "the two ends are acceptable" holds only at the high end** (0.8–0.9 gap −0.160, 0.9–1.0 gap −0.093): **the low end runs the other way, with large gaps** — the 0.0–0.1 bin by **+0.939** (n=**1**) and the 0.1–0.2 bin by **+0.343** (n=**22**), i.e. **very low claimed probabilities that the data contradicts**.
→ **⚠️ Ninth-round correction (ERRATA §10.1 item 8)**: this table previously printed only **5** of the 10 bins and on that basis wrote "the two ends are, if anything, acceptable". **The five omitted bins include the two largest miscalibrations in the whole table (+0.939 and +0.343, both at the low end)**, so "the two ends are acceptable" is **false at the low end**; the omitted ones also included 0.2–0.3, 0.3–0.4 and 0.8–0.9. **All 10 bins are now printed** (all carry mass; the n's sum to **1,100**, matching P19's n). **⚠️ The two low-end bins have n = 1 and n = 22 — a bin with n=1 cannot carry any conclusion**; they are printed **not in order to claim anything from them**, but because **omitting them makes this table read as support for a sentence it does not support**.

**Per-case evidence** (retained, as points on the curve):

| observation | value | source |
|---|---|---|
| **the highest** confidence **on a wrong answer** (**not** the probe maximum) | **0.9981 — on the single wrong answer** | R13 |
| **the probe maximum** confidence (**on a pure-noise state**) | `noul 0.0011 / confidence` **0.9989** | R13 |
| same p, different framing | confidence **0.5399 vs 0.0046** (a 117× difference) | R13 |
| **carrier removed (all wrong, n=48)** mean confidence | **0.218** | P9b |
| **with carrier (same conventions: wrong items only, n=26)** mean confidence | **0.115** (the whole arm's mean is 0.178, but that arm has 22/48 correct and **is not an all-wrong arm**, so it must not be placed alongside it) | P9b |
| high cardinality (20 options) | the correct option **p = 0.0000** while confidence **1.0000** | P1 |
| **the LLM on the same batch of items** | all ≈1.0 and **all correct** | P14 |

**⚠️ Ninth-round correction (ERRATA §10.1 item 1)**: this table originally printed **0.9981** as "the **highest** confidence in the whole probe", and **that wording is wrong**: **the very next row** (pure-noise state) records **0.9989**, which is higher. The source `recon\R13-laya-probe.md:456` records **0.9989**; and **the same file at `:430` says 0.9981 is "the highest value anywhere in this entire probe" — the source contradicts itself**. The table therefore separates the two facts: **0.9981 is the highest value on a wrong answer; the probe maximum is 0.9989, on a pure-noise state.** Together the two rows say what this section needs to say: `confidence` indicates neither correctness nor whether the input carries information. (**Process note**: `p44` and `p45` each tried to repair this sentence and each reported MISS, because both were pointed at `06-results-B-draft.md` — it has never been in that file. ERRATA §10.1 item 1's file label was wrong in the same way and has been corrected.)
**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: the four rows of the table above marked **R13** (0.9981, 0.9989, 0.5399 vs 0.0046, and `noul 0.0011`) **have no `results\` artifact** — they come from the lab record `recon\R13-laya-probe.md` (`:430`, `:456`, `:448-449`), which records those responses as verbatim JSON, but **no result JSON corresponds to them**; the table's other two rows (P9b's 0.218 / 0.115) do have artifacts. **So those four rows can only be read as case records**: their value is the **shape** (the same field can be far from correctness in either direction), not re-checkability. Turning them into re-checkable evidence would require the requests and responses of that round to be written to an artifact (not done).
**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: the four rows of the table above marked **R13** (0.9981, 0.9989, 0.5399 vs 0.0046, and `noul 0.0011`) **have no `results\` artifact** — they come from the lab record `recon\R13-laya-probe.md` (`:430`, `:456`, `:448-449`), which records those responses as verbatim JSON, but **no result JSON corresponds to them**; the table's other two rows (P9b's 0.218 / 0.115) do have artifacts. **So those four rows can only be read as case records**: their value is the **shape** (the same field can be far from correctness in either direction), not re-checkability. Turning them into re-checkable evidence would require the requests and responses of that round to be written to an artifact (not done).
→ **Value as a contrast**: **on the same batch of items, one judge's maximum confidence is right and the other's is wrong.** A user cannot tell them apart from the returned values.

---

## 6.3 Instance one: `no_support` — reading "not stated" as support (n=220)

**Design intent**: the **sole purpose** of this stratum is to test the rule R12 wrote into the protocol —

> "Something is supported only when the STATE actually says it. **A non-statement does not constitute evidence for it.**"

| judge | accuracy | **mean claimed P(true)** | ground truth |
|---|---|---|---|
| **Laya** | **0.3091** | **0.5643** | all FALSE |
| LLM | **1.0000** | 0.0012 | all FALSE |

→ **Faced with items where "the candidate value does not appear at all", Laya gives a mean P(true) = 0.564, i.e. it tends to assert that that value is the current value.**

**Another severe asymmetry** (the same n=220 per stratum):

| difficulty stratum | accuracy | mean claimed P(true) |
|---|---|---|
| `explicit_support` | **0.9909** | 0.7811 |
| `partial_support` | 0.6818 | 0.5881 |
| `partial_contra` | 0.5818 | 0.4922 |
| **`explicit_contra`** | **0.2727** | **0.6070** |
| **`no_support`** | **0.3091** | **0.5643** |

→ **`explicit_contra` (0.273) is worse than `partial_contra` (0.582).** When the state **explicitly declares that another value is the current one**, it is **more likely** to judge the candidate value to be the current value.
→ **It is looking for "the candidate value appeared", not for "it is the current value".**
→ **This explains why Laya scored 1.00 on this project's early simple items**: that is precisely the only shape it is good at.

---

## 6.4 Instance two: cross-language — it is not reading English, yet it affirms all the same (n small, qualitative)

**Premise correction**: this item is **not** a routing measurement. A probe proved that **the HTTP sidecar never routes** — for every kind of input (including Cyrillic and Devanagari) it reports `routing.reason = "explicit model selection"`, **and likewise when started without `--model`**.

| writing-system group | n | accuracy | mean P(true) on true items | **mean P(true) on false items** |
|---|---|---|---|---|
| **native English** | 2 | 1.000 | 0.975 | **0.407** (correctly negated) |
| other Latin scripts | 12 | 0.500 | 0.917 | **0.747** |
| non-Latin scripts | 2 | 0.500 | 0.968 | **0.912** |

→ **On English it separates true from false perfectly; once the text is not English it stops separating, and instead tends to affirm the claim**, and **the false items' P(true) reaches 0.912**.

**Limitation**: English and Russian have only 2 items each → **only the qualitative shape can be reported; no per-language claim is made**.

---

## 6.5 Why the three instances are the same thing

| instance | what must be "noticed" | consequence of not noticing | what the self-reported fields say |
|---|---|---|---|
| silent truncation | the input was discarded | the answer flips wrong | `fits: true`, no `truncated`, no warning |
| `no_support` | the evidence does not exist | asserts true (P=0.564) | `band` gives low confidence, but `noul` is above 0.5 (**⚠️ not traceable: `P19-calibration.json` has no `band` column, see below**) |
| cross-language | the language does not match | affirms across the board (P=0.912) | confidence is not low |

→ **The three share one mechanistic hypothesis: the judge's judgment depends on "matching some pattern in the text", not on "confirming the existence or the authority of that pattern".**
→ **When the pattern appears, it is right; when the pattern **should be absent** or **should not match**, it has no corresponding detection channel, and so degenerates into affirmation.**

**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: the `band` assertion in the `no_support` row above **has no artifact behind it** — the 1,100 rows of `P19-calibration.json` **have no `band` field** ( `band` is an access-layer derivation; P19 records `noul` and `laya_p`). That row is therefore **kept as a shape description only**: what the artifacts support is the distribution of `noul` (mean 0.5643) and the accuracy (0.3091), **not** any distribution of `band` values. **Claiming a `band` distribution would require a rerun that records that field** (not done).

**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: the `band` assertion in the `no_support` row above **has no artifact behind it** — the 1,100 rows of `P19-calibration.json` **have no `band` field** ( `band` is an access-layer derivation; P19 records `noul` and `laya_p`). That row is therefore **kept as a shape description only**: what the artifacts support is the distribution of `noul` (mean 0.5643) and the accuracy (0.3091), **not** any distribution of `band` values. **Claiming a `band` distribution would require a rerun that records that field** (not done).

**This hypothesis can be falsified**: if, on items where "the candidate value does not appear", it is given an **explicit absence marker** (such as the state stating "there is no record of this item"), and it still answers "true", then the hypothesis holds; if it then answers correctly, the problem is that it was **not told** rather than that it **cannot perceive**.
→ **This is a cheap and decisive experiment that has not yet been run**, listed as a next step ⬜.

---

## 6.6 Mandatory protocol clauses (new in this section, continuing the list from the Results B section)

> **⚠️ Numbering note (rewritten in the ninth round, ERRATA §10.1 item 12)**: this section has **8 clauses, numbered 14–21**, listed below.
> **The previous note was self-contradictory and has been withdrawn**: it said "this section's clauses were originally numbered 14–17, one of them duplicated clause 13 of Results B verbatim, the duplicate has been deleted, this section is now 14–21" — **14–17 is four clauses, and deleting one cannot yield eight**. And **none of 14–21 restates clause 13 of Results B** (the closest, clause 16, requires difficulty strata to cross "explicit support / explicit contradiction", which is not the same clause as 13's "the corpus must contain items in which the candidate value does not appear" — different wording, different referent).
> **What is checkable is this**: of §4.4's four clauses (`04-method-draft.md`: probability semantics, per-response type/key assertions, the prose extractor, impossible-value review), **the 1st and 2nd duplicate Results B's 8th and 10th**; Results B has **13 clauses**; this section has **8**. So the paper's non-duplicate total is **4 + 13 + 8 − 2 = 23** — **the 23 stands; only the half-sentence about "this section was originally 14–17" is withdrawn**.

14. **A calibration report must give the Brier score and the constant-predictor baseline at the same time** — reporting only ECE understates the problem of a judge whose errors on the two sides cancel each other out;
15. **Capability numbers must not cite a conditional within-layer skill** (such as P7's 0.867); **the end-to-end value for the deployed setting must be reported** (0.225);
16. **Difficulty strata must cross "explicit support / explicit contradiction"**, because the gap between the two (0.991 vs 0.273) is more informative than the overall accuracy;
17. **Wherever a judge arm is sampled through an API, `temperature` must be pinned explicitly, and the item-level label agreement between repeated draws must be reported.** **Basis**: this project's recorded draw did not pass `temperature`, so the chain regime's point estimate moved between reruns by 0.07 (overall), 0.20 (κ) and 0.20 (Δ_catch), and the item-level label agreement is **58.8–63.2%** (the three pairings are 40/68, 43/68 and 41/68 respectively); after dropping the 7 items whose option set changed it is **60.7–63.9%**, see §8.6.1. **⚠️ An early version printed only the lowest of the three (58.8% / 60.7%), writing a range as a single value**; once pinned it rises to **86.8–89.7%**. **The judge (non-generative) arm should reach 100%** — on **items whose option set did not change, that arm is exactly 61/61 = 100% (3/3 draws)**, and its only disagreement with the recorded draw falls on exactly one item whose option set changed, so it is a deterministic function of (state, options); failing to reach that shows the arm is not reproducible.
18. **The number of digits in a point estimate must not exceed the precision its interval width allows.** **Basis**: "κ = 0.0062 is indistinguishable from chance" is a four-decimal-place statement about an estimate whose bootstrap 95% CI is **[−0.185, +0.206]**. **【NOT TRACEABLE ⚠️ ERRATA §10.2】**: that bootstrap interval has **no `results\` artifact and no script** — `P28-recomputed-statistics.json` recomputes Wald / Newcombe / Fisher / Clopper-Pearson and **contains no bootstrap**; the interval comes from a one-off interpreter session during the audit. The clause's lesson does not depend on this particular interval (the artifacts support enough κ-adjacent statistics to make the point), but **the number itself cannot be re-checked**. **【NOT TRACEABLE ⚠️ ERRATA §10.2】**: that bootstrap interval has **no `results\` artifact and no script** — `P28-recomputed-statistics.json` recomputes Wald / Newcombe / Fisher / Clopper-Pearson and **contains no bootstrap**; the interval comes from a one-off interpreter session during the audit. The clause's lesson does not depend on this particular interval (the artifacts support enough κ-adjacent statistics to make the point), but **the number itself cannot be re-checked**.
19. **Before aggregating, the "bucket list" must be checked for agreement with the actual data.** **Basis**: P1's buckets are hard-coded as `(2,5,10,15,20,25)` while the generator actually produces `…20, 21`, and **3 calls fell into no bucket and silently vanished from `by_n`** (that artifact: `n_items` 18, 18 rows, `instrument.calls` 18, while **the bucket total is only 15** — **the one internal inconsistency**). **⚠️ Qualification**: what was dropped is the **aggregation**, not the **measurement**; the 18 rows themselves are complete, and every published P1 number is still reproducible (an independent replay of the 18 requests is **field-by-field, bit-for-bit identical** except for `latency_ms`). **【NOT TRACEABLE ⚠️ ERRATA §10.2】**: **that independent replay has no artifact and no script** — `P1-rank-vs-choice.json` has only `summary` and `rows`, **with no replay record of any kind**; the replay result comes from a one-off session during the audit. So the honest statement here is "the record says the replay was bit-identical", **not "this has been reproduced"**; asserting that would require the replay itself to be a script with a stored artifact (not done). **【NOT TRACEABLE ⚠️ ERRATA §10.2】**: **that independent replay has no artifact and no script** — `P1-rank-vs-choice.json` has only `summary` and `rows`, **with no replay record of any kind**; the replay result comes from a one-off session during the audit. So the honest statement here is "the record says the replay was bit-identical", **not "this has been reproduced"**; asserting that would require the replay itself to be a script with a stored artifact (not done). The code has already been changed at `p1_rank_vs_choice.py:253-267` to **derive the buckets from the data** (**⚠️ Eighth-round correction**: it originally cited 236-246 — those 11 lines are row-dictionary fields and have nothing to do with bucketing); **the artifact is kept as it stands under the established policy in `results\ERRATA.md`** (that file states explicitly that raw artifacts are measurement records and are not modified in place), with the discrepancy recorded in its §6.
20. **For any item of the "notice an absence / a mismatch" kind, the option order must be decorrelated from the correct answer.** **Basis**: in P26 the decoy is always in first position and the ground truth always in last position, while the judge picks the first position 10/10 times ⇒ position preference and "truncation" are indistinguishable in the results (§5.3.2, §8.7).
21. **The ground truth must be derivable from the rendered question, and that property must be enforced by a build-time assertion.** **Basis**: CHAIN-AUDIT's generator rewrote the parity while `simulate()` does not reproduce it, so **the scored ground truth is not derivable for 11/69 items (15.9%)**, and for 10 of them the faithful answer is not even among the options (§8.6.1). **【NOT TRACEABLE ⚠️ ERRATA §10.2】**: the 69 rows of `P22-chain-audit.json` **carry no derivability field** (the row keys are `truth` / `llm_*` / `laya_*` / `alt_in_options` only), so **the count of 11 cannot be obtained from the artifact**; it comes from an independent recomputation during the audit. **After the fix** the battery enforces the property by build-time assertion (**96 → 0 → 68**), and **that part is checkable**; the historical "11/69 before the fix" can only be read as a record. **【NOT TRACEABLE ⚠️ ERRATA §10.2】**: the 69 rows of `P22-chain-audit.json` **carry no derivability field** (the row keys are `truth` / `llm_*` / `laya_*` / `alt_in_options` only), so **the count of 11 cannot be obtained from the artifact**; it comes from an independent recomputation during the audit. **After the fix** the battery enforces the property by build-time assertion (**96 → 0 → 68**), and **that part is checkable**; the historical "11/69 before the fix" can only be read as a record.

---

## 6.7 Limitations

1. **The corpus is templated** (5 templates × a constant pool): **the absolute accuracy is not a capability estimate**; what is usable is the **relative differences between difficulties and the shape of the calibration**;
2. **The LLM hits the ceiling** (1.0000/1100) → this corpus has **no discriminating power** for the LLM, so **this cannot be used to claim that "the LLM is generally better than Laya"**;
3. **Cross-language items have a tiny n** (2/12/2), qualitative only;
4. **One sample per judge per item**; the typed judge is deterministic (bit-identical when measured in R13), while the LLM is at default temperature in non-thinking mode;
5. **Not measured**: the explicit absence-marker experiment (§6.5), multi-hop chained verification (a harder battery design), the same kind of curve for the `typed-decisions` and `multilingual` checkpoints.


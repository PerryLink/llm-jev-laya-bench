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
| 0.0–0.2 | 3 | — | 0.67 |
| 0.2–0.4 | 2 | — | 0.00 |
| 0.4–0.6 | 5 | **2** | 0.50 |
| 0.6–0.8 | 2 | — | 0.50 |
| 0.8–1.0 | 2 | — | 0.00 |
| **Total** | **14** | **9** | — |

**⚠️ The denominators must be spelled out (the original omitted that middle column)**: the **items** column has all 14 items as its denominator, while the **accuracy** column has the **binary-ground-truth subset** as its denominator — so "5 items × 0.50" is arithmetically impossible. The original set the two columns side by side without marking that the denominators differ, and the reader cannot reproduce it.
**⚠️ And the original's summary figure cannot be reproduced from this table**: the original writes "binary items at threshold 0.5 → **5/10 = chance**", but this table's binary items sum to **9**; enumerating the (hits, total) combinations compatible with the rate column, the unique solution is **4/10 = 0.40**. Here it is corrected, per the reproducible value, to **4/10 = 0.40** (or the whole summary should be withdrawn).
- **Brier 0.359**, while **a constant predictor at 0.5 has Brier 0.25** → on **these 10 items that carry binary ground truth** (14 items in the whole battery), the mock's probabilities are **worse than the constant predictor**;
- **The original wrote "anti-information" — that wording is too strong and has been downgraded**: at n=10 the standard error of a Brier difference of 0.109 is about 0.10 (t ≈ 1.1, **not significant**). The correct statement is "**shows no information on this sample**";
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

- **`probability` is "the probability of the selected option", not P(true)** — recording `probability` as P(true) **will flip the sign of its half of the items**;
- **In the same response `band` points toward true** (0.02 → `"no"`), **while `probability` points toward the selected option** (0.98) → **the two "confidence-like" fields point in opposite directions**;
- Measured to satisfy `answer=="true" ⇒ probability==noul` and `answer=="false" ⇒ probability==1−noul`; **the third round confirmed this in both directions on live** (`true`→0.98/0.98; `false`→0.02/0.98).
  **⚠️ But this identity rules out less than it appears to, and must be qualified**: (a) the machine-readable evidence is only **7 rows** (`P27b`'s plugin route, and **hand-transcribed**), of which **only 1 row** (`answer=="false"`, noul 0.02 vs probability 0.98) actually does any discriminating work — the other 6 rows have `noul = 0.98` and `answer=="true"`, and the four candidate hypotheses are all equal to 0.98 on those rows, zero information;
  (b) **"P(the answered option)" and "the maximum of `probabilities`" are identical under this access layer and cannot be told apart** — for a 2-option `noul`, the access layer defines `answer` as `noul ≥ 0.5`, i.e. the **argmax**, so "the selected is the maximum" is **constructive** and holds at any value of noul; the same goes for `choice`/`score` (the selected level is always the argmax in `legend`). **So an access layer whose `answer` is always the argmax cannot, in principle, produce a row that tells the two hypotheses apart**;
  (c) hence this section **really establishes only one thing**: `probability` is **not** `P(true)` (ruled out by that 1 row). **The stronger reading "= P(the answered option)" is not established, and does not affect any conclusion** — the two are numerically identical, and either reading leaves every number in the paper unchanged.

### 3.4.1 ⭐ These three fields are **not supplied by the provider** (one direct-route measurement per primitive, three primitives) — direct evidence from the direct route

The third round built an independent HTTP direct route (`POST /api/v1/systemone`, `src\instrument\jev_client.py`) which takes **the same path** as the DSH plugin (same `noul`, same `input_tokens`, same `cost`, bit-identical). **The provider's raw response has only** `{model, provider, id, answers, usage}` **at the top level**, while **the keys inside the answer object change with the primitive** (one measurement per primitive, three primitives):

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
| `truncated`, `stateChars`, `questionsChars`, `redactions` | **the access layer's egress accounting** |
| `latencyMs` | **the access layer's own measured clock** |

⇒ **These three kinds of field (the singular `probability`, `band`, `answer`) and all the egress/latency fields are, under the three primitives measured (one call each), not supplied by the provider**; so **within the range observed** they are indeed synthesised by the access layer. **⚠️ The `check` and `rank` primitives were never measured (n=0) and cannot be extrapolated** — this section's attribution table is split by primitive precisely because attribution changes with the primitive.
⇒ But **`confidence` and `probabilities` (plural) are indeed returned by the provider in the single call each of `choice`/`score`**, and must not be mixed into the "self-reports are untrustworthy" list — **that distinction is itself this section's lesson: attribution must be measured field by field and cannot be extrapolated from one primitive.**
⇒ **⚠️ The amount of evidence must be reported alongside**: `choice` and `score` have **only n=1 each** in the whole `results\` tree (`P27d-primitive-fields.json` has 1 per primitive; `P27`'s provider-field list added only 1 `noul`; `P27b`'s 7 rows are **plugin-route `noul` rows, hand-transcribed by the AI**, and the artifact carries its own `transcription_risk` declaration). So this section's conclusion is "**not seen in these 3+1 observations**", not "the provider never returns them" — **a single observation is enough to establish "these keys do exist", and is not enough to establish "those keys never appear".**

⇒ **This is direct, on-line evidence for the paper's claim that "self-reported fields are untrustworthy"**: these fields are **not reported by the party under test**, but **synthesised by an intermediate layer**.
⇒ Hence the accurate statement of Result B is **about the access layer**, not about any engine's own protocol — consistent with the attribution statement in §3.1.1, and now with a mechanism-level proof.
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

**Design**: eight live `jev_check` calls, covering support / negation / **explicit conflict** / **symmetric conflict** / irrelevant / weakly relevant / hearsay / a single unattributed note.

| nature of the evidence | supports | contradicts | **sufficient** | verdict |
|---|---|---|---|---|
| verbatim support | 0.99 | 0.02 | 0.88 | `supported` |
| clear contradiction | 0.02 | 0.98 | 0.92 | `contradicted` |
| **explicit conflict** | 0.43 | 0.67 | **0.07** | **`insufficient`** |
| **symmetric conflict** | 0.55 | 0.67 | **0.14** | **`insufficient`** |
| completely irrelevant | 0.01 | 0.03 | 0.02 | `insufficient` |
| weak / hearsay | 0.22 | 0.10 | 0.08 | `insufficient` |
| a single unattributed note | 0.06 | 0.04 | 0.03 | `insufficient` |

**`sufficient` does not exceed 0.14 in any of the**5 `insufficient` calls** (**⚠️ Eighth-round correction**: the original printed "all 7" — but in this section's own table only **5** rows are `insufficient`, and the other two rows' `sufficient` values are **0.88** and **0.92**, **both greater than 0.14**. The error was inherited verbatim from `probes\P13-jev-remaining-measurements.md:60`, and has been recorded as audit finding m-8 in `protocol\AUDIT-FINDINGS.md:225`; the first draft was not synchronised)**, while the parser needs sufficiency ≥ a threshold (≈0.5) before it will give `undecided` / `conflicted`.

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
| 4 | field layer | `probability` is P(the selected option); it flips the sign of **every item answered `false`** (about half of that corpus), and points opposite to `band` |
| 5 | semantic layer | `conflicted`/`undecided` are in practice unreachable; conflict is reported as "insufficient evidence" |
| 6 | semantic layer | "not stated" is read as support (n=220) |
| 7 | semantic layer | under non-English text it does not separate true from false (n small, qualitative) |

> **Unified shape**: **this judge fails on the occasions where it "must notice an absence or a mismatch", and is near-perfect on the occasions where "the answer is explicitly stated"; in both cases the confidence it self-reports is not low.**

**These seven depend on no generator battery**, and on no long-horizon task either — they **all fall in the access layer** (see the attribution statement in §3.1.1 and §6.4.1). This section is therefore the **most robust and most reproducible** section in the whole paper.

---

## 3.9 Limitations

1. **Item 7's n is tiny** (2/12/2); only the qualitative shape;
2. **Item 1 is the behaviour of the mock provider**, not the behaviour of live Jev — its value lies in the **methodological warning**, not in an assessment of Jev;
3. **Items 2 and 3 were obtained under three loadouts, english/multilingual/typed-decisions**, and **all are three-checkpoint loadouts** — the window figures must be reported together with the launch loadout (see §4.8);
4. **Item 4's live verification is n=7 rows in machine-readable artifacts (plugin route, hand-transcribed), and only 1 of those rows has discriminating power**; the semantic rule (`probability` ≠ `P(true)`) is established by that row. **"= P(the answered option)" and "= the maximum of `probabilities`" are identical and indistinguishable under this access layer** (the selected is the argmax), so the paper claims only the weaker of the two. The 8/8 and the n=13 come from P12/P13's **report text, with no JSON artifact**, and are not used as a basis;
5. **Item 6 is n=220 per stratum, but the corpus is templated** — the absolute accuracy is not a capability estimate; what is usable is the **relative differences between difficulties and the shape of the calibration**;
6. **Not measured**: the exact truncation point of Jev's **plugin-side** 16,000-character constant (proved only up to 15,002; the vendor documentation's `state` limit of 32k token was not measured); the live behaviour of `rank`'s over-limit refusal.

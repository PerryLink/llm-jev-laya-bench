# §5 Results A — cost is not the constraint: a three-way measurement

*(English translation of `paper/05-results-A-draft.md` (§5 Results A). Faithful, not abridged: every hedge,
every ⚠️ marker, every blockquote, every n and every decimal place is carried across. Terminology follows
`paper/TRANSLATION-GLOSSARY.md`; field names, verdict vocabulary, artifact IDs, paths and statistics are left
untranslated. The draft's own audit annotations and their round numbers are retained. This section contains
no citation keys `[@key]`.)*

> The core move of this section is a **change of axis**: the paper therefore replaces the question "who is cheaper" with "**which axis actually separates the three**".

---

## 5.0 Why this section needs a change of axis

**The original plan**: to prove that "a decision model is cheaper than an LLM".
**The measured verdict**: **the claim is arithmetically meaningless** — the per-call cost of all three **sits at the 10⁻⁵ dollar order of magnitude**, while the design has only 120 checkpoints per run.

| Judge | Per-call cost | 120 checkpoints / run |
|---|---|---|
| **Laya** (local cuda, self-hosted) | **marginal ≈ $0** (compute only) | ≈ $0 |
| **Jev** (openrouter, `typesafe/jev-1.13`) | **$0.0000146 – $0.0002406** (8 measured points, **rising monotonically with input tokens**; within the design's state range **$0.0000146–$0.0000588**) | **$0.0018 – $0.0289** (within the design range **$0.0018–$0.0071**) |
| **LLM** (`deepseek-flash`, non-thinking) | **$0.0000326 – $0.00009645** (**the upper bound is the measured maximum over all 96 calls of P14**; $0.0000484 is the **mean**, and an earlier version printed it as the midpoint of the interval, whereas the upper bound $0.0000566 **is not the maximum of any batch** — this paper's own `_provenance` block had long since recorded the correct pair) | **$0.0039 – **$0.0116**** |
| **LLM** (the `max` setting, most expensive) | $0.0001010 | **$0.0121** |

→ **The most expensive combination (the LLM at the `max` setting) runs all 120 checkpoints for about 1.2 cents.**
→ **"Saving money" is not a defensible claim for this paper.** This section therefore **reports cost but does not treat cost as a conclusion**.

---

## 5.1 Cost: the measured numbers, and two qualifications that must be given together

**The LLM, effort tier by effort tier** (P21, n=6 per tier; peak price is 2× off-peak, recorded alongside):

| effort | mean completion tokens | **mean reasoning tokens** | mean cost (off-peak) | relative to non-thinking | p50 latency |
|---|---|---|---|---|---|
| **none** | 13.0 | — (the field does not exist) | **$0.0000398** | **1.00×** | 720 ms |
| **low** | 70.3 | 57.0 | $0.0000780 | 1.96× | 909 ms |
| **high** (default) | 84.3 | 71.2 | $0.0000864 | 2.17× | 916 ms |
| **max** | 108.7 | 96.3 | $0.0001010 | **2.54×** | 961 ms |

**Qualification one: reasoning tokens count toward the output price**, and account for **81–89%** of output (`max`: 96.3/108.7).
→ **Pricing by the visible answer alone would badly understate the cost** (V3's observation is confirmed here). But **the absolute quantity is small** (about 100 token), so the multiple is limited.

**Qualification two: the peak/off-peak price gap is exactly 2×** (first-hand source: [DeepSeek pricing page](https://api-docs.deepseek.com/quick_start/pricing/); cache hit $0.003 / miss $0.15 / output $0.60 are the off-peak prices, peak is 2× those, and the peak hours are UTC Monday–Friday 01:00–04:00 and 06:00–10:00). → **A cost must be labelled with its time period**; reporting only one tier is a choice the reader cannot audit.

**Jev's billing difference (important, and it overturns an earlier assumption)**:
- **On the TypeSafe route, `costUsd: 0` means "not reported", not "free"**;
- The **OpenRouter route this project actually uses does report a real `costUsd`**, and **bills output tokens** (measured 20 token per call).
→ **The two routes' billing models differ, and a single cost table must not be used for both.**

---

## 5.2 Latency: **this is the axis that separates the three**

| Judge | p50 | mean | max | n | Qualification |
|---|---|---|---|---|---|
| **Laya** (local cuda) | **37.4 ms** (wall-clock median; self-reported 30.0 ms) | — | **—** (see footnote 4) | 30 | **batch size 1**; **wall clock** |
| **LLM** (non-thinking) | **671 ms** | 699 ms | 1,008 ms | 48 | direct API, **client-side wall clock** (`deepseek_client` wraps the HTTP call in `perf_counter`) |
| **Jev** (openrouter) | **1,192 ms** (n=20, **the only run with an artifact**; the pooled n=35 median is 1,073 ms) | 1,551 ms | 4,019 ms | **20** | **wall clock; a single sampling, see footnote 1** |

→ **p50 spans about 25–32×** (37.4 ms → 671 ms → ~0.9–1.2 s). **The interval can only be taken from artifact-backed numbers: the lower bound of 28.7× from the pooled n=35 median (1,073.4 ms), and the upper bound of 31.9× from the one run that has an artifact (n=20, p50 1,191.8 ms)**. **⚠️ An earlier version wrote here that the lower bound came from the first run and the upper from the second — that two-run account was withdrawn in the seventh round (915.1 ms is the pre-repair value of a derived field, not a run), so 24.5× is withdrawn along with it**: the 915 ms it depends on exists only in an early report whose **artifact was not kept**. **The direction favours the local judge**, but **the single run on this axis is not reproducible** (see footnote 1).

**⚠️ Four points must be stated at the same time, and points 1 and 3 are our own errors corrected in this round**:
1. **⚠️ Jev's latency column has only one run with an artifact; the "two independent runs" claimed by an earlier version does not hold (seventh-round withdrawal).**
   **The facts**: `results\P27-jev-live.json` records **n=20, p50 1,191.8 ms, mean 1,550.6 ms, max 4,018.6 ms** — **this is the only live run with an artifact**. The "first run 915 / 1,001 / 1,802 ms" printed by an earlier version **is not a run**: `915.1` is the **pre-repair value** of `unmatched_direct_for_reference.p50_ms` in `P27b-plugin-crossval.json`, and that field is itself a **copy** of P27's `latency.p50_ms`; after the repair re-read that copy, it became 1,191.8. **No artifact in the whole tree records a Jev latency run at p50 = 915**, and the latency block of P27's copy in `_superseded\` is **bit-identical** to the current one.
   **And "+30% / +55% / +123%" are also not comparable in the type of statistic**: they respectively subtract a **pre-repair p50** from a **post-repair mean**, and a **single max** from a **pooled max** — even if two runs had really happened, these three differences are not a run-to-run range.
   **What can be said**: one run with an artifact; the pooled n=35 median of 1,073.4 ms (`P27-summary`, **pooled from two collections of different states, n=20 and n=15**); and that **an early report recorded 915 ms while the artifacts did not retain that run** — **this is a documentation gap, not a measured reproducibility conclusion**.
   (The previously printed **938.6 ms / 25×** came from an old summary that pooled the first run with `P27c`; recomputed against the current artifacts it is **1,073 ms / 28.7×**. Both numbers are kept here, **because they are themselves the evidence that this axis is not reproducible**.)
2. **All three are in fact client-side wall clock** (Laya times locally; the LLM's HTTP is wrapped in `perf_counter` by `deepseek_client.py`; Jev is timed by this client) — an earlier version of the paper wrote the LLM column as "provider self-reported", and **that was wrong**. So this ladder is a **same-basis** comparison.
3. **But this axis mostly measures network topology, not the judge's inference cost**: R13's **unauthenticated 403 rejection** round trip is **1,011–2,349 ms**, **≥ Jev's p50** — that is, **a round trip with zero inference already reproduces the entire Jev difference**. So the correct reading is: **local vs remote** differs by about 25× (real and stable), while the **remote vs remote** stretch **is not a property of the judge**.
3. **Jev was originally printed as 1,380 ms (n=13), and that was the plugin's self-reported value.** The third round built an independent direct HTTP route, and measured both on the same route and on **same-size states**:

| Measurement | n | p50 | min | max |
|---|---|---|---|---|
| Plugin self-reported `latencyMs` (state 128 characters) | 7 | **1,851 ms** | 1,233 | 3,141 |
| **This client's wall clock (state 126 characters, size-matched)** | 5 | **956 ms** | 855 | 2,172 |

⇒ **The plugin's self-reported latency is about 1.5-1.9× the independent wall clock** (**⚠️ Eighth-round correction: this ratio is not a stable number.** It is a ratio between two LATENCY measurements, and section 5.2 itself establishes that Jev's latency is the quantity that does not reproduce -- same state, same n, same cost, same token count: p50 1,191.8 -> 952.9 ms (-20%), max 4,018.6 -> 6,360.4 ms (+58%). **The size-matched rung is intact** (126 characters / 347 tokens / n=5 in both runs); what moved is that rung's own p50, 956.2 -> 1,244.8 ms. The correct statement is therefore **about 1.5-1.9x**: **1.94** against the pre-repair artifact and **1.49** against the current one. **The section's substantive finding is unaffected**: p50 stays roughly flat across a 127x state increase, in the same direction in both runs (+12% published, -10% re-run) -- **the SHAPE reproduces; only the level moves with the environment, by 4-33%**.) (**same-size state** compared).
**⚠️ Three limitations**: (a) the two groups were **not collected as a paired batch** (n=7 vs n=5), so the gap may contain network drift; (b) the paper's own **unauthenticated 403 rejection control** (1,011–2,349 ms, and measured at `api.typesafe.ai` rather than openrouter) **overlaps the plugin's self-reported interval (1,233–3,141 ms)**, so that control **weakens rather than supports** the "plugin overhead" reading; (c) so this is recorded only as a **flag pending verification**, not a conclusion. **This table uses the wall-clock values.**
4. **Laya's max is left blank**: an earlier version of the paper printed **4,864 ms** in that cell, but that is an outlier of the **`P1` probe (n=18, median 26.4 ms)** and **does not belong to this row's R13 n=30 series** (whose max is 50.5 ms) — **two batches of samples were once mixed into one column**, and it has been deleted. No long tail was measured on R13's n=30, so this row's max is left blank.
5. An even earlier version of the paper also printed **n=23 / p50 1,408 ms / mean 2,372 ms / max 12,055 ms** — these four numbers **have no source anywhere in the tree** and have been deleted; and P13's summary mean of 1,879 ms is **arithmetically impossible** (with n=13 it admits no solution together with min 919 / max 11,984; see `results\ERRATA.md` N-1), and **has likewise been deleted**.

→ This **is** the real selling point of "a small local judge": **not saving money, but saving time.**

### 5.2.1 Jev's latency is dominated by **transmission** — essentially flat across a 127× state range

**Independent wall-clock measurement** (`P27c`, 5 per point):

| State characters | Input tokens | **p50** | min | max |
|---|---|---|---|---|
| 126 | 347 | **956 ms** | 855 | 2,172 |
| 7,896 | 1,400 | **881 ms** | 864 | 1,897 |
| 15,999 | 2,495 | **1,073 ms** | 939 | 1,873 |

⇒ **The state is magnified 127×, and p50 moves only from 956 to 1,073 ms** ⇒ latency is dominated by **transmission**, not determined by state size.
- **Key control**: the **unauthenticated 403 rejection** round trip measured by R13 is **1,011–2,349 ms**, the **same order of magnitude as a real call** ⇒ **this axis mostly measures network topology, not the judge's inference cost**.
→ **We must not write this latency as an intrinsic property of the judge** — it varies with network location.
→ **Protocol clause**: when reporting a remote judge's latency, one must (a) **state the measurement point** (wall clock or self-reported), (b) attach a **control round trip that performs no inference** (such as a 403 rejection), and (c) **not take the latency self-reported by the party under evaluation on trust without an independent measurement** — this section's Jev column was corrected by about 2× for exactly this reason.

### 5.2.2 Laya's latency must carry the batch size

| Batch size | Amortised per question |
|---|---|
| 1 | **30.0 ms** (wall clock 37.4 ms) |
| 5 | 6.0 ms |
| 10 | 3.9 ms |
| 20 | **3.2 ms** |

→ **Batching amortises by about 9×.** But **two-plane replay has only one question per state, so the batch size is forced to 1** — quoting 3.2 ms would be **11.7× optimistic** (against the wall-clock median of 37.4 ms; against the table's own amortisation basis of 30.0 ms it is **9.4×** — **the two bases must not be mixed**, and the "12×" printed by an earlier version came precisely from dividing the wall-clock value by the self-reported batch value).
→ **Mandatory clause: latency must always be reported together with the batch size and the device.**

---

## 5.3 The state window: the second axis of separation

| Judge | Largest state at which the decisive evidence is still usable | Failure mode |
|---|---|---|
| **Laya** (english, three-checkpoint loadout) | **~3,082 characters** (the 512 token clamp) | **silently discards the tail**; `truncated` lags by 111 characters |
| **Jev** (the **access layer** window) | **≥15,002 characters** (plugin); **the direct route accepted 39,927 characters in measurement** | accommodates, or **warns** |
| **LLM** | 1M context (documented) | not applicable |

**⚠️ The "16,000-character cap" has been shown by measurement to belong to the access layer (the plugin), not to the provider.**
The third round built an independent direct HTTP route (`P27`) and pushed the state ladder to **39,927 characters**:

| State characters | 1,965 | 7,959 | 14,952 | 15,951 | 16,395 | 23,943 | **39,927** |
|---|---|---|---|---|---|---|---|
| Input tokens | 598 | 1,408 | 2,353 | 2,488 | 2,548 | 3,568 | **5,728** |
| `noul` | 0.97 | 0.97 | 0.97 | 0.97 | 0.97 | 0.97 | 0.97 |

**The evidence is token accounting, not an assertion of "no truncation"** (this point must be stated clearly):
- On this **route there is no `truncated` field** to consult (§6.4.1), and that probe appended the inert padding **only at the tail, leaving the decisive content at the head** — so it **is blind to "the tail was silently discarded" itself**, and it cannot be used to claim "no truncation".
- **But input tokens grow monotonically with character count**: character increments of 5,994 / 6,993 / 999 / 444 / 7,548 / 15,984 correspond to token increments of 810 / 945 / 135 / 60 / 1,020 / 2,160, **invariably about 12 token / 111 characters**. **Any fixed character cap would freeze the token count above the cap — it did not.**
⇒ So the conclusion holds: **the cap is the plugin's**. But **the provider-side true cap is still untouched** (no rejection point was found, and no trial with the decisive content at the tail was run).

**The same construction** (`DECOY + filler + CORRECTION`, **with the decisive content placed at the very end**):

- **Laya loses the evidence at ~3,082 characters and the answer flips wrong**, while `fits: true`, no `truncated`, no warning;
- **Jev still takes the tail evidence at 15,002 characters and answers correctly** (0.97); **the third round's direct route demonstrated it further at 39,927 characters** (§5.3).

→ **A gap of about 4.9× (counted against the access layer's 15,002; the provider-side cap is untouched, so this multiple can only grow and never shrink), and the failure modes are fundamentally different: Laya silently discards input, Jev either accommodates or warns.**
→ **This is the substantive basis for D1's ruling that "Jev is irreplaceable"**, and it now has measurement behind it.

**Must be reported together with the launch loadout and the checkpoint queried** (§4.8): for the same code, english loaded alone → clamp **1024**; english under a three-checkpoint loadout → **512**; whereas multilingual and typed-decisions on the same machine are still **1024**. (P18 launched each loadout only once, **no determinism repeat was done**.)
→ **"Laya's window is 512 token" is an incomplete statement, and for another operator it may be wrong by a factor of 2.**

### 5.3.1 How the window erodes in a real cumulative run (P24)

**Setup**: 3 sessions × 20 steps, each step appending one record to a **carried ledger**; each step asks one question of each of the two judges.

| Metric | Value |
|---|---|
| Total steps | 60 |
| **Steps that can be asked within the window** | **14 / 60 (23%)** |
| **First overflow** | **step 14** |
| Final state | **1,751 token / 6,875 characters** = **3.4×** the clamp |
| Laya per-session accuracy | session 0: 1.000 (n=14, **6 steps skipped**); sessions 1 and 2: **n=0, all overflowed** |
| LLM per-session accuracy | **1.000 / 1.000 / 1.000** (n=60) |

→ **In a 60-step cumulative run, the local judge is usable for only the first 23%.**
→ **The LLM is 1.000 in all three sessions** — **accumulation caused no drift on this task**, but this **hits the ceiling once again**, so **one cannot claim on this basis that the LLM is unaffected by accumulation**.

### 5.3.2 Whether truncation **changes the answer**: **could not be measured** (P26, with a position confound)

P24 only shows **when the window runs out**; P25 tried to measure "whether running out harms judgment", but **the probe was invalid** (the question stated the answer outright, and the deletion control was 0/6).
P26 redid it after applying the **certificate** — the decisive content is a **narrative correction** located at the **tail**, the question **asks only for the conclusion**, and **the question text contains neither v0 nor v1**; the only difference between the two arms is **whether that correction is present**.

State **1,969–1,982 token** vs the **512** clamp:

| Cell | n | **Selected the "pre-correction" value** | Answered the "post-correction" value |
|---|---|---|---|
| **full (correction present) — Laya** | 10 | **10 / 10** | **0 / 10** |
| dropped (correction deleted) — Laya | 10 | 10 / 10 | 0 / 10 |
| **full — LLM** | 10 | 0 / 10 | **10 / 10** |
| dropped — LLM | 10 | 10 / 10 | 0 / 10 |

**How to read it** (counter-intuitive, and it must be stated): the dropped arm answering the "pre-correction" value **holds by construction** (there is no correction in that arm), so **the diagnostic quantity is not "full is better than dropped" but "can full tell the two states apart"**.

**⚠️ This probe has two fatal design defects; an earlier version claimed that "the missing control was added during review", but that control was *not persisted*, and its numbers have been withdrawn (seventh round).**

**Defect one (the more fundamental): the two arms' visible prefix is completely identical ⇒ "the two arms answer alike" is a necessary consequence of the construction, not a measurement.**
The dropped arm deletes only the `[c1]` line, and the state still has **1,955–1,965 token ≈ 4× the clamp**. A token-by-token check: **the first 512 token ids of the two arms are completely identical on 10/10 items**, while the position of the correction is token **1,943–1,952**. **【NOT TRACEABLE ⚠️ ERRATA §10.2】**: that token position has no `results\` artifact (see the note at §8.7(a)); the "first 512 token ids are identical" part **is indirectly supported by P26's `in_pad` and option records**, but the absolute position is not.
⇒ The truncation happens beyond the two arms' **common tail**, and the visible content fed to the judge is **bit-identical** in the two arms. "The two arms give the same answer" therefore **holds by force of construction**, and carries **zero information** about "whether truncation changes the answer".

**Defect two: the option order is perfectly collinear with the answer.** The options are generated by `sorted({v0, v1, v0+77})`, and `v0 < v0+77 < v1` always holds ⇒ **the decoy is always o01 and the ground truth is always o03**; Laya picks **o01** (first position) in all 10/10 rows. The position effect in this paper's own measurement in §4.5 (first position 1.00 vs 0.125 for the others) **is sufficient on its own to explain** this result.

**The control that was added (originally missing from this paper, newly added during review)**: **remove the padding** so that the correction falls **inside** the window (state **79–92 token**, `truncated = false`):

| Cell | n | Answered the "post-correction" value | Answered the "pre-correction" value |
|---|---|---|---|
| Truncation arm (P26's original design, 512 clamp) | 10 | 0 / 10 | **10 / 10** |
| **Control arm (padding removed, correction visible)** | 10 | **6 / 10** | **4 / 10** |

⇒ **Truncation does raise the proportion answering "pre-correctio**WITHDRAWN in the seventh round**: an earlier version asserted a control-arm result at `p = 0.011`; that arm has no artifact and its state size matches P26's discarded prototype, so the figure is withdrawn.
⇒ **⚠️ This item's quantitative decomposition has been withdrawn (seventh round)**: an earlier version wrote "about **6/10 of the effect comes from truncation**, and the other **4/10 is "the correction was fully visible yet not adopted"**". **These numbers (6/10, 4/10, state 79–92 token, Fisher p = 0.011) have no artifact anywhere in the whole tree** — no row, no script, no cost record; they exist only in the paper's body text and in `protocol\AUDIT-FINDINGS.md`; **and their state size is exactly equal to the state size of P26's own *discarded first prototype***, whose report reads, verbatim, "there was nothing to truncate at all". **This tree cannot distinguish "a new control run" from "the numbers of a discarded prototype".**
⇒ **What can be said now**: P26's artifacts show that **the two arms are bit-identical over the 512 token visible prefix** and that the correction lies outside the window (**a necessary consequence of the construction**); **"truncation happens" has artifact support** (P24: only 14 of 60 steps fit into the window; P26: all 20 calls have `in_pad = 512`, `truncated = true`).
⇒ **What cannot be said**: "truncation changed the answer" — that would require a control that moves the correction into the window and **is persisted**. So this item is **downgraded to "truncation does happen, and its harm could not be separated from the position effect"**.

→ Therefore the two earlier statements must both be qualified:
1. **Truncation does happen** (holds independently): all 20 calls have `in_pad = 512`, `truncated = true`; P3 further proves that after the clamp the output is frozen bit-for-bit.
2. **WITHDRAWN**: an earlier version wrote that truncation does raise the error rate (0.40 -> 1.00, p = 0.011). **That control arm has no artifact**, and its state size matches P26's discarded prototype. **What still holds**: P26's original "both arms answer alike" design is a construction necessity and establishes no causation.
3. The LLM's full 1.000 / dropped 0.000 only reflect **whether the correction text appears in the state** (the LLM's context is 1M and is never truncated), and **do not constitute a control for the consequences of Laya's truncation**.

**Ruling (revised in the seventh round)**: **truncation happens (P24, artifact-backed)**; **but the control arm behind "truncation raises the error rate" has no artifact, so that causal claim is NOT asserted.** An earlier version ruled that it "also raises the error rate (this control arm, p = 0.011), but it is a partial cause" and cited "a further 4/10 of failures occurred with the evidence fully visible" -- **both numbers are withdrawn with that arm**. => **Final ruling: truncation does happen; its harm was not separated from the position effect.**

---

## 5.4 This section's conclusion: the constraint is **latency and window**, not dollars

| Axis | Degree of separation | Direction |
|---|---|---|
| **Per-call cost** | all three in the 10⁻⁵ dollar range; **no substantive separation** | — |
| **Latency** | **p50 spans about 25–32×** (37.4 ms → 671 ms → **0.9–1.2 s**; the lower and upper bounds are taken from the pooled n=35 median and from the one run that has an artifact, respectively -- **the two-run account was withdrawn in the seventh round**); Jev's pooled measured max is 4,018.6 ms | favours local |
| **State window** | **about 4.9×**, and the failure modes differ (silent vs warns) | favours remote |
| **Failure observability** | Laya **silent**; Jev **warns** | favours remote |

→ **The central claim is restated as**:
> **In long-horizon tasks, the benefit of handing judgment to a small local judge is not in cost (cost was never the constraint), but in that it does not occupy a sequential round trip; the price is that its usable state window is an order of magnitude smaller, and that it fails silently when it goes out of bounds.**
> **⚠️ The long-horizon part of this claim is verified only by a reduced version** (P24: 3×20 steps within the same process; **autonomous long-horizon runs were not executed**, see §10.1) — the item "does not occupy a sequential round trip" holds at the **single-step** level and is untested at the **long-horizon** level.

This statement is **narrower and harder than "cheaper", and it avoids the point most easily rebutted**: an LLM can also use context caching to push its input down to $0.003/1M, so "the LLM is expensive" does not stand up arithmetically.

---

## 5.5 Limitations

1. **Both cost and latency are descriptive**: LLM n=48, **Jev n=35**, Laya n=30, and **one machine, one network path, one collection period**.
2. **Jev's and the LLM's latency includes transmission**, so **it must not be treated as a quantity of the same kind as Laya's local latency** — all three carry a qualification.
3. **Whether the collection period fell on peak or off-peak pricing was not recorded**, so the cost numbers may vary with the time of the run (peak/off-peak gap 2×).
4. **Laya's cost is not monetised** (self-hosted compute), so "≈$0" is a **marginal** cost and excludes hardware amortisation. **We must not claim on this basis that Laya is free in every sense.**
5. **The LLM's 1M context is a documented value, not measured**; Jev's **plugin-side 16,000-character constant** is only proved up to 15,002 (the vendor documentation's `state` cap is 32k token, **not measured**).
6. **Not measured**: the LLM's cost and latency at long state (its cost is $0.15/1M for uncached input, and will change substantially on long tasks).

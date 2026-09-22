# §9 Discussion: if you are going to use a judge of this kind, what should you do

*(English translation of `paper/09-10-11-discussion-limits-repro-draft.md` (§9 Discussion, §10 Limitations,
§11 Reproducibility), carried in one file: §9 first, then §10, then §11. Faithful, not abridged: every hedge,
every ⚠️ marker, every ⬜, ✅ and ❌, every n and every decimal place is carried across. Terminology follows
`paper/TRANSLATION-GLOSSARY.md`; field names, verdict vocabulary, artifact IDs, paths, statistics and model
IDs are left untranslated. Cross-references `§N.M` are reproduced exactly as the Chinese draft writes them,
so that `paper/_assemble.py` remaps them identically in both builds. The draft's own audit annotations and
their round numbers are retained. The source contains no citation keys `[@key]`.)*

This section gives only recommendations that are **supported by measurement**, each with its basis and its
cost stated. We do not write engineering opinions that have no evidence behind them.

## 9.1 Put input validation in the harness, not in the judge

**Basis**: Laya returns `ok: true`, **no error, no warning, `fits: true`** for an **empty state and a
pure-noise state** (R13). For empty input it still gives `choice: "technical"`.
**Basis two**: the `no_support` stratum (n=220) — **when the candidate value does not appear at all, it
returns a mean P(true)=0.564**.
**What to do**: reject empty / low-information states before the call, and **explicitly check "does the
evidence actually exist"**, instead of letting the judge answer a question for which it has no detection
channel.
**Cost**: it requires harness-side implementation, and "exists" has to be defined for every task class.

## 9.2 Never gate on a self-reported field; always compute it yourself

**Basis**: `truncated` **is wrong in both directions** (english lags by 111 characters; multilingual
false-positives **4,773** characters early; typed-decisions **3,774** early) (§3.2). All three checkpoints'
flags fire at **the same point, 3,193 characters**, while their real clamps differ by **a factor of 2**.
**Basis two**: `fits: true` and **input that has already been truncated** can hold at the same time (§3.3).
**What to do**:
- **count with the checkpoint's own tokenizer**, and compare against `512 − head_tokens − 1`;
- treat `truncated`/`fits` as **descriptive reporting only**, and **also report the "flag error"** metric;
- **put the decisive evidence first** — what Laya discards is the **tail**.

## 9.3 Do not compare confidence across systems or across framings

**Basis**:
- Jev's `probability` is **P(the selected option)**, not P(true) — recording `probability` as P(true)
  **reverses the sign of every item answered `false`** (measured: **29.8%**, 328/1100; the LLM on the
  same corpus is **60.0%**, 660/1100 — **neither is "about half"**; source `P19-calibration.json`, see §6.4); and **in the same
  response `band` points toward true while `probability` points toward the selected option** (§3.4);
- the LLM's `prob` is **the confidence of the label it answered**, the same trap (this project stepped on
  it once on each side);
- Laya's `confidence` is a **concentration statistic**: the same p under different framings is **0.5399 vs
  0.0046** (a 117× difference).
**What to do**: **record only the quantity oriented toward true** (for Jev record `noul`; for the LLM
record P(true) derived from the label); **report the full distribution** rather than the winner.

## 9.4 Choose tasks by "will it notice an absence", not by "is it accurate"

**Basis** (§6's unified shape):
| Task shape | Laya, measured |
|---|---|
| the answer is explicitly stated | **0.9909** (n=220) |
| requires finding an authoritative source | 0.4583 (n=48) |
| the evidence does not exist | **0.3091** (n=220) |
| requires semantic interpretation (77 classes) | 0.0333 (n=30) |
**What to do**: **treat "does the evidence exist" as a first-class check**; on these judges, do not deploy a
pipeline that says "a judgment should be given even when the evidence is missing".

## 9.5 If you need a large state, reconsider the loadout

**Basis** (P18, one launch per loadout; **no repeated launches were done, so we do not claim determinism**):
| Checkpoints loaded | Usable window |
|---|---|
| **1** | **1024 token** |
| **≥2** | **512 token** |
**What to do**: **loading only one checkpoint doubles the usable window**, at the cost of losing the
multilingual and specialised checkpoints.
→ **And the window must be recorded together with the launch loadout** — "window = 512" may be wrong by 2×
for another operator.

## 9.6 Hybrid architectures: do not assume complementarity, measure it first

**Basis** (§7): on **three** regimes, the heterogeneous judge provided no **established** incremental coverage —
- regime one (authority location, n=48): on the **forced-choice arm** it **caught none** of the items the LLM
  missed (judge-only correct **0**, against LLM-only correct **26**); **⚠️ but on the same 48-item battery's
  prose arm the LLM errs on 2 items and the judge catches 1 of them, Δ_catch = +0.0435 (interval containing
  0)** — so the wording here can only be "no established incremental coverage", not "no incremental
  coverage" (§8.2);
- regime two (77-class intent classification, n=40, **4 draws of the LLM arm**): judge-only-correct **0–2**
  items against LLM-only-correct **23–27**, **Δ_catch negative in 4/4 draws** (−0.033 / −0.250 / −0.029 /
  −0.257); the judge's accuracy is bit-identical across the 4 (0.225);
- regime three (multi-hop chained verification, **re-judged after the ground-truth fix**, n=68, **3 draws**):
  LLM **0.662–0.677**, judge **0.294**, **Δ_catch = −0.182 to −0.247**, **under an unpaired Wald interval 2
  of the 3 exclude zero, but that interval is spuriously narrowed by a zero cell; under Newcombe only 1
  robustly excludes and 1 sits at the boundary**, **failure correlation φ = +0.19…+0.26**; `P(judge correct
  \| LLM wrong)` = 0.13–0.17, **below** its marginal of 0.294 ⇒ **consistent with shared failure** (but
  Fisher p = 0.049/0.086/0.163, significant in only 1/3);
  **⚠️ But MDE = 0.28–0.30, still larger than the pre-declared +0.10 gate ⇒ the point estimates are
  consistently negative, yet the precision remains limited.**
**What to do**:
- **before choosing "a cheap first tier + escalation", run a paired complementarity measurement**;
- the criterion is **the sign of Δ_catch**, not the count of "first tier only correct";
- if the first tier **provides no incremental coverage**, it is **a worse second tier** and should simply be
  removed — **the latency advantage is not enough to compensate** (§8.3.1: the tier is a **net gain** for
  Laya, but end-to-end it is only **0.200**, far below the LLM's flat 0.750–0.900).

## 9.7 One honest sentence about "long-horizon"

**This project's long-horizon evidence is a "reduced version", not a complete autonomous run.** The horizon
slope was **downgraded to descriptive** by D2's ruling, and **was not executed**.
P24 provides a **cumulative measurement of 3×20 steps inside the same process** (window erosion 23%, final
state 3.4× the clamp); P26 demonstrated **that truncation does happen** (all 20 calls `in_pad=512`,
`truncated=true`), but **because the option order was perfectly collinear with the answer, it could not
demonstrate that truncation changed the answer** (§5.3.2).
But there was **no tool use, no cross-process resumption, and the judge was invoked in the judging role
rather than as an autonomous agent**.
→ The recommendations of this section **rest on single-step judgments and reduced-version accumulation**,
and **must not be upgraded into a conclusion about "autonomous long-horizon running"**. ⬜

---

# §10 Limitations

## 10.1 Experiments not executed (by importance)

| # | Not done | Impact |
|---|---|---|
| 1 | **A complete autonomous long-horizon run** (cross-process resumption, tool use, multi-session scheduling) | the central theme, "long-horizon", **is validated only by the reduced version** (P24, 3×20 steps in the same process); **the reliability of autonomous running was not measured** |
| 2 | **The error-compounding curve over a long horizon** (`token_ratio(t)` along a real run, drift across sessions) | P24 measured window erosion and no drift in the LLM (at ceiling), but **no dose–response was done** |
| 3 | **The calibration curve covers templated items only** | usable for **differences between curve shape and difficulty**, **not usable for estimating absolute capability** |
| 4 | ~~the LLM's logprobs ladder~~ | ✅ **Completed** (P23): verbal and internal probabilities agree (difference −0.0033) |
| 5 | **The prompt-variant band (P1–P4) was not run** | R16's anti-strawman requirement is **unmet**; the LLM arm used only one wording |
| 6 | **Multilingual mis-routing was not tested** (and it has been corrected: this interface does no routing) | we **must not** make any statement about the plugin's Python `Router` |
| 7 | the exact truncation point of Jev's **plugin-side** 16,000-character constant | proved only up to **15,002** (the vendor documentation's `state` cap is 32k token; not measured) |
| 8 | the live behaviour of `rank`'s over-limit rejection | the formula comes from the mock (it agrees across 4 points); **not re-verified on live** |
| 9 | the abstention comparison | **unavailable for every judge**: neither the LLM's nor Laya's option set has an abstain channel; Jev's check has one, but the semantics differ |
| 10 | **Repeated sampling of the remaining LLM arms** | P14 (authority location), P19 (n=1100 calibration), P21 (thinking cost), P23 (logprobs), P24 (horizon) **are still single draws**. The two complementarity regimes have been changed to `temperature=0` × 3–4 draws with agreement reported; the rest have not, and **their point estimates should not be read as precise values** |
| 11 | ~~Jev's live reproduction~~ | ✅ **Completed** (round three, P27): an independent direct-HTTP route was built (`src\instrument\jev_client.py`), **field-by-field identical** to the DSH plugin at the same state size; it produced **5 JSON files** (latency n=35, cost by tier, the two-way `probability` semantics, the per-primitive field inventory, derived summary). **Jev's column now has machine-readable artifacts.** Not touched: **the provider-side window cap** (proved only that at 39,927 characters tokens still grow monotonically with characters) |

## 10.2 Methodological limitations

1. **A single LLM configuration**: `deepseek-flash`, non-thinking mode. **Not tested**: `deepseek-v4-pro`, a
   self-consistency sampling arm, the quality difference under thinking mode (because the corpus is at
   ceiling, **all four P21 tiers have accuracy 1.00, so "does thinking buy quality" cannot be answered**).
   → **The sampling protocol has been partly tightened**: the two complementarity regimes (P15, CHAIN-AUDIT)
   are now **repeatedly sampled 3–4 times at `temperature=0`** with the item-level label agreement reported.
   **The remaining LLM arms (P14, P19 calibration, P21 cost, P23 logprobs, P24 horizon) are still single
   draws**, and their point estimates likewise must not be read as conclusions at the four-decimal level;
   this clause has been entered in §10.1.
2. **One machine, one device, one network path, one collection period**: latency and cost **vary with
   location and period** (a 2× peak/off-peak price spread; the collection period was not recorded).
3. **Laya's cost is not monetised**: self-hosted compute; "≈$0" is a **marginal** cost and excludes hardware
   amortisation.
4. **Several conclusions rest on synthetic/templated items**: absolute accuracy is not a capability estimate.
5. **n is extremely small for the cross-language items** (2 each for English and Russian): qualitative only.
6. **The hierarchy grouping is procedurally generated** (label-name token similarity): **the quality of the
   top-level grouping is itself the bottleneck** (group selection 0.275). **A semantically better grouping
   might improve Laya's end-to-end** — this is the explanation §7 least rules out.

## 10.3 On the scope of "a component with no judgment capability produces a credible results table"

This conclusion rests on **Jev's mock provider**, that is, a **deliberately constructed synthetic backend**.
→ **Its value is a methodological warning, not an assessment of Jev.** We must not let it be read as "Jev is
unreliable".
→ But it **extrapolates to any judging component that returns probabilities**: there is no distinguishable
difference between the mock and a real judge in **the shape of the results table** — that is exactly where
the danger lies.

## 10.4 The list of what cannot be extrapolated

| Cannot be said | Because |
|---|---|
| "Jev/Laya are generally worse than the LLM" | only **three** regimes were measured: the first two put the LLM at ceiling (**not measurable**), the third had its ceiling broken and was **re-judged after the ground-truth fix** (n=68), where Δ_catch is negative in 3/3 draws but **the precision is limited** (MDE = 0.28–0.30) |
| "No complementarity exists under any circumstances" | as above; the negative result holds only on the regimes measured, and the third regime **lacks the power to exclude** a moderate effect (MDE far larger than the pre-declared threshold of +0.10) |
| "Laya's window is 512 token" | it is a function of **"launch loadout × checkpoint queried"**: 1024 when english is loaded alone, 512 when three are loaded, while multilingual/typed-decisions is still 1024 under three loads |
| "The architectural claim has been falsified" | all one can say is that **no complementarity was found**, and that the third regime is **consistent with "shared failure" but did not reach significance** (Fisher p = 0.049/0.086/0.163) |
| "Perceptrons are generally unreliable" | not tested; this paper does not touch it |
| "On cost the judge is cheaper" | all three sit in the same 10⁻⁵ order of magnitude; and the LLM can use caching to push input down to $0.003/1M |

---

# §11 Reproducibility

## 11.1 Instrument freeze

**The instrument under test is a work tree under active development**: during this session `worker.py` was
rewritten **three times** (source: the self-account in `src\instrument\laya_client.py`, and
`planning.py / worker.py / server.py` rewritten at **18:16–18:17**), and **two entry points were at one time
serving different revisions at the same time**.

**Disposition**:

| Mechanism | File |
|---|---|
| **Six instrument hashes** (per-file SHA256) | `protocol\INSTRUMENT-FREEZE.json` |
| **Immutable snapshot** (13 `.py` + 2 config) | `protocol\instrument-snapshot\` (including `PIN.json`) |
| **Pinned launcher** (asserts that `laya_mcp.__file__` falls inside the snapshot, and exits on failure) | `src\instrument\run_pinned_sidecar.py` |
| **Every result carries its own instrument record** | `laya_client.instrument_record()` is written to disk alongside the result file — ✅ coverage **39/42**, the other 3 being **purely derived files** (no measurement to attribute), **unexplained gap 0**; the count is derived by `src\analysis\p30_inventory.py`, not hand-written. **⚠️ But the LLM arm's client `deepseek_client.py` still has no file hash of any kind** |
| ~~**Drift abort**~~ | ❌ `laya_client.assert_instrument()` has **zero call sites (dead code)**; the related claim in an earlier version has been deleted |

**This mechanism has actually been used**: all three launches P16–P18 printed the import path that passed the
assertion, and ran on **independent ports** (8791–8794), without disturbing the host harness's 8787.

## 11.2 Versions

| Component | Version / identifier |
|---|---|
| Laya | `0.3.4` / `laya-mcp 0.1.0`, sidecar `0.2.1`; checkpoint `convaiinnovations/laya` (english / multilingual / typed-decisions) |
| **Launch loadout** | `--model english --also multilingual --also typed-decisions --device cuda --max-len 1024 --head-max-len 512` (**the window is decided by this, see §5.3**) |
| Jev | `typesafe/jev-1.13-20260917` (**a specific dated version**, not `jev-latest`) |
| LLM | `deepseek-flash` (DeepSeek-V4.1-Flash), `thinking: disabled`, `reasoning_effort` noted per experiment |
| Device | RTX 5060 Laptop (8,151 MiB, sm_120), Intel Ultra 7 255HX, torch 2.11.0+cu128 |

## 11.3 Data and ground truth

- **Ground truth is computed by construction**: no human annotation, no model annotation (the 1100-item
  calibration corpus and all the item families are decided entirely by the generator's bookkeeping);
- **Public data serves only as secondary evidence**: Banking77 (77 intents, **10,003 train / 3,080 test**;
  published total 13,083, see [arXiv:2003.04807](https://arxiv.org/abs/2003.04807)); **and we state
  explicitly that Laya's prior sets (AG News / DAIR / Banking77) are never used as a headline**;
- **Contamination stance**: DeepSeek-V4.1-Flash **has not published a knowledge cutoff date**, so a
  "post-cutoff dataset" line of defence does not exist; the paired internal comparison is the main result.
  **The direction of contamination must be stated per side**: Banking77 is a prior set for Laya, but the
  **LLM's exposure is more direct** (45T token, including Common Crawl), and this regime's negative Δ_catch
  is carried precisely by "LLM-only correct on 23 items" ⇒ **contamination on the LLM side runs in the same
  direction as the negative conclusion, and is not the conservative direction**; the one genuinely free of
  public-corpus contamination is **regime three** (its ground truth is generated by program simulation).

## 11.4 Summary of the mandatory protocol clauses

Across the paper there are **23 non-duplicate clauses** (§4.4 has four + §6 has thirteen + §7.6 has eight;
two of the §4.4 clauses duplicate §6, hence 4+13+8−2 = 23), of which the five most critical are:

1. **To tell live from mock, always use `provider == "mock"`**, never the absence of a warning;
2. **Never gate on `truncated`/`fits`**; always compute the tokenizer yourself;
3. **Record only the confidence quantity oriented toward true** (for Jev record `noul`; for the LLM derive
   it from the label); **never record `probability`**;
4. **Option order must be decorrelated from correctness**, and **option keys must be opaque**;
5. **A classification cell with n<20 cannot be a basis for a conclusion** (this project **four times** drew
   a wrong conclusion from a high score in a small cell).

## 11.5 Inventory of raw artifacts

Under `results\` there are **42** JSON files, of which **39 carry a provenance record** and the other **3 are
all purely derived files** (`P22f` denominator fix, `P22g` agreement-rate provenance, `P30` evidence
inventory — none of them produces a measurement, so no instrument can be attributed), **with an unexplained
gap of 0**; **the count is derived from the directory by `src\analysis\p30_inventory.py`, and is no longer a
hand-written number** (hand-written counts repeatedly went stale in this project, which is itself a lesson).
The three LLM artifacts (`P14-llm-arm-full`, `P14-llm-arm-probe`, `P21-thinking-mode-cost`) previously had no
provenance of any kind; they now carry a `_provenance` block **explicitly self-labelled as recorded after the
fact** (`status: RETROACTIVE`) — **this is *not* a contemporaneous instrument record**: these two scripts
never called `instrument_record()`, and they **do not use the Laya sidecar at all** (they call DeepSeek), so
writing them into the Laya hash manifest would be a **category error**; nor were they re-run for this
purpose, because both scripts **do not pass `temperature`** (default sampling), and re-running would move
already-published numbers in order to backfill metadata. `P3` carries a record and a `loadout` after its
round-three re-run (re-run again in round five, with the numbers reproducing digit for digit). Under
`probes\`, **22** measured reports; under `recon\`, 20 reconnaissance and audit reports; under `decisions\`,
3 decision-unit reports + `DECISIONS.md`; under `protocol\`, the freeze and incident records (including this
round's `AUDIT-FINDINGS.md`).

**Reproducible artifacts added in round three**: the `temperature=0` repeated samples
`P22b-fixed-r1..r3.json` (the chain battery, after the ground-truth fix) and `P15b-rep-r1..r3.json` (the
77-class regime); **Jev's live artifacts** `P27-jev-live.json`, `P27b-plugin-crossval.json`,
`P27c-jev-latency-sweep.json`, `P27-summary.json`. In addition `results\ERRATA.md` records fields that were
superseded or withdrawn.

**Added in round five: the analysis layer and the repair layer each became a script** (previously both
existed only inside one-off sessions).
- `src\analysis\p28_recompute_all_stats.py` — recomputes every statistic in the paper with **the standard
  library alone** (Wald / Newcombe method 10 / Wilson / Clopper-Pearson / Fisher exact / CMH permutation /
  φ / AUC / Murphy equal-frequency decomposition / Brier), emitting `P28-recomputed-statistics.json`. Every
  interval and p value in the paper can now be checked cell by cell against it.
- `src\analysis\p30_inventory.py` — **derives** the evidence inventory from the directory (artifact count,
  count with records, purely derived count, coverage of the loadout/drift/sampling records), emitting
  `P30-evidence-inventory.json`. The paper no longer hand-writes these counts.
- `paper\verify_all.py` — turns this project's self-checks into **executable** checks: the manuscript's
  freshness relative to the drafts, all `§` references resolvable, headline numbers consistent with the
  artifacts, no unexplained gap in the inventory, artifacts cited by ERRATA exist, no credential leakage.
  **24 checks, all passing.**
- `src\items\p22f/p22g`, `src\instrument\p27f/p29` — the four kinds of repair above each became a script,
  and **the object of the repair and the reason for the repair both land in the artifact** (`_repair` /
  `_ledger_reconciliation` / `_hash_corrections` / `_provenance.status = RETROACTIVE`).
⇒ **Rationale**: the error type that recurs in this project is "one's own defect masquerading as a result
about the object", and **hand counting and one-off statistics** are precisely the two high-incidence entry
points for that class of error — both have actually happened here (hand-written evidence counts going stale;
a Wald value relabelled and taken as a Newcombe value). **Scripting the two is the only consistent
application of this paper's own conclusion to itself.**

**⚠️ Two known gaps in traceability** (listed honestly, not glossed over):
1. ~~**None of Jev's numbers had a machine-readable artifact**~~ → ✅ **closed in round three**:
   `P27-jev-live.json` (latency n=35, cost by tier, the ground-truth battery 8/8),
   `P27b-plugin-crossval.json` (plugin vs direct-route cross-validation, the two-way `probability`
   semantics, field attribution), `P27c-jev-latency-sweep.json` (latency vs state size),
   `P27-summary.json`. **Jev's column now has artifact support like every other column.**
2. **`P3` (the source of Result B's headline number) once had no instrument record** → ✅ **closed in round
   three**: after re-running it **reproduced digit for digit** and carried `_instrument` and **loadout** for
   the first time.
Every number is traceable to a specific JSON and to the script that generated it.

**⚠️ But round five found: this sentence was previously false for the *statistics*.** All the intervals and
exact tests (8 Δ_catch intervals, Fisher, Wilson, Newcombe, Clopper-Pearson, CMH permutation, φ, AUC, Murphy
decomposition, Brier) **previously had no script that could reproduce them** — `src\` contained no Wald /
Newcombe / Fisher / CMH / bootstrap / AUC code, and every one of them was computed during the audit inside a
one-off interpreter session. **The cost of this gap is concrete and pointable-to**: the Newcombe row of
`P15/P15b` has **two cells that are wrong**, of which the cell for the recorded draw **equals the Wald value
in the same column digit for digit** (a number whose label had been changed), and the r2 cell **is not any
Newcombe interval for that data**; and precisely because there was no script, this error survived several
rounds of audit before it was found.
⇒ Now supplied: **`src\analysis\p28_recompute_all_stats.py`** recomputes all the statistics above with **the
standard library alone** (this environment has no scipy), emitting
`results\P28-recomputed-statistics.json`; every interval and p value in the paper can now be checked cell by
cell against that artifact. Among them, AUC **0.7136**, Murphy **REL 0.0556 / RES 0.0397 / UNC 0.2400**
(**equal-frequency** 10 bins — note that `p19_calibration.py` itself bins by **equal width**, i.e. this
decomposition was previously not produced by code either), and Brier **0.2571** (computed directly; the
decomposition gives 0.2559, the difference arising only from binning) have all been reproduced cell by cell.
⇒ And it has been honestly recorded in §7.6/§8.3: under this paper's **own pre-declared Holm rule**, the
Fisher p of the three fixed draws (0.086 / 0.049 / 0.163) **did not survive even once** (the first threshold
being 0.0167) — **"significant in 1 of 3" is only an uncorrected statement**.

## 11.6 Numbers traceable only to a lab record, with **no `results\` artifact**
(`results\ERRATA.md` §10.2, complete)

**This paper's standard is that a number which cannot be re-checked cannot serve as evidence.
The numbers below are printed in the body, but there is NO `results\` artifact behind them** —
most exist only in a `recon\` / `probes\` lab record, or in a one-off interpreter session
during the audit. **They are not necessarily wrong** (several were independently recomputed to
within Monte Carlo error), but **by this paper's own standard they cannot serve as evidence**.
Each is marked where it appears; they are collected here so that a reader who samples the paper
still sees the disclosure.

| # | number | where printed | what it actually rests on | artifact-backed alternative |
|---|---|---|---|---|
| 1 | mock battery **Brier 0.359**, **t ≈ 1.1** | §6.1, abstract, §1, §3 | `recon\R12-jev-probe.md:187` (the t is hand-computed from 0.109/0.10) | none (the live calibration battery's Brier **0.2571** does have one: `P19-calibration.json`) |
| 2 | the κ bootstrap 95% CI **[−0.185, +0.206]** | §7.6 clause 18, §8.6 | a one-off session; `P28` contains no bootstrap | Wald / Newcombe / Fisher / Clopper-Pearson (`P28-recomputed-statistics.json`) |
| 3 | CMH permutation p **0.059 / 0.055 / 0.201** | §8.6.1(d), abstract | a one-off session; **no definition, no seed** | per-stratum and pooled φ (`P28` has φ; **the per-stratum values are still prose-only**) |
| 4 | the 68-item permutation test (**+0.243**, p = 0.057), **its definition and seed** | §8.6.1(c) | a one-off session, definition and seed unrecorded | none |
| 5 | two **n=69** chain reruns (Δ_catch **−0.0328 / −0.2071**) | §8.6.1 | a one-off session; `ERRATA.md` §5 records them in prose | the three post-fix **n=68** draws (`P22b-fixed-r1..r3.json`) |
| 6 | **11/69 (15.9%)** non-derivable ground truths | §7.6 clause 21, §8.6.1 | an independent recomputation during the audit; **`P22` has no such field** | the post-fix **96 → 0 → 68** (build-time assertion, `P22b`) |
| 7 | "an independent replay of the 18 requests, bit-identical except `latency_ms`" | §7.6 clause 19 | a one-off session; `P1` has no replay key | the 18 rows of `P1-rank-vs-choice.json` themselves |
| 8 | **every `jev_check` verdict reading** (the 7-row table) | §6.5 | `probes\P13-jev-remaining-measurements.md:47-56` | none (**no JSON under `results\` contains a `sufficient` field**) |
| 9 | the **`band` distribution** on `no_support` items | §7.5 table | same; `P19` **has no `band` column** | the `noul` distribution and accuracy (`P19-calibration.json`) |
| 10 | **four R13 case points** (0.9981 / 0.9989 / 0.5399 vs 0.0046 / 0.0011) | §7.2 | `recon\R13-laya-probe.md:430`, `:456`, `:448-449` | P9b's two rows (0.218 / 0.115, `P9b-...json`) |
| 11 | the correction's **token position 1,943–1,952** | §5, §8.7(a) | a one-off session; `P25`/`P26` have no such field | the two arms' shared 512 window (`P26`'s `in_pad`) |
| 12 | — | — | — | — |

**⚠️ This table is itself an application of the paper's argument**: it is **hand-written**, and
will therefore also go stale — row 12 is blank because the categories listed in ERRATA §10.2
are already covered by rows 1–11, not because an item is missing. **The list of categories is
determined by `results\ERRATA.md` §10.2, not by this table**; if that section changes, this
table must change with it.


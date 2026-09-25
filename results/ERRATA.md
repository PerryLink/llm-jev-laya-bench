# ERRATA for `results\`

**Added:** during the independent audit (`protocol/AUDIT-FINDINGS.md`).
**Policy:** the raw result files are **not modified in place** — they are measurement
records. Where a recorded field is wrong or stale, it is documented here instead.
**Status: two of the entries below have since been RESOLVED by re-running** (see the
resolution banner on each).

---

## 0. RESOLVED — resolved in round 3 by re-running

| file | was | now |
|---|---|---|
| `P3-clamp-calibration.json` | **no instrument record at all** (the source of the paper's headline clamp number had no provenance, and no freeze file recorded the launch loadout) | **re-run: reproduced every number bit-for-bit** (512/3,082/3,193/+111; 1,024/7,966/−4,773; 1,024/6,967/−3,774; frozen scores 0.3383/0.0764/0.4939) **and now carries `_instrument` with the loadout read live** (`loaded_checkpoints`, n=3, port 8787) plus all 13 snapshot hashes |
| `P16-pinned-clamp-replication.json` | verdict was a **retracted false positive**; the grid stopped at 791 tokens (never reached a cap) and compared english-ONLY against P3's THREE-checkpoint 512 | **re-run with a loadout-matched reference and a grid that crosses the cap**: english alone on the pinned snapshot clamps at **1024** (onset 6,967 chars) — **independent-process replication of the loadout attribution** |
| `P15-complementarity-strong-regime.json` | verdict said `COMPLEMENTARITY EXISTS` while its own `delta_catch` was −0.033; artifact predated its script | **superseded by `P15b-rep-r1..r3.json`** (temperature pinned, 3 draws). The stale file is retained as the recorded draw; its `verdict` must not be cited |

**New finding from the same round (N-1): P13's summary statistics are mutually impossible.**

| field | value |
|---|---|
| P12 lists all n=9 values | 1638, 1782, 1228, 1724, 1342, 963, 947, 919, 1465 — sum **12,008**, p50 1,342, mean 1,334 |
| P13 claims | n=13, **mean 1,879**, p50 1,380, max 11,984 |

n=13 with mean 1,879 requires a total of 24,427. P12's nine already sum to 12,008, so the
four added values must sum to 12,419 — but one of them **is** the 11,984 outlier, leaving
**435** for the remaining three, each of which is ≥ the stated minimum of 919 (≥2,757
required). **No such sample exists.**

**Consequence for the paper:** the **mean of 1,879 ms is not citable** and has been removed.
The paper now cites only the fully listed P12 distribution (n=9) and reports the later
round's 11,984 ms outlier as a heavy-tail observation, with n stated as 9+ for that reason.

**SUPERSEDED (round 4):** the whole Jev latency / cost / window column is now measured
through an independent route and no longer rests on `P12`/`P13` at all. See
`probes/P27-jev-live-report.md` and `results/P27*.json`. The replacement figures:

| quantity | P12/P13 (markdown only) | P27 (machine-readable, independent wall clock) |
|---|---|---|
| latency p50 | 1,342 ms (n=9) / 1,380 ms (n=13), **plugin self-report** | **938.6 ms (n=35)**, wall clock |
| cost per call | $0.0000142–$0.0000991 | **$0.0000146–$0.0001048** (8 size steps) |
| state window | ≥15,002 chars, cap "16,000" | **39,927 chars accepted** ⇒ the 16,000 cap is the **access layer's**, not the provider's |

`P12` and `P13` are retained as the record of the earlier rounds; their numbers should be
read as **plugin self-reports**, which `P27b` measures at ~**2.02×** the independent wall
clock for the same route and state.

---

## 1. `P15-complementarity-strong-regime.json` — stale `summary.verdict`

| field | value |
|---|---|
| `summary.verdict` (recorded) | `COMPLEMENTARITY EXISTS in Laya's strong regime: it caught 2 item(s) the LLM missed` |
| `summary.delta_catch` (recorded) | **−0.0333** |
| current script would emit | `NO COMPLEMENTARITY: delta_catch=… is not positive` |

**Diagnosis:** the artifact was produced by a **superseded revision** of
`src\items\p15_complementarity_strong_regime.py`. Evidence: artifact mtime **20:04:19** is
**19 s older** than the script's mtime **20:04:38**. The numeric fields are the
**corrected** ones; only the `verdict` string is stale.

**Consequence for the paper:** none. The paper's §8.4 already reports that the first
criterion said `COMPLEMENTARITY EXISTS` and that the criterion was replaced by the sign of
Δ_catch. **The recorded verdict must not be cited as a result.**

**Resolution:** this draw is retained as the **recorded** draw in a 4-draw replication
study (`P15b-rep-r1..r3.json`, `temperature=0`). Across all four draws Δ_catch is **≤ 0**;
this recorded draw (−0.033) is the **most favourable to the complementarity hypothesis**,
and it is still negative. Note also that its LLM accuracy (0.750) is the **lowest** of the
four draws (0.750 / 0.900 / 0.875 / 0.875).

---

## 2. `P16-pinned-clamp-replication.json` — retracted false-positive `verdict`

| field | value |
|---|---|
| `summary.verdict` / top-level `verdict` (recorded) | `DIFFERS from P3 (clamp 791 vs 512, gap −1776 vs 111): the revision matters and every pre-snapshot Laya measurement must be re-run` |

**Diagnosis — two compounding defects, and the second was not merely staleness:**
1. P16's character grid **maxed out at 791 tokens**, so it **never reached any clamp**;
2. the reference was **P3's three-checkpoint english clamp (512)** even though P16 launches
   english **alone** — an apples-to-oranges comparison.

Together they produced a "the revision matters" verdict from what was actually a
loadout difference plus a too-short grid.

**Resolution (round 3):** re-run with a **loadout-matched expectation (1024)** and a grid
that crosses the cap. Result: **english alone clamps at 1024 tokens (onset 6,967 chars)** on
the pinned snapshot, whereas the same checkpoint clamped at **512** under the three-checkpoint
loadout. So the variable is **neither the code revision nor the checkpoint** — it is the
loadout, replicated here by an independent process. A `grid_reached_cap` guard now refuses
to draw a conclusion from a grid that never reached a cap.

**Incidental finding worth keeping:** `truncated` first fired at **3,193 characters in all
four configurations tested** (three-checkpoint english/multilingual/typed-decisions, and
one-checkpoint english) while the real clamp took values 3,082 / 7,966 / 6,967 / 6,967.
**The flag is completely insensitive to the budget** — which is the paper's Result B claim,
now supported across four configurations rather than three.

---

## 3. `P14-llm-arm-probe.json` — 5/12 parse failures recorded as wrong answers

| field | value |
|---|---|
| `llm_prose_accuracy` (recorded) | `0.5` |
| `prose_label is None` | **5 of 12** rows |

**Diagnosis:** the 5 `None` labels are **extraction failures**, not model errors. Re-running
the **current** `parse_label` over the recorded `prose_text` recovers all 5 as correct keys
(`k03/k02/k04/k05/k03`). The artifact is **stale**: produced **19:59:54**, before
`src\instrument\deepseek_client.py` was last rewritten at **20:00:10**.

**Consequence for the paper:** none — the paper cites `P14-llm-arm-full.json` (n=48,
46/48 = 0.9583, **0** parse failures). This `probe` file is **superseded** and retained only
as an incident record. Banner added to `probes\P14-llm-arm-and-complementarity-report.md`.

---

## 4. `P22-chain-audit.json` — scored truth not derivable for 11 of 69 items

**Diagnosis:** `make_chain()` silently adjusted parity on odd `div` steps, and `simulate()`
— documented in the source as *"Authoritative truth"* — could not reproduce it. **11 of the
69 reported items (15.9 %)** therefore had a scored truth that **cannot be derived from the
rendered state**; for 10 of them the faithful reading was not even offered among the
options. The certificate the docstring describes was never implemented.

**Generator fixed** (`src\items\p22_chain_audit.py`): the adjustment is now recorded per
step, `simulate()` replays it **before** the superseded check, and `build_items()` asserts
derivability. Verified: **96 generated → 0 non-derivable → 68 admitted** (was 11/69).

**Consequence for the paper:** disclosed in §8.6, with the robustness check showing the
conclusion **strengthens** when the 11 items are removed (LLM 0.5942 → 0.6034; Laya 0.2899
→ 0.2759). ⚠️ **The recorded numbers belong to the pre-fix battery** and must be re-judged
(≈$0.003), not patched: the fix changes what *truth* means for the affected items.

**Also:** `P22` is **not** a zero-cost probe — item generation is free, but the 69 judgments
are paid calls (recorded rows sum to **$0.00394**).

---

## 5. `P22-chain-audit.json` — LLM arm is a single stochastic draw

Two independent replications (n=69 each, $0.00267 each) diverge from the recorded point
estimates:

| reading | recorded | re-run s1 | re-run s2 |
|---|---|---|---|
| LLM overall | **0.5942** | 0.5217 | 0.5217 |
| K=4 cell | **1.000** | 0.8333 | 0.8333 |
| κ | **0.0062** | 0.0322 | **0.2030** |
| Δ_catch | **−0.0070** | −0.0328 | −0.2071 |

Per-item label agreement with the recording is **40/68 = 58.8 %**; between the two re-runs,
54 %. **Root cause:** `p22` calls `chat()` without `temperature`, and the client only sets
it when explicitly passed ⇒ the API default sampling applies.

> **⚠️ Corrected denominator (round 5).** This entry originally read `40/69 = 58 %`. The
> denominator cannot be 69: `CH-K16-009` exists only in the recorded pilot, so no re-run can
> ever agree with it on that item. The comparison is over the **68 shared items**, giving
> **40/68 = 58.8 %**. A second correction is in §6 below: **7 of those 68 items had a
> different OPTION SET** in the two runs, so 4 of the 28 disagreements are not sampling
> disagreements at all. Excluding them: **37/61 = 60.7 %**. The conclusion is unchanged —
> unpinned sampling destroys item-level reproducibility — but the figure is 58.8 %, not 58 %,
> and the clean comparison is 60.7 %.

**Bootstrap on the recorded rows:** κ's 95 % CI is **[−0.185, +0.206]** — so "κ = 0.0062,
no better than chance" reports **four decimals of a ±0.2-wide estimate**.

**What replicates:** item generation (byte-exact), the **Laya arm (69/69 identical labels)**,
and every qualitative claim (ceiling broken, depth collapse, Laya flat).

**Paper status:** disclosed in §8.6 with the full table, plus a new protocol clause
requiring the between-replication label-agreement rate for any arm run under API default
sampling.

---

## 6. `P1-rank-vs-choice.json` — stale `summary.by_n` (retained per policy)

**Retained, not regenerated.** The file's own measurement is intact and correct; only the
SUMMARY AGGREGATION is stale, and regenerating it in place would destroy the evidence that
is the literal 依据 of paper lesson 19.

| quantity | value | consistent? |
|---|---|---|
| `summary.n_items` | **18** | ✓ |
| recorded row objects | **18** | ✓ |
| `summary.instrument.calls` | **18** | ✓ |
| Σ `summary.by_n[*].n_calls` | **15** | ✗ |
| distinct `by_n` buckets | **5** (`2,5,10,15,20`) | ✗ — `21` missing |

The three unaggregated rows are `RC-00-N21`, `RC-01-N21`, `RC-02-N21`. The generator renders
`n=25` as **21 options** (`k = min(n-1, 20)`), and the item id uses the rendered count, while
the old bucket list was hard-coded to `(2,5,10,15,20,25)` — so those three calls fell into no
bucket and vanished from `by_n`. **The bug dropped rows from the aggregation, never from the
measurement.** The code fix (`p1_rank_vs_choice.py:236-246`) derives buckets from the data and
would emit the missing bucket `{n_calls 3, accuracy 0.0, auc_mean 0.5833, win_rate 0.0,
p_supported_mean 0.0015333, any_truncated true}` plus `unexpected_option_counts: [21]`.

**Also corrected: "15 LLM calls" was wrong twice over.** All 18 rows are **Laya sidecar**
calls; the probe imports no LLM client and makes **zero** LLM calls (cost $0.00).

**A separate arithmetic error, in the report not the artifact.** `probes\P1-rank-vs-choice-report.md`
printed N=21 "average AUC = 0.47" — that is the median / a single row. The three N=21 rows are
0.9, 0.475, 0.375 ⇒ **mean 0.5833**. Likewise "1.00 (N=5,10)" should read N=5 = 1.00,
N=10 = 0.963. The verdict (choice ≠ rank) survives on accuracy 0/3 at N=20 and 0/3 at N=21.

**Every published P1 number remains reproducible.** An independent replay of all 18 requests
against the live sidecar reproduced all 18 rows **bit-identically in every field except
`latency_ms`** (`p_supported`, `chosen`, `confidence`, `auc`, `truncated`, `warnings`,
`state_tokens`). A re-run would change exactly four things: the `by_n` aggregation, the new
`unexpected_option_counts` key, `instrument.restart_count` 1 → 0 and `cold_start_ms`
19,164.2207 → null (a sidecar is already up, so `ensure_up()` never restarts it), and the
per-row latencies — the last of which would silently falsify the published cold-start figure.

---

## 7. `P27` family — stale derived fields and an unreconciled ledger

Three defects, all downstream of one event: **`P27-jev-live.json` was re-run late in round 3,
after artifacts quoting it had already been written** (P27 json 21:40:30; P27b json 21:38:53;
the live report 21:37:48). Its wall-clock figures moved:

| P27 n=20 | written downstream as | actual |
|---|---|---|
| p50 | 915.1 | **1191.8** |
| mean | 1001 | **1550.6** |
| max | 1802 | **4018.6** |

1. **`P27b-plugin-crossval.json` stored a superseded derived figure.** Its
   `unmatched_direct_for_reference.p50_ms` was 915.1 and `ratio_of_medians_unmatched` 2.02;
   the generating expression (`p27b_plugin_crossval.py:83`) reads the figure dynamically and
   now evaluates to **1191.8**, hence **1.55**. The code was right and the artifact stale.
   The derived fields have been recomputed; **the plugin's 7 hand-transcribed rows are
   untouched**. Its **size-matched** figures (126 chars / 347 tok / p50 956.2 / ratio
   **1.94**) were always current and are the ones the paper should quote.
2. **`P27-summary.json` omitted one of its own declared sources.** It summed P27, P27c and
   P27d but not `P27b-plugin-crossval.json` — 7 charged calls, **$0.000102018** — while
   `_sources` listed the file. Corrected total: **$0.002280516** (was $0.002178498).
3. **`P27-jev-live.json`'s ledger exceeded its own rows by exactly one call.** The section-C
   provider-field-inventory call was charged into `_spend_usd` but stored no cost row, so any
   total recomputed from rows alone came out short. Residual: **$0.000014280 = exactly
   1.428e-05**, one call. The generator now persists cost/latency/attempts for that call; for
   this artifact the residual is recorded in `cost._ledger_reconciliation` rather than
   inferred into a fabricated row, because that call's latency and attempt count were never
   recorded.

**Also fixed in the generators:** `p27c_latency_sweep.py` discarded `_attempts`, so it could
neither exclude nor quantify the retry bias `p27` documents (a timeout-then-success call
contributes only its SHORT final leg). Attempts are now recorded per repetition. And
`p27e_summary.py` described the ladder as mixing "Laya wall clock, LLM **provider
self-report**, Jev wall clock" — all three are in fact client wall clock around the HTTP call
(`deepseek_client.py` uses `perf_counter`), so the caveat now says that.

**Repaired by:** `src/instrument/p27f_repair_p27_family.py` (no API calls: every repaired
number is arithmetic over existing artifacts).

---

## 8. Regenerated in round 5 — `P16` and `P3`

Both were one revision behind their own scripts: the verdict/note logic had been corrected
but the artifacts still carried the old text. Both were regenerated from the live local
sidecar (**$0 API spend**; 21 calls for P16, 54 for P3). Neither moved a published number.

**`P16-pinned-clamp-replication.json`** — the recorded verdict read *"LOADOUT ATTRIBUTION
REPLICATED…"*, which matched **no branch of the current gate**. The gate had been fixed to
check the clamp **and** the unwarned gap separately, because the run's `unwarned_gap_chars`
was **−3774** — the **opposite sign** to P3's **+111**, and 34× its magnitude (a NEGATIVE gap
means the flag fired *earlier* than the clamp, i.e. a false positive, whereas P3's +111 was a
silent window). The artifact now reads:

> CLAMP EFFECT REPLICATED, UNWARNED-GAP NOT: english ALONE on the pinned revision clamps at
> 1024 tokens (P3 measured english at 512 under the three-checkpoint loadout), so the LOADOUT
> is the variable for the clamp. But this run's gap is −3774 chars versus P3's +111 — opposite
> sign, so the FLAG behaviour was NOT replicated here.

and carries the previously missing `gap_sign` = `flag_fires_early_false_positive`,
`gap_matches_P3` = false, and `clamp_matches_reference_loadout_effect` = true.

**`P3-clamp-calibration.json`** — its `_note` still said english 512 vs
multilingual/typed-decisions 1024 was *"a checkpoint difference, not a loadout difference"*.
That is wrong twice over: the clamp is a function of **(loadout × queried checkpoint)**, and
english alone clamps at 1024. The regenerated `_note` says so. All clamp numbers reproduced
bit-for-bit (english 512 / onset 3082 / flag error +111; multilingual 1024 / 7966 / −4773;
typed-decisions 1024 / 6967 / −3774).

**Also corrected: `protocol\INSTRUMENT-FREEZE.json`.** Its `worker.py` hash (`6FE665BF…`)
matched no file on disk, no tree, and no committed revision. The file was frozen at
10:18:25Z, **before** the snapshot (10:20:01Z), and hashed the **live working tree** — the
pre-fix manifest held only 4 modules + 2 root configs, and that version of
`instrument_hashes()` hashed the worktree. `worker.py` was rewritten 18 s later, at
10:18:43Z, which is the revision the campaign is attributed to. The value is corrected to
`829EB8C3…` with the superseded value retained under `_hash_corrections`. **No published
number was affected**: 0 result artifacts contain `6FE665BF…`, all 28 that record a
`worker.py` hash record `829EB8C3…`, and no code reads the freeze file. Separately, that
file's `sidecar_capabilities_state_budget` records the sidecar's **self-reported** budget as
`512/512/512` while P3 measured `512/1024/1024` — left as recorded, with a correction note,
because it is a verbatim observation of what the service claimed, and because the
disagreement is itself an instance of Result B.

---

## 9. `P14` and `P21` — provenance added retroactively, and labelled as such

`P14-llm-arm-full.json`, `P14-llm-arm-probe.json` and `P21-thinking-mode-cost.json` carried
**no provenance of any kind**: their scripts never import or call `instrument_record()`, and
no script produces `P14-llm-arm-probe.json` at all.

**Two fixes were considered and REJECTED.**

- **Re-running** is unsafe as a provenance patch. Both scripts call `chat()` with **no**
  `temperature`, and `deepseek_client.py` sets the field only when one is passed, so API
  default sampling applied. Re-running would move published numbers (the paper cites LLM
  1.0000 at n=48 and 0.958 for the prose arm) in order to fix a metadata gap — the same
  failure mode §5 above documents for P22, where default-sampled re-runs agreed with the
  recording on only 58.8% of items.
- **Backfilling a Laya `instrument_record()`** would be a **category error**. These arms
  never call the Laya sidecar; they call DeepSeek. A Laya hash manifest would describe an
  instrument that did not participate — and a hash computed today honestly describes the
  snapshot *as it exists now*, not what ran *then*.

**What was done instead** (`src/instrument/p29_backfill_llm_provenance.py`): a block that
states only what is independently knowable and **labels itself** —
`_provenance.status = "RETROACTIVE … IT IS NOT A CONTEMPORANEOUS RECORD"` — recording the
route and model, the sampling caveat, the measured spend (P14-full $0.00531221 over 96
calls; P21 $0.00183090 over 24), and, for the probe, that it is superseded and script-less.
**No measured number was modified.**

**A real gap this exposed, and did not close:** `deepseek_client.py` — the LLM arm's own
client — is hashed **nowhere** in the project. The blocks record its current sha256 as a
*retroactive* value, which is not the same as a run-time pin. The project can pin its judge
and cannot pin its generator.

---

## 10. Known but NOT yet fixed (trace audits, rounds 6-8)

The sentence-level trace audits checked roughly 350 printed numbers against the artifacts.
Most reproduce exactly. The entries below are defects that are recorded here rather than
silently dropped -- a defect that is written down is still better than one that is not.

### 10.1 Paper text

| # | Location | Defect |
|---|---|---|
| 1 | `07-results-C-draft.md:90` (section 6.2) -- **corrected file: this said `06-results-B-draft`** | prints 0.9981 as "the highest confidence in the whole probe" while the NEXT line prints 0.9989 (and the source, `recon/R13-laya-probe.md:456`, records 0.9989) |
| 2 | `08-results-D-draft` | the one-sided p-values 0.052 / 0.043 / 0.103 are NORMAL APPROXIMATIONS and are not labelled as such; the exact binomial lower tails are 0.076 / 0.061 / 0.149, so none is significant under either convention -- but the convention must be stated |
| 3 | `07-results-C-draft` 7.2 | P14's PROSE arm is never mentioned: LLM 46/48, one judge-only item, **delta_catch = +0.0435**. It is the one measurable delta in regime 1 and it is POSITIVE, while the section declares the regime unmeasurable on the strength of the forced-choice arm alone. The artifact's own `_provenance.published_figures_at_risk` lists "prose arm 0.958" |
| 4 | `06-results-B-draft` 3.5 | a 7-row table contains only 5 `insufficient` rows; "sufficient never exceeds 0.14 in all 7" is falsified by its own table (the other two print 0.88 and 0.92). One instance was corrected; check for others |
| 5 | `06-results-B-draft` 3.1 | "the unique solution is 4/10 = 0.40" is not unique: 5/10 = 0.50 is equally consistent unless a zero-rate bin is forced non-empty. R12's original 5/10 is as supportable |
| 6 | `06-results-B-draft` 3.1 | the corrected table prints the binary column as an em-dash in 4 of 5 rows, so its own "total 9" is not derivable from it |
| 7 | `06-results-B-draft` 3.9 | "flips every item answered false (about half of this corpus)": the LLM answered false on 60.0%, the JUDGE on 29.8%. "About half" fits neither |
| 8 | `07-results-C-draft` 6.2 | the reliability table shows 5 of 10 bins and says all carry mass; the five omitted bins include the LARGEST miscalibrations (+0.939 and +0.343 at the low end), and "both ends are tolerable" is false at the low end |
| 9 | `07-results-C-draft` 6.1 | L25 and L28 are the same measurement printed twice; P14 consumes P9b, so the two rows are the two arms of ONE 48-item battery and the capability profile double-counts it |
| 10 | `07-results-C-draft` 6.1 | "centre about 0.875" -- the median is 0.875 but the MEAN is 0.850; and 3 of the 4 draws are P15b, cited as P15 |
| 11 | `06-results-B-draft` 3.4.1 | the attribution table omits `warnings`, which P27d also lists as provider-absent (9 keys vs the paper's 5) |
| 12 | `07-results-C-draft` 6.6 | the clause-counting note is internally incoherent: it says one duplicate was deleted from the original 14-17, yet 14-17 all survive and none restates clause 13; a real deletion would subtract 3, not 2 |
| 13 | `06-results-B-draft.md:150` (section **3.5**, not 3.1) -- **corrected location** | "8 live jev_check calls" contradicts P13's own design line ("seven"), and the prose lists 8 categories against a 7-row table |

### 10.2 Untraceable numbers (prose-only; no `results/` artifact)

Brier 0.359 and its `t ~ 1.1`; the kappa bootstrap CI `[-0.185, +0.206]`; the CMH
permutation p-values; the 68-item permutation test's definition and seed; the two n=69
chain re-runs behind clause 17; "11/69 non-derivable" and "independent replay of 18
requests"; every `jev_check` verdict number (NO results JSON contains a `sufficient`
field); the `band` distribution on `no_support` items (P19 has no `band` column at all);
the four R13 case points; the correction's token position "1,943-1,952".

These are not necessarily WRONG -- several were independently reproduced to within Monte
Carlo error -- but they cannot be checked from the tree, which by this project's own
standard makes them unusable as evidence as printed.

### 10.3 Artifact-integrity defect

`results/P27b-plugin-crossval.json` -> `latency_self_report_vs_wall_clock._stale_superseded`
now records `superseded_unmatched_p50_ms = 1191.8` and `superseded_ratio = 1.55` -- the
CURRENT values, not the superseded ones (915.1 and 2.02 per ERRATA 7.1 and the repair
script's own docstring at `src/instrument/p27f_repair_p27_family.py:15-16`). The repair
script ran twice and its second pass overwrote the historical record with the repaired
values. The script is not idempotency-safe. The published 1.55 is nonetheless the correct
current value.

### 10.4 Method note

Two audit rounds each independently caught a defect of the SAME shape: a number that is
correct in itself, attached to the wrong object. The mock battery's Brier was computed on
the 10 items with binary ground truth but printed against the 14-item battery; the Jev p50
of 915.1 was the pre-repair value of a DERIVED field but printed as a second run. Both
survived five earlier audit rounds because every individual figure was right and only the
ATTACHMENT was wrong. This is worth recording as a class: **checking numbers is not the
same as checking what they are numbers OF.**

### 10.5 Why two of these items survived four fix attempts

ERRATA 10.1 items 1 and 13 named the **wrong files**. Fix scripts `p44` and `p45` searched for
them, reported `MISS`, and moved on -- twice each -- on the assumption that the pattern did not
match. It did match; it was looked for in the wrong document.

The project has a guard (**J1**) against a retraction that fails to propagate. It has no guard
against an **index that is wrong**, and no habit of **chasing a MISS**. Both are now recorded,
because the failure was not that the defects were hard to find -- it is that a wrong entry in
this very table silently converted two real defects into two apparent pattern mismatches.

**Rule adopted**: a fix script that reports `MISS` is not finished. Either the pattern or the
location is wrong, and the difference must be established before moving on.


---

## 11. RESOLVED in round 9 -- the section-10 worklist, closed

**Status: all 13 paper-text defects (10.1), all 12 untraceable-number categories (10.2) and the
1 artifact defect (10.3) are fixed.** The fixes are scripts rather than hand edits, because a
hand edit cannot be re-run and this project's standard is that every claim is re-checkable.
Each script exits non-zero when its anchor is missing, and each was written to be idempotent
(`src/analysis/p70`-`p81`). `paper/verify_all.py` now carries the invariants as **K1-K10**,
which print their evidence on success as well as on failure -- a check that says nothing when
it passes is indistinguishable from a check that never ran.

### 11.1 The thirteen paper-text defects

| # | Fixed by | Backed by | Held by |
|---|---|---|---|
| 1 | `p74` (zh) + `p75` (en) | `recon/R13-laya-probe.md:430` vs `:456` | K4 |
| 2 | `p70` computes both conventions, `p71` labels them | `P28-recomputed-statistics.json` -> `regime3[*].vs_marginal_one_sided` | K2 |
| 3 | `p70` (interval), `p71`/`p72` (text) | `P14-llm-arm-full.json` -> `complementarity_prose_arm`; `P28` -> `regime1` | K1 |
| 4 | `p73` | `probes/P13-jev-remaining-measurements.md:47-56` (5 of the 8 recorded rows are `insufficient`) | `p73`'s own rescan |
| 5 | `p73` | `recon/R12-jev-probe.md:181-185` (per-bin counts) + `:187` (the prose summary) | -- |
| 6 | `p73` | same source's per-bin counts 2/2/2/2/1 | -- |
| 7 | `p73` (Results B, discussion) + `p72` (abstract) | `P19-calibration.json` -> `bins`: 660/1100 and 328/1100 | K6 |
| 8 | `p74` | `P19-calibration.json` -> all 10 bins, n summing to 1,100 | K3 |
| 9 | `p74` | `P14-llm-arm-full.json` -> `_provenance.consumes` = `P9b` | -- |
| 10 | `p74` | `P15-complementarity-strong-regime.json` + `P15b-rep-r1..r3.json` | -- |
| 11 | `p73` | `P27d-primitive-fields.json` -> `never_returned_by_provider`, 9 keys | K5 |
| 12 | `p74` | `04-method-draft.md` §4.4 vs `06-results-B-draft.md` clauses 8 and 10 | K7 |
| 13 | `p73` | `probes/P13-jev-remaining-measurements.md:45` vs `:47-56` | -- |

Every one of the thirteen is also present in the English section files (`p75`), because a
correction that exists in one language only leaves the two published versions disagreeing.

### 11.2 The twelve untraceable-number categories

Each is now **marked in place in both languages** -- 15 Chinese and 15 English markers
(`src/analysis/p76_mark_untraceable_numbers.py`, `p77_sync_english_untraceable.py`) -- and listed
once in a new **§11.6** of the manuscript that states, per category, what the number does rest on
and which artifact-backed alternative exists. Nothing was deleted and nothing was invented: the
numbers that cannot be re-checked are labelled as such at the point where a reader meets them.
Held by **K8**.

### 11.3 The artifact defect (10.3)

Resolved in three parts, and the third has moved again:

1. **The generator is fixed.** `p27f` now writes `_stale_superseded` **once** and preserves an
   existing block verbatim, counting further passes instead of overwriting them
   (`src/analysis/p78_fix_p27f_idempotency.py`, which also proves the guard on a scratch copy and
   asserts that `save()` still refuses to overwrite an existing `.pre-repair` backup).
2. **The historical values were never lost**, and are asserted recoverable: 915.1 ms / 2.02
   survive verbatim in `results/_superseded/P27b-plugin-crossval.json.pre-repair` and in
   `rerun/baseline/_superseded/P27b-plugin-crossval.json.pre-repair`.
3. **This section's closing sentence is superseded.** "The published 1.55 is nonetheless the
   correct current value" no longer holds: the re-run campaign regenerated `P27-jev-live.json`
   and `P27b-plugin-crossval.json`, the live artifact carries no `_stale_superseded` block at
   all, and the size-matched ratio now reads **1.49** against a denominator of 1,244.8 ms (it
   was 1.94 against 956.2 ms). That instability is exactly why the paper no longer prints either
   point value: the text now reports **about 1.5-1.9x** with both artifacts named and the reason
   stated, see `results/RERUN-RATIO-INSTABILITY.md` and
   `src/analysis/p79_fix_unstable_latency_ratio.py`. Held by **K9**.

### 11.5 The author's ruling on the chain battery: OPTION A (published battery is the record)

**Decided in round 9, and implemented in the manuscript (both languages).** The published battery
is what the paper's claims rest on and what its text describes; the generator changed *after* the
artifact was made, so the published battery is the correct measurement **of the protocol the paper
describes**. Substituting the re-measured battery would rewrite every regime-3 number to describe
a protocol the paper never claimed to have run, for no gain: Delta_catch is negative in 3/3 draws
either way.

**But the re-measurement is disclosed in the body, not in a footnote** (`p90`,
`src/analysis/p90_option_a_disclosure.py`): the manuscript now carries the before/after table
(Delta_catch -0.233/-0.247/-0.182 -> -0.056/-0.099/-0.066; Fisher p 0.086/0.049/0.163 ->
0.787/0.425/0.595; phi +0.24/+0.26/+0.19 -> +0.06/+0.11/+0.07) and says plainly that the
**direction survives while the "shared failure" reading loses the weak support it had**, because
the effect is substantially a function of **how the options are built**. That is this paper's own
thesis applied to this paper's own central measurement, which is why it belongs in the text.

**The record is pinned and checked**: `results/_superseded/P22b-fixed-r*.json.pre-repair` and
`rerun/baseline/P22b-fixed-r*.json` are byte-identical (sha256 `b11561727d5d` / `6f68f6152c9b` /
`d712f9269846`). `verify_all.py`'s **K2** recomputes the printed p-values from those pins -- never
from the live artifacts, which now hold the re-measured battery -- and requires the disclosure to
be present, so the check cannot be made green by deleting the follow-up. **K11** fails if either
side of a pinned pair is disturbed.

**The n=69 pilot needs no rebuild.** `results/P22-chain-audit.json` is **byte-identical** to the
immutable baseline `rerun/baseline/P22-chain-audit.json` (sha256 `8cab72f8d71b`, 69 rows,
`_repair` present, LLM 0.5942, Delta_catch -0.006968641): the published recorded draw is the
artifact in the tree. The overwrite reported in `RERUN-P22-PILOT-OVERWRITTEN.md` was transient.
**The hazard is closed at the generator**: `p22_chain_audit.py` now refuses to overwrite an
existing artifact whose `n_items` differs from the run's, unless a 4th argument forces it -- so
the record is no longer one command away from being destroyed by code that builds a different
battery.



### 11.4 New defects found while closing this worklist

Recorded because the pattern is by now familiar: none of these was found by reading, and each
was found by *running* something.

1. **A concurrent edit overwrote a per-artifact value with its own summary.** The ratio fix
   replaced the point value with the range `1.5-1.9` across the drafts and hit a sentence that
   reports what the ratio reads **against each artifact** -- yielding "reads 1.5-1.9 (baseline
   artifact) and 1.49 (live artifact)", which is not a sentence. Restored by `p79` to the value
   the baseline artifact records. **Class: a value and its summary share digits and differ in
   referent** -- this file's 10.4, one level down.
2. **`paper/verify_all.py` crashed while reporting its own results**: a detail string held a
   character the host console's GBK codec cannot encode, so the gate died in a
   `UnicodeEncodeError` traceback instead of printing a verdict. `stdout` is now reconfigured to
   UTF-8 with `errors="replace"`.
3. **Two of the new checks fired on correct data, because each tested the wrong object.** K3's
   row scan also collected the mock battery's bin table in section 3.1 (15 rows, not 10), and K4
   read the correction's own quotation of the withdrawn wording as the withdrawn claim. Both are
   repaired in `src/analysis/p81_repair_k_checks.py`. **The paper's own lesson applies to its
   tooling: a check that fails on correct data is a check that will be switched off.**
4. **`results/P27b-plugin-crossval.json` no longer reconstructs its own history.** After the
   re-run regenerated it, the artifact carries no `_stale_superseded` block, so the earlier
   values survive only in the two `.pre-repair` copies. Provenance that lives only in a backup
   is provenance with one deletion between it and nothing -- the same shape as 10.1 item 3,
   where the artifact's own `published_figures_at_risk` list named a figure the text never used.

5. **The chain battery was re-measured after the re-run campaign's own summary, and section
   8.6.1 is now stale in both languages.** `results/P22b-fixed-r1..r3.json` were rewritten at
   23:33-23:35, after `RERUN-CAMPAIGN-SUMMARY.md` (23:32:44), so no document yet records it.
   The regenerated battery is **not the same measurement**: the generator now inserts the
   ignore-SUPERSEDED value among the options, so **2** items lack it instead of **7**, the
   option sets therefore differ, and the judge's answers move with them -- for a deterministic
   judge, **24 of 68 labels changing** is proof of a construction change, not sampling noise.
   This is the class the re-run agent named for P20 and P5 (`RERUN-CAMPAIGN-SUMMARY.md` §3), and
   it lands on the one regime whose published numbers rest on item-level agreement.

   | quantity (n=68, three pinned draws) | published | recomputed from the live artifacts |
   |---|---|---|
   | LLM overall | 0.6765 / 0.6618 / 0.6618 | **0.5294** (r1 only; the artifacts differ per draw) |
   | judge overall | 0.2941 (3x identical) | **0.2794** (3x identical) |
   | judge-only-correct | 3 / 3 / 4 | **8 / 7 / 7** |
   | Delta_catch | -0.2332 / -0.2473 / -0.1816 | **-0.0556 / -0.0985 / -0.0663** |
   | Fisher p (2x2) | 0.086 / 0.049 / 0.163 | **0.7873 / 0.4246 / 0.5954** |
   | phi | +0.239 / +0.257 / +0.189 | **+0.0618 / +0.1094 / +0.0731** |
   | one-sided binomial lower tail vs the judge's marginal | 0.076 / 0.061 / 0.149 | **0.4425 / 0.3299 / 0.4132** |

   **The direction survives and the strength does not.** Delta_catch is still negative in 3/3
   draws, so "no complementarity" still holds; but the *shared-failure* reading -- the paper's
   positive claim about phi -- loses even the weak statistical support it had: Fisher p goes from
   "significant in 1 of 3 uncorrected" to "nowhere near significant in any draw", and phi falls
   from +0.19...+0.26 to +0.06...+0.11. The claim that the judge arm is a **deterministic
   function of (state, options)** -- 61/61 = 100% on items whose option set did not change -- must
   also be re-derived, because the count of changed option sets is itself different (7 -> 2).

   **Which battery is canonical is a decision, not a computation.** `RERUN-P22-PILOT-OVERWRITTEN.md`
   asks the same question about the n=69 pilot; the live pilot artifact currently matches the
   published recorded round, so only the fixed battery is affected. Until that decision is made,
   the paper's section 8.6.1 block cannot be re-derived -- and `verify_all.py`'s **K2 check fails
   on purpose**, because the manuscript prints tails (0.076 / 0.061 / 0.149) that the live
   artifacts no longer produce (0.443 / 0.330 / 0.413). **The gate is red because the paper and
   its artifacts disagree; making it green without fixing that would be the failure mode this
   whole section documents.**

---

## 12. The token-density claim: a correct measurement attached to the wrong text type

**Status: corrected in the manuscripts, the exploration records, three decision documents and the
instrument's own docstring. Held by a new invariant, `K12`.**

### 12.1 What was printed

Section 3's access-layer defect 3 said:

> `planning.py` estimates tokens with `chars / 4.0 × 1.15`, i.e. an implied 3.478 chars/token;
> whereas that encoder measures **≈6.33 chars/token on English prose** → **the planner
> overestimates the token count by about 1.8×**, and `exact` is `false` on every response.

### 12.2 What is actually true

| | value | how it was established |
|---|---|---|
| the 6.33 | **is real** | reproduced here at **6.782** by rebuilding the sweep's state from `src/instrument/p3_clamp_calibration.py:57-60` and tokenizing it |
| **what it measures** | **the sweep's own synthetic state** | `DECOY + FILLER×45 + CORRECTION` — **one filler sentence repeated 45 times** |
| **English prose** | **4.31 chars/token** | `results/P31-token-density.json`; an independent audit measured 4.008–4.430 across Banking77's 10,003 real requests and prose-stripped paper sections |
| the over-estimate **on that state** | **1.949×**, not 1.82× | the R13 table's token column runs **7–8% high** (it records 804 tokens at 5,086 chars; 804 would need ≈5,530 chars at the measured density) |
| the over-estimate **on prose** | **1.239×** | artifact |
| **the dangerous direction** | **never reported at all** | on JSON (2.40), source (3.24), Chinese (1.65) and CSV (1.62) the planner **under**-estimates by 1.075×–2.150×, and the 1.15 safety factor does not cover it |

**So the sentence was wrong twice in the same way this paper documents**: a correctly measured number
attached to the wrong object, *and* a stated magnitude that its own source did not support. The
correction also removes an omission: the failure mode that matters — `fits: true` on a state the model
silently truncates — is in the direction the paper did not report.

### 12.3 Why it survived every earlier audit

A ratio carries no record of the text it was measured on. The number and its object were both present
and correct; **only their attachment was wrong**, and no check in the suite compared an attachment. The
6.33 was also reproducible — anyone re-running the sweep would get it — so the usual "can this be
reproduced?" test passed.

### 12.4 The counter-evidence that should have been noticed first

`planning.py`'s own docstring says the material it serves is *"a contract, a log, or an email thread"*
and *"the serialized JSON form of a mapping"*. The one input type the paper measured was a repeated
sentence — the single most favourable input the estimator could be handed, because repetition raises
compressibility monotonically (×1 = 5.550, ×100 = 6.920 chars/token). **The estimator's behaviour on the
inputs its own module documents was never measured until this correction.**

### 12.5 Where it had propagated

Not only prose. The bad constant had been adopted as a project design input:

| file | what it said | disposition |
|---|---|---|
| `recon/R13-laya-probe.md` §2.2, §644, §679 | "≈6.33 on English prose"; §679 instructed the project to **assume 6.3 chars/token for prose** | corrected in place; the instruction is **withdrawn** — there is no safe single constant |
| `recon/R2-verified-externals.md` | "true density ≈6.33 chars/token" | corrected |
| `recon/R5-synthesis.md` | row 6 of the synthesis table | corrected |
| `recon/V3-feasibility-audit.md` | "the same model that is 1.8× wrong" | corrected |
| `decisions/DECISIONS.md:24` | `16,000 ÷ 6.33 ≈ 2,530 token` used to argue a window never triggers | recomputed: **≈3,712 (prose) to 6,667 (JSON)**; **conclusion unchanged and stronger** |
| `decisions/D1-jev-live-decision.md:71` | same arithmetic | recomputed; conclusion unchanged |
| `decisions/D3-public-datasets.md:114` | "≈6.3 chars/token on English prose" as a constraint | corrected to the both-directions statement |
| `src/instrument/laya_client.py:10` | the constant in the instrument's own rationale | corrected |

**The design conclusions survive because the corrected figures widen the gap they relied on.** That was
checked rather than assumed: 3,712–6,667 tokens is further above the 300–1,500 token design range than
2,530 was.

### 12.6 What was added so it cannot recur

`paper/verify_all.py` gains **`K12`**, which asserts two properties against the artifact rather than
against the text:

1. every `chars/token` figure the manuscript quotes is one `results/P31-token-density.json` records,
   with the one exception of 2.20, which the text explicitly attributes to the independent audit; and
2. **6.33 survives only on a line carrying a retraction marker** — the same shape as `K10`, which holds
   0.912 inside its retraction.

The measurement itself is reproducible: `uv run --quiet --no-project --with tokenizers python
src/analysis/p31_token_density.py`, which pins the three tokenizer files by SHA256 and needs no GPU and
no model weights. Two of the sixteen samples are **constructed** and are labelled `_CONSTRUCTED` in
their names, because the two densest realistic input types have no verbatim file in the tree.

### 12.7 Found while verifying this, and recorded separately

**Defect 6 was added to the manuscript: `noul` answers from its label words rather than from the state**
(upstream issue #156, three independent reproducers, confirmed by the maintainer as the most important
open defect). This paper's own P19 battery **did not** reproduce the reported saturation — it uses
`noul` with `"true"`/`"false"` criteria keys and its 1100 `laya_p` values span 0.061–0.963 with real
discrimination — so the manuscript records both the external finding and this path's counter-evidence,
and qualifies `explicit_support 0.9909` as measured on this project's access path rather than as a
general property of `noul`.

Separately: **defect 2's attribution was narrowed.** Auditing every assignment to `fits` in `laya-mcp`
finds it cannot emit a non-boolean (the single assignment is `fits=not any_truncation`), and no `value`
key exists in that package, so the JSON-Schema violation is raised client-side. The manuscript now says
the call was observed failing here while the violation comes from whatever validated the result. The
regression test that holds `fits` to its boolean contract was missing and has been added.

---

## 13. The gate's own size: one script, two totals in one manuscript

**Status: corrected in both manuscripts and seven repository documents. Held by two new invariants,
`L1` and `L2`.**

### 13.1 What was printed

The published PDFs describe `paper/verify_all.py` twice, and the two descriptions disagree:

| where | text |
|---|---|
| §11, ZH p71 / EN p90 | "**24 项检查**，全部通过。" / "**24 checks**, all passing." |
| §13, ZH p74 / EN p93 | "**49 项自动检查**" / "**49 automated checks**" |

A third figure appears in `results/ERRATA.md` as quoted by the AI disclosure ("N sections recording
self-reported defects"): the tree held **10**, **11** and **12** at the same time, in different files.

### 13.2 What is actually true

Neither 24 nor 49 was the count of the script that shipped beside them. Measured by running the gate at
the two commits where the PDFs were built:

| commit | what it was | gate printed |
|---|---|---|
| `870c7fd` | the original manuscripts were rebuilt here | **59** (recorded independently in `RELEASE.md` and in that commit's own message) |
| `30c2ea3` | the erratum manuscripts were rebuilt here | **60** |

The ERRATA section count was wrong in the same way, and **§12 of this document is what made it wrong**:
the disclosure says "11 sections", `ERRATA.md` had 11 sections numbered `§1`–`§11` when that sentence was
written, and §12 was appended without the sentence being revisited. Adding a section to the audit trail
invalidated the count of the audit trail in the paper that cites it.

### 13.3 Why it survived — and why this is the second time

`src/analysis/p59_author_and_disclosure.py` had already caught this exact defect once. Its docstring
records the finding and the reasoning:

> the draft said "31 automated checks" and "ten sections of self-reported defects", but verify_all.py
> now runs 49 checks and ERRATA.md has 11 sections. **A disclosure containing a stale count would be
> self-refuting in a paper about unverified numbers**, so the text states the current figures.

The reasoning was right and the fix did not hold, **because the fix was two more handwritten numbers.**
31 → 49 and ten → 11 were typed in by hand, nothing read them afterwards, and the script grew past 49
while a section was appended to this file. This is the defect the paper documents, committed by the
script written to prevent it: a value correct at the moment it was written and attached to an object
that moved.

### 13.4 Where it had propagated

| file | what it said | disposition |
|---|---|---|
| `paper/09-10-11-discussion-limits-repro-draft.md:173` | "24 项检查" | → the gate's own figure |
| `paper/en/09-10-11-discussion-limits-repro.md:276` | "24 checks" | → the gate's own figure |
| `paper/13-ai-disclosure-draft.md:26` | "49 项自动检查" | → the gate's own figure |
| `paper/en/13-ai-disclosure.md:40` | "49 automated checks" | → the gate's own figure |
| `paper/13-ai-disclosure-draft.md:29` | ERRATA "11 节" | → counted from `ERRATA.md` |
| `paper/en/13-ai-disclosure.md:47` | ERRATA "11 sections" | → counted from `ERRATA.md` |
| `README.md:24`, `RELEASE.md:10,151`, `PUBLISHED.md:130`, `SUBMISSION-PLAN.md:15`, `HOW-TO-SUBMIT.md:84,129`, `OUTREACH.md:164,173` | "59 checks" / "59 项检查" / "59-check suite" | → the gate's own figure |
| `README.md:89,126`, `paper/AI-DISCLOSURE-DRAFT.md:51` | ERRATA "10 sections" | → counted from `ERRATA.md` |
| `ZENODO-EDIT-VS-VERSION.md:52` | ERRATA "12 节" | → counted from `ERRATA.md` |

Two kinds of site are **deliberately excluded, and must not be "corrected" later**:

- **`recon/` uses the word in a different sense.** "120 checks/run" and "69,120 checks" are battery and
  run sizes, not the gate's size. A blanket rule over the repository would have flagged them.
- **Lab records state what was true when they were written.** `results/RERUN-REPORT.md` records
  "48 passed, 1 warning, 0 failures (49 checks)" as the output of a run at that time, and `NEXT-STEPS.md`
  records "(47 checks)". Rewriting those would destroy the record rather than fix it.

### 13.5 What was added so it cannot recur

`paper/verify_all.py` gains two checks, and **the numbers they enforce are derived, never typed**:

1. **`L1`** counts the numbered sections of `results/ERRATA.md` and requires every document that states
   that count to state it correctly.
2. **`L2`** requires every document that states the gate's own size to state the size the gate is about
   to print. `L2` computes that figure as `len(results) + 1` at the moment it runs, so it is true by
   construction rather than by maintenance.

Both scan **only** the documents that assert the current state of the tree; the two excluded classes
above are named in the check's own comment, so the exclusion is a decision on the record rather than an
oversight.

`src/analysis/p97_sync_declared_counts.py` rewrites those sites, and takes both figures from their
sources: it **runs the gate and parses the total the gate prints**, and it **counts `ERRATA.md`**. The
difference from `p59` is the whole point — this correction cannot go stale the way that one did, because
there is no number in it to go stale.

---

## 14. An upstream status stated as current, which stopped being current in nine hours

**Status: corrected in both manuscripts, with the confirmation now dated. `OUTREACH.md`'s status block
is generated from the APIs rather than typed.**

### 14.1 What was printed

Defect 6 ended its description of the `noul` label defect with:

> **独立复现者三人**（报告者、MrJev、AlKor13），**维护者已确认这是当前最重要的未修复缺陷**，并指出成因**未定**
>
> **Three independent reproducers** (the reporter, MrJev, AlKor13), and **the maintainer has confirmed
> it as the most important open defect**, with the cause **undetermined**

Present tense, no date, and no indication of when it was confirmed.

### 14.2 What is actually true

`NandhaKishorM/laya#156` was **closed on 2026-09-23T13:43:43Z**, `state_reason=completed`.

The erratum manuscript carrying that sentence was assembled at **04:55:23Z** the same day. **The claim
was true for eight hours and forty-eight minutes.**

What landed, in order:

| when (UTC) | what |
|---|---|
| 2026-09-23T13:43:41Z | **#163 merged** — an opt-in `labels` override, so the label-word effect can be measured without changing defaults |
| 2026-09-23T13:43:43Z | **#156 closed** (completed) |
| 2026-09-23T17:44:38Z | **#249 merged** — **authored in this project**: a `noul` `criteria` dict keyed anything other than `true`/`false` is now an **error** instead of being silently replaced by the default pair. Verified by a third party on 0.3.11 |

**What did not change is the defect.** The maintainer, closing it: *"The English-checkpoint bias itself
needs a retrained checkpoint, so this stays open."* The bias is still present; what is fixed is its
**measurability** and the **silent substitution**. The manuscript now says exactly that, and dates the
confirmation to 2026-09-22.

One caveat on the mitigation, measured by a third party on 0.3.20: the `labels` override **helps on
`laya` but is worse than the default on `laya-typed-decisions`** — so it is checkpoint-dependent, and a
reader should not take it as a general remedy. The manuscript records this next to the mitigation rather
than presenting the override as sufficient.

### 14.3 Why nothing caught it

**No check in this project reads an *external* status.** Every check in `verify_all.py` compares the
paper against the repository's own artifacts, and the state of somebody else's issue tracker is not in
the repository. A claim about the outside world is the one class of statement the gate structurally
cannot hold.

The blast radius was one sentence, and that was **luck rather than method**: enumerating every
`github.com/…/(issues|pull)/N` across all 21 manuscript source files finds **exactly one** upstream
link — `NandhaKishorM/laya#156`, cited in `paper/03-systems-draft.md` and
`paper/en/03-04-systems-method.md`. A paper with twenty upstream links would have had twenty stale
claims, and nothing would have said so.

### 14.4 A second status, wrong in the other direction — and the paper was already right

`typesafe-ai/typesafe-sdk-python#11` was **closed as `not_planned`** on 2026-09-24. The closing replies
say the report was filed against a project that does not own the code:

> `jev_check` is not an official TypeSafe tool or endpoint. It comes from third-party community MCP
> servers … The verdict mapping and `jev_check` harness do not exist in the official SDK.

**No manuscript change follows from that, because the manuscript never made the claim.** Checked
against the text:

| the manuscript says | where |
|---|---|
| the Jev-side **access layer** whose self-reported fields are synthesised is **the DSH plugin** | `paper/03-systems-draft.md:16,30` (EN `03-04-systems-method.md:25,40`) |
| an access-layer finding must not be written as an engine finding — the same rule that forbids "Convai's Laya misreports truncation" | `paper/03-systems-draft.md:33-36` (EN `:46,295`) |
| the verdict-vocabulary finding says "**the plugin's** actual vocabulary has only five" | `paper/en/06-07-results-BC.md:184` |

So the error was **in the venue, not in the attribution** — the same family as everything else in this
file, committed in the outreach rather than in the paper. It is recorded in `OUTREACH.md`, and the
project's contribution to the thread is that a maintainer asked for a human reply rather than an
agent's.

### 14.5 What was added

- Both manuscripts state the confirmation **with its date** and carry a dated status paragraph, so a
  reader who follows the link to a closed issue finds the paper already saying it closed.
- **`src/analysis/p99_refresh_outreach_status.py`** regenerates `OUTREACH.md`'s status block **from the
  GitHub and Zenodo APIs**. That document had been hand-corrected twice and gone stale twice — §13's
  lesson, applied to a second document, where the durable fix is again to stop writing the figures down.

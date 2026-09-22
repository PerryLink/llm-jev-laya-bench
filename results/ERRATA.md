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

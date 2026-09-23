# R13 — Laya Live Probe: Real Operating Characteristics

**Unit:** R13 (recon/probe)
**Date of measurements:** 2026-09-22, 00:38–01:05 local (UTC+8)
**Method:** live calls only. Every headline number below is backed by a call made in this session.
**Entry points used:** plugin tools (`laya_ask`, `laya_noul`, `laya_plan`), MCP tools (`mcp__laya__*`), and direct HTTP to the sidecar the plugin tools wrap (`http://127.0.0.1:8787`).

> **Labeling convention.** Every section ends with **OBSERVED** (a value a call returned, or a line of a file I read) and **INFERRED** (my reasoning on top of it). Nothing in OBSERVED is a guess. Where the sample is too small to support a claim, I say so in the same sentence as the claim.

---

## 0. Availability: the sidecar was down, and I started it

The first calls in this session failed:

```
Error: cannot reach the sidecar at http://127.0.0.1:8787 (fetch failed).
Start it with `laya-mcp serve`, then retry.
```

This was **not** a missing install and **not** a missing checkpoint. The Python package and all three checkpoint snapshots are already on disk; the sidecar process simply was not running. I started it:

```powershell
& 'D:\Projects\laya-family\.venv-laya\Scripts\python.exe' -m laya_mcp serve `
    --model english --also multilingual `
    --model-root D:\Projects\laya-family\_models\laya `
    --device cuda --port 8787 --max-len 1024 --head-max-len 512
```

Ready in ~8 s. First `/health`:

```json
{"ok": true, "loaded": true, "degraded": false, "calls": 0, "failures": 0,
 "last_latency_ms": 0.0, "uptime_s": 1.4,
 "checkpoints": {
   "english":      {"device": "cuda", "max_len": 1024, "head_max_len": 512, "fitted_temperature_buckets": 6},
   "multilingual": {"device": "cuda", "max_len": 1024, "head_max_len": 512, "fitted_temperature_buckets": 0}}}
```

`GET /version` → `{"ok": true, "version": "0.2.1", "primitives": ["noul","choice","score"]}`.
The running package resolves to `D:\Projects\laya-family\laya-mcp-pkg\src\laya_mcp\__init__.py`, so the source tree I read below **is** the code that served these calls. Across the whole session: `calls: 202, failures: 0`.

**OBSERVED.** Sidecar version 0.2.1; device cuda; two checkpoints loaded; zero call failures; the earlier "cannot reach the sidecar" error came from an unstarted process.
**INFERRED.** Any "Laya is unavailable" conclusion drawn from that error is an artefact of process lifecycle, not of capability. Per `HANDOFF.md` §3 the sidecar is known to die silently, so the experiment harness must health-check and relaunch rather than assume.

---

## 0b. THE TWO ENTRY POINTS ARE TWO DIFFERENT HOSTS — read this before anything else

This is the single most consequential thing I found, and it invalidates any protocol that says "call Laya" without saying *which* Laya.

During the probe I noticed `budget_summary.head_max_len` was sometimes `192` and sometimes `512` for the same checkpoint. It is not random. It correlates perfectly with **which tool family** I called:

| Entry point | Reaches | Planner `max_len` | Planner `head_max_len` |
|---|---|---|---|
| Plugin tools `laya_ask` / `laya_noul` / `laya_plan` | HTTP sidecar **pid 45708**, port 8787, started with `--max-len 1024 --head-max-len 512` | **1024** | **512** |
| MCP tools `mcp__laya__laya_*` | stdio MCP server **pid 34292**, launched as `laya_mcp mcp --model-root ...` with **no budget flags** | **512** | **192** |

Verified by process table (`Get-NetTCPConnection` showed exactly one listener on 8787, pid 45708; `Get-CimInstance Win32_Process` showed pid 34292 running `laya_mcp mcp --model-root D:\Projects\laya-family\_models\laya` and listening on nothing — a stdio server with its own backend).

Same request, both paths, verbatim planner output:

```jsonc
// mcp__laya__laya_plan  {"state":"test", "questions":{"q":{"type":"noul","instructions":"Is this a test?"}}}
{"ok": true, "checkpoint": "english", "max_len": 512, "head_max_len": 192, "exact": false,
 "questions": [{"question_id":"q","type":"noul","option_count":2,"option_tokens_each":49,
   "options_compressed":false,"head_tokens_estimated":106,"state_tokens_estimated":1,
   "state_room_estimated":405,"would_truncate_state":false}],
 "state_chars": 4, "fits": true, "warnings": [], "recommendation": null,
 "worst_question": "q", "tightest_option_tokens_each": 49}

// POST http://127.0.0.1:8787/plan  — identical request body
{"ok": true, "checkpoint": "english", "max_len": 1024, "head_max_len": 512, "exact": false,
 "questions": [{"question_id":"q","type":"noul","option_count":2,"option_tokens_each":49,
   "options_compressed":false,"head_tokens_estimated":106,"state_tokens_estimated":1,
   "state_room_estimated":917,"would_truncate_state":false}],
 "state_chars": 4, "fits": true, "warnings": [], "recommendation": null,
 "worst_question": "q", "tightest_option_tokens_each": 49}
```

Note `state_room_estimated`: **405 vs 917 tokens for the same question**. Below, "Path A" = plugin/8787, "Path B" = MCP/stdio. I report which path produced every number.

**OBSERVED.** Two live Laya hosts with different token budgets answered me in the same session; the tool name determines which.
**INFERRED.** `--max-len`/`--head-max-len` are applied to the `Agent`'s config, and the planner reads the agent's live config, so the CLI flags move the *planner's* arithmetic. §2 shows they do **not** move the runtime clamp.

---

## 0c. Checkpoint identity — read from the local model directory

I did not assume the architecture. These are verbatim reads.

`D:\Projects\laya-family\_models\laya\rl_agent_config.json` (the **english** checkpoint that served every call here):

```json
{"encoder": "answerdotai/ModernBERT-large", "head_layers": 2,
 "max_len": 512, "head_max_len": 192, "max_prefixes": 6,
 "act_costs": {"escalate": 0.5}, "cost_wrong_act": 3.0, "amp_dtype": "bf16",
 "model_name": "rl-agent",
 "temperature": [1.6369030475616455, 1.2514300346374512, 1.983399510383606],
 "temperature_by_options": {
   "choice:3-5": 1.7601518630981445, "choice:6-10": 1.0000158548355103,
   "score:3-5": 1.2514300346374512, "noul:2": 1.983399510383606,
   "choice:11+": 0.10058280825614929, "choice:2": 1.9063563346862793},
 "training": {"updates": 7313, "epochs_completed": 1, "hours": 1.96,
              "world_size": 1, "fine_tuned_from_checkpoint": true}}
```

`D:\Projects\laya-family\_models\laya\encoder\config.json`:

```json
{"architectures": ["ModernBertForMaskedLM"], "model_type": "modernbert",
 "hidden_size": 1024, "num_hidden_layers": 28, "num_attention_heads": 16,
 "intermediate_size": 2624, "vocab_size": 50368, "max_position_embeddings": 8192,
 "local_attention": 128, "layer_types": ["full_attention","sliding_attention","sliding_attention", ...]}
```

Sibling checkpoints: `multilingual/rl_agent_config.json` → `jhu-clsp/mmBERT-base`, `max_len 1024`, `head_max_len 256`, `temperature [1.0,1.0,1.0]`, `temperature_by_options {}` (**uncalibrated**). `typed-decisions/rl_agent_config.json` → `answerdotai/ModernBERT-large`, `max_len 1024`, `head_max_len 256`.

**OBSERVED.** English checkpoint = a 28-layer, 1024-hidden ModernBERT encoder with a 2-layer head, 50368-token vocab; fine-tuned 7313 updates / 1 epoch / 1.96 h. It ships **six fitted per-option-count temperatures**, including `choice:11+ = 0.1006`.
**INFERRED.** `choice:11+ = 0.1006` divides logits by 0.1, i.e. multiplies them by ~10 before softmax — a deliberately sharpened distribution for 11+ option questions. §5 shows the measured consequence.
**NOT ESTABLISHED.** Parameter count (I did not read tensor shapes), pretraining corpus, and whether `typed-decisions` was trained on the same data. Do not put a parameter count in the paper from this file.

---

## 1. BUDGET MAPPING

### 1.1 What the planner actually computes

Read from `D:\Projects\laya-family\laya-mcp-pkg\src\laya_mcp\planning.py` (the running 0.2.1 code):

- `_CHARS_PER_TOKEN = 4.0`, `_SAFETY = 1.15` → `state_tokens_estimated = int(chars / 4.0 * 1.15)`.
- `would_truncate_state = state_tokens_estimated > (max_len - head_tokens - 1)`.
- **`exact: false` in every single response I received** — the sidecar never passes a tokenizer, so the state budget is always a character estimate.
- `fits = not any(would_truncate_state)` — **state only**. Option compression does *not* clear `fits` (see §3.4).

### 1.2 `laya_plan` (plugin tool) is broken in this session

```
Error: tool "laya_plan" returned invalid output: "value.fits" must be a boolean
```

`mcp__laya__laya_plan` works and returns the full plan. `HANDOFF.md` §8 documents this exact failure as a stale ESM module cache in the mounted plugin, curable only by restarting the harness process. The transport endpoint (`POST /plan`) is fine — I used it directly for the sweep below.

### 1.3 Step sweep of the state budget (Path A, `POST /plan`)

Fixed question: `{"q1":{"type":"noul","instructions":"Does the state mention quarterly progress?"}}`, state = repeated English prose padded to an exact character count.

| state chars | `state_tokens_estimated` | `state_room_estimated` | `would_truncate_state` | `fits` |
|---|---|---|---|---|
| 100 | 28 | 910 | false | true |
| 400 | 115 | 910 | false | true |
| 1000 | 287 | 910 | false | true |
| 2000 | 575 | 910 | false | true |
| 3000 | 862 | 910 | false | true |
| **3148** | **905** | 910 | false | true |
| **3166** | **910** | 910 | false | true |
| **3200** | **920** | 910 | **true** | **false** |
| 4000 | 1150 | 910 | true | false |
| 8000 | 2300 | 910 | true | false |

Verbatim, at the two ends:

```jsonc
// chars=100
{"ok":true,"checkpoint":"english","max_len":1024,"head_max_len":512,"exact":false,
 "questions":[{"question_id":"q1","type":"noul","option_count":2,"option_tokens_each":49,
   "options_compressed":false,"head_tokens_estimated":113,"state_tokens_estimated":28,
   "state_room_estimated":910,"would_truncate_state":false}],
 "state_chars":100,"state_tokens_estimated":28,"fits":true,
 "warnings":["noul question(s) q1 have no criteria. ..."],
 "recommendation":null,"worst_question":"q1","tightest_option_tokens_each":49}

// chars=4000
{"ok":true,"checkpoint":"english","max_len":1024,"head_max_len":512,"exact":false,
 "questions":[{"question_id":"q1","type":"noul","option_count":2,"option_tokens_each":49,
   "options_compressed":false,"head_tokens_estimated":113,"state_tokens_estimated":1150,
   "state_room_estimated":910,"would_truncate_state":true}],
 "state_chars":4000,"state_tokens_estimated":1150,"fits":false,
 "warnings":["the state is close to or over its budget, so its tail is likely to be discarded; raise max_len at startup, shorten the state, or set strict=true to refuse instead",
             "noul question(s) q1 have no criteria. ..."],
 "recommendation":"raise `max_len` above 1024 at startup, shorten the state, or split the state across several calls",
 "worst_question":"q1","tightest_option_tokens_each":49}
```

**Planner thresholds** (solve `chars/4*1.15 > room`):

- Path A, 2-option noul carried as a choice (`room = 905`): **3148 chars**.
- Path B, same question (`room = 405`): **1409 chars**.

### 1.4 Option budget, both paths (exact arithmetic, from `/capabilities` and code)

`/capabilities` → english: `state_budget_tokens: 512`,
`option_tokens_at: {"2":49,"4":49,"8":49,"12":42,"20":25,"30":17,"50":10,"77":7,"100":5}`,
`max_options_8_tokens_each: 70`, `high_cardinality_advisory: 20`.

| options | Path A tokens/label (`head_max_len 512`) | Path B tokens/label (`head_max_len 192`) |
|---|---|---|
| 2 | 49 | 49 |
| 3 | 49 | 49 |
| **4** | 49 | **45 ← compression starts** |
| 8 | 49 | 33 |
| 10 | 49 | 27 |
| **11** | **46 ← compression starts** | 25 |
| 12 | 42 | 23 |
| 15 | 34 | 19 |
| 20 | 25 | 15 |
| 30 | 17 | 11 |
| 50 | 10 | 7 |
| 77 | 7 | 5 |
| 100 | 5 | 4 |

**OBSERVED.** The planner is a pure character model: 4 chars/token × 1.15 safety, `exact:false` always. On Path A it begins predicting state truncation at 3148 chars; on Path B at 1409 chars, for the identical question. Option compression starts at 11 options on Path A and at **4** on Path B.
**INFERRED.** The `max_len`/`head_max_len` overrides move the planner but (per §2) not the runtime, so **the two paths have opposite error directions**: Path A's planner is optimistic, Path B's is pessimistic.
**NOT KNOWN.** Whether the planner's char model was ever validated against this encoder's tokenizer. §2 shows it is wrong on the synthetic sweep state — **⚠️ corrected 2026-09-23: by ~1.9× in the OPTIMISTIC (safe) direction on that state, and by up to ~2.2× in the DANGEROUS direction on JSON, code and CJK, which are the inputs the planner's docstring says it serves.** See §2.2's correction block and `results/P31-token-density.json`.

---

## 2. TRUNCATION DAMAGE — the central finding

### 2.1 Method

State = `DECOY + filler(n) + CORRECTION`, where

- `DECOY` = `"The vault access code is AAA-1111."`
- `CORRECTION` = `" Correction: the vault access code is now ZQX-4471."`
- `filler(n)` = repeated English prose padded to `n` chars.

Question (`criteria` supplied, so the noul is carried as a two-option choice):

```json
{"code": {"type": "noul",
  "instructions": "According to the state, is the vault access code ZQX-4471?",
  "criteria": {"true":  "the state gives ZQX-4471 as the vault access code",
               "false": "the state does not give ZQX-4471 as the vault access code"}}}
```

Ground truth is **TRUE** (the correction is present and authoritative in the full state). Two variants: **TAIL** puts the correction last (so truncation removes it); **HEAD** puts it first (so it survives). Real token counts measured with the checkpoint's own tokenizer (`_models/laya/tokenizer/tokenizer.json`, via `tokenizers.Tokenizer`).

### 2.2 Measured real token density

| state chars | real tokens | chars/token |
|---|---|---|
| 135 | 28 | 4.82 |
| 1035 | 168 | 6.16 |
| 2035 | 323 | 6.30 |
| 3035 | 479 | 6.34 |
| 5086 | 804 | 6.32 |

The planner assumes **3.478** effective chars/token (4.0 ÷ 1.15). This encoder actually delivers **≈6.33** on the state built above — **which is not ordinary English prose but one filler sentence repeated 45 times**. On that state the planner over-estimates token count by **≈1.8×**.

> **⚠️ CORRECTED 2026-09-23** (see `results/ERRATA.md` §12). Two things went wrong when the sentence above was carried into the paper, and one thing was never reported at all.
>
> **(a) The object.** 6.33 is a property of *this sweep's synthetic state*, not of English prose. Measured against the shipped tokenizer, real English prose runs **4.31** chars/token on the english checkpoint (`results/P31-token-density.json`). The paper printed "on English prose", which names a different quantity.
>
> **(b) The magnitude.** Re-measuring with the exact constants from `src/instrument/p3_clamp_calibration.py:57-60` gives **6.782** chars/token at 5,080 chars / 749 tokens, not 6.326 — **this table's token column runs about 7–8% high** (at 5,086 chars the table records 804 tokens; 804 would require roughly 5,530 chars at the measured density). The over-estimate on this state is therefore **1.949×**, not 1.82×.
>
> **(c) The direction that matters.** On JSON (2.40), source code (3.24) and Chinese (1.65) the planner **under**-estimates, and the 1.15 safety factor does not cover the gap. Those are the inputs `planning.py`'s own docstring says it serves ("a contract, a log, or an email thread", plus serialised JSON). Full measurements: `results/P31-token-density.json`.
>
> The design instruction at §679 below, which told the project to assume 6.3 chars/token for English prose, was wrong for prose and has been corrected there too.

### 2.3 The runtime clamps at 512, regardless of `--max-len 1024`

`usage.input_tokens_padded` is the real built sequence length (it tracked `state_tokens + 61` exactly for small states, e.g. 434+61=495). It **stops growing at 512**:

| state chars | real state tokens | `input_tokens_padded` | clamped? |
|---|---|---|---|
| 2735 | 434 | 495 | no (434+61) |
| 2935 | 464 | **512** | **yes** |
| 5086 | 804 | **512** | **yes** |

Nothing ever exceeded 512, although the state alone reached 804 tokens and the planner believed `max_len` was 1024.

### 2.4 The flip

| state chars | real tokens | TAIL p | TAIL answer | `truncated`? | `fits` | in_pad | HEAD p | HEAD answer |
|---|---|---|---|---|---|---|---|---|
| 86 | 26 | 0.7626 | TRUE | absent | true | 86 | 0.1953 | false |
| 1286 | 211 | 0.4765 | false | absent | true | 271 | 0.3325 | false |
| 2086 | 335 | 0.4143 | false | absent | true | 395 | 0.4581 | false |
| 2486 | 398 | 0.2088 | false | absent | true | 458 | 0.5470 | TRUE |
| 2686 | 429 | 0.2651 | false | absent | true | 489 | 0.7047 | TRUE |
| **2836** | **453** | **0.4034** | **false** | **absent** | **true** | **512** | **0.7861** | **TRUE** |
| 2936 | 469 | **0.2376** | false | absent | true | 512 | **0.7297** | TRUE |
| 3036 | 484 | 0.2376 | false | absent | true | 512 | 0.7297 | TRUE |
| 3136 | 500 | 0.2376 | false | absent | true | 512 | 0.7297 | TRUE |
| **3236** | **515** | 0.2376 | false | **PRESENT** | **false** | 512 | 0.7297 | TRUE |
| 5086 | 804 | 0.2376 | false | PRESENT | false | 512 | 0.7297 | TRUE |

Three results, all from this one table:

1. **The answer flips and the flip is correct evidence of truncation.** At exactly the clamp point (2836 chars / 453 tokens) HEAD = **0.7861 TRUE** (right) vs TAIL = **0.4034 false** (wrong). By 2936 chars they have separated cleanly: HEAD 0.7297 vs TAIL 0.2376.
2. **The outputs freeze.** From 2936 to 5086 chars — a 2150-character span — TAIL returns *bit-identical* `0.2376` and HEAD *bit-identical* `0.7297`. Identical outputs mean identical effective input: the model stopped seeing new text. This is the cleanest available proof that the tail is gone.
3. **`truncated` does not tell you.** It is **absent** at 2836, 2936, 3036 and 3136 chars, with `fits: true` and no warning, even though truncation had already destroyed the deciding evidence. It first appears at **3236 chars**.

### 2.5 The silent window, quantified

- Real truncation begins at `state_tokens > 512 − head_tokens − 1`. For this question (`head_tokens = 61`) that is **> 450 tokens ≈ 2850 chars**.
- Path A's planner first warns at **3148 chars**.
- → **Path A silent window ≈ 2850–3148 characters (≈ 300 chars, ≈ 47 tokens)** in which the tail is discarded, `fits` is `true`, `truncated` is absent, and no warning fires.

### 2.6 Path B makes the opposite error — false positives

`mcp__laya__laya_ask`, state = 1399 chars (21 repetitions of a sentence + the marker), same question:

```json
{"ok": true,
 "answers": {"code": {"type":"noul","noul":0.8719,"confidence":0.8719,"band":"yes", ...}},
 "usage": {"input_tokens_padded": 265, "output_tokens": 0, "questions": 1, ...},
 "truncated": {"state": {"estimated": true, "state_chars": 1399, "state_tokens_estimated": 402,
   "note": "the state exceeded its token budget and Laya keeps the FRONT of it, discarding the tail; the answer is about the surviving prefix only"}},
 "warnings": ["the state is close to or over its budget, so its tail is likely to be discarded; raise max_len at startup, shorten the state, or set strict=true to refuse instead"],
 "budget_summary": {"fits": false, "head_max_len": 192, "tightest_option_tokens_each": 49,
   "recommendation": "raise `max_len` above 512 at startup, shorten the state, or split the state across several calls"}}
```

**`truncated` fired, `fits` is false, a warning fired — and no truncation happened.** `input_tokens_padded: 265` against a 512-token budget. The marker survived and the answer (0.8719, "yes") is correct. The planner estimated 402 tokens where the true count was ~221.

**OBSERVED.** Real runtime budget is ~450 state tokens (≈2850 chars for this question) on **both** paths. Path A's `truncated`/`fits`/warning arrive ~300 chars too late. Path B's arrive ~1440 chars too early. The decisive evidence was destroyed and the answer flipped to wrong while every reported field said the request was fine.
**INFERRED.** Root cause is one line of design: the planner estimates tokens as `chars/4×1.15` instead of running the checkpoint's tokenizer it already has loaded. On Path A the error is compounded by `--max-len 1024` reaching the planner but not the runtime clamp.
**NOT VERIFIED.** Why the runtime still clamps at 512 when the planner sees 1024. `worker.py:263-266` writes `agent.cfg["max_len"]=1024` and `_describe` reads it back, so the override *is* applied to the agent object I inspected; the clamp nonetheless stayed at 512. I did not isolate the mechanism, and the paper should not assert one.

---

## 3. OPTION-COUNT DEGRADATION

### 3.1 Setup

Identical state (`Ticket 88121 ... charged twice ... duplicate 49.00 USD charge refunded ...`), one option (`billing`) is unambiguously correct, distractor sets grown from a shared pool. Path A (`laya_ask`).

### 3.2 Ladder

| options | `choice` | p(top) | `confidence` | correct? | `tightest_option_tokens_each` | `truncated` | `warnings` |
|---|---|---|---|---|---|---|---|
| 2 | billing | 0.9700 | 0.8055 | ✅ | 49 | absent | none |
| 5 | billing | 0.8699 | 0.6530 | ✅ | 49 | absent | none |
| 10 | billing | 0.9466 | 0.8690 | ✅ | 49 | absent | none |
| 15 | billing | **1.0000** | **1.0000** | ✅ | 34 | options | 2 warnings |
| **20** | **mobile_app** | **0.9993** | **0.9981** | ❌ | 25 | options | 1 warning |

20 options, verbatim (trimmed to the informative fields):

```json
{"answers": {"intent": {"choice": "mobile_app",
   "probabilities": {"billing":0.0007,"technical":0,"sales":0,"account_access":0,"shipping":0,
     "cancellation":0,"data_privacy":0,"feature_request":0,"abuse_report":0,"general_feedback":0,
     "onboarding":0,"pricing_question":0,"integration_help":0,"api_usage":0,"performance":0,
     "mobile_app":0.9993,"documentation":0,"partnership":0,"legal_request":0,"other":0},
   "confidence": 0.9981}},
 "truncated": {"options": {"estimated": false,
   "questions": [{"question_id":"intent","option_count":20,"tokens_each":25}],
   "note": "options were re-cut below the 48-token ceiling to fit head_max_len, so labels may no longer be distinguishable from one another"}},
 "budget_summary": {"fits": true, "head_max_len": 512, "tightest_option_tokens_each": 25,
   "recommendation": "question 'intent' has 20 options and this checkpoint keeps them distinguishable to about 70; raise `head_max_len` at startup, shorten the label text, or shard the choice into two steps"},
 "warnings": ["question 'intent' has 20 options sharing 512 tokens, which is ~25 tokens per label; choice accuracy falls off sharply in this range"]}
```

15 options additionally produced:

```json
"warnings": ["question 'intent' leaves only 8 tokens for its own instructions, so the question text is being cut",
             "question 'intent' has 15 options sharing 512 tokens, which is ~34 tokens per label; choice accuracy falls off sharply in this range"]
```

### 3.3 Practical ceiling

- Compression begins at **11 options** (Path A) / **4 options** (Path B).
- Correct and saturated through **15** options on this item.
- Catastrophically wrong at **20** options, and **reproduced bit-identically** on a second identical call (`mobile_app 0.9993`, `confidence 0.9981` both times).
- The observed break is therefore in **(15, 20]** — one item per rung, so this brackets a ceiling, it does not estimate an accuracy curve.

### 3.4 `fits` does not cover options — a protocol trap

In the 20-option response, `truncated.options` is present and a warning fires, yet **`budget_summary.fits` is `true`**. In `planning.py`, `fits = not any_truncation`, and `any_truncation` only considers `would_truncate_state`. The module docstring claims `fits` is true only "when no state truncation is expected **and no question's options were compressed hard enough to be unreadable**". The code does not implement the second clause.

**OBSERVED.** Accuracy held at 2/5/10/15 options and collapsed at 20; the two 20-option calls were identical; `fits:true` coexists with `truncated.options`.
**INFERRED.** The saturation at 15 (1.0000) and 20 (0.9993) is the shipped `choice:11+ = 0.1006` temperature at work: near-10× logit sharpening turns a shaky argmax into a 0.9993 assertion. The sharpening does not create the error; it makes the error maximally confident and removes the distribution shape that would have revealed it.
**NOT VERIFIED.** That the argmax would have been correct at 20 options without the temperature sharpening — I did not run a modified checkpoint. Do not claim the temperature *caused* the wrong label.

---

## 4. CALIBRATION SEED DATA

12 items, Path B (`mcp__laya__laya_noul`, boundaries supplied). Ground truth is my own annotation; the two ambiguous items have no determinate truth and are excluded from scoring.

| # | class | state (trimmed) | question | truth | `noul` | `confidence` | `band` | correct? |
|---|---|---|---|---|---|---|---|---|
| 1 | clear T | invoice INV-2291 paid in full 12 April | paid in full? | TRUE | 0.6021 | 0.6021 | uncertain | ✅ |
| 2 | clear F | INV-2291 remains unpaid, 45 days overdue | paid in full? | FALSE | **0.5598** | 0.5598 | uncertain | ❌ |
| 3 | clear T | server responded HTTP 503 | 503? | TRUE | 0.9825 | 0.9825 | yes | ✅ |
| 4 | clear F | server responded HTTP 200 | 503? | FALSE | 0.0558 | 0.9442 | no | ✅ |
| 5 | clear T | prescribed 10-day amoxicillin | prescribed? | TRUE | 0.7603 | 0.7603 | yes | ✅ |
| 6 | clear F | penicillin allergy; amoxicillin withheld | prescribed? | FALSE | 0.3337 | 0.6663 | uncertain | ✅ |
| 7 | clear T | shipment arrived in Oslo 6 May | arrived? | TRUE | 0.8013 | 0.8013 | yes | ✅ |
| 8 | clear F | shipment returned to warehouse | arrived? | FALSE | 0.2271 | 0.7729 | no | ✅ |
| 9 | ambiguous | renewal charged; customer disputes | charged twice? | — | 0.3698 | 0.6302 | uncertain | n/a |
| 10 | ambiguous | revenue broadly flat, EMEA grew 4% | did revenue grow? | — | **0.5001** | 0.5001 | uncertain | n/a |
| 11 | adversarial | *"Your app is broken"* but logs show no errors and the charge was duplicated | primarily a technical bug report? | FALSE | **0.6132** | 0.6132 | uncertain | ❌ |
| 12 | adversarial | *"You won a free iPhone"* from `paypa1-secure.ru`, asks for password | phishing? | TRUE | 1.0000 | 1.0000 | yes | ✅ |

**Determinate items: 10. Correct: 8. Accuracy 0.80.**

### 4.1 Crude reliability table (determinate items only)

| p bin | n | correct | empirical accuracy | mean stated p |
|---|---|---|---|---|
| [0.0, 0.5) | 3 (items 4, 6, 8) | 3 | 1.00 | 0.21 |
| **[0.5, 0.6)** | **1 (item 2)** | **0** | **0.00** | 0.56 |
| [0.6, 0.8) | 3 (items 1, 5, 11) | 2 | 0.67 | 0.69 |
| [0.8, 1.0] | 3 (items 3, 7, 12) | 3 | 1.00 | 0.93 |

### 4.2 This table is not evidence of calibration

**State this in the paper explicitly.** With n=10 determinate items, accuracy 0.80 has a Wilson 95% interval of roughly **[0.49, 0.94]** — it is consistent with near-chance *and* with near-perfect. Every bin above except one contains ≤3 items; the [0.5,0.6) bin contains one. The apparent mid-range over-confidence is exactly the shape a 10-item sample produces by chance, and I am not claiming it.

**Sample size the real experiment needs.** For a per-judge accuracy figure at ±0.05 with 95% confidence, n ≈ 385 items (worst case p=0.5); budget **400 per judge per condition**. For a reliability/ECE curve, ≥10 bins × ≥50 items = **≥500 items**, and ≥1000 to compare two judges' ECE. For a two-judge accuracy difference of 0.10 at 80% power, **≈390 per arm**. The 12 items here are a smoke test for the pipeline, nothing more.

### 4.3 One genuinely good behaviour

Item 10 — a question with no determinate answer — returned **0.5001 / 0.5001 / band "uncertain"**. The model does have a well-behaved "I cannot tell" region for `noul`. This matters because it is the *only* primitive with that escape hatch (see §7).

**OBSERVED.** 8/10 determinate items correct; item 2 (explicit "remains unpaid") answered TRUE at p=0.56; item 11 (adversarial surface cue) answered TRUE at p=0.61; item 10 returned 0.5001.
**INFERRED.** Both errors are in the *same direction*: an explicit negation ("unpaid", "no errors") is not treated as decisive negative evidence. Two errors cannot establish a pattern.
**NOT ESTABLISHED.** Any calibration claim whatsoever. n=10.

---

## 5. CONFIDENCE DECOUPLING

`confidence` is documented in every response as a concentration statistic: `1 − H(p)/log k` for choice/score, `max(p, 1−p)` for noul. I found concrete cases on both sides.

### 5.1 High confidence, wrong

The 20-option call in §3.2:

```json
{"choice": "mobile_app", "probabilities": {"billing": 0.0007, "mobile_app": 0.9993, ...},
 "confidence": 0.9981}
```

Truth: `billing`. **`confidence` 0.9981 — the highest value anywhere in this entire probe — on the only wrong answer.** Reproduced bit-identically on a repeat call. A pipeline that escalated on `confidence > 0.95` would have burned its most confident decision on this.

### 5.2 Low confidence, right

4-option urgency `choice`, low-stakes ticket ("asks whether invoices can be exported to CSV; no deadline"):

```json
{"choice": "not urgent",
 "probabilities": {"not urgent": 0.4833, "low": 0.3837, "high": 0.118, "critical": 0.0149},
 "confidence": 0.2543}
```

Correct at `confidence` **0.2543** — the lowest choice confidence I measured. And calibration item 6: correct "no" at `confidence` **0.3337**.

### 5.3 Two more decouplings worth putting in the paper

**(a) The confidence scale changes meaning with the question's shape.** Identical state, identical prose question, `p ≈ 0.54`:

- bare `noul` (no `criteria`): `confidence` = `max(p,1−p)` → **0.5399**
- same question with `criteria` supplied (carried as a 2-option choice): `confidence` = `1 − H(p)/log 2` → **0.0046**

Same field name, same request, two different scales, differing by a factor of ~117. Any threshold policy that mixes the two forms is meaningless.

**(b) Confidence on inputs that contain no information.** From §7:

- empty state, `choice`: `{"choice":"technical","probabilities":{"billing":0.2683,"technical":0.7317},"confidence":0.1609}` — no warning.
- pure noise state, `noul`: `{"noul":0.0011,"confidence":0.9989}` — near-maximal confidence about a state made of `zxcv qwer asdf 8!! @@##`.

**OBSERVED.** Highest confidence in the probe (0.9981) on a wrong answer; correct answers at 0.2543 and 0.3337; `confidence` 0.5399 vs 0.0046 for the same p depending on framing; 0.9989 on pure noise.
**INFERRED.** The paper's warning is not merely theoretical — measured here at the extremes in both directions. `confidence` carries no information about correctness that `p` does not already carry, and it is not comparable across primitives or across noul framings.
**NOT VERIFIED.** Any monotone relationship between `confidence` and accuracy. Testing that needs the §4.2 sample size.

---

## 6. ORDER SENSITIVITY AND DETERMINISM

### 6.1 Determinism: bit-identical

The same state and the same 3-question batch, sent twice (Path A):

```jsonc
// call 1, latency_ms 266.263
"q_dep_first":  {"choice":"billing","probabilities":{"billing":0.9003,"technical":0.045,"sales":0.0295,"other":0.0252},"confidence":0.6893}
"q_tech_first": {"choice":"billing","probabilities":{"technical":0.0719,"billing":0.8678,"sales":0.03,"other":0.0303},"confidence":0.6223}
"q_rev":        {"choice":"billing","probabilities":{"other":0.0476,"sales":0.0335,"technical":0.0701,"billing":0.8488},"confidence":0.5786}

// call 2, latency_ms 33.053  — byte-for-byte the same answer payload
"q_dep_first":  {"choice":"billing","probabilities":{"billing":0.9003,"technical":0.045,"sales":0.0295,"other":0.0252},"confidence":0.6893}
"q_tech_first": {"choice":"billing","probabilities":{"technical":0.0719,"billing":0.8678,"sales":0.03,"other":0.0303},"confidence":0.6223}
"q_rev":        {"choice":"billing","probabilities":{"other":0.0476,"sales":0.0335,"technical":0.0701,"billing":0.8488},"confidence":0.5786}
```

All probabilities and confidences identical to 4 dp. The 20-option failure also reproduced exactly. **Answers are deterministic; `latency_ms` is not** (266 ms vs 33 ms for the same request — the first included warm-up).

### 6.2 Criteria order: argmax stable, numbers not

The same labels and descriptions, permuted, asked against the same state inside **one** batch:

| criteria order | p(billing) | p(technical) | argmax | `confidence` |
|---|---|---|---|---|
| billing, technical, sales, other | 0.9003 | 0.0450 | **billing** | 0.6893 |
| technical, billing, sales, other | 0.8678 | 0.0719 | **billing** | 0.6223 |
| other, sales, technical, billing (reversed) | 0.8488 | 0.0701 | **billing** | 0.5786 |

- **Chosen label: stable.** `billing` under all three permutations.
- **Probability mass: not stable.** p(billing) spans 0.8488–0.9003 (Δ = 0.0515); p(technical) spans 0.0450–0.0719 (Δ = 0.0269) — a 60% relative change for the runner-up.
- **`confidence`: not stable.** 0.5786–0.6893, **Δ = 0.1107** — a swing far larger than any plausible escalation threshold.

**OBSERVED.** Identical requests are bit-identical. Permuting criteria keys left the argmax unchanged and moved probabilities by up to 0.05 and `confidence` by 0.11. n = 1 label set, 4 labels, 3 permutations.
**INFERRED.** Prompt order is a live nuisance parameter for any numeric use of Laya (thresholds, ranking, calibration, "was it close?"), and a non-issue for pure argmax use. The protocol should freeze one canonical criteria order rather than merely record it.
**NOT ESTABLISHED.** That argmax is *always* order-stable. One label set where the winner led by 0.16 is the easy case; a near-tied argmax is exactly where permutation could flip it, and I did not find one.

---

## 7. FAILURE MODES

All Path B, `mcp__laya__laya_ask`.

### 7.1 Empty state — accepted silently

`state: ""`, one `noul` + one `choice`:

```json
{"ok": true,
 "answers": {
   "c": {"type":"choice","choice":"technical",
         "probabilities":{"billing":0.2683,"technical":0.7317},"confidence":0.1609},
   "q": {"type":"noul","noul":0.266,"confidence":0.734,"band":"no"}},
 "usage": {"input_tokens_padded": 78, "output_tokens": 0, "questions": 2},
 "budget_summary": {"fits": true, "head_max_len": 192, "tightest_option_tokens_each": 49}}
```

**No error. No `truncated`. No `warnings`. HTTP 200, `ok: true`.** A confident-looking intent label from a state containing zero characters.

### 7.2 Pure-noise state — accepted, and maximally confident

`state: "zxcv qwer asdf 8f3a 99!! @@## %%^^ &&** (( )) __ ++ == ~~ || // .. ,, ;; 7g6h 5j4k l2m3 n1b0 vcxy zuts rqpo"`:

```json
{"ok": true,
 "answers": {
   "c": {"type":"choice","choice":"technical",
         "probabilities":{"billing":0.3668,"technical":0.6332},"confidence":0.0518},
   "q": {"type":"noul","noul":0.0011,"confidence":0.9989,"band":"no"}},
 "usage": {"input_tokens_padded": 190, "output_tokens": 0, "questions": 2},
 "budget_summary": {"fits": true, "head_max_len": 192, "tightest_option_tokens_each": 49}}
```

Again no error, no warning. The `noul` returns **0.0011 at confidence 0.9989** — near-total certainty about a string of keyboard mash.

### 7.3 Near-synonymous option labels — a definite answer to an indefinite question

Four paraphrases of the same request:

```json
{"refund_kind": {"type":"choice","choice":"a",
  "probabilities": {"a":0.4951,"b":0.4736,"c":0.0165,"d":0.0149},
  "confidence": 0.3996}}
```

labels: `a` = "the customer wants a refund", `b` = "the customer is requesting their money back", `c` = "the customer asks for a reimbursement", `d` = "the customer would like to be repaid".

The distribution splits 0.4951 / 0.4736 between two indistinguishable paraphrases, and the API still returns a hard `"choice": "a"`. Plus the Path-B option-compression warning (`tokens_each: 45`).

### 7.4 Genuinely indeterminate — handled well

Item 10 in §4: `{"noul": 0.5001, "confidence": 0.5001, "band": "uncertain"}`. `noul` has a `band` field (`no` / `uncertain` / `yes`) that flags this. **`choice` and `score` have no equivalent** — their only uncertainty channel is a numeric `confidence` with no band and no calibrated meaning.

### 7.5 Does "score is the weakest primitive" hold?

Tested directly: same state, same instructions, one `score` (4 ordered levels) and one `choice` (the same 4 levels as labelled options) in a single batch.

**State A — clearly critical** ("production database is down and all customers are blocked"):

```json
"urgency_choice": {"choice":"critical","probabilities":{"not urgent":0.0091,"low":0.02,"high":0.4065,"critical":0.5645},"confidence":0.416}
"urgency_score":  {"score":2.4371,"probabilities":{"0":0.0022,"1":0.022,"2":0.5122,"3":0.4635},"confidence":0.4254}
```

**State B — clearly trivial** ("asks whether invoices can be exported to CSV; no deadline"):

```json
"urgency_choice": {"choice":"not urgent","probabilities":{"not urgent":0.4833,"low":0.3837,"high":0.118,"critical":0.0149},"confidence":0.2543}
"urgency_score":  {"score":0.0805,"probabilities":{"0":0.9441,"1":0.0329,"2":0.0213,"3":0.0016},"confidence":0.813}
```

- State B: `score` was **decisively right** (P(level 0) = 0.9441, confidence 0.813) where `choice` managed only 0.4833 / confidence 0.2543.
- State A: both were indecisive; `choice` picked the correct top level at 0.5645, while `score`'s expected value (2.4371) landed between levels 2 and 3 because P(2)=0.5122 slightly exceeded P(3)=0.4635.

**`score` was equal or better on both items — the "weakest primitive" self-description did not reproduce here.** n=2. This is a falsification of a doc claim on a tiny sample, not a replacement claim; but given the paper intends to lean on it, it needs a real test with ≥200 items before it is repeated.

**OBSERVED.** Empty and noise states accepted with `ok:true`, no warnings, `fits:true`. Near-synonymous labels yield a hard choice at 0.3996 confidence. `noul` has `band`; `choice`/`score` do not. `score` matched or beat `choice` on 2/2 items.
**INFERRED.** There is no "I cannot answer this" path for degenerate input. The only defensible posture is that the harness owns input validation and must reject empty/noise states itself, because Laya will not.
**NOT ESTABLISHED.** That `score` is generally stronger than `choice`. n=2; the doc may still be right.

---

## 8. THROUGHPUT

### 8.1 Method and its precision limits

- Python `time.perf_counter()` (sub-µs clock resolution) wrapped around `urllib.request` `POST http://127.0.0.1:8787/ask`.
- 3 warm-up calls discarded before each series; warm, persistent sidecar; `cuda`; nothing else running on the GPU.
- **Precision limits:** the clock is not the constraint — the loopback HTTP + JSON encode/decode floor is. From the minimum observed (26.0 ms wall vs 30.0 ms sidecar-reported, i.e. wall can *under*-read the internal timer on some calls), treat anything under ~10 ms as noise, and treat the sidecar's own `latency_ms` as the better estimate of pure inference.
- `latency_ms` returned by the sidecar is its own `time.perf_counter()` around the forward pass.

### 8.2 Laya, local (Path A)

| batch | n | wall mean | wall median | wall p95 | wall min | sidecar mean | per-question |
|---|---|---|---|---|---|---|---|
| 1 question (`noul`) | 30 | 42.8 ms | 37.4 ms | 50.5 ms | 26.0 ms | 30.0 ms | 30.0 ms |
| 5 questions | 15 | 38.4 ms | 34.7 ms | 48.6 ms | 31.5 ms | 30.0 ms | **6.0 ms** |
| 10 questions | 15 | 48.6 ms | 49.8 ms | 56.3 ms | 40.6 ms | 38.9 ms | **3.9 ms** |
| 20 questions | 10 | 79.2 ms | 81.5 ms | 84.1 ms | 66.5 ms | 64.2 ms | **3.2 ms** |

Cold (very first call after model load): **389.894 ms**. Warm-up after that is immaterial.

### 8.3 Jev, remote — the transport floor

`api.typesafe.ai` (the endpoint named in `packages/core` of the jevcore integration), unauthenticated `POST /v1/systemone`, n=6:

```
attempt 1: http_status=403 round_trip=1384.5 ms  {"detail":{"error_type":"authentication_error","message":"Must supply an API key! ..."}}
attempt 2: http_status=403 round_trip=1113.5 ms
attempt 3: http_status=403 round_trip=1361.0 ms
attempt 4: http_status=403 round_trip=1010.9 ms
attempt 5: http_status=403 round_trip=2349.0 ms
attempt 6: http_status=403 round_trip=1086.0 ms
→ min 1010.9 · median 1361.0 · max 2349.0 ms
```

**This is DNS + TCP + TLS + HTTP + a rejection. It contains zero inference, no queueing, and no model work.** Every authenticated Jev decision must be at least this slow, plus inference.

### 8.4 The comparison, stated carefully

- Laya full local decision, 1 question: **~37 ms median wall**.
- Jev remote service *refusing the request*: **~1361 ms median**.
- Laya is ~**36× faster** than the remote service's rejection.
- Batching compounds it: 20 questions in one Laya call costs 3.2 ms/question, ~12× cheaper than 20 separate calls.

**OBSERVED.** All numbers above, from real calls on this machine.
**INFERRED.** Local inference is genuinely faster per decision in wall-clock terms, by a margin large enough that the transport alone settles it — no authenticated Jev measurement is needed to establish the direction.
**NOT MEASURED / CAVEATS.** (i) No authenticated Jev call was made (no API key was used or sought), so **Jev's real per-decision latency is unknown**; the authenticated figure = transport + queue + inference ≥ 1011 ms. (ii) Laya's figures are from *this* machine on *cuda*; a CPU-only host is 10–15× slower per the sidecar's own degraded-mode warning. (iii) The remote path's latency depends on this host's network distance; **re-measure from the experiment host before publishing**. (iv) Cost per decision (money) was not measured.

---

## 9. OBSERVED vs INFERRED — consolidated

**OBSERVED (measured or read verbatim):**

1. Sidecar 0.2.1 was not running; started with the documented command; ready in ~8 s; 202 calls, 0 failures.
2. Two Laya hosts answer this session: plugin tools → 127.0.0.1:8787 with planner `max_len 1024 / head_max_len 512`; MCP tools → a stdio server with planner `max_len 512 / head_max_len 192`.
3. English checkpoint: `answerdotai/ModernBERT-large`, 28 layers, hidden 1024, 2-layer head, vocab 50368; `temperature_by_options` includes `choice:11+ = 0.1006`, `noul:2 = 1.9834`.
4. Planner is a character estimate (`chars/4 × 1.15`), `exact: false` in every response.
5. Real token density on the synthetic sweep state ≈ 6.33 chars/token (**corrected: 6.78**; and **not** ordinary prose — real English prose is 4.31) → planner over-estimates tokens ~1.8× on that state (**corrected: 1.949×**).
6. Real built sequence length clamps at **512** tokens on both paths, despite Path A's planner believing 1024.
7. Real state budget ≈ 450 tokens ≈ **2850 chars** for a 2-option question.
8. Path A: answer flips and outputs freeze at the clamp; `truncated` absent for ~300 chars past the real cut (2850→3148).
9. Path B: `truncated` + warning + `recommendation` fire at 1399 chars where **no truncation occurred** (`input_tokens_padded: 265`).
10. Option ladder: correct at 2/5/10/15, wrong at 20; 20-option failure bit-identical on repeat; compression begins at 11 options (Path A) and 4 (Path B).
11. `budget_summary.fits` is `true` while `truncated.options` is present.
12. Calibration: 8/10 determinate items correct.
13. `confidence` 0.9981 on a wrong answer; correct answers at 0.2543 and 0.3337; `confidence` 0.5399 vs 0.0046 for the same p under two framings; 0.9989 on pure noise.
14. Identical requests → bit-identical answers. Permuted criteria → stable argmax, Δp ≤ 0.052, Δconfidence = 0.111.
15. Empty and noise states → HTTP 200, no error, no warning, `fits: true`.
16. `noul` has `band`; `choice` and `score` do not.
17. `score` matched or beat `choice` on 2/2 items.
18. Latency: 37.4 ms median (1 question) → 3.2 ms/question at batch 20.
19. `api.typesafe.ai` unauthenticated refusal: 1011–2349 ms, median 1361 ms.
20. The plugin `laya_plan` tool errors with `"value.fits" must be a boolean`; `mcp__laya__laya_plan` works.

**INFERRED (my reasoning, not measured):**

1. The silent-truncation hazard is real and its magnitude on Path A is ~300 characters of state.
2. `choice:11+ = 0.1006` is why 15/20-option answers saturate at ~1.0000; it makes errors maximally confident but I did not show it *causes* the wrong argmax.
3. Argument order is a nuisance parameter for anything numeric, and safe for pure argmax — untested at near-ties.
4. Local inference is decisively faster per decision than the remote service; the transport floor alone establishes the direction.
5. The two paths' planner errors are opposite-signed (A optimistic, B pessimistic) and stem from one root cause (no tokenizer in the planner) plus one deployment discrepancy (the `--max-len` override reaching the planner but not the runtime).

**NOT ESTABLISHED / DO NOT CLAIM:** parameter counts; why the runtime clamps at 512 under a 1024 override; any calibration or ECE claim; that `score` is stronger than `choice`; that argmax is always order-stable; Jev's real per-decision latency; Laya's behaviour on non-English text or on `typed-decisions` (not exercised here).

---

## 10. CONSTRAINTS FOR THE EXPERIMENT DESIGN

Every rule below is forced by a measurement above. Each cites its section.

### State size

1. **Express every state budget in TOKENS, never characters**, and measure those tokens with the checkpoint's own tokenizer (`_models/laya/tokenizer/tokenizer.json`). The planner's character model was wrong on the synthetic sweep state (§2.2) — **but ⚠️ CORRECTED 2026-09-23: it was wrong in the SAFE direction on that state and in the DANGEROUS direction on the inputs the planner actually serves.** Measured against the shipped tokenizer: English prose **4.31** chars/token (planner over-reserves 1.239×), but JSON **2.40** (under-reserves 1.450×), source code **3.24** (1.075×), Chinese **1.65** (2.105×) and a CSV table **1.62** (2.150×) — all below the 3.478 break-even, so on those the preflight reports `fits` for a state the model will truncate. **The following instruction in the previous print was wrong for prose and is withdrawn: "assume 6.3 chars/token for English prose".** If the harness cannot tokenize, there is no safe single constant; measure, or reserve for the densest input expected. `results/P31-token-density.json`.
2. **Hard ceiling: 450 state tokens per question** (≈2850 English characters), and lower it by the question's own head cost. The safe formula is `state_tokens ≤ 512 − head_tokens − 1`; the real clamp is 512 regardless of `--max-len` (§2.3).
3. **Safe / warning / silent-cut zones (Path A, 2-option question):**
   - **Safe:** ≤ 400 real tokens (≈2500 chars).
   - **Warning:** 400–450 tokens (≈2500–2850 chars) — approaching the clamp; no flag will tell you.
   - **Silent-cut:** 450–3148 chars-equivalent. **The tail is already gone and every reported field still says the request is fine** (§2.5). This zone is the hazard; it is ~300 characters wide.
   - **Flagged-cut:** > 3148 chars — `truncated` finally appears.
4. **Never place load-bearing evidence at the end of a state.** Put the decisive fact in the first 400 tokens, or restate it early. §2 is a direct demonstration that trailing evidence is the first thing destroyed.
5. **Freeze one deployment.** Pin either Path A or Path B and record it in the methods section. Do not let tool choice float: the two hosts differ by 2× in `max_len`, 2.7× in `head_max_len`, and have opposite planner error signs (§0b).
6. **Reload/health-check the sidecar at the start of every run.** It was down at session start and `HANDOFF.md` §3 records repeated silent deaths. A run that begins with a dead sidecar produces a *zero-accuracy* result that looks like a model property.

### Options

7. **Hard ceiling: 10 options per choice question on Path A; 3 on Path B** (compression begins at 11 and 4 respectively — §1.4). Treat 11–15 as "saturated, unverified" and **never exceed 15** (§3.3).
8. **Treat `tightest_option_tokens_each < 49` as a design failure, not a warning.** The `warnings` string admits "choice accuracy falls off sharply in this range". Shard the question instead.
9. **Do not trust `budget_summary.fits` to mean "the options are fine."** It is state-only; `truncated.options` can be present with `fits: true` (§3.4). Check `truncated` and `warnings` explicitly.
10. **Keep all option descriptions near-equal in length.** Rendered option text shares one token budget, so a long description steals tokens from its siblings.

### Mandatory preflight

11. **Preflight with `mcp__laya__laya_plan`, not the plugin `laya_plan`.** The plugin tool is broken in this session (`"value.fits" must be a boolean` — §1.2). If the harness cannot be restarted, call `POST /plan` on the sidecar directly.
12. **Use the preflight to reject, not to warn.** Because Path B produces false positives and Path A false negatives (§2.5–2.6), `fits` alone is not a sufficient gate. Combine it with a tokenizer-computed state size (rule 1) and an option-compression check (rule 8). Gate on your own arithmetic; use Laya's numbers as corroboration only.
13. **Reject empty, whitespace-only and low-alphabet states in the harness.** Laya answers them at HTTP 200 with no warning (§7.1–7.2). Add a minimum-content check before any call.

### How to treat `confidence`

14. **Never use `confidence` as a probability of correctness, a threshold, or a routing signal.** Measured: 0.9981 on a wrong answer, 0.2543 on a right one, 0.9989 on pure noise (§5).
15. **Never compare `confidence` across primitives or across noul framings.** The noul scale is `max(p,1−p)`; the noul-carried-as-choice scale is `1−H/log k`. The same p gave 0.5399 and 0.0046 (§5.3a). Report `p` (or the full distribution) and never the derived confidence as a primary outcome.
16. **If the paper reports an uncertainty signal at all, use `band` — and only for `noul`.** It is the sole calibrated-looking "I cannot tell" channel (`uncertain` at p=0.5001, §7.4, §4.3). `choice` and `score` have no equivalent; for those, report the full distribution.
17. **Pre-register the escalation rule as a distributional test** (e.g. top-2 margin or entropy) rather than a confidence threshold, and report the margin, so that the 20-option saturation is visible as saturation rather than as certainty.

### Determinism caveats

18. **Freeze one canonical criteria order and use it everywhere.** Argmax was stable under permutation, but probabilities moved up to 0.052 and `confidence` by 0.111 (§6.2). Any numeric comparison across differently-ordered question sets is confounded.
19. **Answers are deterministic, so do not spend budget on repeated identical calls for variance** — reserve repeats for the near-tie case, where order stability is genuinely untested (§6).
20. **Never use `latency_ms` as a stable measurement of the model.** It varies 8× for identical requests (266 ms vs 33 ms; §6.1). Use it only as a distribution over many warm calls, and always discard warm-up.

### Throughput and cost

21. **Re-measure the Jev remote latency from the experiment host with credentials.** My 1011–2349 ms figure is an unauthenticated *refusal* — a floor, not Jev's decision time (§8.3). Publishing it as "Jev's latency" would be wrong.
22. **Report per-question cost at the batch sizes the experiment actually uses.** 30.0 ms at batch 1 vs 3.2 ms at batch 20 (§8.2). A per-decision comparison that batches one judge and not the other is not a comparison.
23. **Record the device and re-measure if it is not `cuda`.** A CPU fallback is 10–15× slower and is reported only in `degraded`, never in the answer.

### Sample size

24. **≥400 items per judge per condition** for an accuracy claim at ±0.05; **≥1000** for a reliability/ECE curve; **≈390 per arm** to detect a 0.10 two-judge difference at 80% power. The 12-item battery in §4 is a pipeline smoke test and must not appear as a calibration result (§4.2).
25. **Before running the main study, re-test the `score`-vs-`choice` claim on ≥200 items.** The "score is weakest" doc claim did not reproduce on the 2 items I ran (§7.5), and the design currently leans on it.

---

### Appendix — reproduction pointers

- Sidecar launch: `HANDOFF.md` §3, `D:\Projects\laya-family\HANDOFF.md`.
- Budget/truncation logic read: `D:\Projects\laya-family\laya-mcp-pkg\src\laya_mcp\planning.py` (esp. `plan_questions`, `truncation_report`, `_PER_OPTION_CEILING`, `_SAFETY`).
- Capability derivation: `...\src\laya_mcp\capability.py` (`option_token_budget`, `max_options`, `to_dict`).
- Override + capability caching: `...\src\laya_mcp\worker.py:256-301, 366-392, 396-449, 520-593`.
- HTTP surface: `...\src\laya_mcp\server.py:102-181` (`/health`, `/capabilities`, `/version`, `/ask`, `/plan`).
- MCP-layer trimming (`budget_summary`): `...\src\laya_mcp\mcp_server.py:498-515`.
- Checkpoint configs: `D:\Projects\laya-family\_models\laya\{rl_agent_config.json, encoder\config.json, multilingual\rl_agent_config.json, typed-decisions\rl_agent_config.json}`.
- Upstream API surface (secondary source, not re-derived here): `D:\Projects\laya-research\LAYA_API_REFERENCE.md`.

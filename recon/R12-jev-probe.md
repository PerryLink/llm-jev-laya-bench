# R12 — Jev probe: operating characteristics

**Unit:** recon/probe R12 · **Date of probes:** 2026-09-22 · **Tools:** `jev_ask`, `jev_check`, `jev_rank` (DSH plugin `jevcore-dsh` v0.4.1)
**Scope measured:** TypeSafe Jev only (Laya is a separate sidecar and was out of remit).

---

# ⛔ MOCK PROVIDER — MEASUREMENTS VOID

**Every number in this file that looks like a probability is a hash of my own input. None of it is a Jev measurement.**

Every successful Jev call in this session returned, verbatim:

```json
{
  "provider": "mock",
  "model": "jev-latest",
  "latencyMs": 0,
  "usage": { "inputTokens": 0, "outputTokens": 0, "costUsd": 0 },
  "warning": "These answers are SYNTHETIC. The mock provider derived them from a hash of the input; they carry no judgment. Set provider to \"live\" or \"openrouter\" with a credential for real answers."
}
```

The deciding config is one line, in the plugin's installed patch layer:

`C:\Users\zzhdz\.dsh\profiles\web\node_modules\jevcore-dsh\cordis.patch.yml`

Reproduced verbatim (19 lines, whole file):

```yaml
- insert:
    - id: jev
      name: 'jevcore-dsh'
      config:
        # Offline by default. With `provider: mock` this plugin makes no network
        # call at all; every answer is synthetic. See the "Egress contract"
        # section of the README for exactly what each provider sends.
        provider: mock

        # Judging tool calls, and reading tool results, both send content to a
        # third party. Both stay off until you turn them on. `enabled` accepts
        # the literal true/false, so `safety: false` also works as shorthand.
        gates:
          safety:
            enabled: false
            # What to do when Jev cannot decide: ask the human, allow, or deny.
            onUndecided: ask
          context:
            enabled: false
```

The plugin's own `docs/limits.md` §4 states the mechanism and calls the mock what it is:

> **Determinism.** Each answer is FNV-1a over `questionId + "\u0000" + JSON.stringify(state)`, rounded to four decimals (`packages/core/src/provider/mock.ts:35-51` and `:88`).
> **What it ignores is the point.** … The instructions, a noul's `criteria`, and a choice's option descriptions never enter the hash … **Rewrite a question so it means the opposite and the number does not move.**
> Read a mock answer as a fixture, never as a judgment: it is a hash of your own input. **Do not tune a threshold against it.**

**Rule for every reader downstream: nothing in this file may be quoted as a Jev measurement, a Jev probability, a Jev calibration datum, or a Jev latency.**

## Salvage count (item 1 of the lead's instruction)

| Outcome | Count | Signature |
|---|---|---|
| Successful mock responses | **62** | `provider: "mock"`, `latencyMs: 0`, `inputTokens: 0`, `outputTokens: 0`, `costUsd: 0`, SYNTHETIC `warning` present |
| Refused before the provider | **6** | error string only — no `provider`, no `usage`, no `egress` |
| **`provider` != `"mock"`** | **0** | — |
| Non-zero `latencyMs` / `inputTokens` / `costUsd` | **0** | — |
| Total Jev tool invocations | **68** | — |

**No real datum exists.** Not one call reached a live model.

Two envelope defects found while counting, both material:

1. **One mock response carried no `warning` field at all.** `jev_rank` with `candidates: []` returned the complete raw body `{"provider":"mock","model":"","latencyMs":0,"ranking":[]}` — no `warning`, no `usage`, no `egress`, and `model` is an **empty string** rather than `jev-latest`. A short-circuiting call therefore looks *cleaner* than a normal one. **Detecting the mock by the absence of a warning is unsound; detect it by `provider == "mock"`.**
2. **`model` is not a reliable mock marker either.** The vendor doc says the mock reports `mock/jev-synthetic` "unless a model was configured"; the profile configures the default `jev-latest`, and all 62 responses said `"model": "jev-latest"` — indistinguishable from a live model id.

---

# PART 1 — CONFIRMED INTERFACE FACTS (these survive the mock)

Every fact below is either (a) enforced by the plugin before/around the provider call, or (b) reproducible from the vendor's shipped source and confirmed by my calls. They remain true after a credential is installed.

## 1.1 The mock's exact contract — verified empirically

I did not take the doc's word for it; these are my measurements.

| Probe | State/question delta | Result | Verdict |
|---|---|---|---|
| Identical call repeated | none | `0.4253 / 0.9751` both times — bit-identical | deterministic |
| One character changed | `doc_id` `INC-2024-11-03-A` → `-B`; body byte-identical | `0.4253/0.5751` → `0.139/0.861`; **`answer` flipped `true`→`false`** | hash, not judgment |
| Question **id** changed | `sat` → `sat_b`; instructions identical | `0.7941` → `0.2317` | question id **is** hashed |
| **Instructions rewritten** | `"satisfied"` → `"pleased"` | `0.7941` → **`0.7941`** | instructions **not** hashed |
| **Boundary declared vs not** | none → boundary A → boundary B | **`0.7941` three times, delta `0.0000`** | boundary **not** hashed |
| Choice, 20 options, repeated | none | identical ranking and identical `questionsChars: 3341` | deterministic |

Raw, from the boundary-sensitivity triple (same state, same question id, same instruction text, three different boundaries; `questionsChars` 87 → 240 → 227 proves the boundary *was* serialised and counted, yet the answer did not move):

```json
{"question":"sat","type":"noul","answer":"true","band":"yes","noul":0.7941,"probability":0.7941}
{"question":"sat","type":"noul","answer":"true","band":"yes","noul":0.7941,"probability":0.7941}
{"question":"sat","type":"noul","answer":"true","band":"yes","noul":0.7941,"probability":0.7941}
```

**Consequence:** a boundary-sensitivity experiment run on the mock returns **exactly zero delta** and would "prove" that boundary wording is irrelevant. That is a false negative produced by the fixture, not a finding about Jev. This is the single most dangerous trap in the original remit.

`confidence` is a hard-coded constant under the mock — **0.5 in all 4 choice and all 2 score responses**, independent of option count (max option probability ranged 0.6969 → 0.1123) and independent of correctness. Doc: `MOCK_CONFIDENCE`, `mock.ts:32`. Nothing about concentration or accuracy may be read from it.

## 1.2 Budget and plumbing envelope (provider-independent)

| Fact | Measured | Notes |
|---|---|---|
| `state` cap | **16,000 characters**, truncate-not-refuse | 4,180-char state → `truncated: false`; ~17.3k-char state → **`"truncated": true` at top level AND `egress.truncated: true`, `egress.stateChars: 16000`** |
| `truncated` top-level field | present **only** when truncation happens | absent (not `false`) on all normal responses |
| `questions` cap | **4,000 characters**, refuse-not-truncate | for `jev_rank`; see below |
| `egress` block | `{truncated, stateChars, questionsChars, redactedFields, redactedValues, redactionRules, redactions}` | present on all three tools |
| Routing | `jev_ask`, `jev_check`, `jev_rank` all route through one path | all 62 responses carry the same envelope shape |

Rank batch cap, measured and matched against the vendor's published table:

| Criterion length | N | `questionsChars` | Outcome |
|---|---|---|---|
| 376 | 5 | 2,511 | accepted |
| 376 | 7 | 3,515 | accepted |
| 376 | 8 | *(4,017)* | **refused** |
| 376 | 10 | *(5,021)* | **refused** |
| 40 | 5 | 831 | accepted |
| 40 | 20 | 3,341 | accepted |

Exact refusal text (verbatim):

```
Error: "questions" for "tool:jev_rank" is 5021 characters, over the declared limit of 4000. Send fewer or smaller questions. This is refused rather than truncated because answers are keyed by question, so a shortened question map would return answers that cannot be matched to what was asked.
```

Per-candidate cost is `126 + len(criterion)`, confirmed at four points; my measured `L=40, N=20 → 3341` reconciles exactly with the vendor's table entry `L=69, N=20 → 3921` (Δ580 = 20 × 29). Operative rule: **`N_max ≈ floor(3999 / (126 + len(criterion)))`**, with the documented exact boundary `L=69 → 20`, `L=400 → 7`, `L=1,000 → 3`. A long criterion costs candidates one-for-one, and a refused batch **cannot** be fixed by retrying.

Also documented and protocol-relevant (`docs/limits.md`): **an over-long candidate list is truncated inside `state`, and every candidate still returns a score that describes the fragment** — the ranking looks complete while having judged part of the input.

## 1.3 Pre-provider validation matrix (fires regardless of provider)

These are enforced by the plugin before any provider call, so they are genuine interface constraints.

| Input | Result | Exact error / behaviour |
|---|---|---|
| `choice` with 1 criterion | **refused** | `Error: question "cause" is choice but declares 1 criteria` |
| `choice` with 0 criteria | **refused** | `Error: question "cause" is choice but declares 0 criteria` |
| `noul` with empty instructions | **refused** | `Error: question "q" has empty instructions. A string, object or array is accepted, but it has to say something: an empty one leaves the model nothing to judge.` |
| Empty `questions` map | **refused** | `Error: a Jev request needs at least one question` |
| `choice` with **25** options | **accepted** | full 25-way distribution returned, sums to 1.0000 |
| `jev_rank` with 0 candidates | **accepted** | degenerate envelope `{"provider":"mock","model":"","latencyMs":0,"ranking":[]}` — no warning/usage/egress |
| `jev_check` with empty claim **and** empty evidence | **accepted** | returned `"verdict": "conflicted"` — **no validation on check inputs at all** |
| Empty state (`""`) | **accepted** | `stateChars: 2`, answer returned |
| Unknown question `"type": "ranking"` | **accepted, silently coerced** | response came back `"type": "score"` with a 2-level legend |

The last row is a real hazard: **a typo in `type` does not error — it silently changes which primitive answers.** A `choice` intended as a classification can return a `score` envelope that a naive harness will record as a classification.

## 1.4 Response schema semantics (inferred from 62 responses; consistent in every one)

**`noul`.** `noul` is the score; `answer` is `noul >= 0.5`; **`probability` is P(the answered option), not P(true)** — `probability == noul` when `answer` is `"true"` and `probability == 1 - noul` when `answer` is `"false"`. This held in all 62 responses. *Any harness that records `probability` as P(true) will silently invert roughly half its items.*

**`band`.** Consistent with a 0.7 confidence band on the answered option: `"yes"` observed only at `probability ≥ 0.7441` (not at 0.6998), `"no"` only at `probability ≥ 0.7195` (not at 0.6998), `"uncertain"` otherwise. Both brackets contain the documented default **`minConfidence: 0.7`**. (INFERRED: the band is the confidence gate; the exact constant was not read from source.)

**`choice`.** Returns the winner, its `probability`, the **full `probabilities` map over every declared key**, and a constant `confidence`. Distributions are normalised (verified summing to 1.0000 at N=2, 5, 20, 25). Full distributions *are* obtainable — the paper can report them.

**`score`.** Returns `answer` (the argmax level's *description string*), a numeric `score`, a `legend` mapping integer index → description, and per-level `probabilities`. Verified exactly twice: **`score` = Σ(index × probability)** — `0.2089×0 + 0.2099×1 + 0.1969×2 + 0.1151×3 + 0.2692×4 = 2.0258`, matching the returned `score`. **`score` and `answer` can disagree**: score 2.0258 (≈ level 2) was returned alongside `answer` = level 4, because `answer` is the argmax and `score` is the mean. Scale direction is whatever order the `criteria` map is written in, and `legend` echoes that order with 0-based indices.

**`check`.** Verdict vocabulary, read from `src/check.ts`: `['supported','contradicted','conflicted','insufficient','undecided']` — **`unknown` is not in the plugin's list**, although the tool description offered to me lists it. The tool's own `reconcileVerdict` applies exactly two rewrites on top of the core resolver:
- `supported` with **no** sufficiency answer → `insufficient`
- `insufficient` while its own sufficiency answer is `>= thresholds.sufficiency` → `undecided`

All 11 of my check calls fit one rule with this precedence: *conflicted > insufficient > supported/contradicted > undecided*, bracketing the constants at **support threshold ∈ (0.5714, 0.7021]**, **contradiction threshold ∈ (0.6245, 0.8103]**, **sufficiency threshold ∈ (0.4108, 0.5044]** (≈ 0.5). This mapping is plugin logic, not model output, so it is real and will apply to live runs — but the probabilities that feed it were synthetic, so the *observed verdicts* mean nothing. Notably a check with **no claim and no evidence** returned `"conflicted"`.

**Redaction is real and it fires on option keys.** A 20-option choice reported `"redactedFields": ["auth_token_expired"], "redactionRules": ["key-name"], "redactions": 1`; a 5-option choice with keys `api_key`, `auth_token`, `client_secret`, `password` reported **all four** redacted (`redactions: 4`). The values still came back in this instance, but the event is flagged and the plugin's README is explicit that redaction is "best-effort". **Option labels that look like credential names trigger redaction events inside a measurement instrument.**

## 1.5 What the probe battery produced: FIXTURES, not calibration

I ran the full 14-item calibration battery the remit asked for. Here is its result, presented **only** as a demonstration of what a hash looks like when it is mistaken for a judge.

| Bin (P(true)) | items | binary items | observed true-rate |
|---|---|---|---|
| 0.0–0.2 | 3 | 2 | 0.67 |
| 0.2–0.4 | 2 | 2 | 0.00 |
| 0.4–0.6 | 5 | 2 | 0.50 |
| 0.6–0.8 | 2 | 2 | 0.50 |
| 0.8–1.0 | 2 | 1 | 0.00 |

On the 10 items with binary ground truth, thresholding at 0.5 gives **5/10 correct = chance**, and **Brier score 0.359 — worse than a constant 0.5 (0.25)**. The mock is not merely uninformative about truth; its numbers are anti-informative. This is the failure mode most likely to survive review unnoticed: the output *looks* like a mediocre-but-real evaluator, with a plausible spread of confidences, and would not read as "broken" in a results table.

**This sample is far too small to conclude anything even about a live model, and the live experiment needs far more.** For a reliability curve with 5 bins at ±0.10 (95% CI, worst case p=0.5): `n ≈ 1.96²·0.25/0.10² ≈ 96` **per bin**, i.e. **≈ 500 binary items minimum**, and **≥ 1,000** if ECE is to be reported within ±0.05. Repeated measures over shared states are not independent and reduce the effective n; only items with unambiguously binary ground truth may enter the bins.

---

# PART 2 — BLOCKED MEASUREMENTS (inventory)

Every item from the original remit, re-scored:

| # | Remit item | Status |
|---|---|---|
| 1 | Baseline sanity: answer from state vs world knowledge | **BLOCKED** — all values hash-derived |
| 1 | Silent state → ~0.5, extreme, or other | **BLOCKED** — observed spread 0.0317–0.8495 across fixtures is the hash, not a behaviour |
| 2 | Boundary sensitivity / confound | **BLOCKED — and actively misleading**: on the mock the delta is exactly 0.0000 by construction |
| 3 | Choice: accuracy and concentration vs option count | **BLOCKED** — accuracy was 0/3 on the root-cause ladder, 1/1 on near-synonyms; both are hash draws. `confidence` is a hard-coded 0.5 |
| 4 | Score: on/between levels, legend, per-level probabilities | **BLOCKED** — although the *schema* is now fully known (§1.4) |
| 5 | Calibration seed data / reliability table | **BLOCKED** — table produced, Brier 0.359, all noise |
| 6 | `check` verdicts across four regimes | **BLOCKED for the verdicts**, **RESOLVED for the mapping rule** (§1.4) |
| 7 | Failure modes: long state, empty, noise, near-synonyms, indeterminate | **PARTIALLY RESOLVED** — caps, truncation flag, validation errors and the degenerate-envelope defect are real facts (§1.2, §1.3). Degradation *in judgment* is BLOCKED |
| 8 | Throughput / latency budget | **BLOCKED** — see Appendix B |

---

# PART 3 — ACTIVATION RECIPE AND EGRESS CONSEQUENCES (decision for the human owner)

## 3.1 Is a credential present? **NO.**

- **Environment:** zero variables matching `typesafe|jev|openrouter|openai|anthropic|api_key|apikey|token`. Present `DSH_*` variables are `DSH_HOME`, `DSH_SESSION_ID`, `DSH_SHELL`, `DSH_WEB_URL` only.
- **`C:\Users\zzhdz\.dsh\.credentials.yaml`:** the only named ref is **`DEEPSEEK_API_KEY`**. No `TYPESAFE_API_KEY`, no `OPENROUTER_API_KEY`. (Key *names* only were inspected; no value was read or printed.)
- No key, no `JEV_PROVIDER` override, and `cordis.patch.yml` pins `provider: mock`.

**Absent. Nothing can reach a live model today.**

## 3.2 The change that would be required (not applied — this is an egress decision)

Two parts, both needed:

1. **Register a credential** in DSH's credential service under the ref `TYPESAFE_API_KEY` (`apiKeyRef` default). ⚠️ **See §3.5 — exporting it in the shell will not work.**
2. **Point the plugin at the live route.** Preferred: an id-targeted override in the *profile* patch file `C:\Users\zzhdz\.dsh\profiles\web\cordis.patch.yml`, which already contains `- id: jev` / `disabled: false` — add the config there rather than editing the copy inside `node_modules` (which package updates overwrite):

```yaml
- id: jev
  disabled: false
  config:
    provider: live          # was: mock
    apiKeyRef: TYPESAFE_API_KEY
```

Reverting is deleting `provider: live` (or setting `mock`). `provider` is read per call, so a key added while the process runs is picked up. An unknown config value is rejected at load naming the key, so a typo fails loudly rather than silently changing the privacy posture. Confirm the change took by finding this line at startup:

```
[jevcore] provider=live  endpoint=https://api.typesafe.ai  egress=ON
```

## 3.3 Egress consequences, per feature (from the plugin's own contract)

| Feature | Default | What leaves the machine | Cap |
|---|---|---|---|
| `tool:jev_ask` | runs when called | the arguments the model passed, after redaction | state ≤ 16,000c, questions ≤ 4,000c |
| `tool:jev_rank` | runs when called | the query plus **every candidate** | state ≤ 16,000c, questions ≤ 4,000c |
| `tool:jev_check` | runs when called | the claim and its evidence | state ≤ 16,000c, questions ≤ 4,000c |
| `gate:safety` | **off — explicit opt-in** | tool name, its arguments, **the workspace root** | state ≤ 8,000c, questions ≤ 2,000c |
| `gate:context` | **off — explicit opt-in** | a large tool result the agent just received | state ≤ 6,000c, questions ≤ 2,000c |

Destination for `provider: live` is `https://api.typesafe.ai`. Redaction runs first but is explicitly **best-effort**: it strips values under sensitive field names and known secret shapes, and the README states plainly that "a secret that sits under an unrecognised key name *and* does not match a known shape will pass through." For this paper's protocol the exposure is the *task corpus itself*: full task states are uploaded on every call. **Turning the two gates on is a strictly larger decision than turning the provider on**, because gates fire on every matching tool call rather than only when the model chooses to call Jev — which is exactly why they are opt-in.

## 3.4 Is `openrouter` viable?

Yes, and it is a documented route rather than an approximation: OpenRouter hosts the System One models at the same `POST /v1/systemone` path, one level below its own API root. `provider: openrouter` + `openRouterApiKeyRef: OPENROUTER_API_KEY`; it needs an OpenRouter key instead of a TypeSafe key. Three differences that matter to a paper:

- **A different third party receives the state** (OpenRouter, not TypeSafe) with different retention and logging. The startup report names the endpoint precisely so the destination is read rather than inferred.
- **It returns a cost**, so `usage.costUsd` is populated on this route and absent on the TypeSafe route. Note the vendor's own warning that **`costUsd: 0` on the TypeSafe route means "not reported", not "free"** — a cost table built from zeros would be fiction.
- **Model ids are constrained**: a bare `jev-*` id, or a versioned `typesafe/jev-1.13`. `typesafe/jev-latest` is **not accepted**; any other id would route to a chat model and is refused before the call.

## 3.5 The trap that would silently keep the experiment on the mock

The plugin README records that **DSH strips environment variables whose names contain `KEY`, `PASSWORD`, `SECRET` or `TOKEN` from any server it spawns**, and merges its own credential map back afterwards. A `TYPESAFE_API_KEY` exported in a shell **never arrives**, and the plugin stays on the offline mock **without reporting an error**. The credential must be registered through DSH's credential service, not the shell. *Any live-run checklist that does not include "confirm the startup line says `provider=live egress=ON`" is one silent misconfiguration away from publishing a second set of hash numbers.*

---

# PART 4 — LIVE-vs-MOCK VALIDATION HARNESS

## 4.1 The two decisive discriminators (run these first, one call each)

| # | Probe | Mock result (measured) | Live must show |
|---|---|---|---|
| **A** | State that states the claim three ways (`C1` below), noul with a declared boundary | `noul = 0.0317` | **`noul` ≥ 0.9**. A decisive state must not score near zero |
| **B** | Boundary sensitivity: same state, same question id, same instruction text, boundary declared vs not | **delta exactly `0.0000`** | **non-zero delta** |

If either fails, the credential did not take effect and the run is still on the mock regardless of what any other field says. Assert also, on every response: `provider == "live"`, `warning` **absent**, `latencyMs > 0`, `inputTokens > 0`, and for choice/score `confidence != 0.5`.

## 4.2 Per-tool smoke checklist

1. Startup report prints `provider=live  endpoint=…  egress=ON` (the only reliable activation evidence).
2. Discriminator A passes; discriminator B moves.
3. `jev_check` on evidence that plainly supports its claim returns `supported`; on evidence that plainly contradicts it returns `contradicted`. (On the mock, verbatim-support returned `undecided` and verbatim-contradiction returned `undecided`.)
4. `jev_rank` on 4 candidates where one is directly supported must not rank an irrelevant candidate first. (On the mock, "The moon is made of cheese." ranked **#1 at 0.9116**, above the directly-supported invoice statement at 0.5062.)
5. `choice` with a state-internal ground truth must select the correct key; record the full distribution, not the winner.
6. `score` with an ascending legend must return a `score` near the known level; confirm `score == Σ(index × probability)` still holds, since that identity is cheap to assert continuously.

## 4.3 What must be re-run before any paper claim

Sections 1, 2, 3, 4, 5, 6 and 8 of the original remit are **all** to be re-run live. Section 7 splits: the cap/validation/truncation findings in §1.2–1.3 stand as-is and need no re-run; the judgment-degradation parts must be re-run.

---

# APPENDIX A — verbatim probes and trimmed raw output (FIXTURES)

All bodies below are mock output. Included because the remit requires the raw JSON behind headline claims, and because they are the fixtures the live runs must differ from.

**A1 — Decisive state, must-be-true claim (discriminator A).**
State: `{"t": "Audit memo. Invoice INV-4471 is fraudulent. The forensic accountant confirmed the fraud and the vendor admitted it in writing."}`
Question: `{"q": {"type":"noul","instructions":"Is invoice INV-4471 fraudulent?","boundary":{"true":"the state states that invoice INV-4471 is fraudulent","false":"the state does not state that invoice INV-4471 is fraudulent"}}}`
Returned: `{"answer":"false","band":"no","noul":0.0317,"probability":0.9683}` — a state that asserts the claim three times scored **0.0317**.

**A2 — Silent state (warehouse inventory) asked about an invoice.** `{"answer":"true","band":"yes","noul":0.7734,"probability":0.7734}` — and the identical question with a declared boundary in the same call returned `{"answer":"false","band":"no","noul":0.204,"probability":0.796}`. Two different numbers for one question, differing only in the question *id* and the boundary.

**A3 — `check` on evidence that states the claim verbatim.**
Claim: `Invoice INV-4471 is fraudulent.` Evidence: `Audit finding. Invoice INV-4471 is fraudulent. The forensic accountant confirmed the fraud, the vendor has admitted it in writing, and the invoice has been voided.`
Returned: `{"verdict":"undecided","probabilities":{"supports":0.5223,"contradicts":0.5753,"sufficient":0.7276}}` — **both sides above 0.5 simultaneously**, for evidence that is a verbatim restatement of the claim.

**A4 — `check` with empty claim and empty evidence.** Raw body:

```json
{"provider":"mock","model":"jev-latest","latencyMs":0,"verdict":"conflicted",
 "probabilities":{"supports":0.7021,"contradicts":0.8103,"sufficient":0.2757},
 "warning":"These answers are SYNTHETIC. …","egress":{"truncated":false,"stateChars":26,"questionsChars":1101}}
```

**A5 — `rank` where a directly-supported candidate loses to an absurd one.** Criterion: *"Is this statement supported as true by the audit evidence?"*, query: *"Which statement does the audit evidence support?"*

```json
{"ranking":[{"index":3,"candidate":"The moon is made of cheese.","relevance":0.9116},
            {"index":0,"candidate":"Invoice INV-4471 is fraudulent and has been voided.","relevance":0.5062},
            {"index":1,"candidate":"The warehouse temperature log was nominal in Q3.","relevance":0.0197},
            {"index":2,"candidate":"The load balancer was misconfigured.","relevance":0.0114}]}
```

**A6 — `score`, showing `score` vs `answer` divergence** (legend echoed exactly as declared, 0 = most severe):

```json
{"answer":"cosmetic or no user impact","score":2.0258,"probability":0.2692,
 "legend":{"0":"total loss of service with data loss or safety impact","1":"full loss of a customer-facing service for a sustained period without data loss","2":"degraded performance for a small number of users","3":"partial loss of function or noticeable degradation for many users","4":"cosmetic or no user impact"},
 "probabilities":{"0":0.2089,"1":0.2099,"2":0.1969,"3":0.1151,"4":0.2692},"confidence":0.5}
```

**A7 — 20-option choice, showing the redaction event and the concentration collapse.** `{"answer":"quota_exceeded","probability":0.1123,…,"confidence":0.5,"egress":{"redactedFields":["auth_token_expired"],"redactionRules":["key-name"],"redactions":1}}` — top option held **11.2%** of the mass versus **69.7%** at N=2, with `confidence` 0.5 in both.

**A8 — Truncation.** ~17.3k-char state → `{"truncated": true, "egress": {"truncated": true, "stateChars": 16000, "questionsChars": 216}}`.

**A9 — The degenerate envelope.** `jev_rank` with `candidates: []` → `{"provider":"mock","model":"","latencyMs":0,"ranking":[]}` (no `warning`, no `usage`, no `egress`).

---

# APPENDIX B — method, and its precision limits

**Method.** Sequential blocks in one session: `pwsh` timestamp → Jev tool block → `pwsh` timestamp, alternating, with an empty (no-call) interval interleaved as a null control.

| Interval | Payload | Wall clock |
|---|---|---|
| S1 → S2 | **1** `jev_ask` call | **4.441 s** |
| S2 → S3 | **0** calls (null control) | **4.683 s** |
| S4 → S5 | **5** parallel `jev_ask` calls | **5.833 s** |

**Interpretation.** The interval is essentially **constant across 0, 1 and 5 calls**. The null control is *longer* than the one-call interval. Therefore this method measures agent/harness turn overhead, not provider time: the marginal cost of four extra parallel calls (~1.4 s total) is inside the noise. Precision limits: one harness round-trip per interval with unbounded jitter, `Get-Date` resolution, and ±~1.4 s observed spread — **it cannot resolve a sub-second provider call**, and with `latencyMs: 0` reported for every mock call (the vendor states the mock's `latencyMs` is "normally 0"), **no latency budget can be derived from this session at all.**

For budgeting the live experiment, the only usable numbers are documented rather than measured: a **40,000 ms total budget per Jev call** (error text `the call exceeded its total budget of 40000ms`), with **up to three wire attempts for one logical call** because the same state may be sent once per retry. Live per-call cost must be read from the provider's own `latencyMs`/`usage` fields, never from wall clock around a tool call.

**Unrelated harness defect, reported because it blocks team workflow:** loading the session skill `typesafe-ai-dsh` failed twice with `Error: loaded skill "typesafe-ai-dsh" source must be a string`. The skill file exists on disk (`…\jevcore-dsh\skills\typesafe-ai-dsh\SKILL.md`, 8,124 bytes), so this is a harness-side load failure, not a missing file.

---

# CONSTRAINTS FOR THE EXPERIMENT DESIGN

## C0 — Blocking constraints (nothing proceeds until these are met)

1. **No Jev column may be populated until a live credential exists and the activation discriminators (Part 4.1) pass.** A paper built on this session's numbers would report a hash function as an evaluator.
2. **Record `noul` as P(true), never `probability`.** `probability` is P(the answered option) and inverts roughly half the items.
3. **Do not use `confidence` as a measure of anything.** It was hard-coded 0.5 in every mock choice/score; on live it is a concentration statistic, and the plugin's own `minConfidence` default is 0.7 — below which an answer is "not acted on".
4. **Every Jev response must be stored with `provider`, `warning` and the full `egress` block.** Detection is `provider == "mock"`; *absence* of a warning is not evidence of a live call (A9).
5. **Mandatory boundary declaration is NOT justified by measurement** — it is unmeasured. Record the boundary in the protocol for reproducibility, but do not claim a measured effect either way until the live boundary-sensitivity delta is shown non-zero.
6. **Declare the scale direction explicitly and assert it after the fact.** `score` is Σ(index × probability) over the legend as written; a `criteria` map written in descending order silently inverts every score. Store the returned `legend` with each response and verify it matches the intended order.

## C1 — Instrument construction rules

7. **Option counts up to 25 are accepted**; there is no demonstrated option ceiling. Cap at 20 by choice, not by force, and record the full distribution rather than the winner.
8. **`choice` needs ≥ 2 criteria and every question needs non-empty instructions** — both are hard refusals. Build the batch validator before the run.
9. **Never let a `type` typo through.** An unrecognised type is silently coerced to `score`; assert the returned `type` equals the requested `type` on every response.
10. **Option labels must not look like credentials.** Keys such as `api_key`, `auth_token`, `client_secret`, `password` trigger key-name redaction inside the instrument.
11. **`jev_check` performs no input validation** — an empty claim and empty evidence returned a confident `conflicted`. Validate claim/evidence upstream; never let an empty pair enter the dataset.
12. **Validate the verdict vocabulary against the plugin's five values** (`supported`, `contradicted`, `conflicted`, `insufficient`, `undecided`). `unknown` is not among them despite appearing in the tool description.

## C2 — Batch-size and budget rules

13. **`jev_rank` batch size: `N_max ≈ floor(3999 / (126 + len(criterion)))`** — exact at four measured points; documented boundaries `L=69→20`, `L=400→7`, `L=1,000→3`. Over-cap batches are **refused, not truncated, and retrying cannot help**. Size the batches from the formula at protocol-build time.
14. **`state` is truncated at 16,000 characters, silently and in-envelope.** Every response must be checked for `truncated: true` before its data enters the analysis; a truncated ranking still returns a full-looking ranking over the fragment.
15. **Budget ≥ 40,000 ms per call** and assume up to **three wire attempts** per logical call when sizing wall clock and rate limits.

## C3 — Measurement-design rules

16. **Calibration needs ≈ 100 binary items per probability bin (≈ 500 minimum, ≥ 1,000 for ECE ±0.05), and only unambiguous binary ground truth may enter the bins.** Repeated measures over shared states are not independent. *This session's 14-item battery is two orders of magnitude short and, on the mock, scored Brier 0.359 — worse than a constant 0.5 — while looking entirely plausible.*
17. **Include the two discriminators (Part 4.1) as guard assertions at the head of every run**, and re-run them at the end to prove the provider did not change mid-experiment.
18. **Report latency from provider fields only** (`latencyMs`, `usage`), never from wall clock around tool calls; state the 40,000 ms ceiling and the retry multiplicity as documented, not measured.
19. **Treat `costUsd: 0` as "not reported", not "free"** — the vendor documents that the TypeSafe route does not report cost at all; only the OpenRouter route populates it.
20. **All evaluator comparisons are blocked, not merely deferred:** the same providers and thresholds must be re-validated live before any Jev-vs-LLM-vs-Laya claim is written.

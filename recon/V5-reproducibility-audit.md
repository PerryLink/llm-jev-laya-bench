# V5 — Adversarial audit: reproducibility and claim defensibility

**Unit:** V5 (verification — adversarial). **Date:** 2026-09-22.
**Audited artefact:** [R5-synthesis.md](R5-synthesis.md) (the merged design), against [R16](R16-baselines-and-positioning.md), [R2](R2-verified-externals.md), [R4](R4-blockers-and-activation.md), [R13](R13-laya-probe.md), with [R1](R1-architecture-and-threat-model.md), [R11](R11-dsh-testbed.md), [R12](R12-jev-probe.md), [R14](R14-long-horizon-battery.md), [R15](R15-arms-and-process-metrics.md) consulted for cross-document consistency.
**Methodology exemplar:** <https://docs.litellm.ai/blog/jev-auto-router-benchmark> (frozen corpus + protocol + registry with SHA256; `jev-latest` pinned to `jev-1.13.0`; seeded shuffle; clustered bootstrap over 80 case clusters; registry-priced cost recomputation; explicit "what we did not establish"). R2 §C.4 already commits the team to align to it. **This audit measures the current design against that commitment** — and the design is far behind it.

**First-party measurements made for this audit (not taken from any recon file):**

| Measured | Value | How |
|---|---|---|
| Laya english checkpoint true parameter count | **421,293,830 (421.3 M)**, 206 tensors, dtype F16 | parsed the `model.safetensors` header |
| Laya multilingual checkpoint size | 643.8 MB on disk (≈322 M @ F16) | directory scan |
| Graphically available device | **NVIDIA GeForce RTX 5060 Laptop GPU, 4 GB VRAM**, driver 32.0.16.1047 | `Win32_VideoController` |
| CPU | Intel Core Ultra 7 255HX, 20 cores / 20 threads | `Win32_Processor` |
| Torch / CUDA | **2.11.0+cu128 / CUDA 12.8** | interpreter probe in `.venv-laya` |
| OS | Windows 11 Home (zh-CN) | `Win32_OperatingSystem` |
| `planning.py` SHA256 (first 16) | `70E90EE8BB32356B` | `Get-FileHash` |
| `worker.py` SHA256 (first 16) | `8A0ABEE5F6156B3A` | `Get-FileHash` |
| `_models/laya/rl_agent_config.json` SHA256 | `AE287B56BBCF5F8C…` | `Get-FileHash` |
| `_models/laya/encoder/config.json` SHA256 | `BF3AB80598FDCCF4…` | `Get-FileHash` |

---

## 0. Executive findings, ordered by severity

1. **BLOCKER-1 — the headline contribution has no home in the experiment matrix.** The paper's thesis is silent truncation vs horizon. R14's gate G1 **rejects every item that would truncate** (`laya_plan(strict=true)`, state ≤512 tok, target ≤497, "reject, never trim"), and R15 §0.3/R14 §5.2 fix the carrier at 5 lines / ≤55 tokens. An item battery built to R14's spec therefore produces a truncation rate that is **zero by construction**, while R15's `token_ratio(t)` curve requires states that exceed the window. Two incompatible state-growth models are running in the same design. The paper's best claim (S3) currently has no instrument.
2. **BLOCKER-2 — the mechanism that defines the instrument is unhashed and partially unexplained.** The silent window (2850→3148 chars, ~450-token clamp) is produced by specific constants in `planning.py` (`_CHARS_PER_TOKEN = 4.0`, `_SAFETY = 1.15`) and a runtime clamp in `worker.py` whose mechanism R13 §2.6 explicitly did **not** isolate. The design pins the sidecar *version string* (`0.2.1`) and the *checkpoint* — but never the **code**. A patch release that changes either constant moves the paper's central curve and no reader could tell. Hashes of the actual instrument exist (above) and are not in the design.
3. **BLOCKER-3 — either the design is unfunded by 100× or R15's dominant budget line is off by 100×.** R15 §6.2 prints "**Gold evaluation pass, 5 judges × 120 checkpoints × 576 runs (69,120 calls) — $0.066 per run — $3,802**" and calls it "~55% of the total," driving a $6,000–7,500 budget. $0.066 × 576 = **$38.02**, not $3,802. The arithmetic error is in the design's own money model.
4. **BLOCKER-4 — the Jev arm cannot be made reproducible on the route the cost model assumes.** The registry price ($0.042/1M in, $0 out) belongs to the **TypeSafe** route, but R12 §3.4 records that TypeSafe **does not report cost at all** (`costUsd: 0` means "not reported", not "free") and that `typesafe/jev-latest` is **not accepted** on the OpenRouter route, which is the only route that returns cost. Traceability requires the provider fields to exist. Since the Jev price is **the** input to "the output-token advantage," the cost chapter currently rests on a number that cannot be reconciled against a usage record on the route that produces it.
5. **The "1000 items" ECE corpus does not exist in any unit's plan.** R5 ⚖️ conflict 2 rules "**total items 1000**, of which R14's 300 form the horizon sub-design." No document generates the other 700. R14 §4.5 fixes N=300 with a conditional "+75 slots (375)" extension rule. The design's own "core deployment conclusion" (calibration) therefore has no collection procedure.
6. **Two "horizon" dials with different values are both called the horizon knob** (R14 `J ∈ {1,4,8,32,128}` / `d ∈ {0,4,28,124}` vs R5 §5.2 `d ∈ {0,4,28,124}`), and the paper's figures are titled "vs horizon" — which R16 D.4 #8 explicitly forbids without the matched short-stage residual baseline.
7. **The measurement plane cannot measure the metric the paper stakes itself on.** `T90`/`LEAD` are defined from verdicts (`revise|halt`), but the replay plane is open-loop by construction (nothing it "detects" can change anything). R15 §3.2 argues lead time "is causally upstream of the outcome" — true online, false on replay. R5 §5.5 names `T90` primary without naming a plane.
8. Minor but concrete: R15's power/latency model cites an **"M1 Max GPU"** that is not this experiment host; R15 §6.1 prices the LLM at **$0.28/$0.42/Mtok** while R16 §B.1 *verified* **$0.15/$0.60** off-peak; both appear in the same design; R5 §8.1's open item 1 is this audit's finding 3.

---

## 1. Reproducibility of the artefact — every input a third party needs

The exemplar publishes a tarball containing `cases.jsonl`, `protocol.json`, `attempts.jsonl`, `wire.jsonl`, `metrics.json`, the captured registry, environment versions, **setup failures**, and a **hash manifest**, plus `analyze.py` and `SHA256SUMS`. Measured against that bar:

| # | Input | Status | Evidence / note |
|---|---|---|---|
| 1 | Generator model version | **UNSTABLE** | `deepseek-flash` = DeepSeek-V4.1-Flash (R2 §A). Legacy ids `deepseek-v4-flash*` "retired but still served by V4.1-Flash" — the alias layer can move under a fixed call name. No dated *served* version token is recorded per response; the design records no response-side model field at all. |
| 2 | Generator provider version / endpoint | **ABSENT** | No API base, region, or gateway version recorded. R12 §3.4 shows route choice changes billing *semantics*, not just price. |
| 3 | Judge-LLM sampling config per arm | **PARTIAL** | R16 §A.2 gives the levers (`logprobs`, `top_logprobs`, `reasoning_effort ∈ {none,low,high,max}`, `top_p` floor 0.95 in thinking mode, `temperature` inert in thinking mode). R5 §4.4 #17 pins only "non-thinking for self-consistency". The **primary** effort level for the headline LLM number is not named anywhere; R14 §5.4 leaves it to `[→ARMS]`. |
| 4 | Prompt variants P1–P4 | **ABSENT** | R16 §A.2.3 pre-registers four configurations; none of the four is written out verbatim in any design document. Exemplar published the full `protocol.json`. |
| 5 | Frozen corpus (`cases.jsonl` equivalent) | **ABSENT** | `protocol/` and `probes/` exist and are **empty** (verified). R14 §7 S4 "hash every state" is a plan; no corpus, no hashes. |
| 6 | Serializer `SER` | **PARTIAL** | R15 §0.3 defines it in prose (newest-first, K records, `DROPPED: n` last). **K is never given a value.** No hash — R15 §5.6 promises the hash into the pre-registration, unexecuted. |
| 7 | Question bank | **PARTIAL** | Nine templates named (R15 §0.4); instruction text, option strings, rubric anchors not written. Exemplar froze the rubric *and* the wire format. |
| 8 | Option counts and canonical order | **PARTIAL** | R5 §4.3 #8 and #12 freeze ceilings (10/3) and a canonical `criteria` order — but the canonical order itself is not specified, and R14 allows choice-4 while R15's bank allows choice-8. Two different option-count regimes. |
| 9 | Laya checkpoint identity | **PARTIAL** | Paths named (`_models/laya/…`), configs read (R13 §0c). **No checkpoint hashes, no weight hashes.** I computed them above; the design does not contain them. |
| 10 | Laya sidecar *code* identity | **ABSENT — critical** | `planning.py` / `worker.py` / `capability.py` determine the token estimator, the compression thresholds, the `fits` semantics and (somewhere) the runtime clamp. Version string `0.2.1` is not a code identity. |
| 11 | Sidecar launch flags | **PRESENT (Path A)** | `--model english --also multilingual --model-root … --device cuda --port 8787 --max-len 1024 --head-max-len 512` (R13 §0). Path B's launch line (`laya_mcp mcp --model-root …`, no budget flags) is known but never written into the protocol. |
| 12 | Device | **PRESENT but incomplete** | R5 §4.1 #2 requires `device: cuda` + CPU-fallback detection. Missing: the GPU model, VRAM, driver, torch/CUDA build, OS. R15 §1.4/§6.1 cite an **"M1 Max GPU"** that is not this host — the design's device story is contaminated by template text from another machine. |
| 13 | Runtime token budget `W` | **UNSTABLE** | Two accountings in one design: 512 seq-tok `W` (R15 §3.5) and 450 **state**-tok cap (R5 §4.2 #5), vs a planner told 1024 and a runtime clamp at 512 that R13 §2.6 could not explain. R13 §2.4 also shows truncation damage appearing at 453 real state tokens, i.e. *below* 512. Report the measured threshold with its uncertainty; do not print "512" as if it were a specification. |
| 14 | Tokenizer + counting rule | **PRESENT** | `_models/laya/tokenizer/tokenizer.json`; R5 §4.2 #4. Exemplar-grade. |
| 15 | Jev live status / provider route | **UNSTABLE** | `provider: mock` today (R4 P0-1). Activation is a one-line change; nothing binds each *row* to `provider == "live"` at collection time. |
| 16 | Jev model id / resolved version | **UNSTABLE** | Registry says bill as `typesafe/jev-1.13.0`; requests say `jev-latest`; R12 §3.4 says `typesafe/jev-latest` is rejected on OpenRouter and a bare `jev-*` id or `typesafe/jev-1.13` is required. The design pins nothing, and the exemplar explicitly warns that a future `jev-latest` resolution requires a new experiment. |
| 17 | Jev pricing snapshot + billing treatment | **UNSTABLE** | $0.042/1M input, $0 output (R2 §C.1) — but whether output is truly unbilled is **still open** (R2 §C.5, R5 §8.7), and on the TypeSafe route cost is unreported by design. |
| 18 | Agent/system config hash for Jev | **ABSENT** | R4 §5 wants "the hash of the config file and the collection date"; R12 §3.2 gives the exact file (`cordis.patch.yml`). Not in the design. |
| 19 | Pricing snapshot + date + window | **PRESENT (needs enforcement)** | R16 §B.1 gives the dated off-peak/peak table and the UTC windows, and requires re-verification at freeze and submission. What is missing is the per-run **recorded** peak/off-peak flag: R5 §4.4 #18 says fix the window, R16 §B.1/§B.6 say report it. A run that crosses 01:00 UTC has a 2× discontinuity no post-hoc analysis can undo. |
| 20 | Calibration corpus | **ABSENT** | R5 P5 (4 families × 40 runs) is the *input to* τ* and does not exist. Worse: R5's phase order runs P2/P5 with **mock Jev** (see §3). |
| 21 | Escalation thresholds τ*, s* | **UNSTABLE** | Fit procedure is fully specified (R15 §1.5) — but the fit will consume mock-derived confidences if executed in the current order. |
| 22 | Analysis code | **ABSENT** | No `analyze.py` equivalent anywhere in the plan; P11 "analysis" has no code deliverable. The statistical plan (RI permutation, CR2, wild cluster bootstrap, TOST, discrete-time survival) is non-trivial enough that unshared code makes every number unreproducible in practice. |
| 23 | Raw artefacts + failure log | **PARTIAL** | R5 §5.4's immutable `SNAP[run][t]` snapshots are the right primitive and are the design's best decision. But nothing specifies packaging, retention of *failed* runs, or a hash manifest — the exemplar retains its three failed configurations and says so. |
| 24 | Seed / randomizer | **ABSENT** | The exemplar publishes seed `20260918`. R14 §5.2 #7 and R15 §5.3 randomize option position and arm assignment; **no seed, no generator, no Latin square artefact.** |
| 25 | Parameter count claim ("421M") | **PRESENT, derivable** | R13 §0c forbids citing a parameter count. I measured it: **421,293,830** in the `model.safetensors` header (206 tensors, F16). Include it *with the derivation*, never as a README quote. |

**Silent-change surfaces named in the remit, adjudicated:**

- **`jev-latest` resolution** — genuinely unstable; the alias is resolved server-side at request time. Pin-to-version then collect, and record the resolved version from the billing identifier on every row.
- **Off-peak/peak windows** — the *definition* is stable and documented; what is unstable is the run's position in it (and the Chinese-public-holiday exclusion, which is not a machine-readable calendar). Record peak/off-peak **per run** with the local timezone.
- **Laya checkpoint revisions** — the paths are local and mutable with no revision control in evidence; the design's identity story is a version string plus a path. Hash the weights and both configs.
- **The two Laya hosts** — see §2. This is the one the remit is right to isolate: it is the only reproducibility hazard that a reader can trigger *accidentally*, by doing nothing wrong.

**VERDICT: unsound.** The design reproduces the *idea* of the experiment but none of its *inputs*. Against the exemplar's own checklist (R2 §C.4 items 1–7), items 1 (frozen corpus + SHA256), 3 (clustered bootstrap is present in R15 §5.3, good), 5 (stated non-establishments, present in R16), 6 (failure retention) and 7 (version pinning) are respectively absent, partial, present, absent, partial. Three of the four headline numbers (cost, truncation onset, calibration) depend on inputs marked UNSTABLE/ABSENT above.

---

## 2. The two-Laya-hosts problem

**The hazard, precisely.** R13 §0b establishes that the *tool name* selects the instrument: plugin tools reach an HTTP sidecar on `:8787` launched with `--max-len 1024 --head-max-len 512`; MCP tools reach a stdio server launched with no budget flags and therefore planner `max_len 512 / head_max_len 192`. Same request, same checkpoint, same second: `state_room_estimated` **917 vs 405**. Below the planner, the runtime clamp is ~512 on both paths, so the *behavioural* difference is in (a) the announced budget, (b) the option-compression onset (**11 on Path A, 4 on Path B** — R13 §1.4), and (c) the sign of the planner's error (**A optimistic, B pessimistic**).

**Why pinning one host is not sufficient.** In this very session the tool families reach *different* hosts with no visible signal in the response body: the reply envelope carries `budget_summary.head_max_len` (192 vs 512) but a reader is not told which is "the instrument." Both are reachable through the same product, from the same machine, by the same nominal operation. A reader who follows the paper's text ("we query Laya with a typed `noul` question") will arrive at whichever host their harness happens to wire. That is not a robustness contrast — it is an **undetectable re-instrumentation**.

**What the methods section must state, minimally:**

1. **The entry point by invocation, not by product name.** Name the exact tool (`laya_noul`/`laya_ask` via the plugin, i.e. `POST http://127.0.0.1:8787/ask`) *and* the exact launch command including every budget flag. State explicitly: "the MCP entry point (`mcp__laya__*`, stdio, planner 512/192) is a **different instrument** and its numbers appear only in the labelled robustness panel."
2. **That no host parameter exists in the API.** Readers cannot select a host declaratively; they must select a transport. Say so.
3. **A per-response provenance assertion.** Every recorded row must carry the observed `budget_summary.head_max_len` (or a `host=` tag derived from the transport), and the analysis must hard-fail on a mixed-value column. This is the only mechanism that survives a reader's misconfiguration.
4. **Instrument hashes for both hosts.** Checkpoint config + weights + `planning.py`/`worker.py` hashes, per host.
5. **Both hosts' launch lines and both hosts' `state_room_estimated` at a fixed probe state** — the "canary" that lets a replicator verify in one call that they are on the paper's instrument. R13 already has the exact probe (`{"state":"test","questions":{"q":{"type":"noul","instructions":"Is this a test?"}}}` → 917 vs 405). Publishing it costs one line and removes the whole class of error.
6. **The undetermined mechanism, disclosed.** R5 §8.4 already says the paper must not assert why the runtime clamps at 512 under a 1024 override. Good — but then the paper must also state that the *effective window is an empirical property of this build*, and that the planner's advertised budget is not the operative one.
7. **The direction of the contrast.** Do not sell Path B as "robustness": with opposite error signs and a 2.7× option-budget difference, it is a **second instrument**, and differences are instrument artefacts first, findings second. R5 §4.1 #1 currently says "because the two paths' error directions are opposite, this is itself a result" — that is defensible only if the contrast is labelled as *instrument comparison*, never pooled into any claim about "Laya."

**VERDICT: sound-with-fix** — the design already chose a primary host and knows the hazard (R13 §10 rules 5, 11, 12). What is missing is that the *question bank and budget in the primary analysis must be expressed in a form that only one host can satisfy* (≤3 options and ≤405-token planner room would be satisfied by both, so a reader on Path B would silently get compressions that Path A never sees — or vice versa). Encode the host requirement in an item gate, publish the canary probe, and assert provenance per row.

---

## 3. The mock-Jev exposure

**What is already contaminated.** R12 documents 68 tool invocations, 62 successful mock responses, **zero** live data. R12 §1.5 ran a full 14-item calibration battery whose output is the hash — Brier **0.359**, i.e. *worse than a constant 0.5* — and whose reliability table (0.67 / 0.00 / 0.50 / 0.50 / 0.00 by bin) is exactly the kind of mediocre-looking spread a reader would accept as a real evaluator. R4 records the config (`provider: mock`) and quotes the SYNTHETIC warning. R5 §2 fact 1 records the mock as a designed constraint.

**Catalogue of ways this corrupts the record:**

1. **Numbers already collected are unusable and look usable.** 62 synthetic probabilities, 4 choice/score `confidence` values hard-coded to **0.5**, one `score` = 2.0258, one 20-option distribution, two `check` verdicts, one `rank` ordering. Every one is a deterministic function of `questionId + "\0" + JSON.stringify(state)`.
2. **The synthetic answers are *anti*-informative, not merely uninformative.** Brier 0.359 > 0.25. A draft that includes them makes Jev look like a bad-but-real judge — a *plausible* result that no reviewer can detect from a table.
3. **The mock is insensitive to exactly the manipulations the paper is about.** R12 §1.1: instructions, `criteria`, and the `boundary` text are **not hashed** and never move the answer (measured delta **0.0000** across three different boundaries, while `questionsChars` moved 87→240→227, proving the text was serialised). A boundary-sensitivity or wording-sensitivity result computed on the mock is a false negative *by construction* — R12 calls this "the single most dangerous trap."
4. **The detection signal itself is unreliable.** R12 §1.1 defect 1: `jev_rank` with `candidates: []` returned `{"provider":"mock","model":"","latencyMs":0,"ranking":[]}` — **no `warning`, no `usage`, no `egress`**, and `model` is an empty string. A short-circuiting call therefore looks *cleaner* than a normal one. `model` is not a marker either (`"jev-latest"` on all 62). **Only `provider == "mock"` detects the mock.**
5. **`confidence: 0.5` is a tell, and it is the tell that matters most.** Any Jev reliability figure in the paper would be a flat line at 0.5. If a draft ever shows Jev well-calibrated, that is proof of contamination, because the mock cannot produce it — and if it shows Jev *poorly* calibrated at 0.359 Brier, that is also contamination, because it looks like a finding.
6. **Downstream artefacts already quote them.** R4 §P0-1 says "`jev_check` returned `insufficient` on near-verbatim support — this must be retracted as an artefact of the hash." The retraction is correct and must be carried into every document that quotes it, including R5 §2.
7. **The phase order makes the corruption *structural*, not accidental.** R5 §7 runs **P2 (pipeline dry-run, mock Jev) → P3 → P4 (Jev smoke, gated on P0) → P5 (calibration corpus) → P7 (pilot)**. P5 fits **τ***, and R4's own instruction is "do not tune a threshold against it." A τ* fit on mock data is not merely useless: R15 §1.5's acceptance rule is `τ* = min{τ : prec(τ) ≥ 0.99}`, and on hash-derived confidences pinned at 0.5 that rule degenerates. The escalation arm (A4) then runs on a frozen threshold that encodes nothing.
8. **The activation trap.** R12 §3.5: DSH strips env vars containing `KEY`/`PASSWORD`/`SECRET`/`TOKEN` from spawned servers, so a shell-exported `TYPESAFE_API_KEY` never arrives and **the plugin stays on the mock without reporting an error**. Any live run is one silent misconfiguration away from a second set of hash numbers, and the failure is invisible in the response body except via `provider`.
9. **The writing-stage risk.** Nothing in the design binds a *paper number* to a *source row*. The realistic failure is that a plausible mock figure survives into a draft because it was in the same table as a real one. R12's own §1.5 note names this exactly: "the failure mode most likely to survive review unnoticed."

**The verification gate that must pass before any Jev number enters the paper.**

A response may enter the dataset only if **all** of the following hold, asserted at collection time and re-asserted in the analysis as a hard failure:

| # | Assertion | Source |
|---|---|---|
| G1 | `provider == "live"` on every recorded response | R12 §4.1 |
| G2 | `warning` field **absent** (necessary, not sufficient) | R12 §4.1 / §1.1 |
| G3 | `latencyMs > 0` and non-constant across ≥10 repeats of an identical call | R4 §5 |
| G4 | `usage.inputTokens > 0` and positively correlated with state character count | R4 §5 |
| G5 | `confidence != 0.5` for every choice/score response, and not constant across option counts | R12 §1.1 |
| G6 | **Discriminator A**: a state asserting a claim three ways returns `noul ≥ 0.9` (mock: 0.0317) | R12 §4.1 |
| G7 | **Discriminator B**: declared vs undeclared boundary on the same state/question-id/instructions produces a **non-zero** delta (mock: exactly 0.0000) | R12 §4.1 |
| G8 | `jev_check` returns `supported` on verbatim-supporting evidence and `contradicted` on verbatim-contradicting evidence | R12 §4.2 |
| G9 | Startup line observed: `[jevcore] provider=live  endpoint=…  egress=ON` | R12 §3.2 |
| G10 | Run manifest records plugin version, `cordis.patch.yml` SHA256, credential **ref name** (never the value), date, timezone, and gates' actual values | R4 §5, R12 §3.2 |
| G11 | G6/G7 re-run at the **end** of every batch to prove the provider did not change mid-experiment | R12 C3 #17 |
| G12 | Every row carries a non-null provenance tag (`provider`, resolved model id, collection timestamp); a Jev column with any null tag is dropped, not imputed | new — fail-closed rule |

**Two design changes this audit recommends, beyond the gate.** (a) **Move P5 after P4.** The calibration corpus that fits τ\\* must not be generated under the mock; today's locked order makes that mistake available. (b) **Do not build a Jev threshold at all until live.** R15 §1.5's `prec(τ) ≥ 0.99` rule should be evaluated once, after activation, with the pre-registration hash written afterwards — which is legitimate, since τ* is a fitted constant, not a hypothesis.

**Disclosure the paper owes if Jev remains unavailable** (R4 option 2, which this audit endorses as the default until a credential exists):

- Delete arm A2 and the A4 Jev branch; remove "three judgment layers" from the title, abstract and figures; the study becomes **two judges + one interface contract**.
- Downgrade Jev to: the *interface* description, the *third-party* pricing citation ($0.042/1M in, $0 out — attributed to LiteLLM's registry, dated), and the *third-party* head-to-head (95.00% vs 73.75%, 5.43× p50, 96.118% cost saving) explicitly labelled as **not measured here**.
- State that the Jev column of the cost model is a **registry-price estimate**, that the TypeSafe route does not report cost, and that no latency figure for Jev was obtained (R12 §8.3's 1011–2349 ms is an **unauthenticated refusal**; R13 §8.4(iii) already forbids publishing it as latency).
- Disclose the mock as a methods hazard in its own right: report that the fixture was run, that it produced Brier 0.359 at a hard-coded `confidence` 0.5, and that boundary sensitivity measured exactly 0.0000 **because the boundary is not present in the hash** — this is a genuine, citable observation about *synthetic-fixture pipelines*, and publishing it turns a liability into a methodological contribution.
- Quarantine, in the artefact, every mock row with `provider: "mock"` and a `SYNTHETIC` label, and state in the data dictionary that those rows are fixtures. The exemplar's practice of retaining failed configurations is the model here.

**VERDICT: unsound** — not because the team has been careless (R4/R12 are unusually honest) but because the *design's phase order and provenance model permit a synthetic number to become a paper number*, and the only detector the design relies on (the warning field) is documented as unreliable in two places.

---

## 4. Claim-by-claim defensibility

### 4.1 SAFE claims (R16 D.1) — does the design produce the evidence?

| # | Claim | Produces the evidence? | Defect |
|---|---|---|---|
| **S1** | Dated, first-party, device-qualified characterization of per-decision cost, latency, calibration and truncation for **three** judgment layers | **NO, as written** | Two of the four properties are blocked for one of the three layers: Jev has **no latency** and **no calibration** measurement, and its cost is a registry estimate on a route that does not report cost. Device qualification is single-device and, per this audit, the design's device text cites a machine that is not the host. Calibration for all arms requires the missing 1000-item corpus. |
| **S2** | The LLM's four readouts differ measurably in calibration | **NO, currently** | The design names the levers but not the configuration; the logit readout needs `max_tokens=1`, `logprobs`, `top_logprobs=20`, non-thinking, with renormalisation over present letters and a discard rule (§A.2.1) — none of which appears in R5. Power is the binding problem: ECE comparison needs ≥1000 items (R13 B.9) and the collection plan tops out at 300. |
| **S3** | The local judge's **truncation rate (and the rate at which its answer fails to flag truncation) grows with state length/horizon** | **NO — by construction** | This is BLOCKER-1. R14's G1 rejects every item that would truncate; R15 §0.3's serializer would produce large states but violates the same gate. The paper's most defensible claim has no powered instrument, and the measured "≈300-character silent window" is a **single-slot demonstration**, not a rate. |
| **S4** | Per-decision cost is not a single number; sensitivity grid and break-even prices published | **YES, structurally** | Methodological claim under the authors' control (§B.6 grid is complete). One contamination: R15 §6.1's LLM prices disagree with R16 §B.1's verified snapshot by 1.9×/1.4×, and R15's per-run ledger silently uses the wrong ones. |
| **S5** | Equal-spend frontier per arm at its best pre-registered configuration, clustered CIs, both directions | **YES, structurally** | Reporting commitment. Note the design already downgraded this from "primary" (R3's arbitration) while R15 §5.4/§1.6 and R5 §5.5 still call `T90` at matched dollars the primary endpoint — the paper must not describe the frontier as the headline if the endpoint is `T90`. |

### 4.2 CONDITIONAL claims (R16 D.2) — the specific result that would make each reportable

| # | Claim | Making result | Current gap |
|---|---|---|---|
| **C1** | Typed judges improve **final task quality** at matched spend | Best-variant LLM arm ≤ typed arm on the frontier, with task-level clustered CI excluding zero | The primary N (R14 §4.5) is a **decision-accuracy** battery; final task quality needs the F1–F4 completion oracles at 24 families × 4 runs. R14 §4.5 says per-cell claims are unsupportable (MDE 16–20 points at n=60). Reportable only if the frontier is estimated on runs, not items — and the current plan estimates it on items. |
| **C2** | Typed judges make **more decisions affordable** at fixed spend | Measured Laya marginal cost per decision including **per-question re-encoding**, plus cache-hit sensitivity | The re-encoding premise is **[SECOND-HAND]** (R2 §B.2, upstream issue #49) and R5 §8 leaves it unresolved. R13 §10 rule 22 ("a per-decision comparison that batches one judge and not the other is not a comparison") is **violated by the current arm set**: A5b batches ≤8 checkpoints per LLM call while A3 asks one question per checkpoint. Fix the batching asymmetry first; then C2 is either true or false on measured numbers. |
| **C3** | Abstention available to all arms and improves cost-adjusted quality | Risk–coverage curves per arm at matched spend | **The LLM arm has `uncertain` and Jev has `insufficient/undecided`, but Laya's `choice`/`score` have no abstention channel at all, and R5 §4.3 #10 forbids using `confidence` for gating.** Laya therefore emits a hard label for every item, including near-ties (R13 §7.3: 0.4951/0.4736 and still returns `"a"`). This violates R16 §0 corollary 1 (abstention symmetry) and makes C3 untestable for one arm. Fix: pre-register Laya's abstention as a **distributional** rule (top-2 margin or normalised entropy), which R13 §10 rule 17 explicitly permits and R5 §4.3 #11 already contemplates. |
| **C4** | Typed judge delivers equal quality at lower latency | Device-qualified warm timings, no per-question serialisation | Achievable and already measured (37.4 ms median warm, 3.2 ms/question at batch 20). Must be reported **with** the batch-matched LLM arm and with cold-start records separately (P0-4's 389.9 ms vs R11's 4935.863 ms for the same event is a 12.7× disagreement inside the team's own record). |
| **C5** | The judgment layer **causally** affects the executor's trajectory | Judge-on/off ablation with the executor held fixed | Two obstacles. (a) There is **no true judge-off arm**: S0 records A0's prose verdicts and R15 §1.1 deliberately keeps them in the state; a no-verdict generator prompt is never run. (b) The offline replay plane cannot move control flow, so **C5 is only testable on the control plane**, while the design's headline metric is defined on the replay plane. |
| **C6** | One readout class beats another *for this model on this battery* | Paired comparison at n≥1000 with the four readout definitions fixed | Same power gap as S2. |

### 4.3 DO-NOT-CLAIM items (R16 D.4) — which are nonetheless implied by the framing?

| D.4 item | Currently implied by | Where |
|---|---|---|
| #6 "any latency number without a device qualifier" is banned | The **brief's own working title** says "a **~421M** non-autoregressive decision model" — R13 §0c and R2 §B.2 both say the parameter count is **not established** and must not be written. | Paper title (draft), R15 §3.2 reason 3 ("the 421M-parameter judge"), R14 §4.2 Q4 ("where a 421M encoder can plausibly beat…") |
| #8 "any horizon claim without the matched short-stage baseline" is banned | The title claims **long-horizon**; Figure 2 is "error-detection lead time vs horizon"; contribution ② is "truncation rate vs horizon" | R5 §0 title, R5 §5.5, R16 §C.7 #2, R5 appendix §7 |
| #1 "Jev/Laya outperform the LLM" is banned | S3 and the abstract's "silent degradation is the real cost" read as a comparative verdict about Laya whenever the LLM arm is the referent. Mitigated only if the abstract keeps the word "measurement". | R5 §0, R5 appendix §1 |
| #3 "typed judges are better calibrated as a general law" is banned | Contribution ⑤ ("cross-species calibration comparison done properly") plus "ECE is one of the paper's core deployment conclusions" invites the reading. The design is safe **only** because R14 T5 forbids cross-judge raw-probability comparison — a rule R15 §4.1 contradicts (see 4.4). | R16 §C.7 #5, R5 ⚖️ conflict 2 |
| #4 "we propose a cascade" is banned | A4 is a cascade with `esc(t)` as a headline curve; the abstract sentence must keep "we do not propose a new cascade". | R15 §1.5, R16 §C.7 one-liner |

### 4.4 Additional claim-level defects found while testing

1. **The truncation claim is a claim about one product's planner bug, presented as a claim about decision models.** R5 §0's honest title is *"the real cost of discriminative judges on long-horizon tasks: cost is not the constraint, silent degradation is."* The mechanism measured by R13 is `_CHARS_PER_TOKEN = 4.0` × `_SAFETY = 1.15` in a Python planner — a **software defect**, not a property of non-autoregressive decision models. Any reviewer will say so. The claim must be scoped to the artifact ("this implementation, this build, this host"), and the generalisation to "decision models" must be withdrawn unless replicated on a second implementation (the `von` README claims a drop-in alternative; that is the cheapest replication target in R2 §D).
2. **The two-calibration-regimes contradiction.** R15 §4.1 explicitly states the uncalibrated multilingual 100%/0% behaviour is *not* corrected before the primary analysis. R14 T5 forbids exactly that and mandates within-judge temperature scaling on a disjoint 20% split. R16 §A.2.2 rule 4 mandates the same repair budget for both sides. R5 §4.3 #13 and ⚖️ conflict 3 are silent. **Adopt R14 T5/R16 §A.2.2 verbatim**, and report the uncalibrated behaviour as a *primary finding* rather than letting it contaminate an ECE comparison.
3. **Two horizon dials.** R14 §5.1: levels `J = {1,4,8,32,128}`, `d = {0,4,28,124}`. R5 §5.2: floor `J1` + `d ∈ {0,4,28,124}` with "judge × log2(H)" analysis. Same numbers, different symbol, different reference (junction index vs distance from poison) — and `H4` is `J128` in R14 while R5's carrier is fixed at ≤55 tokens. Since R5 is the audited artefact, R5 must restate the dial exactly once, and the pre-registration must carry that one definition.
4. **`n` is never stated for the headline endpoint.** R5 ⚖️ conflict 2 sets 1000 items / 300 horizon items; R14 sets 60 slots × 5 levels; R15 §5.5 computes power at 576 runs (24 × 4 × 6) while R5 §7 P8 says "24 families × 4 runs × arms" with the arm count unstated. Three different denominators coexist.
5. **The "equal-spend frontier" and the "matched sequential round-trips" panel are conflated.** R5 §5.5 primary endpoint is `T90` at matched dollars; R15 §1.6 pre-registers a TOST equivalence test on the dollar axis. If the design already expects *no* dollar difference (R3's whole argument), then the primary endpoint's conditioning variable is a non-effect — the paper should say the dollars axis is a **null by design** and place the estimand on round-trips. As written, the reader cannot tell whether a null dollar result confirms or undermines the thesis.

**VERDICT: sound-with-fix.** The SAFE/CONDITIONAL/DO-NOT-CLAIM structure is unusually disciplined and is the design's strongest asset. But two SAFE claims (S1, S3) lack instruments, one (S2) lacks power, C3 and C5 are structurally untestable as designed, and five DO-NOT-CLAIM items are implied by the title, the figures and the arm set. All fixes are cheap; none is optional.

---

## 5. The novelty question, answered bluntly

**Is "a real local non-generative decision model + a measured truncation-versus-horizon curve" enough?**

**No — not for a main-conference paper, and the reason is structural rather than a matter of polish.**

- The **architecture is prior art** and R16 §C.7 already concedes all of it (FrugalGPT, RouteLLM, AutoMix, cascaded human-AI decision-making, learning-to-defer, Calibrate-Then-Delegate, Bayesian self-escalation). Replacing the middle tier's *species* is a **substitution**, and the paper's own framing sentence ("we replace the judge inside one cascade") announces that it is one.
- The **truncation curve is a bug report, not a scientific law.** It is a measurement of `planning.py`'s character estimator plus an unexplained clamp in one build. It is genuinely *useful* and genuinely *unmeasured in the literature* (R16 §C.7 #2 is right about that), but its scope is one artifact, and the team's own R13 §2.6 forbids explaining its mechanism. Reviewers reward negative results about tools — in **tooling and systems venues**, not at a general ML/CL venue where the reviewable unit is a mechanism or a generalisable finding.
- The **process metric** (error-detection lead time) is a contribution only if it is shown to *differentiate judges in a way accuracy cannot* — that is a claim the design currently asserts (R15 §3.2 reasons 1–2) but never tests. As designed, `T90` is a **new axis to plot existing judges on**, not evidence that the axis matters.
- The design also cannot support any claim about "decision models" as a class: **one implementation, one checkpoint, one device, one machine** (n = 202 warm calls in the entire probe record). R16 §D.3 N1 already concedes this.

**Where it flies / where it does not.**

| Venue class | Verdict |
|---|---|
| ACL/EMNLP/NAACL main conference | **No.** Single-system measurement studies without a mechanism or a multi-model ablation are routinely rejected as "engineering report." |
| NeurIPS/ICML main track | **No.** No new method, no theory; the empirical-track bar expects a broad, generalisable measurement. |
| ICLR | **No** for the same reason; the blogpost track is a different story. |
| **MLSys / EuroSys / OSDI-adjacent systems tracks, ICSE/ASE tooling tracks** | **Yes** — "a local decision-model judge changes the latency/cost structure of agent verification loops, and its failure mode is silent" is exactly a systems finding, and device-qualified first-party numbers are the coin of that realm. |
| **Workshops** (efficient ML, agentic systems, LLM-as-judge, calibration) | **Yes**, comfortably, as a strong workshop paper with a released artifact. |
| **TMLR** | **Possible but risky** — TMLR rewards correctness and clarity and tolerates the absence of a new method, but it will apply the same "one artifact, no mechanism" critique unless the claim is scoped hard. |
| **ICLR Blogposts / an upstream bug report + artifact** | **Yes, and this should be done first regardless of the paper's fate.** Filing the silent-window finding upstream converts a product defect into a citable, timestamped, independently verifiable artefact and creates the published-tool-release citation a venue can point at. |

**The additional experiment that would make it enough — concrete, and it is not the one the design is planning.**

The publishable claim is **not** "the cheap judge is nearly as good." It is: **"a cheap, local, non-generative judge detects a set of errors that a frontier generative judge at matched spend systematically misses."** That is a *mechanism-free, generally interesting* result — it is why ensembles and cascades work, and it has not been measured across judge *species*.

**Experiment D (diversity / complementary detection).** On the frozen 1000-item battery, with every judge answering every item byte-identically (the design already guarantees this), compute:

- the 2×2×… joint correctness table across {A1 structured LLM, A4-prose LLM, Laya, Jev-if-live};
- the **conditional detection rate** `P(catch | LLM judge wrong)` for each typed judge, with a **paired** bootstrap clustered by slot and run lineage;
- **error correlation**: Cohen's κ and the φ coefficient between judges' error indicators;
- the headline number: `Δ = P(typed catches | LLM wrong) − P(typed catches | LLM right)` — a **paired within-item** contrast, so it is immune to the accuracy-level confound that kills every comparative claim in the current design;
- the cost of that incremental detection per item, at matched spend.

**Why this is the right experiment.** It converts the paper's weakest comparative claim (typed judges are worse/similar in accuracy) into its strongest (typed judges are *differently* wrong, and the difference is worth money). It needs **no new mechanism, no new model and no new task family** — only the existing snapshots, one more LLM arm configuration, and the analysis code the design is already missing. It directly answers C1/C2 and gives the frontier figure a second dimension. It also explains *why* a cascade with a different-species first tier beats one with a same-species first tier (AutoMix, RouteLLM and FrugalGPT all operate within-family), which is a genuine, citable delta rather than a substitution.

**Secondary, and needed if the team insists on a "decision models degrade with horizon" generalisation:** replicate the truncation/window curve on **≥3 checkpoints of different encoder scale** (at minimum `english` 421 M, `typed-decisions` 421 M, `multilingual` ~322 M) plus one non-Laya implementation (the `von` drop-in named in R2 §D). One implementation cannot carry a class-level claim; three plus an independent implementation can carry a *narrow* one.

**Blunt verdict:** as specified, this is a **good systems/workshop paper and a rejected main-conference paper**. Adding Experiment D (diversity), scoping the truncation claim to the artifact, and filing the upstream bug report moves it to a credible systems-venue submission. Nothing else in the current plan does.

---

## 6. What a hostile reviewer writes

Three objections, in a competent skeptical voice, ordered by "the design currently cannot answer this."

> **Reviewer objection 1 — "Your 'horizon' result is a context-length result, and your truncation curve is a configuration artefact."**
>
> "The experiment manipulates *distance from a planted error inside one frozen run*, not task length, not step count, and not required capability. The authors' own manipulation check concedes that at d = 124 the decisive trace may not survive into the shipped 55-token carrier, in which case a wrong answer measures the *item construction*, not the judge (their R14 §6 T3). Meanwhile the 'truncation versus horizon' curve conflates horizon with input size, and input-size degradation is already well characterised — lost-in-the-middle, RULER, NoLiMa, Context Rot. The paper's own related-work section cites the residual-benchmarking position paper that requires a matched short-stage baseline for any horizon claim, and then does not compute one. And the window is not a property of the judge at all: it is a character-counting constant (`chars/4 × 1.15`) plus a 512-token clamp the authors explicitly decline to explain. So we have a bug in one vendor's planner, plotted against a manipulated variable that is not horizon, with no matched baseline."
>
> **Defusing experiment/disclosure:** (a) rename every axis — "distance from planted error", "input tokens", never "horizon"; (b) compute the horizon residual from R16 §D.5 objection 2 and pre-register the stages; (c) report the manipulation check per level and run the primary analysis on `survives` items only, with `absent` as a lower-bound control (R14 §5.3 already specifies this — it must be *executed*, and the exclusion rate reported); (d) add the solvability-floor audit; (e) state that `W` is empirical and report the measured clamp with its uncertainty; (f) include the multi-checkpoint replication from §5 above.

> **Reviewer objection 2 — "The comparison is rigged in three separate places, and two of them are yours to fix."**
>
> "First, the LLM judge is forbidden retrieval and tool use (their R14 §4.1 R3) while the typed judges see a *curated ≤497-token state* — so the LLM judge is being asked to reason about a truncated input it is not allowed to supplement, while the local judge sees an input engineered to fit its window. That is an affordance asymmetry, and their own symmetry command forbids it. Second, batching: their A5b lets the LLM batch up to 8 checkpoints per call while the typed arm asks one question per checkpoint — and their own probe document warns that 'a per-decision comparison that batches one judge and not the other is not a comparison.' Third, the Jev arm is entirely absent: the artefact's Jev results are a *hash function*, by the authors' own admission, and there is no live measurement. The cost chapter nevertheless prices Jev from a registry entry for `jev-latest` on a route that the authors' own probe says does not report cost, and compares it against a price page captured on a different date in a different pricing window."
>
> **Defusing experiment/disclosure:** (a) give the LLM judge the same retrieval affordance as a declared, budget-charged arm, or declare the no-retrieval rule as an explicit scope limitation with a paid-for sensitivity arm; (b) make batching symmetric across all judges — the same checkpoint windows, the same batch size, charged identically — before any efficiency number is computed; (c) either activate Jev and pass the §3 gate, or delete the arm, retitle the study as a two-judge comparison, and label the Jev economics as third-party; (d) publish the frozen corpus, protocol, price snapshot, timezone and per-run peak/off-peak flag with SHA256s, exactly as the benchmark the authors say they aligned to does.

> **Reviewer objection 3 — "Your lead-time metric is measured where it cannot matter, and its control shows nothing about drift."**
>
> "The abstract claims error-detection lead time as the paper's central process contribution, on the argument that a judge's value is its ability to flag a fault *while intervention is still possible*. But the metric is computed on an **offline replay plane on frozen snapshots**, where by construction no verdict can change anything — so the quantity reported is not lead time, it is a flag count on a transcript. Separately, the drift control is inadequate: judges are compared on detection *plus* a benign-paraphrase false-alarm rate, but a control that merely restates the same content cannot distinguish a judge that is sensitive to real faults from one that is sensitive to perturbation magnitude. And two of the three claimed detection channels are unmeasured for one judge: Laya's `choice` and `score` primitives have **no abstention or uncertainty channel at all** (its `confidence` is measured at 0.9981 *on the one wrong answer*, and its only calibrated 'I cannot tell' signal exists for `noul` alone), while the design forbids using `confidence` for gating — so Laya is forced to commit on every item, including near-ties where it splits 0.4951/0.4736 and still returns a hard label."
>
> **Defusing experiment/disclosure:** (a) define and report **both** planes: an online scheduled-detection estimate that drives actual control flow, and an offline exhaustive-replay detection estimate that is schedule-free, labelled as such, with the plane named in every table; (b) build a graded benign-perturbation ladder (paraphrase, reorder, length-matched distractor, semantically null edit) and report the full false-alarm curve rather than a single paraphrase cell; (c) pre-register Laya's abstention as a **distributional** rule (top-2 margin or normalised entropy) so abstention exists on all arms, and report the full distribution for `choice`/`score` rather than the argmax; (d) report the B0 column beside every detection number, per R15 §4.0, and report the false-alarm *trend* with horizon, not just its level.

**Also worth pre-empting (cheap):** the discovery that the paper's central window number is a **12.7× disagreement inside the team's own records** (cold start "389.9 ms" in R13 vs "4935.863 ms" in R11, both quoted as the same event) will be read as a proxy for the care taken elsewhere. Reconcile it before publication, or report both with their provenance.

---

## REPRODUCIBILITY MANIFEST

Status key: **PRESENT** = specified and stable · **PARTIAL** = specified incompletely · **UNSTABLE** = value can change silently · **ABSENT** = not specified anywhere.

| # | Item | Status | Where it must be recorded |
|---|---|---|---|
| 1 | Generator served model version (per response) | UNSTABLE | Methods §System; per-call row; cost table |
| 2 | Generator API base / region / legacy-alias mapping | ABSENT | Methods §System; run manifest |
| 3 | Prompt P1–P4 texts, verbatim | ABSENT | Pre-registration appendix; frozen protocol file |
| 4 | Primary reasoning effort for the headline LLM arm | ABSENT | Pre-registration §Primary endpoint |
| 5 | Logit-readout configuration (`max_tokens=1`, `logprobs`, `top_logprobs`, non-thinking, renormalisation, discard rule) | ABSENT | Pre-registration; §A.2.1 of the paper |
| 6 | Question bank: 9 instantiations, option strings, rubrics, boundaries | PARTIAL | Frozen `question_bank.json` + SHA256 |
| 7 | Canonical `criteria` order | PARTIAL | Frozen bank; per-response assertion |
| 8 | Option-count regime (4 vs 8 vs 10) | PARTIAL | Design decision; item gate |
| 9 | Frozen corpus states + keys | ABSENT | `cases.jsonl` + `SHA256SUMS` |
| 10 | Serializer `SER` text **and `K`** | PARTIAL | Pre-registration; `SER` hash |
| 11 | Laya host (Path A), full launch line | PRESENT | Methods §System |
| 12 | Laya host (Path B) launch line, labelled as second instrument | PARTIAL | Methods §Robustness |
| 13 | Per-response host provenance field | ABSENT | Every row; hard-fail on mixture |
| 14 | Canary probe (`state:"test"` → 917 vs 405) | ABSENT | Methods footnote; replication script |
| 15 | Laya checkpoint weights + config hashes (all 3 checkpoints) | ABSENT | `SHA256SUMS`; run manifest |
| 16 | `laya_mcp` code identity (`planning.py` `70E90EE8BB32356B…`, `worker.py` `8A0ABEE5F6156B3A…`) | ABSENT | Methods §System; `SHA256SUMS` |
| 17 | Sidecar/Python/torch versions (`0.2.1`, 3.12.14, torch 2.11.0+cu128, CUDA 12.8) | PARTIAL | Run manifest |
| 18 | Device (RTX 5060 Laptop 4 GB, driver 32.0.16.1047; Intel Ultra 7 255HX; Win11) | UNSTABLE | Methods §System; every latency table |
| 19 | Runtime clamp value and measurement basis (512 seq-tok vs ~450 state-tok; damage seen at 453) | UNSTABLE | Results §Silent degradation; limitations |
| 20 | Tokenizer + counting rule | PRESENT | Methods; artefact |
| 21 | Parameter count (421,293,830, from `model.safetensors` header) | PRESENT (derivable) | Methods footnote with derivation |
| 22 | Jev provider route (`live` vs `openrouter`), endpoint, gates' values | ABSENT | Methods §System; run manifest |
| 23 | Jev credential **ref name** (never value); `cordis.patch.yml` SHA256 | ABSENT | Run manifest |
| 24 | Jev resolved model id + billing identifier **per row** | UNSTABLE | Every Jev row |
| 25 | Jev output-billing treatment | UNVERIFIED | Cost table footnote |
| 26 | Jev live/mock discriminator assertions (G1–G12) | ABSENT | Collection script; analysis hard-fail |
| 27 | Pricing snapshot, fetch date, per-run peak/off-peak flag, timezone | PARTIAL | Cost table; run manifest |
| 28 | Peak/off-peak definition + holiday calendar source | PRESENT (definition) / ABSENT (calendar) | Cost table footnote |
| 29 | Gold-evaluator identity (model or human) and its accuracy audit (≥200 cells) | PARTIAL | Methods §Evaluator |
| 30 | `tol`, `B_lo`, `B_hi`, `ε`, deviation predicate, τ*, s* | PARTIAL | Pre-registration |
| 31 | Calibration corpus (4 families × 40 runs) + hash | ABSENT | Pre-registration |
| 32 | Randomisation seed + arm/onset/option-order assignment artefact | ABSENT | Pre-registration; artefact |
| 33 | Option-position Latin square | PARTIAL | Artefact |
| 34 | Analysis code (`analyze.py` equivalent) | ABSENT | Artefact; version-pinned |
| 35 | RI permutation (≥10,000 draws), CR2, wild cluster bootstrap `B=9,999` implementations | ABSENT (specified in prose) | Analysis code |
| 36 | Immutable snapshots `SNAP[run][t]` + hash manifest | PRESENT (spec) / ABSENT (artefact) | Artefact |
| 37 | Failed-run retention and disclosure | ABSENT | Methods; artefact |
| 38 | Budget arithmetic (R15 `$3,802` vs `$38.02`) reconciled | UNSTABLE | Budget table |
| 39 | LLM price used in the cost model ($0.15/$0.60 verified vs $0.28/$0.42 in R15) | UNSTABLE | Cost table |
| 40 | "What we did not establish" section | PARTIAL (R16 supplies material) | Paper §Limitations |

## DISCLOSURE OBLIGATIONS

1. **Jev provenance.** Any Jev datum in the paper must carry: `provider`, resolved model id, collection date/time, timezone, peak/off-peak flag, plugin version, config SHA256, and the assertion set G1–G12. If Jev remained mock, publish **no** Jev number; state the mock explicitly, report its fixture properties (Brier 0.359 at hard-coded `confidence` 0.5; boundary delta exactly 0.0000 **because the boundary is not in the hash**), and label it a methodological hazard.
2. **Arm removal.** If Jev is unavailable: delete A2 and the A4-Jev branch, retitle to a two-judge comparison, remove "three judgment layers" from abstract and figures, and present Jev as interface contract + third-party pricing + third-party head-to-head, explicitly marked **not measured here**.
3. **Two-instrument disclosure.** State that the plugin and MCP entry points are different instruments with different announced budgets and opposite planner error signs; name the primary by invocation and flags; publish the canary probe; state that the API exposes no host selector.
4. **Code identity.** Declare that the silent-truncation window is a property of a specific `laya_mcp` build, and publish the SHA256 of the instrument files. Without this the paper's central number is not reproducible.
5. **Mechanism.** State that the runtime clamp's cause was not isolated and that no mechanism is asserted (R5 §8.4 already commits to this).
6. **Window definition.** Report the effective window as measured, with its uncertainty; never present "512" as a specification; report that damage was observed at 453 real state tokens.
7. **Scope of the degradation claim.** Restrict it to this implementation, checkpoint, device and build. Do not generalise to "decision models" without the multi-checkpoint and second-implementation replication.
8. **Device.** Publish the exact hardware/OS/driver/torch/CUDA stack; state that no M1 Max (or any other) measurement is included; report CPU-fallback detection and cold-start records separately.
9. **Calibration repair.** Fit temperature scaling within-judge on a held-out split for **all** arms with equal budget; never compare raw probabilities or `confidence` across judges or across framings; report the uncalibrated 100%/0% behaviour as a finding.
10. **Budget charging.** Charge every retry, every sample, every batch, and every escalation to its arm's budget; report the batching configuration for every arm; disclose and explain the retrieval asymmetry.
11. **Lead-time plane.** Name the plane (online control vs offline replay) in every table and figure legend; never present an offline replay flag as "intervention while it still mattered."
12. **Exclusions.** Report the G1 item-rejection rate, the poison-invisibility rate, the solvability-audit exclusion rate, and every failed configuration, in the paper and in the artefact.
13. **Horizon naming.** Every figure or table whose independent variable is distance-from-poison or input size must say so; the word "horizon" may appear only where the matched short-stage residual baseline is also reported.
14. **Money.** Report the corrected budget arithmetic, the price snapshot with date, and the model's sensitivity grid; state which claims survive if the LLM price is the verified snapshot rather than R15's template values.

---

### One-paragraph summary for the parent

The design's *threat model* is better than most published work and its SAFE/CONDITIONAL/DO-NOT-CLAIM discipline is genuine. Its *reproducibility* is not: no frozen corpus, no protocol file, no hashes, no analysis code, no seed, no checkpoint identity, and an instrument whose defining constants live in unhashed Python. Its *central contribution* currently has no instrument, because the item gates reject exactly the states whose truncation the paper exists to measure. Its *comparison* is asymmetric in two fixable places (retrieval for the LLM judge, batching across judges) and one unfixable one (a mock Jev arm). Its *novelty*, as specified, is a substitution plus a bug report — a good systems or workshop paper, a rejected main-conference paper. The cheapest route to a real contribution is the cross-species error-diversity experiment, which needs no new mechanism and uses snapshots the design already plans to collect.

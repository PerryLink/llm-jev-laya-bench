# R11 — DSH Instrumentation Testbed

**Question.** What does the DeepSeek Harness checkout at `D:\deepseek-harness` actually let us
measure, automatically, and at what granularity?

**Method.** Every claim below is backed by either a real file read, a real tool call, or a decoded
session record. Items I could not establish are marked **NOT VERIFIED**.

**Runtime facts observed first-hand** (from the live session this report was produced in):

- Session state root: `C:\Users\zzhdz\.dsh` (contains `settings.yaml`, `sessions/`, `storages/`,
  `profiles/`).
- LLM route: `provider = deepseek-official`, `model = deepseek-flash`, `contextWindow = 1000000`,
  `reasoningEffort = max`, `maxTokens = 256000`.
- **Jev provider is `mock`** — see §4.2. This is the single biggest instrumentation gap in the
  testbed.

---

## 1. Skill-catalog format, resolved

### 1.1 Where the skill actually lives

| Item | Value |
|---|---|
| Skill name | `typesafe-ai-dsh` |
| On-disk file | `C:\Users\zzhdz\.dsh\profiles\web\node_modules\jevcore-dsh\skills\typesafe-ai-dsh\SKILL.md` |
| Registered by | `C:\Users\zzhdz\.dsh\profiles\web\node_modules\jevcore-dsh\src\skill.ts` (shipped build: `lib\skill.js`) |
| Plugin entry | `C:\Users\zzhdz\.dsh\profiles\web\node_modules\jevcore-dsh\src\index.ts` |
| Catalog source package | `D:\deepseek-harness\packages\skill\skill\src\index.ts` |

The skill is **not** discovered from a `skills/` directory by a filesystem provider. The plugin
contributes it programmatically through the registry:

```ts
// jevcore-dsh/src/index.ts:384-400
const skills = ctx.get('skills') as
  | { register: (registration: unknown) => () => void }
  | undefined
if (skills === undefined) { logger.warn(/* ... */) } else {
  try {
    const registration = skillRegistration()
    ctx.effect(() => skills.register(registration))
  } catch (error) { logger.warn(/* ... */) }
}
```

Note the registration object is typed `unknown` at the cast above. **That cast is the reason the
defect is invisible to TypeScript** — the compile-time contract on `skillRegistration()`'s return
value is never applied.

### 1.2 Exact schema of a skill definition

From `D:\deepseek-harness\packages\skill\skill\src\index.ts`:

```ts
// line 40
export type SkillSource = 'project-dsh' | 'project-agents' | 'runtime' | 'user-dsh'
  | 'user-agents' | 'custom' | 'bundled' | (string & {})

// lines 57-74 — SkillSummary
readonly path?: string
readonly name: string            // kebab-case, SKILL_NAME grammar
readonly description: string     // must be non-empty
readonly whenToUse?: string
readonly invocation: SkillInvocationPolicy   // { modelInvocable: boolean; userInvocable: boolean }
readonly source: SkillSource     // <-- REQUIRED
readonly provider: string
readonly resourceBase?: SkillResourceBase

// lines 87-92 — SkillDefinition extends SkillSummary
readonly content: string
readonly metadata?: Readonly<Record<string, unknown>>

// lines 95-100 — SkillRegistration (what ctx.skills.register() accepts)
export type SkillRegistration = Omit<SkillDefinition, 'invocation' | 'provider'> & {
  readonly invocation?: SkillInvocationPolicy
  readonly provider?: string
}
```

**`SkillRegistration` omits only `invocation` and `provider`. `source` is required by the type.**

### 1.3 The SKILL.md frontmatter schema

Two scalar fields, parsed by a hand-rolled parser (`jevcore-dsh/src/skill.ts:43-78`):

```ts
const FRONT_MATTER = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/
```

Each line is split on the **first** `:`; blank lines and lines starting with `#` are skipped; both
`name` and `description` must be present or `parseSkill()` throws. The real file:

```yaml
---
name: typesafe-ai-dsh
description: Use TypeSafe Jev for narrow judgments inside DeepSeek Harness — routing, ...
---
```

### 1.4 The concrete reason a definition loads with a non-string `source`

**There is an asymmetry: `source` is validated on LOAD but not on REGISTER.**

| Path | Function | Checks `source`? |
|---|---|---|
| `SkillRegistry.register()` (line 439) | `validateRuntimeSkill()` (line 741) | **No.** Validates `name`, `description`, `invocation` only. |
| defaults applied at register (lines 447-451) | — | Defaults **only** `invocation` and `provider`. `source` is left `undefined`. |
| `SkillRegistry.get()` (line 500) | `validateDefinition()` (line 748) | **Yes**, line 763. |

```ts
// packages/skill/skill/src/index.ts:763
if (typeof source !== 'string') throw new TypeError(`loaded skill "${name}" source must be a string`)
```

`jevcore-dsh`'s `skillRegistration()` returns exactly four fields and no `source`:

```ts
// jevcore-dsh/src/skill.ts:123-133  (identical in the shipped lib/skill.js:101-110)
return {
  name: skill.frontMatter.name,
  description: skill.frontMatter.description,
  whenToUse: 'A decision turns on a small, fixed set of outcomes, ...',
  content: skill.content,
}
```

**Therefore:** the skill registers successfully (so it appears in the catalog, and the failure is
*not* logged at startup), and throws only when the model calls `skill` on it. Reproduced live:

```
Error: loaded skill "typesafe-ai-dsh" source must be a string
```

**Fix (not applied — outside my write scope):** add one field to `skillRegistration()`'s return
value. The registry reserves the provider name `runtime` (`RUNTIME_PROVIDER = 'runtime'`, line 24),
and `'runtime'` is a member of the `SkillSource` union, so `source: 'runtime'` is the value that
matches the registration path. **NOT VERIFIED:** that this exact value is what upstream intends, or
that any patched build exists. What *is* verified is that the field is missing, that it must be a
string, and that the union admits `'runtime'`.

### 1.5 Why DSH's own tests did not catch it

The test that asserts this error message
(`D:\deepseek-harness\packages\skill\skill\tests\skill.spec.ts:524`) drives a **provider-returned
definition** (`registerProvider(...)`, line 534) with a malformed `source`. The
`ctx.skills.register()` path with an *absent* `source` is not covered.

**Consequence for the paper.** Until this is fixed, the method section cannot cite a working Jev
usage skill loaded through DSH — the file exists and is correct, but it is unreachable. The Jev
tools (`jev_ask`/`jev_check`/`jev_rank`) are unaffected and remain callable; only the guidance
document is unreachable.

---

## 2. Transcript / session record structure

### 2.1 Location and naming

```
<DSH state>/sessions/<encoded-cwd>/<sessionId>/session.v3.jsonl.zstd
```

Real examples:

- Root session for `D:\Projects`:
  `C:\Users\zzhdz\.dsh\sessions\--D-Projects--\session-adfc3a7b-3d8e-4769-9e66-9d0cc0c80c3e\session.v3.jsonl.zstd`
- **Subagent session** (this R11 unit):
  `C:\Users\zzhdz\.dsh\sessions\--D-Projects--\4be5901c-dd8c-435d-9848-2632eac47cee\session.v3.jsonl.zstd`

Two naming conventions coexist in the same bucket:

- root sessions are `session-<uuid>/`
- **spawned subagents are bare `<uuid>/`** — siblings of the parent, in the same encoded-cwd
  directory.

The parent transcript records each child's id, creation time and mode in `subagent/catalog`
records, so the parent→child linkage is recoverable from the parent log alone.

Aggregate: `C:\Users\zzhdz\.dsh\sessions` holds **871 `.zstd` files** across 7 workspace buckets.

### 2.2 Container format

**Concatenated, independently-decodable, checksummed Zstandard frames. One frame holds a *batch*
of JSONL records; the first frame is exactly the session header line.**

Source of truth: `D:\deepseek-harness\packages\session\session-persistence-jsonl\src\zstd.ts`

- magic `0xFD2FB528` (`ZSTD_MAGIC`, line 15)
- `CHECKSUM_OPTIONS` sets `ZSTD_c_checksumFlag` (lines 18-20)
- `scanZstdFrames(buffer, maxFrames)` walks frame headers structurally **without decompressing**
  (lines 48-104) and returns `{ frames: [{start, end}], tornStart? }`
- `decompressZstdFrame()` validates the checksum; `decompressIncompleteFrame()` recovers a torn tail
- the package's own test asserts the default artifact is "one header frame and one first-batch
  frame", and that a *non-independent* header frame is refused

**Practical note.** Node 22's `zstdZstdDecompressSync` / `createZstdDecompress()` decode only the
**first** frame and silently stop. Scanning for the 4-byte magic is **not** a valid frame walk —
magic bytes occur inside compressed payloads (I measured 68 candidate offsets vs 75 real frames).
Use the `scanZstdFrames` walk. Verified counts: parent session = **75 frames → 147 records**;
this unit's session = **226 records**.

### 2.3 Record structure (content redacted)

Two shapes only. The header:

```json
{"type":"session","version":3,"id":"<redacted>","cwd":"<redacted>",
 "createdAt":<epoch-ms>,"isSeeded":false,"delegationDepth":0,"agentPreset":"<redacted>"}
```

The event envelope — **every other record**:

```json
{"type":"<record-type>","seq":<int>,"time":<epoch-ms>,"data":{ /* redacted */ }}
```

Some records additionally carry `"sourceEventSeqs":[<int>]` and `"surfaceOp":"<op>"`.

Real one-line example, structural keys only:

```
{"type":"tool/call","seq":<int>,"time":<epoch-ms>,
 "data":{"turn":<int>,"step":<int>,"callId":"<redacted>","name":"<redacted>","arguments":"<redacted>"}}
```

### 2.4 Record types actually observed (parent session, 147 records)

`session`, `permission/preset`, `sandbox/mode`, `approval/policy`,
`subagent/model-selection-policy`, `agent-preset/selected`, `agent/inbox/spliced`, `turn/start`,
`step/start`, `system/message`, `user/message`, `request/header`, `request/context`,
`session/title`, `session/title-llm-request`, `session-log-deepseek/delivery-accepted`,
`assistant/message`, `tool/call`, `tool/result`, `step/end`, `subagent/catalog`, `todo/write`,
`web/deepseek-search-llm-request`.

### 2.5 The five requested fields — verdicts

| Field | Recorded? | Where | Evidence |
|---|---|---|---|
| **Per-step token usage** | **YES** | `assistant/message.data.usage` | key union verified over 11 usage records: `inputTokens, outputTokens, cacheReadTokens, cacheWriteTokens, totalTokens`. Also duplicated as a `{"type":"usage"}` chunk inside `data.stream`. |
| **Cost (money)** | **NO** | — | Zero cost fields in 147 records. The single line matching `/cost/i` was the parent agent's own grep-argument text. `packages/llm/token-meter` "prices" **tokens** heuristically, not currency. |
| **Timestamps** | **YES** | envelope `time` | 146/147 records carry a numeric epoch-ms `time`; the header carries `createdAt` instead. Stream chunks carry `time` too. |
| **Model id** | **YES** | `request/context.data` and per-message `assistant/message.data.message.source` | `request/context.data = {provider:"deepseek-official", model:"deepseek-flash", contextWindow:1000000}`. Per message: `source = {kind:"model", provider, model, replayState:{response:{kind:"deepseek-messages",version:1,model:"deepseek-flash"}, blocks:[...]}}`. |
| **Reasoning effort** | **YES, but once per session** | `request/header.data.header.config` | `{provider, model, reasoningEffort:"max", maxTokens:256000}`, with `request/header.data.reason = "initial"`. Exactly **1** such record in the session — **not per step**. |

### 2.6 Are tool arguments and results verbatim?

**Arguments: yes, verbatim.** `tool/call.data = {turn, step, callId, name, arguments}` where
`arguments` is the exact JSON string the model emitted. Verified by reading back the full
`laya_ask` argument payload, byte-for-byte, from this unit's own transcript. The token-level
deltas the model streamed are *also* preserved in the preceding `assistant/message.data.stream`
(`{"type":"tool-call-chunks", ... "args":[...]}`).

**Results: yes, verbatim.** `tool/result.data.message =
{role:"user", source:{kind:"tool", callId}, content:[{type:"tool-result", text, isError}], id}`,
with envelope `sourceEventSeqs` and `surfaceOp:"append"`. Verified by finding Laya's own
`latency_ms: 4935.863` and its `warnings` array reproduced verbatim inside the stored result, and
by finding the `laya_plan` wrapper error text preserved with `isError:true`.

**Consequence:** the transcript is a complete, self-contained, offline-replayable record of every
tool round-trip — arguments, results, ordering (`seq`), and wall-clock (`time`). No external logger
is needed to capture *content*.

---

## 3. Subagent lifecycle and resume semantics

### 3.1 The agent/subagent tools in this tool list

| Tool | Orchestration role (from its own description) |
|---|---|
| `subagent` | Background spawn of a context-isolated child. "runs in the background by default, immediately returns a **durable subagent id**, and **keeps the child conversation available for later turns**." Optional `provider`/`model`/`reasoning_effort`. |
| `subagent_fork` | Same, but the child "**inherits this conversation**… seeded with all completed turns so far (it does not see the current in-flight turn)." No model override. |
| `list_agents` | Durable enumeration. Statuses: `running`, `idle` ("loaded but between turns"), `ready` ("exists only in storage — **resumable**, not terminal, and not a result waiting to be collected"). `scope: descendants` walks the tree. |
| `send_message` | Steer or wake. "If the target is still working, the message **steers its nearest step**; if it is idle, the message **starts a turn**." Also reaches a `ready` (cold) child. |
| `interrupt_agent` | "Only the **current turn** stops: messages already queued for the agent stay parked until a later `send_message`, agents it started keep running, and **the agent itself stays available for follow-ups**." |
| `list_subagent_models` | Discover provider/model/effort routes for children without changing the current agent. |
| `workflow` | Scripted fan-out across many subagents (`agent`, `pipeline`, `parallel`, `phase`). |
| `job_list` / `job_output` / `job_kill` | Background *command* jobs (not agents). |

### 3.2 Can a subagent be paused and resumed? — yes, with a precise meaning

**There is no `pause` tool and no `resume` tool.** Resume is *implicit*: the child is a persisted
session, and `send_message` either steers it, wakes it, or **cold-resumes** it.

Observed in the live parent transcript — every child was spawned continuable:

```json
{"version":0,"childId":"<redacted>","childCreatedAt":<epoch-ms>,
 "mode":"continuable","label":"<redacted>"}
```

`mode` is the switch, from `D:\deepseek-harness\packages\subagent\subagent\src\descriptor.ts`:

```ts
// line 55
readonly mode: 'one-shot' | 'continuable'

// line 60  — OneShotSubagentDescriptorData
/** A session-backed subagent that cannot be cold-resumed after its run. */

// line 71-73 — ContinuableSubagentDescriptorData
/** A session-backed subagent whose declared composition supports cold resume. */
readonly mode: 'continuable'
```

`SUBAGENT_DESCRIPTOR_VERSION = 3` (line 48). A non-continuable child is refused explicitly
(`src/continuation.ts:428-430`):

> `subagent "${childId}" has no supported continuation state and cannot be resumed; choose a different target`

Cold resume is a real `agents.resume` call (`src/continuation-activation.ts:634`):

```ts
? await this.ownerCtx.agents.resume({ resumeSessionId: childId, ... })
```

### 3.3 What resume preserves

The persisted **descriptor** plus the child's own **event log**.

| Preserved | Evidence |
|---|---|
| Model route + reasoning effort | descriptor fields `agentProvider`, `agentModel`, `agentReasoningEffort`; tests: "persists a selected reasoning effort and **reapplies it on cold resume**", "reapplies the descriptor model route and reasoning effort on cold resume". |
| Persona / tool scoping | `persona?: string`, `toolFilter?: ToolRestriction` — "Per-child persona that shadows the deployment persona on resume", "Child tool scoping reapplied on resume". |
| Recursion depth | `child-agent.ts:154` — "Durable: the recursion budget must survive persistence and resume." |
| Full conversation context | `subagent-fork-in-process/src/index.ts:87` — "child's own durable transcript, so a later cold resume **replays** that"; test asserts resumed event log = `['child task', 'resume']`. |
| Permission preset — **pinned at creation** | `continuation-inheritance.spec.ts`: "cold resume must not read parent permission"; the resumed child keeps the policy it was created with even if the parent later widened it. |

**A resume is a NEW epoch, not a rewind.** Tests: "A cold resume is a NEW epoch: it must report its
OWN answer, never the [previous one]". So resume continues the conversation; it does **not** roll
back state. This matters for the design: resume is a *context-continuation* mechanism, not a
*checkpoint* mechanism. There is no transcript-level branch/undo primitive.

**Design implication.** For a long-horizon experiment, a subagent can act as a durable worker that
is interrupted (`interrupt_agent`), left idle for an arbitrary period, then woken
(`send_message`) with its full history, its original model/effort/persona, and its original
permission pin. That is a usable long-horizon primitive. What it cannot do is rewind to an earlier
state.

---

## 4. Cost / time accounting

### 4.1 LLM arm (`deepseek-official` / `deepseek-flash`)

**Wall-clock — measurable.** Every record has a millisecond `time`. `tool/result.time −
tool/call.time` gives the duration of a tool round-trip. Verified on the parent session across 31
paired calls (e.g. a `grep` at 30 064 ms, a `web_fetch` at 10 529 ms, a `pwsh` at 592 ms).

**Critical caveat — parallel calls are not separable.** All tool calls emitted in one assistant
step share a single result timestamp. Measured first-hand in this unit's own session: five calls
issued in one batch (`laya_ask`, `laya_plan`, `jev_ask`, `jev_check`, `jev_rank`) recorded
`result@` at `…760318`, `…760319`, `…760320`, `…760320`, `…760320` — deltas of 4967–4968 ms each.
The transcript therefore yields **batch wall-time (max of the batch), not per-call latency**, when
the host runs calls in parallel. `agent-loop.maxParallelToolCalls` is **20** in the active
`settings.yaml`, so this is the normal case, not an edge case.

**Tokens — measurable.** `assistant/message.data.usage`. Measured totals for this unit's session:
`input = 75 511`, `output = 19 207`, `cacheRead = 1 168 640`, `total = 1 263 358`. Arithmetic
verified: `totalTokens = inputTokens + outputTokens + cacheReadTokens`.

**Cost — NOT available from DSH.** No monetary field exists anywhere in the transcript, and
`packages/llm/token-meter` performs heuristic *token* estimation, not currency accounting. Cost
must be computed by an external ledger: `tokens × price`, with cache-hit / cache-miss / output
priced separately. **NOT VERIFIED:** the price table itself, and whether the profile's route
declares one (that is R2's remit, not observable from the harness).

**Programmatic extraction.** No session-query tool is exposed in this session's tool list. The
checkout does contain the machinery — `packages/session-query/session-log-export/src/archive.ts`
(`serializeSessionLog`, `readSessionLogText`, `streamSessionLogZip`), `session-query/src/cold-read.ts`
(`readColdSessionLog`), and a `tool-session-query` package — but **NOT VERIFIED** whether any of it
is composed into the running profile. The path I used and verified is: read the `.zstd`, walk
frames with the `scanZstdFrames` algorithm, `zstdDecompressSync` each frame, split on `\n`,
`JSON.parse` per line. That is ~40 lines and needs no DSH internals.

### 4.2 Jev arm — **the critical gap: the provider is `mock`**

Live call, verbatim excerpt:

```json
{"provider":"mock","model":"jev-latest","latencyMs":0,
 "warning":"These answers are SYNTHETIC. The mock provider derived them from a hash of the input;
            they carry no judgment. Set provider to \"live\" or \"openrouter\" with a credential
            for real answers.",
 "usage":{"inputTokens":0,"outputTokens":0,"costUsd":0}}
```

Configured on disk at
`C:\Users\zzhdz\.dsh\profiles\web\node_modules\jevcore-dsh\cordis.patch.yml:8`:

```yaml
- insert:
    - id: jev
      name: 'jevcore-dsh'
      config:
        provider: mock
        gates:
          safety: { enabled: false, onUndecided: ask }
          context: { enabled: false }
```

Both gates are also disabled.

**What this means concretely.**

- The *schema* for cost and latency exists and is populated: `latencyMs` and
  `usage.costUsd` are real fields on every Jev result.
- The *values* are structurally nullified: `latencyMs: 0`, `costUsd: 0`, `inputTokens: 0`,
  `outputTokens: 0`.
- The *answers* are hash-derived, not judgments. Confirmed independently: `jev_check` returned
  `verdict:"insufficient"` for a claim the stored evidence states almost verbatim, and `jev_rank`
  ordered candidates by nothing meaningful. Neither outcome is a measurement of Jev.
- `jev_ask` also validates client-side before any provider runs — a `score` question with
  integer-like level names was rejected with `Error: score criteria use integer-like level names
  (0, 1, 2, 3). JavaScript reorders integer-like keys…`. That rejection is a **harness-side input
  validation**, not a model measurement.

So: **the Jev arm, as currently configured, measures nothing about Jev.** Its latency, cost and
accuracy are all unobservable until `provider` is set to `live` or `openrouter` **and** a
credential is stored. **NOT VERIFIED:** what `latencyMs` reports under a live provider, since I
cannot switch it (that would be a modification outside my output file, and would require a
credential).

### 4.3 Laya arm

Real, local, warm-by-then call — Laya **self-reports** its own timing and usage inside the tool
result:

```json
{"model":"english","device":"cuda","latency_ms":4935.863,
 "usage":{"input_tokens_padded":346,"output_tokens":0,"questions":2},
 "budget_summary":{"fits":true,"head_max_len":512,"worst_question":"<redacted>",
                   "tightest_option_tokens_each":49},
 "routing":{"model":"english","reason":"explicit model selection","lang":"en"},
 "confidence_semantics":"Laya's `confidence` is a concentration statistic … NOT the probability
                         that the answer is correct …",
 "warnings":["..."]}
```

- **Per-call latency is directly measurable** from `latency_ms` in the tool result — better than
  transcript inference, and immune to the parallel-batch problem. The 4 935.863 ms figure is a
  **cold-start-inclusive first call**; the transcript's batch delta for the same call was 4 968 ms,
  so they agree to within ~0.7 %.
- **Latency is also inferable from the transcript** for a call issued *alone* (batch of one).
- Laya reports its own token accounting (`usage.input_tokens_padded`, with the explicit caveat that
  it "counts the padded batch, so it overstates small requests").
- Sidecar config: `C:\Users\zzhdz\.dsh\profiles\web\node_modules\dsh-laya\cordis.patch.yml` —
  `sidecarUrl: 'http://127.0.0.1:8787'`, `requestTimeoutMs: 120000`, `lifecycle: never`,
  `spawnCommand: null`.

**Broken tool — `laya_plan`.** Live call:

```
Error: tool "laya_plan" returned invalid output: "value.fits" must be a boolean
```

Recorded verbatim in the transcript as a `tool/result` with `isError:true`. Note that
`laya_ask` returns `budget_summary.fits: true` (a genuine boolean) in its own payload, so the
schema the `laya_plan` wrapper validates against is not the shape `laya_ask` produces.
**NOT VERIFIED:** which shape `laya_plan` expects and whether the fault is in the plugin or in the
sidecar response.

**This is itself a measurable datum** — the malformed/non-parseable-output metric the paper wants
has at least one real, reproducible instance on day one.

### 4.4 Summary: measurable vs. needs an external harness

| | **Measurable from DSH alone** | **Requires an external harness** |
|---|---|---|
| **LLM arm** | per-record ms timestamps; batch wall-time per step; per-step token usage (in/out/cache-read/cache-write/total); model id; reasoning effort; tool call arguments and results verbatim; tool-call counts and ordering | monetary cost (needs a price table); **per-call latency when calls are parallel**; any concurrency control; ground-truth scoring |
| **Jev arm** | **nothing about Jev's judgment** under the current `mock` config; batch wall-time only | everything: real answers, real latency, real cost, calibration. Needs `provider: live\|openrouter` + credential, then re-measurement |
| **Laya arm** | per-call `latency_ms` self-reported; `device`; model variant; token accounting; `budget_summary`; `warnings`; full answer payloads; batch wall-time | ground-truth scoring; calibration fitting; controlled repetition sweeps; warm/cold separation beyond the first call |

---

## 5. Proposed measurement matrix

| Metric | LLM arm | Jev arm | Laya arm | Risk of unavailability |
|---|---|---|---|---|
| **Wall-clock latency per decision** | `tool/result.time − tool/call.time`; **only valid for a batch of one** (parallel calls share a result stamp; `maxParallelToolCalls = 20`) | tool result `latencyMs` — **currently `0` under mock**; transcript gives batch wall-time only | tool result **`latency_ms`** — measured, first-hand, per call. Transcript batch delta corroborates (±0.7 %) | **LOW** for Laya, **HIGH** for Jev (config), **MEDIUM** for LLM (parallelism must be forced to 1, which changes the arm being measured) |
| **Tokens consumed** | `assistant/message.data.usage`: `inputTokens, outputTokens, cacheReadTokens, cacheWriteTokens, totalTokens` — measured, sums verified | `usage.{inputTokens, outputTokens}` present but **zeroed under mock**; `stateChars`/`questionsChars` in `egress` are real | `usage.input_tokens_padded`, `usage.questions`, `budget_summary.tightest_option_tokens_each` | **LOW** for LLM and Laya; **HIGH** for Jev |
| **Cost** | **Not recorded.** Compute as `tokens × price`, cache-hit/miss/output separately | `usage.costUsd` field exists, **`0` under mock**; live pricing **NOT VERIFIED** | no monetary field; requires an agreed local-compute amortisation formula | **HIGH for all three** — the metric is synthesised, not observed. Any cross-arm cost claim rests on three different accounting conventions |
| **Tool round-trips** | Exact: count `tool/call` records; `turn`/`step` on each; `callId` links call→result. Fully automatic | same (each `jev_*` call is one `tool/call`) | same | **LOW** — this is the best-instrumented metric on the testbed |
| **Answer correctness vs ground truth** | not recorded; needs an external item battery + scorer | not recorded; needs the same | not recorded; needs the same | **MEDIUM** — the harness captures the *answer* verbatim; nothing captures the *truth* |
| **Calibration** (returned probability vs observed accuracy) | requires the LLM to emit a probability; DSH records whatever text it emits, unparsed | `noul`/`probabilities` are structured and captured verbatim | `noul`/`probabilities` captured verbatim, **plus** Laya ships `confidence_semantics` warning that `confidence` is a concentration statistic — the paper must bin on `noul`, never on `confidence` | **LOW** for capture, **HIGH** for validity (needs N per bin; see §6) |
| **Malformed / non-parseable output rate** | text output is never parsed by DSH, so nothing fails structurally | client-side validation errors are captured verbatim in `tool/result` (e.g. the integer-like-score-levels rejection) | **already observed**: `laya_plan` → `tool "laya_plan" returned invalid output: "value.fits" must be a boolean`, stored with `isError:true` | **LOW** — measurable, and already non-zero |
| **Truncation / budget-overflow rate** | context window 1 000 000; overflow would surface as a provider error in the transcript | `egress.truncated`, `egress.stateChars` recorded per call | `budget_summary`, `warnings`, and `strict:true` can force refusal; `laya_plan` is the intended pre-check **and is broken** | **MEDIUM** — the signal is captured, but the *pre-check* tool is unusable, so overflow must be detected post hoc |
| **Determinism under repetition** | needs repeated identical calls; `settings.yaml` pins effort to `max`, and no sampling controls are exposed in the transcript | needs repetition; mock provider is deterministic-by-hash, so **any determinism result under mock is an artefact** | needs repetition; option-order sensitivity is a live risk (`mcp__laya__laya_choice` warns that accuracy falls off above ~20 options) | **MEDIUM** — repeats are cheap to issue, but ordering/temperature controls are not recorded, so a null result is hard to attribute |

---

## 6. What the testbed cannot measure

Ranked by how much they force the design to compromise.

**G1 — The Jev arm is a mock. (Forces the largest compromise.)**
Every Jev answer today is derived from a hash of the input; `latencyMs` and `costUsd` are `0`.
The paper cannot report a single real Jev number from this harness as configured.
*Cheapest workaround:* set `provider: live` (or `openrouter`) in
`jevcore-dsh/cordis.patch.yml` and store a credential in the DSH credential service.
*Epistemic cost:* the arm becomes a **network** call to a third party — the latency then measures
network + vendor, not the model, and is not comparable to Laya's local `latency_ms`. It also breaks
the "no egress" property the plugin defaults to, so the redaction/egress contract
(`egress.redactedFields`, `stateChars`) becomes a live experimental variable rather than a
footnote. And a hosted service can change under the experiment's feet mid-run.

**G2 — No monetary cost is recorded anywhere.**
*Cheapest workaround:* compute cost externally as `tokens × published price`, separating cache-hit,
cache-miss and output, and record the run window (peak/off-peak) alongside it.
*Epistemic cost:* the Jev and Laya arms have no published per-call price at all, so their cost must
be *modelled* (local compute amortisation). The cross-arm cost comparison is then a model output,
not a measurement — and the model's assumptions drive the headline efficiency claim.

**G3 — Per-call latency is destroyed by parallelism.**
With `maxParallelToolCalls = 20`, a batch of judgments yields one shared result timestamp. Forcing
serial execution recovers per-call latency but changes the thing being measured (an agent with
parallel tool use is not the same system as one without).
*Cheapest workaround:* take per-call latency from the arms' **self-reported** fields where they
exist (`latency_ms` for Laya, `latencyMs` for Jev), and treat transcript deltas as batch
wall-clock only.
*Epistemic cost:* the self-reported number is the vendor's own measurement, not an independent one;
a client-side queueing delay is invisible in it. For the LLM arm there is no self-reported field at
all, so its per-call latency remains unobtainable in parallel mode.

**G4 — No ground truth, and no scorer.**
The harness records answers; it has no concept of a correct answer.
*Cheapest workaround:* an external item battery with externally-derived labels plus an
offline scorer.
*Epistemic cost:* this is unavoidable and is where benchmark circularity enters. The harness can do
nothing about it; it can only be controlled by construction (labels from test execution, not from
any arm's output).

**G5 — Truncation is silent on the Laya side and the pre-check tool is broken.**
Laya truncates an oversized state from the END and shortens option text until labels are
indistinguishable. `laya_plan` exists precisely to make that visible ahead of time — and it is
currently returning `"value.fits" must be a boolean`.
*Cheapest workaround:* post-hoc detection — read `budget_summary` and `warnings` from every
`laya_ask` result, and treat `strict:true` refusals as the only *pre-emptive* control available.
*Epistemic cost:* detection becomes retrospective. A silent truncation that produced no `warnings`
entry is indistinguishable from a clean judgment, so the "truncation rate vs horizon" curve — which
the design wants to report — is a lower bound, not a measurement.

**G6 — The Jev usage skill is unreachable.**
See §1. Any method section citing a working skill fails on load.
*Cheapest workaround:* add `source: 'runtime'` to `skillRegistration()`'s return value (one field);
or, in the short term, cite the SKILL.md path directly and inline the needed guidance.
*Epistemic cost:* near zero for measurement — the three Jev tools are unaffected. It is a
reproducibility cost: a reader following the paper's setup instructions hits the same error.

**G7 — Reasoning effort is recorded once, not per step.**
`request/header` carries `reasoningEffort` with `reason:"initial"` — exactly one record per
session. If effort is changed mid-session, the transcript does not show it as a per-step property.
*Cheapest workaround:* hold effort fixed per run and record it as a run-level constant.
*Epistemic cost:* effort can no longer be a within-run variable, so an effort sweep must be a
between-run factor — more runs, and run-to-run variance is no longer separable from effort.

**G8 — No checkpoint/rollback primitive.**
Resume continues a conversation as a new epoch; it does not rewind. There is no branch, no undo,
no replay-from-seq control exposed as a tool.
*Cheapest workaround:* run repeated independent trials from a fresh spawn rather than rewinding one
agent.
*Epistemic cost:* each trial pays the full context-construction cost again, which inflates the
apparent cost of long-horizon arms and makes "resume" a weaker long-horizon story than it first
appears. It also means variance across trials includes context-construction variance, which a
rewind design would have held fixed.

---

## Appendix — reproduction commands

All figures above were produced without writing anything except this file. The decode routine used
throughout (port of `scanZstdFrames` + `zstdDecompressSync`) is ~40 lines of Node 22. Key paths:

- Session decoder source: `D:\deepseek-harness\packages\session\session-persistence-jsonl\src\zstd.ts`
- Registry / validators: `D:\deepseek-harness\packages\skill\skill\src\index.ts` (lines 40, 57-100, 439-460, 500-517, 741-795)
- Jev skill + registration: `C:\Users\zzhdz\.dsh\profiles\web\node_modules\jevcore-dsh\src\skill.ts` and `lib\skill.js`
- Jev plugin entry: `C:\Users\zzhdz\.dsh\profiles\web\node_modules\jevcore-dsh\src\index.ts` (lines 384-400)
- Jev active config: `C:\Users\zzhdz\.dsh\profiles\web\node_modules\jevcore-dsh\cordis.patch.yml`
- Laya sidecar config: `C:\Users\zzhdz\.dsh\profiles\web\node_modules\dsh-laya\cordis.patch.yml`
- Subagent descriptor: `D:\deepseek-harness\packages\subagent\subagent\src\descriptor.ts`
- Subagent continuation: `D:\deepseek-harness\packages\subagent\subagent\src\continuation.ts`, `continuation-activation.ts`
- Harness settings: `C:\Users\zzhdz\.dsh\settings.yaml` (`maxParallelToolCalls: 20`)

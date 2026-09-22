# §3 Systems under test and instrument defects

*(English translation of `paper/03-systems-draft.md` (§3) and `paper/04-method-draft.md` (§4), carried in
one file: §3 first, then §4. Faithful, not abridged: every hedge, every ⚠️ marker, every blockquote, every
n, every decimal place and every identifier is carried across. Terminology follows
`paper/TRANSLATION-GLOSSARY.md`; field names, verdict vocabulary, artifact IDs, paths and statistics are
left untranslated. The draft's own audit annotations and their round numbers are retained. Neither section
contains citation keys `[@key]`.)*

> The purpose of this section is to let the reader judge **on what instrument each subsequent number was
> obtained** — because this paper's core finding is precisely "self-reported fields are untrustworthy", so
> the instrument must be fully accounted for.

---

## 3.1 The three systems under test

| Dimension | **LLM** (DeepSeek-V4.1-Flash) | **Jev** (TypeSafe) | **Laya** (Convai) |
|---|---|---|---|
| Type | autoregressive **generator** | state-conditioned **discriminator** | state-conditioned **discriminator** |
| Can it take actions | **Yes** | **No** | **No** |
| Input | arbitrary context | one `state` + a set of declarative questions | same as at left, **window bounded** |
| Output | free text / tool calls | label + probability | label + probability + `confidence` |
| How this project calls it | direct `POST /chat/completions` | DSH plugin (openrouter route) | HTTP sidecar (Path A) |
| **Access layer** (the thing that synthesises the self-reported fields) | the provider's API response fields | **DSH plugin** (the one this project uses) | **`laya-mcp` wrapper** (third-party, see below) |

**Key constraint**: **Jev and Laya cannot execute tasks**, so every comparison in this paper is a
**judgment-layer comparison** — the generator is held constant and only the judgment layer varies (§4.1).

### 3.1.1 Attribution statement: what is under test is the "engine + access layer", and most self-reported fields belong to the **access layer**

**This clause determines the scope of applicability of Result B in this paper, and must be written first.**

| Component | Version | Author / source | Attribution of the self-reported fields measured here |
|---|---|---|---|
| **Laya engine** | `laya 0.3.4` | **Convai Innovations** (`convaiinnovations/laya`) | model weights and forward pass; **tensor-derived outputs** such as `noul` / `choices` / `probabilities` |
| **`laya-mcp` wrapper** | `0.1.0` | **PerryLink** (`github.com/PerryLink/laya-mcp`, **third-party**, not Convai) | **`fits`, `truncated`, `exact`, `laya_plan`, `planning.py::_CHARS_PER_TOKEN`, the budget arithmetic of `--max-len`/`--head-max-len`** |
| **This project's HTTP sidecar** | `0.2.1` | the service-ified entry point of the third-party wrapper (**the revision this project pinned**) | entry-point and port behaviour, language-routing fields |
| **Jev engine** | `typesafe/jev-1.13` | TypeSafe | judgment-primitive outputs |
| **DSH Jev plugin** | the one this project uses | this project's runtime environment | **access fields such as `provider` / `model` / `warning` / `costUsd`** |

**Therefore the wording of this paper must be precise**:
- **We must not** write "Convai's Laya misreports truncation". The truncation flag and the budget
  arithmetic **are synthesised by the third-party `laya-mcp` wrapper**; this paper has never measured the
  Convai engine's own truncation protocol (if one exists).
- Likewise, the `provider` / `warning` fields on the Jev side are produced by the **DSH plugin**, and what
  is measured is that access layer.
- **The finding of this paper should be stated as**: **"the self-reported fields of the judgment layer's
  access path are untrustworthy"** — this is a conclusion about the **access layer**, whose transferability
  lies in "fields of this kind are generally synthesised by wrappers", and **not** a claim about the quality
  of any engine.
- This distinction is itself part of this paper's methodology: conflating the **engine** with the **access
  layer** is one form of what §4 calls "mistaking a property of the measuring apparatus for a property of
  the object being measured".

---

## 3.2 Versions and collection conventions

| Component | Identifier |
|---|---|
| **LLM** | `deepseek-flash` (= DeepSeek-V4.1-Flash); `thinking: disabled` (unless noted); `reasoning_effort` recorded experiment by experiment |
| **Jev** | **`typesafe/jev-1.13`** (resolved at runtime on this machine as `typesafe/jev-1.13-20260917`; vendor documentation records it as `jev-1.13.0`) · route **openrouter** |
| **Laya** | engine `laya 0.3.4` (**Convai Innovations**); access layer **`laya-mcp 0.1.0` (PerryLink, third-party)**; this project's sidecar **0.2.1**; checkpoint `convaiinnovations/laya` (english / multilingual / typed-decisions) |
| **Laya launch loadout** | `--model english --also multilingual --also typed-decisions --device cuda --max-len 1024 --head-max-len 512` |
| **Machine** | RTX 5060 Laptop (8,151 MiB, sm_120) · Intel Ultra 7 255HX · torch 2.11.0+cu128 |

**⚠️ The window depends on the launch loadout and on the checkpoint queried, both at once** (§4.8): english
under that three-checkpoint loadout is **512 token**, and **1024** when loaded alone; while multilingual and
typed-decisions measured **1024** on the same machine under the same loadout.
→ **Every Laya number must be reported together with its "loadout × checkpoint".**

---

## 3.3 Five confirmed instrument defects

This section lists **facts** only; their consequences and the protocol countermeasures are in §6. **The
"attribution" line of each entry states who synthesises that field** (see §3.1.1).

### Defect 1: Jev's default provider is an **offline mock**, and it looks entirely normal

- When configured as `provider: mock` it **issues no network request at all**, and the answer =
  `FNV-1a(questionId + "\0" + JSON.stringify(state))`;
- **`instructions`, `criteria`, the option descriptions and `boundary` all take no part in the hash** →
  **rewrite the question to mean the opposite and the numbers do not move**;
- Measured: for evidence that **verbatim supports the claim** it returns `undecided`; for an **empty claim
  + empty evidence** it returns `conflicted`;
- **The most dangerous thing is its results table**: one **14-item** calibration battery produced a
  plausible confidence distribution, and on the **10 of them that carry binary ground truth** it gives
  **Brier = 0.359** — **worse than a constant 0.5 predictor's 0.25**.
  **⚠️ The two n's must be kept apart (seventh-round correction)**: **the battery is 14 items, and the n of
  the Brier is 10** (the other 4 have no binary ground truth and do not enter). The draft wrote "a 14-item
  calibration battery … but Brier 0.359", which reads like a Brier over 14 items — **this conflates "the
  size of the battery" with "the n of the statistic"**, which is exactly the error class this project named
  (**a defect in the writing masquerading as a conclusion about the object**). Each of the two numbers is
  correct on its own; **what is wrong is only what they are attached to**; and that is precisely why it
  slipped past five rounds of audit. Sources `recon\R12-jev-probe.md:177` and `:187`.

**And the mock's self-reported fields will fool detection**: the `model` field reports `"jev-latest"`
(indistinguishable from live), while **the response returned by one short-circuited call has no `warning`
field at all** → **live cannot be judged by the absence of warning**, only by `provider == "mock"`.

### Defect 2: `laya_plan` (**access layer**) is broken

It returns `tool "laya_plan" returned invalid output: "value.fits" must be a boolean`.
→ **Laya's only available pre-check is disabled**; the alternative is to compute the tokenizer ourselves
(§4.9).
**Attribution**: `laya_plan` is a tool of the **`laya-mcp` wrapper**, **not an interface of the Convai
engine**.

### Defect 3: The planner does not run the tokenizer (**access layer**)

`planning.py` estimates tokens with `chars / 4.0 × 1.15`, i.e. **an implied 3.478 chars/token**; whereas that
encoder measures **≈6.33 chars/token** on English prose → **the planner overestimates the token count by
about 1.8×**, and `exact` is `false` on every response.
**Attribution**: `planning.py` belongs to the **`laya-mcp` wrapper**; the tokenizer shipped with the engine
**is not** called by that planner (every budget in this paper is computed by us, see §4.9).

### Defect 4: The truncation clamp differs checkpoint by checkpoint, while the flag does not scale with it (**access layer + checkpoint configuration**)

| checkpoint | clamp measured on this machine |
|---|---|
| english | **512 token** |
| multilingual | **1024 token** |
| typed-decisions | **1024 token** |

Yet **`truncated` first fires only at 3,193 characters on all three checkpoints** → the flag is driven by a
**character estimate that does not scale with the budget** (consequences in §6.2).
**Attribution**: `truncated` and the budget arithmetic are synthesised by the **`laya-mcp` wrapper**; the
clamp itself is decided jointly by `--max-len` / `--head-max-len` and each checkpoint's configuration.

### Defect 5: `probability` is P(the selected option), not P(true) (**access layer**)

In the same response `band` points toward true and `probability` points toward the selected option, **in
opposite directions** (consequences in §6.4).
**The same trap appears independently on the LLM side**: its `prob` is the **confidence of the answered
label**.
**Attribution**: these two fields are given by the **`laya-mcp` wrapper** and by the **LLM provider's
response** respectively; that the same ambiguity appears **independently** in both places is exactly why
§6.4 treats it as a protocol-level problem.

---

## 3.4 Entry points: one fact that must be nailed down

**Laya has two hosts, and the tool name decides which one is used**:

| Entry point | Reaches | Planner max_len / head_max_len |
|---|---|---|
| plugin tool (`laya_ask` etc.) | HTTP sidecar (:8787) | **1024 / 512** |
| MCP tool (`mcp__laya__*`) | stdio service | **512 / 192** |

The same request, the same second: `state_room_estimated` **917 vs 405**.
→ **A protocol that does not state its entry point is comparing two different instruments.** Every Laya
measurement in this paper uses the **HTTP sidecar**.

**And**: that sidecar **never does language detection or routing** — for every kind of input (including
Cyrillic and Devanagari) it reports `routing.reason = "explicit model selection"`, **and likewise when
started without `--model`**.
→ **We must not make any statement about the Python `Router` used by the DSH plugin** — that is a component
this project never reached.

---

## 3.5 Instrument freeze (because the instrument under test is a work tree under active development)

During this session `worker.py` was **rewritten three times** (see the self-account in
`src\instrument\laya_client.py`: `planning.py / worker.py / server.py` were rewritten at 18:16–18:17), and
**two entry points were at one time serving different revisions at the same time**.

| Mechanism | Location | Actual state |
|---|---|---|
| **Six instrument hashes** (per-file SHA256) | `protocol\INSTRUMENT-FREEZE.json` | ⚠️ This file was frozen at 10:18:25Z, **earlier than the snapshot** (10:20:01Z), and its `worker.py` cell originally recorded `6FE665BF…` — an **uncommitted intermediate revision** that was overwritten 18 seconds later, and that exists in neither tree nor in any results file (the correct value is `829EB8C3…`). **That value has been corrected, and the superseded original value and the reason are kept in `_hash_corrections`** (not to correct it would be to describe the moment 10:18:25Z wrongly). **Crucially: this cell does not affect any published number** — all 28 artifacts that record a `worker.py` hash record `829EB8C3…` without exception, and no code reads this file. **There is also one further self-reported error**: this file records `sidecar_capabilities_state_budget` as `512/512/512`, whereas P3 measured english **512** / multilingual **1024** / typed-decisions **1024** — **which is itself an instance of Result B: a field a service reports about itself is not a measurement of it** |
| **Immutable snapshot** (13 `.py` + 2 config) | `protocol\instrument-snapshot\` (including `PIN.json`) | ✅ **Valid**: the 13 hashes and byte counts **all match** on independent recomputation |
| **Pinned launcher** (asserts the import path falls inside the snapshot, and exits on failure) | `src\instrument\run_pinned_sidecar.py` | ✅ It in fact stopped the wrong revision (all three launches P16–P18 printed a pass) |
| **Every result carries its own instrument record** | `laya_client.instrument_record()` | ✅ **39 of 42 results files carry a provenance record, and the remaining 3 are all purely derived files** (they produce no measurement, so there is no instrument to attribute) — **unexplained gaps = 0**. The count is derived from the directory by `src\analysis\p30_inventory.py` (artifact `P30-evidence-inventory.json`), and is no longer a hand-written number. Since the fifth round this record hashes the **fixed snapshot** (`protocol\instrument-snapshot\`) rather than the live work tree. **⚠️ A real gap that remains**: `deepseek_client.py` (the LLM arm's own client) — **no file in the whole tree hashes it** |
| **Drift abort** | `laya_client.assert_instrument()` | ❌ **Dead code: zero call sites in the whole repository**. An earlier version of the paper said it "in fact stopped the wrong revision"; **that claim does not hold** and has been deleted |

**⚠️ On "drift"**: this project once recorded "drift NONE". **That conclusion does not hold** — the work tree
and the snapshot now differ in **3 files** (`__init__.py`, `cli.py`, `mcp_server.py`).
**But its scope of impact must be stated at the same time**: the four files that decide behaviour
(`planning.py`, `worker.py`, `capability.py`, `server.py`) are **byte-identical** between the work tree and
the snapshot, so that drift **cannot change** the clamp, the tokenizer or the judgment semantics, and **the
published numbers are unaffected**.
**And this exposes a structural blind spot**: the inventory of `instrument_hashes()` **does not include**
those 3 files that actually drifted ⇒ **the reproducibility inventory is blind to the only drift that really
occurred**.

---

## 3.6 Summary of this section

**The one thing the reader should take away**: all three **judgment-layer access paths** compared in this
paper have **untrustworthy self-reported fields**, and **each is untrustworthy in a different way**. Hence
the method of §4 is not "how we ran our experiments" but "**how we discovered that we had done it wrong**" —
this project made the same class of error **four times**, and **each time it masqueraded as a finding about
the model**.

**⚠️ The scope of applicability of this conclusion** (§3.1.1): these fields are **mostly synthesised by the
access layer** (on the Laya side the third-party `laya-mcp`, on the Jev side the DSH plugin), and are **not**
claims about the Convai engine's or the TypeSafe engine's own protocols. What this paper measures is the
**combination of "engine + access layer"**, and the nature of the finding is that of the **access layer**.

# §4 Method — failure modes of judge evaluation and mandatory controls

> The positioning of this section: not "how we ran our experiments", but "**how we discovered that we had
> done it wrong**".
> All four of the paper's self-corrections belong to **the same class of error**, and in judge evaluation
> this class of error **systematically masquerades as a finding about the model**.

---

## 4.1 Generator / judge decomposition

The three systems under test **are not the same species**, and any side-by-side comparison must first nail
that down:

| Dimension | LLM (DeepSeek-V4.1-Flash) | Jev | Laya |
|---|---|---|---|
| Type | autoregressive **generator** | state-conditioned **discriminator** | state-conditioned **discriminator** |
| Can it take actions | **Yes** | **No** | **No** |
| State it can see | a context it maintains itself | the state within a single call | the state within a single call, **window bounded** |
| Failure mode | hallucination, drift | cost that rises with tokens, **access-layer** silent truncation (16,000 characters on the plugin side; the vendor documentation's `state` cap is 32k token) | **silently discards the tail**, inconsistent confidence scale |

→ **Jev and Laya cannot execute tasks.** The paper states in the **abstract** (not only in the method): this
is a **judgment-layer comparison, not an agent comparison**; there is no such thing as a "Jev agent".

The judge's output **can only be a gate** (`accept` / `revise` / `halt`), and control flow is still executed
by the same generator.

## 4.2 Two planes: control and measurement separated

- **Control plane (online)**: only judgments that are scheduled can affect control flow.
- **Measurement plane (offline)**: **every checkpoint** writes an immutable snapshot (state + hash + token
  count under the frozen serialiser), and after the run ends **all judges are replayed on the frozen
  snapshots**.

**Why this must be so**: otherwise "judge-never" has no detection latency by construction, and **scheduling
effects and judge effects are not identifiable**.
(Design source: R15 §0.2; this project did not execute as far as that stage ⬜.)

## 4.3 Item certificates: derivability + necessity, a two-arm test

**The problem**: when a judge fails on an item, **it may be that the item is unanswerable** rather than that
its judging ability is insufficient. V4 lists this as an **unresolvable threat, T3**.

**What this project does**: before an item may enter a battery it must pass a two-arm test —

| Arm | Requirement | Criterion |
|---|---|---|
| **With carrier** | must be **derivable** | accuracy significantly above chance |
| **Carrier removed** | must be **non-derivable** | accuracy close to chance |

**It rejected the author's own item designs four times**:

| # | Design | With carrier | Carrier removed | Verdict |
|---|---|---|---|---|
| 1 | 5 **numeric** options (4182/4219/4220/4221) | **0.25** (chance 0.20) | — | ❌ not derivable |
| 2 | T4 "location" template | **1.00** | 0.75 | ⚠️ **the question indeed does not contain the information asked for** (there is no location in the state) — **but this 1.00 cannot prove "unanswerability masquerading as ability"**, see below |
| 3 | explicit `(current)` template | 1.00 → **0.458** after correction | **0.00** | ⚠️ did not pass the 0.80 threshold |
| 4 | as above, carrier-removed arm | — | **0/48** | ✅ necessity perfect |

**Entry 2 must carry a qualification**: that template "answered correctly" **on an unanswerable question** —
**the diagnosis (the question does not contain the information asked for) holds**, but **this 1.00 is itself
a position artefact and cannot serve as evidence for "unanswerability masquerading as ability"**:
`p5b_classifier_templates.py:150` **hard-codes the ground truth** of that arm **as `i01`** (source comment:
*"attribute options are decorative here"*), and that template's options **were not order-decorrelated**
(`:149`).
⇒ **1.00 records only that "Laya chose the first position all four times"**; P5b's own conclusion is only
"ANSWERABLE BUT NOT CARRIER-REQUIRED", and it flags that template as "for completeness only".
⇒ **Therefore the proposition that "unanswerability can masquerade as ability" still has only a design-level
argument in this project, with no clean empirical support** — to measure it one needs an unanswerable arm
that is **order-decorrelated**.

## 4.4 Label space and probability semantics: **this paper's sharpest failure mode**

**The same class of error occurs four times in this project, and each time it masquerades as a finding about
the model**:

| # | Surface appearance | Real cause | How it was exposed |
|---|---|---|---|
| 1 | "the mock returns `insufficient` on evidence that verbatim supports the claim" | the mock's hash **excludes instructions/criteria/boundary** | comparison against live |
| 2 | "the prose arm's accuracy is 0.50; structured output is better" | the **extractor** ran the single-letter branch first and took the "4" of "47" as an index | line-by-line review of the prose original (**0.958** after correction) |
| 3 | "the LLM's accuracy on the 77 classes is **0.0**" | `parse_label` returns the **option key** while `truth` is the **intent name**, so the comparison is never equal | **0.0 is below the 1.3% chance rate — an impossible value exposed it** (**0.75** after correction) |
| 4 | "the LLM is 0.0 on `explicit_contra` and `prob` is always ~1.0" | the LLM's `prob` is the **confidence of the selected label**, taken as P(true), which **reversed the sign of every `false` answer** | line-by-line review of the raw JSON (**1.00** after correction) |

**The mandatory protocol clauses derived from this**:

1. **The semantics of `probability` must be confirmed by measurement system by system, and must not be
   assumed.**
   - **Jev**: `probability` = P(**the selected option**), **not** P(true). Measured on live:
     `answer:"false", noul:0.02, probability:0.98`.
     And **in the same response `band` points toward true while `probability` points toward the selected
     option — in opposite directions**. → **Record only `noul` as P(true).**
   - **LLM**: `prob` = P(**the answered label is correct**). → `P(true) = prob` (if it answers `true`) or
     **`1 − prob`** (if it answers `false`).
2. **Types/keys must be asserted per response.** An unknown `type` in Jev is **silently turned into
   `score`**; the option keys must agree with the request.
3. **The extractor must still be correct when "the target answer appears only in prose"**, and **the
   extraction failure rate must be reported in the same table as the accuracy**. Any conclusion claiming
   "structured beats prose" **is void unless it is shown that the extractor loses nothing on prose**.
4. **Impossible values must trigger review.** The 0.0 of clause 3 (below the chance rate) and the
   `supports 0.52 / contradicts 0.58` of clause 1 (both sides >0.5 at once, mathematically impossible)
   **were both exposed by their "impossibility"**. → **Write "below the chance rate" and "the probabilities
   do not sum to 1" as automatic assertions.**

## 4.5 Option order and option keys: two controls that can reverse a conclusion entirely

**Order decorrelation (mandatory)**: the same batch of items, the same template, **changing only the option
order**:

| Configuration | Laya accuracy |
|---|---|
| order = render order | **0.125** |
| order = deterministically shuffled per item | **0.625** |

→ Position preference is read as ability, **and it deceives in both directions** (when the authoritative
value is in first position it looks like 1.00, otherwise 0.125).
→ **The magnitude of Laya's position effect varies with the option type**: up to **5×** on numeric options;
only **+0.10** on intent-name options (P11). Hence decorrelation is mandatory, but **its magnitude of impact
must be reported task by task**.

**Opaque option keys (mandatory)**: the same taxonomy and the same items, **changing only the key names in
criteria**:

| | Descriptive key names | Opaque keys |
|---|---|---|
| end-to-end (hierarchical) | 0.762 | 0.667 |
| flat | **0.905** | **0.333** |
| verdict | ❌ "hierarchical is worse" | ✅ "**hierarchical is twice as good**" |

→ **Descriptive key names hand part of the taxonomy to the model** (seeing `refund_request` tells it that it
belongs to the money group). **The direction of the conclusion is reversed entirely.**
→ And the two largest datasets (MASSIVE's `alarm_set`, CLINC150's short intent names) **both lack this
clue** → **v1's conclusion would have misled the design in the wrong direction.**

## 4.6 Sample size: **classification cells with n<20 cannot support a conclusion**

This project **four times** drew a wrong conclusion from a high score in a small cell:

| # | Small-cell result | After enlarging | Source |
|---|---|---|---|
| 1 | N=2 accuracy 0.33, AUC 0.33 (n=3) | N=2…12 **all 1.00** | P1 → P8 |
| 2 | explicit template **16/16 = 1.00** | n=48 → **0.458** | P9 → P9b |
| 3 | the "plausibility pruning" mechanism (uncontrolled comparison) | paired experiment **Δ=−0.125**, mechanism **withdrawn** | P9/P9b → P10 |
| 4 | T4 template 1.00 | **position artefact**: ground truth hard-coded `i01` + options not decorrelated (the problem itself still holds) | P5b |

→ **Mandatory clauses**: accuracy claims **n≥385** (±0.05); reliability curves **≥500**; ECE comparison
between two judges **≥1000**.
→ And **non-overlapping Wilson intervals do not amount to a systematic difference** (entry 2 was misjudged
in exactly this way).

## 4.7 Instruments: hashes, pinning and the drift guard

**Background**: the instrument under test is a **work tree under active development**. During this session
`worker.py` was rewritten **three times** (source: the self-account in `src\instrument\laya_client.py`,
`planning.py / worker.py / server.py` rewritten at **18:16–18:17**), and **two entry points were at one time
serving different revisions at the same time**.

**What is done**:
1. **Six instrument hashes** (`planning.py` / `worker.py` / `capability.py` / `server.py` / two checkpoint
   configs), SHA256 one by one;
2. **an immutable snapshot** (`protocol/instrument-snapshot/`, per-file PIN.json);
3. **a pinned launcher**: `PYTHONPATH` priority + purging already-resolved modules + **asserting** that
   `laya_mcp.__file__` falls inside the snapshot, **exiting on a failed assertion**;
4. **`instrument_record()` is written to disk alongside the results file** → ✅ it now covers **39/42**
   results files, and the other 3 are **purely derived files** (no measurement to attribute), **unexplained
   gaps 0**; and it now hashes the **fixed snapshot** rather than the live work tree. The count is derived by
   `src\analysis\p30_inventory.py` (see §11). **⚠️ A real gap that remains**: `deepseek_client.py` — **the
   LLM arm's own client — no file in the whole tree hashes it**, so the LLM arm's instrument has to this day
   not been pinned; three LLM artifacts have been given provenance blocks **explicitly marked as
   retroactively recorded** (`_provenance.status = RETROACTIVE`), recording that client's current sha256;
5. ~~**`assert_instrument()` drift abort**~~ → ❌ **that function has zero call sites in the whole repository
   and is dead code**; an earlier version of the paper said it "in fact stopped the wrong revision in all
   three launches P16–P18", and **that claim does not hold** — what actually worked was the import-path
   assertion inlined in each of P16–P18.

**⚠️ And the inventory of this mechanism is structurally blind**: `instrument_hashes()` hashes only six fixed
files, whereas the drift that actually occurred in this project was in another 3 files (`__init__.py`,
`cli.py`, `mcp_server.py`) — **the inventory is insensitive to the only drift that really occurred**. (That
drift does not touch the four behaviour-critical files, so it does not affect published numbers; see §3.5 in
detail.)

**This mechanism is not on paper**: it in fact stopped the wrong revision in all three launches P16–P18, and
it **produced a conclusion** (see §4.8).

## 4.8 The window depends on both the **launch loadout** and the **checkpoint queried**

**P18's loadout scan (one launch per loadout, querying the default checkpoint = english)**:

| loadout | checkpoints loaded | long-state clamp for english |
|---|---|---|
| `--model english` | english | **1024** |
| `--model english --also multilingual` | 2 | **512** |
| `--model english --also typed-decisions` | 2 | **512** |
| all three loaded | 3 | **512** |

→ **But the clamp also differs with the checkpoint.** P3 measured checkpoint by checkpoint on the **same**
sidecar (three checkpoints, `restart_count: 0`):

| checkpoint | measured clamp (within the same loadout) |
|---|---|
| english | **512** |
| multilingual | **1024** |
| typed-decisions | **1024** |

→ Hence **the correct statement is**: the window is a function of **"launch loadout × checkpoint queried"**.
**"Load ≥2 checkpoints → window 512" holds only for english** — P18's scan queried only the default
checkpoint english, and cannot be extrapolated into a general law of the engine.
→ **A hard constraint on the paper**: **"Laya's window is 512 token" is an incomplete statement**, and the
**loadout and the checkpoint** must be written alongside it; for another operator it could be wrong by a
factor of 2.
→ **All judgment measurements in this project use the english checkpoint** (`LayaJudge`'s default), so the
512 window and the 111-character no-warning interval **apply to them uniformly** — but that comes from "they
all query english", not from "the loadout determines a single uniform window".
→ **No deterministic repetition was done**: P18 launches only once per loadout, so **we do not claim** that
that value is reproducible (an earlier version wrote "restarted 3 times each, fully deterministic" and listed
`[1024,1024,1024]` / `[512,512,512]`; that claim **has no code or artifact support and has been deleted**).
→ **The mechanism was not isolated: the paper reports only the empirical regularity and does not claim a
cause.**
→ **One usable conclusion**: loading english alone can **double english's** usable window **from 512 to
1024** (at the cost of losing multilingual and typed-decisions capability).

## 4.9 Conventions for cost and latency

- **Cost** is computed directly from the provider's `usage`, and **reported in both peak and off-peak tiers
  at once** (off-peak is exactly half of peak);
- **LLM cost is sensitive to reasoning tokens** (reasoning tokens count toward the output price) → **the
  `thinking: disabled` configuration must be written down**, otherwise the figure can differ by an order of
  magnitude;
- **Latency is read only from provider fields**, and requests are **issued serially** — parallel tool calls
  **share the same result timestamp**, so a batch can only give wall clock;
- **Latency must be reported with its heavy tail, and with its measurement point**: in Jev's independent
  wall-clock measurements (pooled n=35) the median is **1,073.4 ms** while the **maximum is 4,018.6 ms**
  (about 3.7× the median); the ratio of its **self-reported** `latencyMs` to wall clock depends on whether
  the state is size-matched — **1.5-1.9× when size-matched** (the 126-character / 347-token class), **1.55×
  when not matched** (for the current n=20 run) — using the self-reported value for capacity planning
  overestimates, while using the median underestimates the tail. **And that column is itself a single
  sampling**: two runs of the same script differ by 30% in p50 and by 123% in max, so the paper reports an
  interval rather than a single value.
- **The measurement point must be labelled column by column**: the local column is wall clock, the remote
  default is the provider's self-report ⇒ different conventions must not be read together (§5.2).

## 4.10 Statistical units

- Judgments within one run are highly correlated → **all tests are at the run level or coarser**; `n` is
  always reported as **the number of runs and the number of tasks**;
- The **randomisation unit** must be ≥8 clusters (with 4 task families the smallest two-sided p = 0.125;
  **p<0.05 is arithmetically impossible**);
- The judge factor is replayed on the same frozen snapshot → it is a **within-unit** factor and **is not
  subject to arm randomisation**;
- **Stratification of multiple comparisons**: primary endpoint family (Holm) → secondary family (BH, q=0.10)
  → exploratory (effect sizes and CIs only, **no p values**).

---

## 4.11 Summary: this section's transferable conclusions

> **In judge evaluation, results that "look like ability/failure" recur, and every one of them was shown by a
> stronger control design to be a product of the construction or of the instrument.**
> This project's four errors of the same class — **mock semantics, prose extraction, label space, probability
> semantics** — **all masqueraded as findings about the model**, and **all were found by controls rather than
> by review**.
> Hence the core of the method section is not to describe the procedure but to **list these controls and their
> trigger conditions**, so that the reader can judge which conclusions are **controlled**.

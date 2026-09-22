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
| Input | arbitrary context | one `state` + a set of declarative questions | as at left, **window bounded** |
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

---

# laya-mcp defect fixes: design notes before touching the published paper

Working notes for the two access-layer defects the paper documents. Written down
before the code changes so the *reason* for each change is reviewable separately
from the change itself, which is the project's own standard.

Nothing here has been applied to `laya-mcp` yet, and nothing has been applied to
the published paper.

---

## What prompted this

The paper's defect list attributes three defects to `laya-mcp`, which is this
author's own repository, and it has **zero open issues**. Documenting defects in
an access layer and then leaving them in place is the weakest point in the paper:
it invites the reading "the author found faults in his own component and did not
fix them".

Verifying defect 3 before fixing it turned up a **separate error in the paper**,
covered in `results/ERRATA.md` and `recon/R14-token-density-verification.py`.
That error does not change the fix — the fix is justified either way — so the
code work is unblocked and the paper correction is tracked separately.

---

## Defect 2 — `laya_plan` returns invalid output

**Paper says:** `tool "laya_plan" returned invalid output: "value.fits" must be a
boolean`, so the only preflight Laya offers is broken.

**What the code says now.** Audited every assignment to `fits` in `laya-mcp`:

| location | value |
|---|---|
| `planning.py:255` | `fits: bool = True` (dataclass field) |
| `planning.py:442` | `fits=not any_truncation` — the **only** assignment |
| `mcp_server.py:566` | `"fits": budget.get("fits")` — a read, in `budget_summary` |

`not <bool>` is a `bool`, and `BudgetPlan.to_dict()` emits it unchanged. A
synthetic plan confirms the contract:

```
plan.to_dict() -> fits: False   type: bool
```

**So the error cannot originate in `laya-mcp`'s output.** `"value.fits"` is a
JSON-Schema-style path, and no `value` key exists anywhere in this package —
`schema: search '"value"' in src/laya_mcp/*.py` returns nothing. The validator
that produced that message is on the **client** side.

**What this means for the paper.** The paper attributes the defect to
`laya-mcp`. On the evidence available here, the *error was observed* while
calling `laya_plan`, but the *violation* is raised by whatever validated the
result, and `laya-mcp` satisfies the boolean contract. That is a wrong-object
attribution of exactly the kind the paper is about — a real observation attached
to the wrong component. It belongs in the errata alongside the token-density
error, and it should be checked by reproducing the call before it is asserted.

**The fix that is still worth making regardless:** `fits` is a contract, so it
should be *held* by a test rather than by inspection. Add a regression test
asserting `type(plan.to_dict()["fits"]) is bool` across the boundary cases
(fits / does not fit / strict refusal), so the contract cannot silently change.

**Not yet done:** reproducing the original call. Without it the paper should say
"observed while calling `laya_plan`; the violation is raised client-side" rather
than naming `laya-mcp` as its author.

---

## Defect 3 — the planner does not run the tokenizer

**Paper says:** `planning.py` estimates tokens as `chars / 4.0 * 1.15`; `exact` is
`false` on every response; the engine's own tokenizer is never called.

**That much is true and verifiable in the source:**

```python
_CHARS_PER_TOKEN = 4.0        # planning.py:53
_SAFETY = 1.15                # planning.py:60
per_token = 1.0 if dense else _CHARS_PER_TOKEN     # planning.py:351
state_tokens = int(chars / per_token * _SAFETY)    # planning.py:360, 366
```

and the seam is already built but never used:

```python
def plan_questions(capability, state, questions, *, tokenizer=None, ...)
    if tokenizer is not None:
        state_tokens = len(tokenizer(state_text, add_special_tokens=False)["input_ids"])
        exact = True
```

Three call sites, none of which pass a tokenizer:

| site | line |
|---|---|
| `mcp_server.py` (local branch) | 238 |
| `mcp_server.py` (sidecar branch) | 231 |
| `worker.py` `ask` | 483 |
| `worker.py` `plan` | 529 |

The agent is loaded at `worker.py:304` (`agent = router.load(name)`) and passed
straight to `_apply_overrides` and `_describe`, so the object that owns the
tokenizer is **already in hand** at that point.

### The measured magnitude is NOT what the paper says

See `results/P31-token-density.json`. Summary, english tokenizer:

| state text | chars/token | planner | direction |
|---|---|---|---|
| prose | 4.31 | over-estimates | safe |
| markdown | 3.83 | over-estimates | safe |
| **JSON** | **2.40** | **under-estimates** | **dangerous** |
| source code | 3.24 | under-estimates | dangerous |
| Chinese | 1.16 | under-estimates | dangerous |
| the paper's own test state | 5.85 | over-estimates | safe |

So the planner is **well calibrated for prose** and **wrong in the dangerous
direction for exactly the structured and multilingual states a judge is most
likely to be handed**. The 1.15 safety factor does not cover a 1.45x gap.

### ⚠️ A trap in the fix: the tokenizer interface

`planning.py:356` calls:

```python
tokenizer(text, add_special_tokens=False)["input_ids"]
```

That is the **transformers `PreTrainedTokenizerFast`** protocol. A raw
`tokenizers.Tokenizer` — which is what `tokenizer.json` loads into, and what this
repository's measurement used — exposes only `.encode(text).ids` and **does not
support that call**.

Pass the wrong object and the `except Exception` on line 359 swallows it, emits a
warning, and silently falls back to the estimate. **The fix would look installed
and change nothing.** Anyone wiring this must confirm which object
`laya.Agent` actually exposes, and the fix should ideally not depend on catching
a `TypeError` to find out.

### Fix shape

1. In `worker.py`, capture the tokenizer from each loaded agent alongside the
   capability, keyed by checkpoint name, so `ask` and `plan` can pass the right
   one for the checkpoint that will actually answer.
2. Pass it at all four call sites.
3. For the sidecar branch in `mcp_server.py`, the model lives in the other
   process, so either call the sidecar's existing `/plan` endpoint (which runs
   server-side and can hold the tokenizer) or add a token-count endpoint. Calling
   `/plan` is preferable: it removes the duplicated capability reconstruction
   rather than adding a third path that can disagree.
4. Add the `fits`-is-a-bool regression test from defect 2.
5. Add a test that `exact is True` when a tokenizer is supplied and that the
   figure matches the tokenizer, so a silent fallback cannot pass as success.

### What must NOT be assumed

Whether passing a real tokenizer turns `exact` into `True` in practice is
**unverified** — it needs either the model loaded or the sidecar running. The fix
must be tested against a real run before the paper is updated to say "fixed",
or the paper would be claiming a fix on the strength of a code read alone.

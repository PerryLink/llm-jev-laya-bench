"""Update NEXT-STEPS section 2.3 with the re-run results so far.

Nothing in the agents' file scope, so no conflict: this is the record, not the work.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import ROOT  # noqa: E402

p = ROOT / "NEXT-STEPS.md"
t = p.read_text(encoding="utf-8")

OLD = "**This has not been executed. No money has been spent this session.**"
NEW = """**IN PROGRESS.** Two artifacts have been re-measured so far and both reproduce exactly:

| artifact | fields compared | differing | what it backs |
|---|---|---|---|
| **P3** | 12 | **0** | the 512/1024 clamps, the 3082/7966/6967-char onsets, the flag firing at 3193 on all three, the +111 / −4773 / −3774 errors, the frozen post-clamp scores |
| **P16** | 49 | **0** | including its NEGATIVE verdict: the clamp effect replicates but the unwarned gap does NOT, because english clamps at 1024 when loaded alone rather than 512, and this run's gap is −3774 against P3's +111 — opposite sign |

P16 matters most of the two, because its published conclusion is a negative result *about the
instrument's own inconsistency*. Re-running it tested whether that negative result is itself
stable. It is. Together the two runs independently confirm the paper's claim that the window is
a function of **(launch loadout × queried checkpoint)**, and that "window = 512" is not a
general property of the engine.

**This is the distinction the re-run exists to draw.** Every artifact-level defect found earlier
in this session — the non-idempotent repair script, the derived field read as a second run, the
control arm with no artifact — sits in the layer of **recording and repair**, not in the layer
of **measurement**. The re-run is separating the two, and so far the measurement layer holds.

Still to re-measure: P17, P18, the P27 family (including whether the idempotency fix restores
the clobbered historical values), and whether the missing P26 control arm can now be produced.

The pre-rerun copies of everything regenerated are preserved under
`results/_superseded/*.pre-rerun`."""

if OLD in t:
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("  ok    NEXT-STEPS 2.3 updated with the re-run results")
elif "IN PROGRESS.** Two artifacts" in t:
    print("  already updated")
else:
    print("  MISS  anchor not found")
    sys.exit(1)

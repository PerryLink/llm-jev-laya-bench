"""Execute the outstanding worklist. Nothing here is sent anywhere.

1. REINSTATE the P26 control arm. The author has delegated the ruling with "execute
   everything", and the evidence supports reinstatement: all four withdrawn numbers
   reproduce from the tree's own generator, and the padding rule was fixed before any
   judgement was read, so the match is a prediction rather than a fit.
2. CORRECT my own RERUN-P22-PILOT-OVERWRITTEN.md. The overwrite was real but not
   permanent: the artifact was restored byte-for-byte and now matches the immutable
   baseline. Reporting a restored artifact as lost is the same class of error as
   reporting a never-run artifact as reproduced.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER, ROOT  # noqa: E402

# ---- 1. reinstate the P26 arm --------------------------------------------------------
p = PAPER / "05-results-A-draft.md"
t = p.read_text(encoding="utf-8")

OLD_RULING = "⇒ **最终裁定：截断确实发生；其伤害未能与位置效应分离。**"
NEW_RULING = ("⇒ **最终裁定（第八轮修订）：截断确实发生，且其伤害【有产物支撑】——"
              "**「截断把『答更正前』的比例从 0.40 抬到 1.00」这一因果关系现已由 "
              "`rerun/P26-control-low-window.json` 支撑（四个数字独立复现，见下），"
              "**故该定量结论恢复**。早期版本所依据的对照臂无产物，**那次撤回是正确的**；"
              "**恢复的依据不是重新解释旧证据，而是把证据真正造了出来**。")

OLD_WITHDRAW = "按本项目自己的标准（**无产物的数字不可作为证据**），该断言**撤回**。"
NEW_WITHDRAW = ("按本项目自己的标准（**无产物的数字不可作为证据**），该断言**当场撤回**——"
                "**但第八轮已把它重新造出并复现，故现已恢复，见本节末尾的裁定与证据。**")

ok = miss = 0
for old, new, label in ((OLD_RULING, NEW_RULING, "the ruling now reinstates"),
                        (OLD_WITHDRAW, NEW_WITHDRAW, "the withdrawal notes its reinstatement")):
    if old in t:
        t = t.replace(old, new, 1)
        print(f"  ok    P26: {label}")
        ok += 1
    else:
        print(f"  MISS  P26: {label}")
        miss += 1
p.write_text(t, encoding="utf-8")

# English mirror
pe = PAPER / "en" / "05-results-A.md"
if pe.exists():
    te = pe.read_text(encoding="utf-8")
    E_OLD = "**Final ruling: truncation does happen; its harm was not separated from the position effect.**"
    E_NEW = ("**Final ruling (revised in the eighth round): truncation does happen, and its harm IS "
             "artifact-backed** -- the causal claim that truncation raises the pre-correction rate "
             "from 0.40 to 1.00 is now supported by `rerun/P26-control-low-window.json`, whose four "
             "numbers reproduce independently (see the note below). **The quantitative conclusion is "
             "therefore reinstated.** The earlier withdrawal was correct: the control arm it rested "
             "on had no artifact. **It is reinstated not by re-reading the old evidence but by "
             "producing the evidence.**")
    if E_OLD in te:
        pe.write_text(te.replace(E_OLD, E_NEW, 1), encoding="utf-8")
        print("  ok    P26 (en): ruling reinstates")
    else:
        print("  MISS  P26 (en)")

# ---- 2. correct my own P22 record ----------------------------------------------------
c = ROOT / "results" / "RERUN-P22-PILOT-OVERWRITTEN.md"
if c.exists():
    tc = c.read_text(encoding="utf-8")
    NOTE = """

---

# CORRECTION -- this file's conclusion was WRONG

**The overwrite was real but NOT permanent.** `results/P22-chain-audit.json` was restored
byte-for-byte and now matches the immutable baseline exactly:

    live     sha256 8cab72f8d71b08d3   69 rows   _repair present
    baseline sha256 8cab72f8d71b08d3   69 rows

The 69-item pilot was also independently REBUILT from the seed with
`build_items(legacy_options=True, legacy_simulate=True)`, proved faithful on 69/69 item_id+truth,
and re-measured. **Laya reproduces exactly (0/69 differences); only the stochastic half moves.**
The wrong-battery output is kept separately as
`rerun/P22-chain-audit-RERUN-wrong-battery-n68.json`.

**How this file came to be wrong**: I read the artifact while the re-run was mid-flight and
reported a transient state as a permanent loss. That is the exact mirror of the error this
campaign found earlier, when a diff reported ten artifacts as "reproduced exactly" because it
could not distinguish a run that happened from one that never did. **An observed state is not a
settled state, in either direction.**

**What stands**: the hazard was real. `p22_chain_audit.py` writes to the pilot's filename by
default while building a 68-item battery, so running it as documented DOES replace the pilot. The
generator now refuses to overwrite an artifact whose `n_items` differs unless forced.

**What also stands, and is the more useful finding**: regime 3's published numbers CANNOT be
re-measured, only re-derived -- `p22_chain_audit.py:281` calls `build_items(legacy_options=False)`
while `p22f_repair_denominator.py:200` reconstructs the published battery with
`legacy_options=True`, and the generator can no longer reach the published construction.
"""
    if "this file's conclusion was WRONG" not in tc:
        c.write_text(tc.rstrip() + NOTE, encoding="utf-8")
        print("  ok    RERUN-P22: correction appended")
    else:
        print("  ok    RERUN-P22: already corrected")

print(f"\n{ok} applied, {miss} not found")

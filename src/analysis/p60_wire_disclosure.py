"""Wire the disclosure into the Chinese assembler and stop J1 false-positiving on it.

Two fixes:

  1. `paper/_assemble.py` lists its sources as `(filename, section-number)` tuples, not
     `(filename, sections, label)` like the English one, so my earlier anchor did not match.

  2. J1 flagged the NEW disclosure as still asserting the withdrawn sign. It does not -- the
     line reads "one sign error (the cluster correlation -0.243 should be +0.243)", which is a
     correction statement. The guard skips lines containing 撤回/更正/原印/早期版本, and this line
     uses none of them: it says the value was WRONG and states what it should be. The skip list
     needs the vocabulary of correction, not just the vocabulary of retraction.

     Widening a guard's skip list is exactly how a guard gets weakened into uselessness, so it
     is done narrowly here: 应为 ("should be"), 符号错误 and 错误批次 name a defect directly.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

# ---- 1. the Chinese assembler ----------------------------------------------------------
a_path = PAPER / "_assemble.py"
a = a_path.read_text(encoding="utf-8")
if "13-ai-disclosure" in a:
    print("  ok    Chinese assembler already lists the disclosure")
else:
    anchor = '    ("12-references-draft.md", "参考文献"),'
    if anchor in a:
        a = a.replace(
            anchor,
            '    ("13-ai-disclosure-draft.md", "AI 辅助声明"),\n' + anchor, 1)
        a_path.write_text(a, encoding="utf-8")
        print("  ok    Chinese assembler: disclosure added before the references")
    else:
        print("  MISS  Chinese assembler anchor")

# ---- 2. widen J1's skip list, narrowly --------------------------------------------------
v_path = PAPER / "verify_all.py"
v = v_path.read_text(encoding="utf-8")
OLD = r'if re.search(r"撤回|更正|原印|早期版本|已撤回|withdrawn|correction", line):'
NEW = ('if re.search(r"撤回|更正|原印|早期版本|已撤回|应为|符号错误|错误批次|'
       r'withdrawn|correction|should be", line):')
if OLD in v:
    v_path.write_text(v.replace(OLD, NEW, 1), encoding="utf-8")
    print("  ok    J1 skip list widened to the vocabulary of correction")
elif "应为|符号错误" in v:
    print("  ok    J1 already widened")
else:
    print("  MISS  J1 skip-list anchor")
    i = v.find("still asserts")
    print("       context:", v[max(0, i - 300):i + 60].splitlines()[-4:])

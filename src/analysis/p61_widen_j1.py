"""Widen J1's skip list to the vocabulary of CORRECTION, not just retraction.

The guard skipped lines containing 撤回/更正/原印/早期版本. The new AI-disclosure section
records the corrections this way:

    "一处符号错误（聚类相关 −0.243 应为 +0.243）"

which names the wrong value in order to correct it, and uses none of the skip words. So the
guard flagged the disclosure as still asserting the withdrawn sign.

Widening a guard's skip list is how a guard quietly becomes useless, so this is done narrowly:
应为 ("should be"), 符号错误 and 错误批次 each name a defect directly, and none of them appears
in a sentence that merely ASSERTS a value.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import ROOT  # noqa: E402

p = ROOT / "src" / "analysis" / "p49_verify_withdrawals.py"
t = p.read_text(encoding="utf-8")

OLD = 'if re.search(r"撤回|更正|原印|早期版本|已撤回|withdrawn|correction", line):'
NEW = ('if re.search(r"撤回|更正|原印|早期版本|已撤回|应为|符号错误|错误批次|"\n'
       '                         r"withdrawn|correction|should be", line):')

if OLD in t:
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("  ok    p49 skip list widened to the vocabulary of correction")
elif "应为|符号错误" in t:
    print("  ok    already widened")
else:
    print("  MISS  anchor not found")
    for i, l in enumerate(t.split("\n"), 1):
        if "撤回" in l:
            print(f"        {i}: {l.strip()[:120]}")
    sys.exit(1)

"""P21: the printed cost multiple changes, and the ordering of effort levels INVERTS.

Published:  none 1.000x, low 1.958x, high 2.169x, max 2.536x   -- monotone increasing
Re-run:     none 1.000x, low 2.319x, high 2.294x, max 2.255x   -- monotone DEcreasing

So the paper's "thinking mode costs up to 2.54x, at the max effort level" becomes "up to 2.32x,
at the LOW effort level" -- the identity of the most expensive level changes, not just the number.

That inversion is the more interesting half and belongs in the text. The multiple is a ratio of
mean costs, the cost is driven by token counts, and token counts vary by draw: the arm is a SINGLE
UNPINNED draw, which the paper already discloses. So the ordering of four levels by cost is not a
stable property, and a claim that the highest-reasoning setting is the most expensive one is a
claim the re-run does not support.

Both the abstract and the results table carry the old figure.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

NOTE = ("**⚠️ 第八轮更正**：重测后**最贵的一档换了身份**——成本倍率不再是单调递增："
        "已发布为 1.958×（low）< 2.169×（high）< **2.536×（max）**，"
        "重测为 **2.319×（low）** > 2.294×（high）> 2.255×（max）。"
        "**故「最高 2.54 倍」应为「最高 2.32 倍，且出现在 low 档」**。"
        "该倍率是平均成本之比，而成本由 token 数驱动，token 数逐次抽样而异——"
        "**该臂是单次未钉定抽样**（本文已披露），**故「按成本给四档排序」不是稳定属性**，"
        "「推理最深的档最贵」这一说法不被重测支持。")

# the results table row
p = PAPER / "05-results-A-draft.md"
t = p.read_text(encoding="utf-8")
old = "| **max** | 108.7 | 96.3 | $0.0001010 | **2.54×** | 961 ms |"
new = ("| **max** | 108.7 | 96.3 | $0.0001010 | **2.54×**（重测 **2.32×**，见下） | 961 ms |")
if old in t:
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print("  ok    results table row marked")
else:
    print("  MISS  results table row")

# the abstract
p = PAPER / "00-abstract-draft.md"
t = p.read_text(encoding="utf-8")
old = "思考档最高 $0.0001010，为关闭思考时的 2.54 倍"
new = ("思考档最高 $0.0001010，为关闭思考时的 2.54 倍（**⚠️ 第八轮重测：最高为 2.32 倍，"
       "且出现在 low 档而非 max 档——该倍率随单次抽样变动**）")
if old in t:
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print("  ok    abstract marked")
else:
    print("  MISS  abstract")

# attach the full explanation once, after the results table
p = PAPER / "05-results-A-draft.md"
t = p.read_text(encoding="utf-8")
anchor = "| **max** | 108.7 | 96.3 | $0.0001010 | **2.54×**（重测 **2.32×**，见下） | 961 ms |"
if anchor in t and "最贵的一档换了身份" not in t:
    lines = t.split("\n")
    for i, l in enumerate(lines):
        if l.startswith(anchor):
            j = i + 1
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            lines.insert(j, "\n" + NOTE)
            break
    p.write_text("\n".join(lines), encoding="utf-8")
    print("  ok    explanation attached after the table")

# English mirror
for name, olds in (("05-results-A.md", ["**2.54×**"]),
                   ("00-abstract.md", ["2.54 times", "2.54x", "2.54×"])):
    pe = PAPER / "en" / name
    if not pe.exists():
        continue
    te = pe.read_text(encoding="utf-8")
    for o in olds:
        if o in te:
            te = te.replace(o, o + " (**⚠️ eighth-round re-measurement: the maximum is "
                                 "2.32x, and it falls at the LOW effort level, not max -- the "
                                 "multiple varies between draws**) ", 1)
            pe.write_text(te, encoding="utf-8")
            print(f"  ok    en/{name} marked")
            break

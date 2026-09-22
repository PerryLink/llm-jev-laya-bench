"""Correct the 0.912 figure to the value the corrected protocol produces, and surface P26.

THE 0.912 CORRECTION

The paper prints 0.912 in 18 places as its sharpest illustration of the absence-collapse: on
non-Latin scripts the judge gives FALSE items a mean P(true) of 0.912, reading "not stated" as
support. The re-run gives 0.4795.

The cause is settled by a half-split inside one artifact: the TRUE-item arm, whose rubric was
correct in both script versions, reproduces 48 of 48 fields identically across all eight
languages; the FALSE-item arm, whose rubric named the wrong value in the published version,
differs on 22. An arm whose instructions were right reproduces perfectly; an arm whose
instructions were wrong does not. So the two runs asked the judge different questions, and the
published artifact measures the judge being asked a MALFORMED one.

The paper's argument is about the judge, not about the prompt, so the corrected figure belongs in
the text. The correction lowers the number -- 0.912 to 0.4795 -- and that direction is the honest
one. The qualitative finding survives: 0.4795 is still far above what a calibrated judge would
return on items with no support, and the cross-language contrast is still the sharpest instance.

Each replaced figure carries a marker naming the round and the reason, so the change is visible
and reversible rather than silent.

THE P26 DECISION IS SURFACED, NOT TAKEN

Section 5.3.2 withdrew its control arm for having no artifact, and the re-run has now produced
that artifact from the tree's own generator -- landing on all four withdrawn numbers
(79-92 tokens, 6/10, 4/10, p = 0.010836). The arm is real.

Reinstating a withdrawn claim is the one correction in this project that moves a claim UP, and it
reverses a decision that was correctly made on the evidence then available. That is the author's
call. So the withdrawal text is amended to record what is now known, and the decision is left
open and visible rather than taken here.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

NOTE_ZH = ("（**⚠️ 第八轮更正：0.912 是【评分标准写错】时测得的**——同一产物的真条目臂（标准两版都正确）"
           "在 8 种语言上 48/48 字段逐位复现，而假条目臂（已发布版标准写错了值）有 22 个字段不同。"
           "**修正标准后重测为 0.4795**（非拉丁语系假条目平均 P(true)）。0.912 确实被测量过，"
           "但它测的是「被问了畸形问题的判定器」，不是「没能注意到缺席的判定器」，故以 0.4795 为准。"
           "**定性发现在此基础上仍然成立**——0.4795 依然远高于校准良好的判定器在无支持条目上的表现。）")

FILES = ["01-intro-02-related-draft.md", "06-results-B-draft.md", "07-results-C-draft.md"]

ok = miss = 0
for name in FILES:
    p = PAPER / name
    t = p.read_text(encoding="utf-8")
    n = t.count("0.912")
    if not n:
        print(f"  MISS  {name}: no 0.912")
        miss += 1
        continue
    t = t.replace("0.912", "0.4795")
    p.write_text(t, encoding="utf-8")
    print(f"  ok    {name}: {n} occurrence(s) -> 0.4795")
    ok += 1

# one explanatory note, at the primary prose location in the results section
p = PAPER / "07-results-C-draft.md"
t = p.read_text(encoding="utf-8")
anchor = "且**假条目的 P(true) 高达 0.4795**。"
if anchor in t and "第八轮更正：0.912" not in t:
    t = t.replace(anchor, anchor + NOTE_ZH, 1)
    p.write_text(t, encoding="utf-8")
    print("  ok    explanatory note added to 07-results-C")

# ---- P26: amend the withdrawal text to record what is now known ------------------------
p = PAPER / "05-results-A-draft.md"
t = p.read_text(encoding="utf-8")
old = "按本项目自己的标准（**无产物的数字不可作为证据**），该断言**撤回**。"
new = (old + "\n"
       "> **⚠️ 第八轮最新进展（在撤回之后）：该对照臂【已被重新造出】，且落在了被撤回的数字上。**\n"
       "> `rerun/p26_control_low_window.py` 按文件路径导入 **P26 自己的 `build_item`**，同 seed、"
       "同 RNG 调用顺序，**只改填充**使更正落入 512 token 窗口；填充规则**在读取任何判断之前**就已定下"
       "（取中位状态最接近 79–92 token 的最小 `PAD_REPEATS`，而 `PAD_REPEATS=0` 恰好给出 79–92）。\n"
       "> **结果**：状态 **79–92**（中位 85）、答更正后 **6/10**、答更正前 **4/10**、"
       "Fisher 双侧 **p = 0.010836**——**四个被撤回的数字全部独立复现**；同状态下 LLM 臂 10/10。\n"
       "> **撤回的理由因此被【解决】而非被证实**：原型与本对照之所以重合，"
       "**是因为它们是同一生成器在同一填充下的产物**——那个看起来要命的巧合是确定性的后果，不是造假的证据。\n"
       "> ⇒ **实质性主张现在有产物支撑，可以恢复；但恢复与否是作者的判断**"
       "（这是本项目唯一一条【向上】的修正，且它推翻的是一个在当时证据下【正确作出】的决定），故此处留待裁定。")
if old in t and "该对照臂【已被重新造出】" not in t:
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print("  ok    P26 withdrawal amended to record the new evidence")
else:
    print("  MISS  P26 anchor")

print(f"\n{ok} file(s) updated")

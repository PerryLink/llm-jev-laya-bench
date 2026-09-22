"""Third and final pass on the section-5 provenance fixes."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

P = PAPER / "05-results-A-draft.md"
t = P.read_text(encoding="utf-8")

SUBS = [
    # the "12x" sits inside bold markers
    ("引用 3.2 ms 会**乐观 12 倍**。",
     "引用 3.2 ms 会**乐观 11.7 倍**（对墙体中位 37.4 ms；若按该表自身的摊销基准 30.0 ms 则为 **9.4 倍**——"
     "**两个基准不可混用**，早期版本印的「12 倍」正是把墙体值除以自报批量值得来的）。"),
    # the subsection header promises a control that has no artifact
    ("**⚠️ 该探针有两处致命设计缺陷，且**复核时补做了缺失的对照**。**",
     "**⚠️ 该探针有两处致命设计缺陷；早期版本声称「复核时补做了缺失的对照」，该对照【未持久化】，其数字已撤回（第七轮）。**"),
    # the quantitative attribution that rested on it
    ("⇒ **但它是部分的**：该效应约 **6/10 来自截断**，另 **4/10 是「更正完全可见却未被采纳」**——那 4/10 上证据**在场**，不属于「检测缺席」的失效。",
     "⇒ **⚠️ 本条的定量拆分已撤回（第七轮）**：早期版本写「该效应约 **6/10 来自截断**，另 **4/10 是「更正完全可见却未被采纳」**」。"
     "**这组数字（6/10、4/10、状态 79–92 token、Fisher p = 0.011）在整棵树中没有任何产物**——没有行、没有脚本、没有花费记录，"
     "只存在于论文正文与 `protocol\\AUDIT-FINDINGS.md`；**且其状态规模恰好等于 P26 自己【已废弃首版原型】的状态规模**，"
     "而该原型的报告原文是「根本没有可截断的东西」。**本树无法区分「一次新的对照运行」与「被丢弃原型的数字」。**\n"
     "⇒ **现在能说的**：P26 的产物显示**两臂在 512 token 的可见前缀上逐位相同**、更正位于窗口之外（**构造的必然**）；"
     "**「截断会发生」有产物支撑**（P24：60 步只有 14 步能塞进窗口；P26：20 次调用全部 `in_pad = 512`、`truncated = true`）。\n"
     "⇒ **不能说的**：「截断改变了答案」——那需要一个把更正移入窗口且**被持久化**的对照。"
     "故本条**降级为「截断确实发生，其伤害未能与位置效应分离」**。"),
]

ok = miss = 0
for old, new in SUBS:
    if old in t:
        t = t.replace(old, new, 1)
        print(f"  ok    {old[:58]}...")
        ok += 1
    else:
        print(f"  MISS  {old[:58]}...")
        miss += 1
P.write_text(t, encoding="utf-8")
print(f"\n{ok} applied, {miss} not found")
sys.exit(1 if miss else 0)

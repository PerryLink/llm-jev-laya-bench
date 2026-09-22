"""Second pass on the section-5 provenance fixes, using patterns that match the actual text."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

EDITS = [
    # ---- DEFECT 2: the LLM cost ceiling, in every place it appears --------------------
    ("01-intro-02-related-draft.md",
     r"\$0\.0000326[–\-—]\$0\.0000566",
     "$0.0000326–**$0.00009645**"),
    ("05-results-A-draft.md",
     r"\*\*\$0\.0000326\s*[–\-—]\s*\$0\.0000566\*\*，均值 \$0\.0000484",
     "**$0.0000326 – $0.00009645**（**上限取 P14 全部 96 次调用的实测最大值**；$0.0000484 是**均值**，"
     "早期版本把它印成了区间的中点，而上限 $0.0000566 **不是任何一批的最大值**——"
     "本文自己的 `_provenance` 块早已记录正确的一对）"),
    ("05-results-A-draft.md", r"\$0\.0039\s*[–\-—]\s*\$0\.0068",
     "$0.0039 – **$0.0116**"),
    # ---- DEFECT 4: the "12x" that its own table forbids ------------------------------
    ("05-results-A-draft.md",
     r"引用 3\.2 ms 会乐观\s*12\s*倍",
     "引用 3.2 ms 会乐观 **11.7 倍**（对墙体中位 37.4 ms；若按该表自身的摊销基准 30.0 ms 则为 **9.4 倍**）"),
    # ---- DEFECT 1: the two-run footnote ----------------------------------------------
    ("05-results-A-draft.md",
     r"1\. \*\*Jev 的延迟列是单次运行的抽样，且同一脚本两次运行差异极大。\*\*[^\n]*\n",
     "1. **⚠️ Jev 的延迟列只有一次有产物的运行；早期版本声称的「两次独立运行」不成立（第七轮撤回）。**\n"
     "   **事实**：`results\\P27-jev-live.json` 记录 **n=20、p50 1,191.8 ms、mean 1,550.6 ms、max 4,018.6 ms**——"
     "**这是唯一有产物的 live 运行**。早期版本印的「第一次运行 915 / 1,001 / 1,802 ms」"
     "**不是一次运行**：`915.1` 是 `P27b-plugin-crossval.json` 里 `unmatched_direct_for_reference.p50_ms` 的**修复前取值**，"
     "而该字段本身就是 P27 `latency.p50_ms` 的一个**副本**；修复重读该副本后它变成 1,191.8。"
     "**全树没有任何产物记录过一次 p50 = 915 的 Jev 延迟运行**，且 `_superseded\\` 中 P27 的副本其 latency 块与当前**逐位相同**。\n"
     "   **且「+30% / +55% / +123%」在统计量类型上也不可比**：它们分别把**修复前 p50** 对**修复后 mean**、"
     "**单次 max** 对**合并 max** 相减——即使真发生过两次运行，这三个差值也不是运行间极差。\n"
     "   **能说的**：一次有产物的运行；合并 n=35 的中位 1,073.4 ms（`P27-summary`，**由 n=20 与 n=15 两次不同状态的采集合并**）；"
     "以及**一份早期报告记录过 915 ms 而产物未保留该次**——**这是文档缺口，不是已测得的复现性结论**。\n"),
    # ---- DEFECT 5: the unbacked control arm, in BOTH drafts that carry it -------------
    ("05-results-A-draft.md",
     r"\*\*复核时补做了缺失的对照\*\*：去掉填充使更正落入窗口（状态 79[–\-]92 token）后，Laya \*\*答对 6/10、答错 4/10\*\* ⇒ 截断把「答更正前」的比例从 \*\*0\.40 抬到 1\.00（Fisher p = 0\.011）\*\*。",
     "**⚠️ 本小节的定量断言已【撤回】（第七轮）**：早期版本在此写「复核时补做了缺失的对照……Laya 答对 6/10、答错 4/10 ⇒ 截断把比例从 0.40 抬到 1.00（Fisher p = 0.011）」。"
     "**这组数字在整棵树中没有任何产物**——没有行、没有脚本、没有花费记录，只存在于论文正文与 `protocol\\AUDIT-FINDINGS.md`。"
     "**且其状态规模（79–92 token）恰好等于 P26 自己【已废弃的首版原型】的状态规模**，而该原型的报告原文是「根本没有可截断的东西」。"
     "故**本树无法区分「一次新的对照运行」与「被丢弃原型的数字」**。按本项目自己的标准——**无产物的数字不可作为证据**——该断言**撤回**。\n"
     "> **现在能说与不能说的**：P26 的**产物**显示两臂在 512 token 的可见前缀上逐位相同、更正位于窗口之外（**构造的必然**）；"
     "**能证明「截断会发生」**（P24：60 步只有 14 步能塞进窗口；P26：20 次调用全部 `in_pad = 512`、`truncated = true`）。"
     "**不能证明「截断改变了答案」**——那需要一个把更正移入窗口且**被持久化**的对照。"
     "⇒ 结论**降级为「截断确实发生，其伤害未能与位置效应分离」**。"),
]

# section 8 repeats the same withdrawal in its summary table
D_EDITS = [
    (r"去掉填充使更正落入窗口（状态 79[–\-]92 token）后，Laya \*\*答对 6/10、答错 4/10\*\* ⇒ 截断把「答更正前」的比例从 \*\*0\.40 抬到 1\.00（Fisher p = 0\.011）\*\*。",
     "**⚠️ 该定量断言已撤回（第七轮）**：那组数字（6/10、4/10、p = 0.011、状态 79–92 token）**在整棵树中没有任何产物**，"
     "且其状态规模恰等于 P26 **已废弃首版原型**的规模。**撤回**；本节只保留「截断会发生」这一有产物支撑的部分。"),
]


def apply(fname: str, edits) -> tuple[int, int]:
    p = PAPER / fname
    t = p.read_text(encoding="utf-8")
    ok = miss = 0
    for pat, new in edits:
        t2, n = re.subn(pat, new.replace("\\", "\\\\"), t, count=1)
        if n:
            t = t2
            ok += 1
            print(f"  ok    {fname}: {pat[:60]}")
        else:
            miss += 1
            print(f"  MISS  {fname}: {pat[:60]}")
    p.write_text(t, encoding="utf-8")
    return ok, miss


a = b = 0
from collections import defaultdict
by_file: dict[str, list] = defaultdict(list)
for fname, pat, new in EDITS:
    by_file[fname].append((pat, new))
by_file["08-results-D-draft.md"] = D_EDITS
for fn, eds in by_file.items():
    x, y = apply(fn, eds)
    a += x
    b += y
print(f"\n{a} applied, {b} not found")
sys.exit(1 if b else 0)

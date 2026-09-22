"""Append the P26 re-measurement to the withdrawal, after the ruling.

The withdrawal text was reworded by the drafts editor, so the earlier anchor no longer matched.
This anchors on the ruling's own closing sentence instead.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

p = PAPER / "05-results-A-draft.md"
t = p.read_text(encoding="utf-8")

ANCHOR = "其伤害未能与位置效应分离。**"

NOTE = """
>
> **⚠️ 第八轮最新进展（在本条撤回【之后】取得）：该对照臂已被重新造出，并落在被撤回的数字上。**
> `rerun/p26_control_low_window.py` 按文件路径导入 **P26 自己的 `build_item`**，同一 seed、同一 RNG 调用顺序，
> **只改填充**，使更正落入 512 token 窗口；**填充规则在读取任何判断结果之前就已定下**
> （取中位状态最接近被撤回臂所称 79–92 token 的最小 `PAD_REPEATS`，而 `PAD_REPEATS=0` 恰好给出 79–92）。
> **结果**：状态 **79–92**（中位 85）、答更正后 **6/10**、答更正前 **4/10**、Fisher 双侧 **p = 0.010836**——
> **四个被撤回的数字全部独立复现**；同状态下 LLM 臂 **10/10**。
>
> **⇒ 撤回的理由被【解决】而非被证实**：原型与本对照之所以重合，**是因为它们是同一个生成器在同一填充下的产物**
> ——**那个看起来要命的巧合是确定性的后果，不是造假的证据。**
>
> **⇒ 实质性主张（截断把「答更正前」的比例从 0.40 抬到 1.00）现在有产物支撑，可以恢复。**
> **但恢复与否留待作者裁定**：这是本项目**唯一一条【向上】的修正**，且它推翻的是一个**在当时证据下正确作出**的决定，
> 故不应被顺手带过。产物在 `rerun/P26-control-low-window.json`（刻意置于 `results/` 之外，
> 因 `p30_inventory.py` 会遍历 `results/*.json`，放入会静默改变论文的产物计数）。"""

if ANCHOR in t and "该对照臂已被重新造出" not in t:
    t = t.replace(ANCHOR, ANCHOR + "\n" + NOTE, 1)
    p.write_text(t, encoding="utf-8")
    print("  ok    P26 evidence appended after the ruling")
elif "该对照臂已被重新造出" in t:
    print("  already present")
else:
    print("  MISS  anchor not found")
    sys.exit(1)

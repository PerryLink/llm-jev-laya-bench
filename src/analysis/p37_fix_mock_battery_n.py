"""Fix a battery-size / statistic-n conflation found by tracing section 3.

THE DEFECT
----------
The primary source is `recon/R12-jev-probe.md`, which says two different things:

  line 177: "I ran the full **14-item** calibration battery the remit asked for."
  line 187: "On the **10 items** with binary ground truth, thresholding at 0.5 gives 5/10
             correct = chance, and **Brier score 0.359** -- worse than a constant 0.5 (0.25)."

So the battery has 14 items and the Brier was computed on the 10 that carry binary ground
truth. Those are different numbers for different objects.

Section 3 and section 1 both wrote "14 项校准电池 ... Brier 0.359", which reads as a Brier
over 14 items. Section 6 and the abstract have it right ("在这 10 项上", "n=10"), so the
paper contradicted itself in four places.

This is the project's own named error class -- a defect of the write-up masquerading as a
property of the object -- and it is worth noting that it survived five audit rounds because
both numbers are individually correct and only their ATTACHMENT is wrong.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

FIXES = [
    ("03-systems-draft.md",
     "- **最危险的是它的结果表**：14 项校准电池产出合理的置信度分布，但 **Brier 0.359**，劣于常数预测器的 0.25。",
     "- **最危险的是它的结果表**：一次 **14 项**校准电池产出了合理的置信度分布，而其中**有二元真值的 10 项**上 **Brier = 0.359**——**劣于常数 0.5 预测器的 0.25**。\n"
     "  **⚠️ 两个 n 必须分清（第七轮更正）**：**电池是 14 项，Brier 的 n 是 10**（另 4 项没有二元真值，不计入）。"
     "初稿写作「14 项校准电池……但 Brier 0.359」，读起来像是 14 项上的 Brier——**这是把「电池规模」与「统计量的 n」混为一谈**，"
     "正是本项目命名的错误类别（**写法的缺陷冒充关于对象的结论**）。两个数字各自都是对的，**错的只是它们的挂靠**；"
     "也正因如此，它躲过了五轮审计。出处 `recon\\R12-jev-probe.md:177` 与 `:187`。"),
    ("01-intro-02-related-draft.md",
     "然而它在一次 14 项校准电池上产出了**合理的置信度分布**——",
     "然而它在一次 **14 项**校准电池上产出了**合理的置信度分布**（其中有二元真值的 **10 项**上 Brier = **0.359**，劣于常数 0.5 的 0.25）——"),
    # the abstract says n=10 without saying what the 10 is out of; make it explicit
    ("00-abstract-draft.md",
     "（该后端产出**完全可信的结果表**：Brier 0.359，劣于常数预测器的 0.25，n=10）",
     "（该后端产出**完全可信的结果表**：14 项电池中**有二元真值的 10 项**上 Brier = 0.359，劣于常数 0.5 的 0.25）"),
    # section 6 has the n right but not the battery size -- make the pair explicit there too
    ("06-results-B-draft.md",
     "- **Brier 0.359**，而**常数预测器 0.5 的 Brier 是 0.25** → 在这 10 项上，mock 的概率**劣于常数预测器**；",
     "- **Brier 0.359**，而**常数预测器 0.5 的 Brier 是 0.25** → 在**有二元真值的这 10 项**（全电池 14 项）上，mock 的概率**劣于常数预测器**；"),
]


def main() -> int:
    applied = missed = 0
    for fname, old, new in FIXES:
        p = PAPER / fname
        t = p.read_text(encoding="utf-8")
        if old not in t:
            print(f"  MISS  {fname}: {old[:70]}...")
            missed += 1
            continue
        p.write_text(t.replace(old, new, 1), encoding="utf-8")
        print(f"  ok    {fname}: {old[:70]}...")
        applied += 1
    print(f"\n{applied} applied, {missed} not found")
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main())

"""Fix two numerical inconsistencies found by sentence-level tracing of the abstract.

DEFECT 1 -- the latency ratio spans wider than the paper says.
  The paper prints "p50 跨约 25-29 倍" for the three judgment layers
  (Laya 37.4 ms / LLM 671 ms / Jev 0.9-1.2 s). The ratio that matters is Jev/Laya:
      915  / 37.4 = 24.5x   (the first P27 run)
      1192 / 37.4 = 31.9x   (the second P27 run, same script, same day)
      1073.4 / 37.4 = 28.7x (the pooled n=35 figure in P27-summary.json)
  So the span is 24.5-31.9, i.e. about 25-32. "25-29" takes the LOW end from one run and
  the POOLED p50 as the high end, mixing two different quantities -- and it sits one line
  away from the text that says the two runs were 915 and 1192 ms, whose ratio is 31.9.
  Corrected to 25-32, with the basis stated.

DEFECT 2 -- "3 次中 2 次 CI 排除零" contradicts the paper's own corrected framing.
  Section 8 was fixed in an earlier round: under the unpaired Wald interval 2 of 3 draws
  exclude zero, but two of those draws have a ZERO CELL (judge-only-correct = 0), which
  makes Wald spuriously narrow. Under Newcombe -- the interval that stays valid at a zero
  cell -- only 1 draw robustly excludes and 1 sits at the boundary. The abstract and the
  section-8 summary still carried the unqualified Wald reading, so the paper contradicted
  itself in three places.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

FIXES: list[tuple[str, str, str]] = [
    # --- defect 1: the latency ratio -------------------------------------------------
    ("00-abstract-draft.md",
     "（p50 跨约 **25–29 倍**：37.4 ms / 671 ms / **0.9–1.2 s**",
     "（p50 跨约 **25–32 倍**：37.4 ms / 671 ms / **0.9–1.2 s**"),
    ("01-intro-02-related-draft.md",
     "而**延迟跨约 25–29 倍**（37.4 ms / 671 ms / **0.9–1.2 s**；n 分别为 30 / 48 / 35，三者均为**客户端墙钟**，Jev 侧同一脚本两次运行 p50 为 915 与 1,192 ms）",
     "而**延迟跨约 25–32 倍**（37.4 ms / 671 ms / **0.9–1.2 s**；n 分别为 30 / 48 / 35，三者均为**客户端墙钟**。**区间取自 Jev 侧的两次同脚本运行**：24.5 倍（p50 915 ms）至 31.9 倍（p50 1,192 ms）；合并 n=35 的中位为 28.7 倍）"),
    ("05-results-A-draft.md",
     "→ **p50 跨约 25–29 倍**（37.4 ms → 671 ms → ~0.9–1.2 s；**按哪一次 Jev 运行取值**），**方向有利于本地判定器**。",
     "→ **p50 跨约 25–32 倍**（37.4 ms → 671 ms → ~0.9–1.2 s）。**区间下沿 24.5 倍取自第一次 Jev 运行（p50 915 ms），上沿 31.9 倍取自第二次（p50 1,192 ms）**；合并 n=35 的中位为 28.7 倍。**方向有利于本地判定器**，但**该轴的单次运行不可复现**（见脚注 1）。"),
    ("05-results-A-draft.md",
     "| **延迟** | **p50 跨约 25–29 倍**（37.4 ms → 671 ms → **0.9–1.2 s**）；Jev 合并实测 max 4,018.6 ms | 有利于本地 |",
     "| **延迟** | **p50 跨约 25–32 倍**（37.4 ms → 671 ms → **0.9–1.2 s**，下沿/上沿分别取自 Jev 的两次运行）；Jev 合并实测 max 4,018.6 ms | 有利于本地 |"),
    # --- defect 2: the zero-cell interval --------------------------------------------
    ("00-abstract-draft.md",
     "故点估计虽 **3/3 次一致为负**且 **3 次中 2 次 CI 排除零**，**精度仍有限**。",
     "故点估计虽 **3/3 次一致为负**，**区间强度却有限**：未配对 Wald 下 3 次中 2 次排除零，**但改用零格可靠的 Newcombe 后仅 1 次稳健排除、1 次在边界**（§8.3）。**精度仍有限。**"),
    ("00-abstract-draft.md",
     "Δ_catch 3/3 次为负、3 次中 2 次 CI 排除零。第二个区制 4/4 次为负。",
     "Δ_catch 3/3 次为负；**未配对 Wald 下 3 次中 2 次排除零，Newcombe 下仅 1 次稳健排除、1 次在边界**。第二个区制 4/4 次为负。"),
    ("08-results-D-draft.md",
     "Δ_catch 一致为负（3/3，其中 2 次 CI 排除零），且失败相关**在 3/3 次抽",
     "Δ_catch 一致为负（3/3；未配对 Wald 下 2 次排除零，**但零格使该区间过窄，改用 Newcombe 后仅 1 次稳健排除、1 次在边界**），且失败相关**在 3/3 次抽"),
    ("08-results-D-draft.md",
     "> **MDE（0.28–0.30）仍大于预声明门（+0.10），故这是「方向 3/3 次一致、2 次 CI 排除零」，不是精确的效应量。**",
     "> **MDE（0.28–0.30）仍大于预声明门（+0.10），故这是「方向 3/3 次一致、Wald 下 2 次排除零（Newcombe 下 1 次稳健、1 次在边界）」，不是精确的效应量。**"),
]


def main() -> int:
    applied = missed = 0
    for fname, old, new in FIXES:
        p = PAPER / fname
        t = p.read_text(encoding="utf-8")
        if old not in t:
            print(f"  MISS  {fname}: {old[:64]}...")
            missed += 1
            continue
        p.write_text(t.replace(old, new, 1), encoding="utf-8")
        print(f"  ok    {fname}: {old[:64]}...")
        applied += 1
    print(f"\n{applied} applied, {missed} not found")
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main())

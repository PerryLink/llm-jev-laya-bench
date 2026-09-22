"""Fix defects from the §6/§7 and §8 trace audits.

Only the findings that change what the paper ASSERTS are fixed here. The rest are recorded
in the audit reports and in results/ERRATA.md.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

EDITS: list[tuple[str, str, str, str]] = [
    # (file, old, new, label)
    # --- §8: the retraction of the P26 control arm was never propagated --------------
    ("08-results-D-draft.md",
     "→ 因此本节的「统一形态」有**三个实例，但第三个只被部分支持**：截断解释其中约 6/10，另有 4/10 发生在**证据完全可见**时。",
     "→ 因此本节的「统一形态」有**两个有产物支撑的实例，第三个的支持不足**："
     "截断那一格**只能证到「截断会发生」**——早期版本印的「解释其中约 6/10、另 4/10 发生在证据完全可见时」"
     "**所依据的对照臂无产物，已撤回（第八轮）**。",
     "§8 propagate: the 6/10 split"),
    ("08-results-D-draft.md",
     "| 超窗状态（对照臂，n=10） | 更正**完全可见**却未被采纳 | **错 4/10** | — |",
     "| 超窗状态（对照臂，n=10） | 更正**完全可见**却未被采纳 | **⚠️ 该对照无产物，数字已撤回** | — |",
     "§8 propagate: the 4/10 table cell"),

    # --- §9.6: the unqualified CI claim, caught by the improved guard -----------------
    ("09-10-11-discussion-limits-repro-draft.md",
     "**Δ_catch = −0.182 至 −0.247**，3 次中 **2 次 95% CI 排除零**",
     "**Δ_catch = −0.182 至 −0.247**，**未配对 Wald 下 3 次中 2 次排除零，但该区间因零格而虚假收窄；"
     "改用 Newcombe 后仅 1 次稳健排除、1 次在边界**",
     "§9.6 unqualified CI claim"),

    # --- §6: M1. the quantifier is falsified by the table directly above it -----------
    ("06-results-B-draft.md",
     "全部 7 次「非支持」调用中都不超过 0.14",
     "**5 次 `insufficient` 调用**中都不超过 0.14（**⚠️ 第八轮更正**：原印「全部 7 次」——"
     "但本节自己的表里只有 **5** 行是 `insufficient`，另两行的 `sufficient` 分别为 **0.88** 与 **0.92**，"
     "**都大于 0.14**。该错误逐字继承自 `probes\\P13-jev-remaining-measurements.md:60`，"
     "且已被 `protocol\\AUDIT-FINDINGS.md:225` 记为审计发现 m-8，初稿未同步）",
     "§6 M1: the 7-call quantifier"),

    # --- §6: M2. the "highest confidence" is exceeded two lines later ------------------
    ("06-results-B-draft.md",
     "全探测最高 confidence 0.9981",
     "全探测最高 confidence **0.9989**（**⚠️ 第八轮更正**：原印 0.9981，但**紧接的下一行就印着 0.9989**，"
     "`recon\\R13-laya-probe.md:456` 亦记 0.9989——0.9989 > 0.9981，故原句自相矛盾）",
     "§6 M2: the highest confidence"),

    # --- §6: M6. the cited artifact records the opposite verdict ----------------------
    ("06-results-B-draft.md",
     "对逐字支持主张的证据返回 `insufficient`",
     "对逐字支持主张的证据返回 **`undecided`**（**⚠️ 第八轮更正**：原印 `insufficient`，"
     "但**被引来源记录的恰恰相反**——`recon\\R12-jev-probe.md:307` 的逐字夹具返回 `undecided`，"
     "`probes\\P13-jev-remaining-measurements.md:69` 同；`insufficient` 只记在**另一个**夹具上"
     "（`recon\\R11-dsh-testbed.md:413`）。**一个夹具各记一边，故普遍化措辞不被所引来源支持**）",
     "§6 M6: the mock's verdict label"),

    # --- §6: O1. n=1 is valid only for the direct-provider inventories -----------------
    ("06-results-B-draft.md",
     "`choice` 与 `score` 在整个 `results\\` 树中各只有 n=1",
     "`choice` 与 `score` 在**直连 provider 的字段清单**中各只有 n=1（**⚠️ 限定**："
     "全树记录的 `choice` **响应**远不止 1 次——`P1-rank-vs-choice.json` 18 次、"
     "`P5c-marker-vs-integration.json` 20 次等——**但那些不是逐字段的 provider 正文检查**，"
     "而是经由接入层的调用。原印「整个 results 树中各只有 n=1」**是错的**，已收窄）",
     "§6 O1: the n=1 scope"),

    # --- §6: M3. the line citation is off by ~18 lines ---------------------------------
    ("07-results-C-draft.md",
     "代码已于 `p1_rank_vs_choice.py:236-246` 改为**从数据推导分桶**",
     "代码已于 `p1_rank_vs_choice.py:253-267` 改为**从数据推导分桶**"
     "（**⚠️ 第八轮更正**：原引 236-246——那 11 行是行字典字段，与分桶无关）",
     "§7 M3: the line citation"),

    # --- §7: O6. the minimum was reported as the value ---------------------------------
    ("07-results-C-draft.md",
     "逐项标签一致率仅 **58.8%**（40/68；剔除 7 条选项集有变的条目后为 **60.7%**，见 §8.6.1）",
     "逐项标签一致率 **58.8–63.2%**（三次配对分别为 40/68、43/68、41/68）；"
     "剔除 7 条选项集有变的条目后为 **60.7–63.9%**，见 §8.6.1。"
     "**⚠️ 早期版本只印三次中最低的那一次（58.8% / 60.7%），把一个范围写成了单值**",
     "§7 O6: the agreement range"),
]


def main() -> int:
    cache: dict[str, str] = {}
    ok = miss = 0
    for fname, old, new, label in EDITS:
        p = PAPER / fname
        if fname not in cache:
            cache[fname] = p.read_text(encoding="utf-8")
        if old in cache[fname]:
            cache[fname] = cache[fname].replace(old, new, 1)
            print(f"  ok    {label}")
            ok += 1
        else:
            print(f"  MISS  {label}")
            miss += 1
    for fname, t in cache.items():
        (PAPER / fname).write_text(t, encoding="utf-8")
    print(f"\n{ok} applied, {miss} not found")
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main())

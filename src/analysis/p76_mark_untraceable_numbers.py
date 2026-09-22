"""ERRATA 10.2 -- mark every number that has no `results/` artifact behind it.

WHY THIS IS THE HARDEST ITEM IN THE WORKLIST, AND WHY IT STILL HAS TO BE DONE
-----------------------------------------------------------------------------
This paper's thesis is that a number which cannot be re-checked is worthless as evidence.
Section 10.2 of `results/ERRATA.md` lists twelve quantities that are printed in the paper
but exist only in `recon/` or `probes/` lab records (or in a one-off interpreter session):
the mock battery's Brier and its `t ≈ 1.1`, the kappa bootstrap CI, the CMH permutation
p-values, the 68-item permutation test, the two n=69 chain re-runs, "11/69 non-derivable",
"an independent replay of 18 requests", every `jev_check` verdict number, the `band`
distribution on `no_support` items, the four R13 per-case points, and the correction's
token position "1,943-1,952".

None of them is necessarily WRONG -- several were independently reproduced to within Monte
Carlo error. They are unusable AS PRINTED, because a reader cannot get from the printed
number to anything in the tree. Deleting them would remove real evidence; leaving them
unmarked keeps the paper's central methodological claim false about its own text. So each
one gets a marker naming what it actually rests on, and section 11 gets one consolidated
list so the disclosure cannot be missed by a reader who only samples the paper.

The alternative -- quietly leaving them -- is the failure mode ERRATA section 10.4 names:
"checking numbers is not the same as checking what they are numbers OF".
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

B = "06-results-B-draft.md"
C = "07-results-C-draft.md"
D = "08-results-D-draft.md"
A = "05-results-A-draft.md"
AB = "00-abstract-draft.md"
DL = "09-10-11-discussion-limits-repro-draft.md"


def mark(source: str, what: str = "") -> str:
    """The standard untraceable marker. One wording, so a reader learns it once."""
    tail = f"（{what}）" if what else ""
    return (f" **【不可核验 ⚠️ ERRATA §10.2】**：该数字**没有 `results\\` 产物**，只存在于实验室记录 "
            f"`{source}`{tail}；按本文自己的标准（§11.5）**它不能作为证据**，此处保留只为记录。")


EDITS: list[tuple] = [
    # ---------------------------------------------------------------- Brier 0.359 and t ≈ 1.1
    (B,
     "**劣于常数预测器**（**⚠️ 该 n=10 出自来源正文；上表逐箱计数合计为 9——差 1 且树内无法裁决，见上**）；",
     "**劣于常数预测器**（**⚠️ 该 n=10 出自来源正文；上表逐箱计数合计为 9——差 1 且树内无法裁决，见上**）；"
     + mark("recon\\R12-jev-probe.md:187", "同一数字在摘要、§1 与 §3 各出现一次，出处相同")
     + "同一 Brier 亦无任何 `results\\` 产物：`results\\` 下唯一的 Brier 是 **live 校准电池**的 0.2571（`P19-calibration.json`），"
       "与这个 **mock 电池**的 0.359 是两个不同对象；",
     "§3.1: Brier 0.359 (10.2)"),

    (B,
     "正确表述是「**在该样本上未显示信息**」；",
     "正确表述是「**在该样本上未显示信息**」；"
     + mark("probes\\P13-jev-remaining-measurements.md", "该 t 值由 0.109/0.10 手算，全树无脚本、无产物")
     + "",
     "§3.1: t ≈ 1.1 (10.2)"),

    # ---------------------------------------------------------------- jev_check verdicts
    (B,
     "| 单条未署名笔记 | 0.06 | 0.04 | 0.03 | `insufficient` |",
     "| 单条未署名笔记 | 0.06 | 0.04 | 0.03 | `insufficient` |\n"
     "\n"
     "**【不可核验 ⚠️ ERRATA §10.2】**：**本表全部 7 行**（以及上引的 `sufficient` 读数）**没有 `results\\` 产物**"
     "——`results\\` 下**没有任何 JSON 含 `sufficient` 字段**，这些读数只存在于实验室记录 `probes\\P13-jev-remaining-measurements.md:47-56`（另见 "
     "`protocol\\AUDIT-FINDINGS.md`）。**故本表只能作为一次记录读，不能作为可复核的测量**；本节据此得出的定性结论（五值词表退化为三值）"
     "在**该记录内部**是自洽的，但**外部核验需要重跑**——而重跑会产生新数字（`temperature` 未固定），这是本项目已经记载过的一类代价。",
     "§3.5: the 7 verdict rows (10.2)"),

    # ---------------------------------------------------------------- kappa bootstrap CI
    (C,
     "18. **点估计的位数不得超过其区间宽度所允许的精度。** 依据：「κ = 0.0062 与随机无异」是对一个 bootstrap 95% CI 为 **[−0.185, +0.206]** 的估计做的四位小数陈述。",
     "18. **点估计的位数不得超过其区间宽度所允许的精度。** 依据：「κ = 0.0062 与随机无异」是对一个 bootstrap 95% CI 为 **[−0.185, +0.206]** 的估计做的四位小数陈述。"
     "**【不可核验 ⚠️ ERRATA §10.2】**：该 bootstrap 区间**没有 `results\\` 产物、也没有脚本**——`P28-recomputed-statistics.json` 重算的是 Wald / Newcombe / Fisher / Clopper-Pearson，"
     "**不含 bootstrap**；该区间出自审计期间的一次性解释器会话。条款本身的教训不依赖这个具体区间（κ 的 2×2 上有产物支撑的统计量已足够说明问题），但**该数字本身不可核验**。",
     "§6.6 clause 18: the kappa bootstrap CI (10.2)"),

    (C,
     "18 行本身完整，全部已发表的 P1 数字仍可复现（独立重放 18 次请求，除 `latency_ms` 外**逐字段逐位相同**）。",
     "18 行本身完整，全部已发表的 P1 数字仍可复现（独立重放 18 次请求，除 `latency_ms` 外**逐字段逐位相同**）。"
     "**【不可核验 ⚠️ ERRATA §10.2】**：**这次「独立重放」没有产物、也没有脚本**——`P1-rank-vs-choice.json` 只有 `summary` 与 `rows` 两个键，**没有任何 replay 记录**；"
     "重放结论出自审计期间的一次性会话。故此处只能写「记录称重放逐位相同」，**不能写「已可复现」**；要真正断言，需要把重放本身写成脚本并留下产物（尚未做）。",
     "§6.6 clause 19: the 18-request replay (10.2)"),

    (C,
     "**11/69 条（15.9%）的判分真值不可推导**，其中 10 条的忠实答案甚至不在选项中（§8.6.1）。",
     "**11/69 条（15.9%）的判分真值不可推导**，其中 10 条的忠实答案甚至不在选项中（§8.6.1）。"
     "**【不可核验 ⚠️ ERRATA §10.2】**：`P22-chain-audit.json` 的 69 行**没有任何可推导性字段**（行键只有 `truth` / `llm_*` / `laya_*` / `alt_in_options`），"
     "**11 这个计数无法由产物得出**；它来自审计期间的独立重算。**修复后**的电池（`P22b-fixed-r1..r3.json`）由构建期断言强制该性质（**96 → 0 → 68**），**那一段是可核验的**；"
     "「修复前 11/69」这一历史数字则只能作为记录读。",
     "§6.6 clause 21: 11/69 (10.2)"),

    # ---------------------------------------------------------------- band on no_support
    (C,
     "| `no_support` | 证据不存在 | 断言为真（P=0.564）| `band` 给出低置信度，但 `noul` 高于 0.5 |",
     "| `no_support` | 证据不存在 | 断言为真（P=0.564）| `band` 给出低置信度，但 `noul` 高于 0.5（**⚠️ 不可核验：`P19-calibration.json` 没有 `band` 列，见下**）|",
     "§6.5: the band cell (10.2)"),

    (C,
     "**这个假说可被证伪**：若在「候选值不出现」的条目上给它一个**显式的缺席标记**",
     "**【不可核验 ⚠️ ERRATA §10.2】**：上表 `no_support` 行的 `band` 断言**没有产物支撑**——`P19-calibration.json` 的 1100 行里**没有 `band` 字段**（`band` 是接入层推导量，P19 记录的是 `noul` 与 `laya_p`）。"
     "本行因此**只作为形态描述保留**：有产物支撑的是 `noul` 的分布（平均 0.5643）与准确率（0.3091），**不是** `band` 的取值分布。**若要主张 band 的分布，需要重跑并记录该字段**（未做）。\n"
     "\n**这个假说可被证伪**：若在「候选值不出现」的条目上给它一个**显式的缺席标记**",
     "§6.5: the band distribution (10.2)"),

    # ---------------------------------------------------------------- the R13 case points
    (C,
     "→ **对照价值**：**同一批条目上，一个判定器的满置信度是对的，另一个的满置信度是错的。** 用户无法从返回值区分。",
     "**【不可核验 ⚠️ ERRATA §10.2】**：本表中标 **R13** 的四行（0.9981、0.9989、0.5399 vs 0.0046、以及 `noul 0.0011`）**都没有 `results\\` 产物**——它们来自实验室记录 "
     "`recon\\R13-laya-probe.md`（`:430`、`:456`、`:448-449`），该文件以逐字 JSON 记录了这些响应，但**没有对应的结果 JSON**；本表另两行（P9b 的 0.218 / 0.115）有产物。"
     "**故这四行只能作为个案记录读**：它们的价值在于**形态**（同一字段在两个方向上都可能远离正确性），而不在于可复核性。要把它们变成可复核证据，需要把当时的请求与响应写成产物（未做）。\n"
     "→ **对照价值**：**同一批条目上，一个判定器的满置信度是对的，另一个的满置信度是错的。** 用户无法从返回值区分。",
     "§6.2: the four R13 points (10.2)"),

    # ---------------------------------------------------------------- 11/69 in section 8
    (D,
     "后果：**11/69 条（15.9%）的判分真值不能由渲染出的题面推出**（其中 10 条的「忠实读法」答案甚至不在选项中）。",
     "后果：**11/69 条（15.9%）的判分真值不能由渲染出的题面推出**（其中 10 条的「忠实读法」答案甚至不在选项中）。"
     "**【不可核验 ⚠️ ERRATA §10.2】**：`P22-chain-audit.json` 无任何可推导性字段，该计数不能由产物得出（详见 §7.6 条款 21 处的标注）；**修复后**的 96 → 0 → 68 由断言强制，那一段可核验。",
     "§7.6.1: 11/69 (10.2)"),

    # ---------------------------------------------------------------- the two n=69 re-runs
    (D,
     "反证就在本项目自己的记录里：对**未经任何修复**的同一 69 条电池两次重跑，Δ_catch 已达 **−0.0328 / −0.2071** —— **不做真值修复也能得到同样的幅度**。",
     "反证就在本项目自己的记录里：对**未经任何修复**的同一 69 条电池两次重跑，Δ_catch 已达 **−0.0328 / −0.2071** —— **不做真值修复也能得到同样的幅度**。"
     "**【不可核验 ⚠️ ERRATA §10.2】**：**这两次 n=69 重跑没有产物**——`results\\` 下与链式电池相关的产物是记录轮（n=69，`P22-chain-audit.json`）与**修复后的 n=68 三次抽样**（`P22b-fixed-r1..r3.json`），"
     "**没有第二个 n=69 的 JSON**；−0.0328 / −0.2071 出自审计期间的会话（`results\\ERRATA.md` §5 有记录，但那也不是产物）。**"
     "本条论证的方向不依赖这两个具体数字**（`P22b` 三次负值与记录轮 −0.007 已足够说明「不做修复也能得到负号」），但**数字本身不可核验**。",
     "§7.6.1: the two n=69 re-runs (10.2)"),

    # ---------------------------------------------------------------- permutation test
    (D,
     "按正确的聚类层级做 68 条目置换检验，相关 **+0.243**、**p = 0.057**；",
     "按正确的聚类层级做 68 条目置换检验，相关 **+0.243**、**p = 0.057**"
     "（**【不可核验 ⚠️ ERRATA §10.2】**：该置换检验**既无产物也无脚本**——`P28-recomputed-statistics.json` 重算的是 Wald / Newcombe / Fisher / Clopper-Pearson / AUC，"
     "**不含置换检验**；其**定义与随机种子均未记录**，故**不可复现**。它在此的作用是**削弱**上文的显著性主张，删去它只会让质疑更少——但它仍应被标注）；",
     "§7.6.1(c): the permutation test (10.2)"),

    (D,
     "**按 K 分层的 CMH 置换检验 p = 0.059 / 0.055 / 0.201——三次没有一次达到 α=0.05**。",
     "**按 K 分层的 CMH 置换检验 p = 0.059 / 0.055 / 0.201——三次没有一次达到 α=0.05**"
     "（**【不可核验 ⚠️ ERRATA §10.2】**：该组 p 值**没有产物、没有脚本，也没有记录种子**，`P28` 不含 CMH；与本条相邻的**逐层 φ**（−0.357 / +0.122 / +0.241 / +0.030 / +0.621 / +0.569 / +0.569）**同样只在 prose 中**。"
     "**但本条的性质必须说清**：这是一个**削弱自身结论**的检验，故不可核验的代价是**结论强度被高估的风险**，而不是结论被夸大的风险——它仍须标注，因为标注的是**可核验性**，不是方向）。",
     "§7.6.1(d): the CMH permutation p-values (10.2)"),

    (D,
     "并如实指出记录轮的 κ = 0.0062 其 bootstrap 95% CI 为 **[−0.185, +0.206]**——用四位小数去读一个 ±0.2 宽的点估计。",
     "并如实指出记录轮的 κ = 0.0062 其 bootstrap 95% CI 为 **[−0.185, +0.206]**——用四位小数去读一个 ±0.2 宽的点估计。"
     "**【不可核验 ⚠️ ERRATA §10.2】**：该 bootstrap 区间无产物、无脚本（`P28` 不含 bootstrap），见 §7.6 条款 18 处的标注。",
     "§7.6: the kappa CI (10.2)"),

    # ---------------------------------------------------------------- token position
    (D,
     "(a) **两臂的可见前缀逐位相同**——dropped 臂仍有 ~4× 钳位，更正位于第 1,943–1,952 个 token，**超出两者共同的 512 窗口**，故「两臂同答」是**构造的必然**；",
     "(a) **两臂的可见前缀逐位相同**——dropped 臂仍有 ~4× 钳位，更正位于第 1,943–1,952 个 token，**超出两者共同的 512 窗口**，故「两臂同答」是**构造的必然**；"
     "**【不可核验 ⚠️ ERRATA §10.2】**：该 token 位置**没有产物**——`P25`/`P26` 的产物记录的是 `in_pad`、`truncated`、选项与判定，**不含更正所在 token 的绝对位置**；"
     "1,943–1,952 出自审计期间的一次性核验。**该论证的方向有产物支撑**（两臂的共同窗口为 512、真值恒在末位），但**这一具体位置不可核验**；",
     "§7.7(a): the token position (10.2)"),

    (A,
     "逐 token 核验：**两臂的前 512 个 token id 在 10/10 条上完全相同**，而更正所在位置是第 **1,943–1,952** 个 token。",
     "逐 token 核验：**两臂的前 512 个 token id 在 10/10 条上完全相同**，而更正所在位置是第 **1,943–1,952** 个 token。"
     "**【不可核验 ⚠️ ERRATA §10.2】**：该 token 位置无 `results\\` 产物（同 §8.7(a) 处的标注）；「前 512 个 token id 相同」这一条**可由 P26 的 `in_pad` 与选项记录间接支持**，但绝对位置不可核验。",
     "§5: the token position (10.2)"),

    (AB,
     "且**失败相关 φ 按难度分层后三次均不显著**（CMH 置换 p = 0.059 / 0.055 / 0.201）。",
     "且**失败相关 φ 按难度分层后三次均不显著**（CMH 置换 p = 0.059 / 0.055 / 0.201；**⚠️ 该组 p 值不可核验——无产物、无脚本、无种子记录，见 §8.6.1(d)**）。",
     "abstract: the CMH p-values (10.2)"),
]

# --------------------------------------------------------------------------- section 11.5
# One consolidated list, so a reader who samples the paper still sees the disclosure.
ANCHOR_115 = "**⚠️ 仍未关闭的缺口**：`deepseek_client.py`——LLM 那一臂自己的客户端——**全树无任何文件哈希它**。"
ANNEX_115 = """## 11.6 只能追溯到实验室记录、**没有 `results\\` 产物**的数字（`results\\ERRATA.md` §10.2 全表）

**本文的标准是「不能复核的数字不能作为证据」。下面这些数字印在正文里，但它们背后【没有】`results\\` 产物**——大多只存在于 `recon\\` / `probes\\` 的实验室记录，或审计期间的一次性解释器会话。**它们不一定是错的**（其中若干曾被独立复算到蒙特卡洛误差以内），但**按本文自己的标准，它们不能作为证据**；正文各处已逐一标注，此处汇总，以免读者抽样阅读时看不到。

| # | 数字 | 正文位置 | 实际出处 | 有产物支撑的替代 |
|---|---|---|---|---|
| 1 | mock 电池 **Brier 0.359**、**t ≈ 1.1** | §6.1、摘要、§1、§3 | `recon\\R12-jev-probe.md:187`（t 值由 0.109/0.10 手算） | 无（live 校准电池的 Brier **0.2571** 有产物：`P19-calibration.json`）|
| 2 | κ 的 bootstrap 95% CI **[−0.185, +0.206]** | §7.6 条款 18、§8.6 | 一次性会话；`P28` 不含 bootstrap | Wald / Newcombe / Fisher / Clopper-Pearson（`P28-recomputed-statistics.json`）|
| 3 | CMH 置换 p **0.059 / 0.055 / 0.201** | §8.6.1(d)、摘要 | 一次性会话；**无定义、无种子** | 逐层 φ 与池化 φ（`P28` 有 φ；**逐层值仍只在 prose**）|
| 4 | 68 条目置换检验（**+0.243**，p = 0.057）的**定义与种子** | §8.6.1(c) | 一次性会话，未记录定义/种子 | 无 |
| 5 | 两次 **n=69** 链式重跑（Δ_catch **−0.0328 / −0.2071**）| §8.6.1 | 一次性会话；`ERRATA.md` §5 有文字记录 | 修复后 **n=68** 三次抽样（`P22b-fixed-r1..r3.json`）|
| 6 | **11/69（15.9%）** 判分真值不可推导 | §7.6 条款 21、§8.6.1 | 审计期独立重算；**`P22` 无该字段** | 修复后 **96 → 0 → 68**（构建期断言，`P22b`）|
| 7 | 「独立重放 18 次请求，除 `latency_ms` 外逐位相同」 | §7.6 条款 19 | 一次性会话；`P1` 无 replay 键 | `P1-rank-vs-choice.json` 的 18 行本身 |
| 8 | **全部 `jev_check` 判定读数**（7 行表）| §6.5 | `probes\\P13-jev-remaining-measurements.md:47-56` | 无（`results\\` 下**没有任何 JSON 含 `sufficient` 字段**）|
| 9 | `no_support` 条目上的 **`band` 分布** | §7.5 表 | 同上；`P19` **无 `band` 列** | `noul` 分布与准确率（`P19-calibration.json`）|
| 10 | **四个 R13 个案点**（0.9981 / 0.9989 / 0.5399 vs 0.0046 / 0.0011）| §7.2 | `recon\\R13-laya-probe.md:430`、`:456`、`:448-449` | P9b 的两行（0.218 / 0.115，`P9b-...json`）|
| 11 | 更正所在 **token 位置 1,943–1,952** | §5、§8.7(a) | 一次性会话；`P25`/`P26` 无该字段 | 两臂共同窗口 512（`P26` 的 `in_pad`）|
| 12 | —— | —— | —— | —— |

**⚠️ 这张表本身就是本文论点的应用**：它是**手写的**，因此也会过期——第 12 行留空是因为 ERRATA §10.2 列出的类别已在 1–11 行覆盖，而不是因为还有一项没写。**计数由 `results\\ERRATA.md` §10.2 决定，不由本表决定**；若该节变化，本表必须同步。

"""
EDITS.append((DL, ANCHOR_115, ANNEX_115 + ANCHOR_115, "§11.6: the consolidated untraceable list (10.2)"))


def main() -> int:
    ok = miss = 0
    cache: dict[str, str] = {}
    for entry in EDITS:
        fname, old, new, label = (entry if len(entry) == 4 else (B,) + tuple(entry))
        if fname not in cache:
            cache[fname] = (PAPER / fname).read_text(encoding="utf-8")
        t = cache[fname]
        if old in t:
            cache[fname] = t.replace(old, new, 1)
            print(f"  ok    {label}")
            ok += 1
        elif new in t:
            print(f"  ok    {label} (already applied)")
            ok += 1
        else:
            print(f"  MISS  {label}")
            miss += 1

    for fname, t in cache.items():
        (PAPER / fname).write_text(t, encoding="utf-8")

    n_marks = sum(v.count("【不可核验 ⚠️ ERRATA §10.2】") for v in cache.values())
    if n_marks >= 11:
        print(f"  ok    {n_marks} untraceable markers now in the drafts (expected >= 11)")
    else:
        print(f"  MISS  only {n_marks} untraceable markers survived")
        miss += 1

    print(f"\n{ok} applied, {miss} problems")
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main())

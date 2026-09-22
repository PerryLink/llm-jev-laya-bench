"""ERRATA 10.1 items 3 and 2 -- the two the author ranked first and second.

WHY THESE TWO MATTER MORE THAN THE OTHER ELEVEN
-----------------------------------------------
Item 3 (section 7.2 never mentions P14's PROSE arm) is not a typo, it is a MISSING
MEASUREMENT -- and the measurement points the other way. Section 7.2 declares regime 1
unmeasurable because the forced-choice arm has the LLM at 48/48. But `P14-llm-arm-full.json`
also carries `complementarity_prose_arm` on the SAME 48 items: LLM 46/48, one judge-only
item, **delta_catch = +0.0435**. That is the only measurable Delta_catch in regime 1 and it
is POSITIVE. A paper whose thesis is that unverifiable numbers are worthless cannot leave
out the one number that argues against its own central negative claim, and the artifact's
`_provenance.published_figures_at_risk` lists that very arm ("prose arm 0.958").

Two previous fix scripts (p44, p45) both targeted this defect and both reported MISS: they
looked for the sentence in `06-results-B-draft.md`, where it has never been. The defect is
in `07-results-C-draft.md` section 6.2 (the per-case table) -- which is why ERRATA 10.1
item 1's own file label is wrong too. This script anchors on the text that actually exists.

Item 2 (the unlabelled p-values 0.052 / 0.043 / 0.103 in section 8.6.1(b)) is the same
failure in miniature: the numbers are real, the CONVENTION is missing. They are normal
approximations; the exact binomial lower tails are 0.076 / 0.061 / 0.149. Under neither
convention is anything significant -- but a reader cannot tell which test produced the
figure, which is precisely what this paper refuses to do elsewhere.

WHAT THIS SCRIPT WILL NOT DO
----------------------------
It will not soften the prose-arm finding, and it will not bury it: the +0.0435 goes in as a
table of its own, immediately under the forced-choice table, with its 2-item denominator and
its wide interval next to it. It also will not silently drop the paper's negative claim --
it corrects that claim to what the two arms jointly support.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

D = "08-results-D-draft.md"

PROSE_BLOCK = """
**⚠️ 但上面的读数是强制选择臂的。同一产物还记录了第二条臂，而它的 Δ_catch 是正的（第九轮补记，ERRATA §10.1 第 3 项）。**
`results\\P14-llm-arm-full.json` 的 `complementarity_prose_arm` 记录的是**同一批 48 条条目**上 LLM 以**散文**作答（标签由抽取器解析）的配对结果：

| 指标 | 值（P14 散文臂，n=48） |
|---|---|
| **LLM 准确率** | **0.9583（46/48）** |
| 判定器准确率（同一批判定器读数） | **0.4583** |
| 两者皆对 / 仅 LLM 对 / **仅判定器对** / 皆错 | 21 / 25 / **1** / 1 |
| **`P(判定器对 \\| LLM 错)`** | **0.5（1/2）** |
| `P(判定器对 \\| LLM 对)` | 0.4565（21/46） |
| **Δ_catch** | **+0.0435** |
| Δ_catch 95% CI（未配对 Wald / Newcombe） | **[−0.664, +0.751] / [−0.386, +0.471]** |
| Fisher 精确 p（2×2） | 1.0000 |

→ **这是区制一唯一可测量的 Δ_catch，而它的符号是正的。** 本节此前只报了强制选择臂，因而把整个区制写成「不可测量」——**该判断对强制选择臂成立，对散文臂不成立。**
→ **分母必须与点估计同时给出，否则 +0.0435 会被读成它不支持的强度**：散文臂上 LLM 只错 **2** 条，故 `P(判定器对 | LLM 错)` 是 **1/2**；两个 95% 区间都很宽且都包含 0，Fisher p = 1.0000。**它不是已确立的互补性；但它也不是 0**——把 +0.0435 读成「无互补」与把它读成「有互补」同样没有依据。
→ **两条臂是同一批 48 条电池的两种作答格式**（该产物的 `_provenance.consumes` 即 `P9b`；判定器在两条臂上同为 0.4583），**不是两份独立证据**；能力画像里它们各自只占一行并须注明配对关系（§6.1）。
→ 上表全部数字由 `src\\analysis\\p28_recompute_all_stats.py` 重算并写入 `results\\P28-recomputed-statistics.json` 的 `regime1` 块；该块同时记录**强制选择臂的 Δ_catch 因 `n_wrong_arm = 0` 而未定义**（不得印成 0）。
→ **⚠️ 该产物的 `_provenance.published_figures_at_risk` 本就列着「prose arm 0.958」**——这一臂自记录起就在「若被改动则论文数字有风险」的清单上，此前却从未在正文出现。
"""

EDITS: list[tuple[str, str, str, str]] = [
    # ---------------------------------------------------------------- item 3: regime 1
    ("→ 能说的只有：**在这个区制上 Laya 未捕获任何 LLM 漏掉的条目（仅 Laya 对 0 / 仅 LLM 对 26）**，而是在 26 个条目上单独失败。",
     "→ 能说的只有：**在这个区制上 Laya 未捕获任何 LLM 漏掉的条目（仅 Laya 对 0 / 仅 LLM 对 26）**，而是在 26 个条目上单独失败。\n"
     + PROSE_BLOCK,
     "§7.2: the omitted prose arm (ERRATA 10.1 item 3)"),

    ("**此区制的证据强度**：**上限效应** —— 它**不能**证明「无互补」，只能证明**本电池无法测量互补性**。",
     "**此区制的证据强度**：**上限效应只适用于强制选择臂**（LLM 48/48）。**散文臂可测**，其 Δ_catch 点估计为 **+0.0435**、区间跨 0、且只建立在 **2** 条 LLM 错项上。"
     "**⚠️ 故本区制的准确表述是：一个作答格式上不可测，另一个上可测、点估计为正、但精度不足以判定**——而不是「本电池无法测量互补性」（第九轮更正：原句只据强制选择臂作出，见上表）。",
     "§7.2: the 'this battery cannot measure complementarity' ruling"),

    # ---------------------------------------------------------------- item 3: conclusions
    ("> 在测过的**三个**任务区制上，**异种判定器不提供增量覆盖**。其中一个区制上 LLM 严格占优（仅 LLM 对 26 / 仅判定器对 0）；",
     "> 在测过的**三个**任务区制上，**异种判定器不提供增量覆盖**。其中一个区制上 LLM 严格占优（强制选择臂：仅 LLM 对 26 / 仅判定器对 0；"
     "**⚠️ 同一 48 条电池的散文臂是 25 / 1，Δ_catch = +0.0435——该区制唯一的可测 Δ_catch 为正，见 §7.2**）；",
     "§7.5 conclusion: the regime-1 arm split"),

    ("1. **区制一存在上限效应**（LLM 48/48），故其证据**不能证明无互补**；",
     "1. **区制一的上限效应只出现在强制选择臂**（LLM 48/48）；**散文臂上 LLM 46/48、仅判定器对 1 条，Δ_catch = +0.0435（Newcombe 95% CI [−0.386, +0.471]），点估计为正但只基于 2 条 LLM 错项** "
     "⇒ 该臂同样**不能证明无互补**，而它**能**给出一个（不精确的）**正向**点估计；本节其余结论建立在**强制选择臂**的「仅判定器对 0」之上，该读数不受此更正影响；",
     "§7.9 limits: regime 1"),

    # ---------------------------------------------------------------- item 2: p-value convention
    ("单侧 p = 0.052 / 0.043 / 0.103 ⇒ **「低于边际」是点估计，不是已确立的不等式**；",
     "单侧 p = **0.052 / 0.043 / 0.103（正态近似，未加连续性校正）** ⇒ **「低于边际」是点估计，不是已确立的不等式**；"
     "**⚠️ 检验口径必须写明（第九轮更正，ERRATA §10.1 第 2 项）**：这三个数此前未标注口径，读者无法知道用的是哪种检验。"
     "**同一组 `(x, n, 基线 0.2941)` 的精确二项下尾为 0.076 / 0.061 / 0.149**——**两种口径下没有一次显著**。"
     "两个口径均由 `src\\analysis\\p28_recompute_all_stats.py` 从产物重算，写入 `results\\P28-recomputed-statistics.json` 的 "
     "`regime3[*].vs_marginal_one_sided`（同处记录 `exact_binomial_lower_tail` 与 `normal_approximation` 两个字段）；"
     "**⚠️ 不要与同处的 Fisher 精确 p（0.086 / 0.049 / 0.163）混为一谈——那是 2×2 表上的另一项检验**；",
     "§7.6.1(b): the unlabelled normal approximation (ERRATA 10.1 item 2)"),
]

# The prose-arm block is inserted as part of an edit above; this asserts it really landed,
# because a fix that reports OK while inserting nothing is the failure this project named.
REQUIRED = [
    ("08-results-D-draft.md", "complementarity_prose_arm"),
    ("08-results-D-draft.md", "Δ_catch** | **+0.0435**"),
    ("08-results-D-draft.md", "0.076 / 0.061 / 0.149"),
    ("08-results-D-draft.md", "正态近似，未加连续性校正"),
]


def main() -> int:
    p = PAPER / D
    t = p.read_text(encoding="utf-8")
    ok = miss = 0
    for old, new, label in EDITS:
        if old in t:
            t = t.replace(old, new, 1)
            print(f"  ok    {label}")
            ok += 1
        else:
            print(f"  MISS  {label}")
            miss += 1

    p.write_text(t, encoding="utf-8")

    for fname, needle in REQUIRED:
        if needle in (PAPER / fname).read_text(encoding="utf-8"):
            print(f"  ok    post-condition: {fname} contains {needle!r}")
        else:
            print(f"  MISS  post-condition: {fname} does not contain {needle!r}")
            miss += 1

    print(f"\n{ok} applied, {miss} not found")
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main())

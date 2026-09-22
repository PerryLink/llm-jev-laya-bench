"""Propagate the regime-1 correction to every summary that repeated the old claim.

WHY THIS IS A SEPARATE STEP
---------------------------
The same defect shape has now been caught three times in this project: a claim is corrected
in the section that owns it and left standing in the sections that quote it. `results/ERRATA.md`
section 10 documents two rounds where that happened (the P26 control-arm retraction; the
section-8 error-compounding sentence), and `verify_all.py`'s J1 check exists because of it.

Adding P14's prose arm in section 7.2 (p71) makes three OTHER places false, because they
summarise regime 1 from the forced-choice arm alone:

  * the abstract's bullet list of the three regimes;
  * the introduction's regime table and its lead sentence;
  * section 9.6 "do not assume complementarity, measure it first".

A NEW DEFECT FOUND WHILE DOING THIS (reported, not hidden)
----------------------------------------------------------
The introduction's lead sentence ended "...and the failure correlation is significantly
positive". That wording was WITHDRAWN in section 8.6.1 ("...故「φ 显著为正」这一表述不成立，
本节及摘要均已删去「显著」二字"), and the abstract carries the qualification -- but the
introduction kept the withdrawn word. The withdrawal guard (J1 /
`p49_verify_withdrawals.py`) did not catch it because it greps for the retraction's exact
strings in specific files, and this instance is a different sentence. Fixed here.

Same sentence also called regimes 1 and 2 "unmeasurable" without distinguishing the two ARMS
of regime 1, which is no longer tenable once the prose arm is on the record.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

EDITS: list[tuple[str, str, str, str]] = [
    # ------------------------------------------------------------------ abstract
    ("00-abstract-draft.md",
     "- **权威定位**：LLM 48/48 全对，判定器 0.4583，**未捕获任何 LLM 漏掉的条目**；",
     "- **权威定位**：**强制选择臂** LLM 48/48 全对，判定器 0.4583，**未捕获任何 LLM 漏掉的条目**；"
     "**⚠️ 同一 48 条电池的散文臂相反**：LLM **46/48**，**仅判定器对 1 条**，**Δ_catch = +0.0435**"
     "（95% CI [−0.386, +0.471]，基于 **2** 条 LLM 错项）。**在三个区制的区制级读数中，这是唯一一个为正的 Δ_catch 点估计**，论文如实报告，"
     "并同时给出它的宽度与分母（§8.2）；",
     "abstract: regime-1 bullet"),

    # ------------------------------------------------------------------ introduction
    ("01-intro-02-related-draft.md",
     "**在三个任务区制上，答案是否定的**（§8）：前两个区制 LLM 触顶使其错误结构**不可测量**，第三个区制上限已破除、**真值修复后重判**，Δ_catch 一致为负且**失败相关显著为正**：",
     "**在三个任务区制上，答案是否定的**（§8）：区制一**的两个作答格式给出不同答案**——强制选择臂 LLM 48/48（错误结构不可测量），"
     "**散文臂可测，且其 Δ_catch 点估计为 +0.0435（正的，区间跨 0）**；区制二 LLM 触顶（0.750–0.900）使其错误结构稀薄，但 **4/4 次抽样 Δ_catch 为负**；"
     "第三个区制上限已破除、**真值修复后重判**，Δ_catch 一致为负，**失败相关池化 3/3 次为正**"
     "（**⚠️ 第九轮更正**：原句在此印「失败相关**显著**为正」——该措辞已在 §8.6.1 撤回（按难度分层后三次均不显著），本处为漏改；见 §8.6.1）：",
     "intro: the three-regime lead sentence"),

    ("01-intro-02-related-draft.md",
     "| 权威定位 | **1.0000** | 0.4583 | **0** | 26 | 不可定义（LLM 零错）|",
     "| 权威定位（**强制选择臂**） | **1.0000** | 0.4583 | **0** | 26 | 不可定义（LLM 零错）|\n"
     "| 权威定位（**散文臂**，同一 48 条） | **0.9583** | 0.4583 | **1** | **25** | **+0.0435**（区间跨 0）|",
     "intro: the regime table"),

    ("01-intro-02-related-draft.md",
     "→ **因此本文的增量不是「首次使用非生成式判别器做第一层」**（该做法已有先例），**而是**：把它当作**受控的第一层**，与前沿生成器在**同一批冻结条目**上做**配对互补性**检验，并报告**未发现**增量覆盖。",
     "→ **因此本文的增量不是「首次使用非生成式判别器做第一层」**（该做法已有先例），**而是**：把它当作**受控的第一层**，与前沿生成器在**同一批冻结条目**上做**配对互补性**检验，"
     "并报告**未发现已确立的**增量覆盖（**⚠️ 第九轮限定**：区制一的散文臂给出一个**正的**、但区间跨 0 的点估计，故「未发现」不得读作「不存在」，见 §8.2）。",
     "intro: the increment sentence"),

    # ------------------------------------------------------------------ discussion 9.6
    ("09-10-11-discussion-limits-repro-draft.md",
     "**依据**（§7）：**三个**区制上，异种判定器均未提供增量覆盖——\n"
     "- 区制一（权威定位，n=48）：它**未捕获任何** LLM 漏掉的条目（仅判定器对 **0**，对比仅 LLM 对 **26**）；",
     "**依据**（§7）：**三个**区制上，异种判定器均未提供**已确立的**增量覆盖——\n"
     "- 区制一（权威定位，n=48）：**强制选择臂**上它**未捕获任何** LLM 漏掉的条目（仅判定器对 **0**，对比仅 LLM 对 **26**）；"
     "**⚠️ 但同一 48 条电池的散文臂上 LLM 错 2 条、判定器捕获其中 1 条，Δ_catch = +0.0435（区间跨 0）**"
     "——故本节的措辞只能是「未确立增量覆盖」，不能是「无增量覆盖」（§8.2）；",
     "§9.6: the regime-1 bullet"),
]

REQUIRED = [
    ("00-abstract-draft.md", "+0.0435"),
    ("01-intro-02-related-draft.md", "散文臂"),
    ("01-intro-02-related-draft.md", "显著"),
    ("09-10-11-discussion-limits-repro-draft.md", "+0.0435"),
]

# `显著为正` must not survive ANYWHERE except inside a retraction, because the claim was
# withdrawn in 8.6.1 and the flag in verify_all's J1 is about exactly this failure mode.
RETIRE = ("已撤回", "撤回", "原印", "早期版本", "不再", "不成立")


def main() -> int:
    ok = miss = 0
    for entry in EDITS:
        fname, old, new, label = entry
        p = PAPER / fname
        t = p.read_text(encoding="utf-8")
        # The full replacement string is not a usable "already applied" sentinel here: these
        # lines have since been EDITED BY ANOTHER WRITER (a concurrent round), so the exact
        # `new` text no longer matches while the correction itself is present. The sentinel is
        # therefore the distinctive fragment the edit introduced -- the value it added -- and
        # the post-conditions below check the substance. A guard on the whole string would
        # report MISS on a file that is correct, which is the failure this project keeps
        # rediscovering.
        sentinel = new[len(old):] if new.startswith(old) else new[:60]
        if sentinel and sentinel in t:
            print(f"  ok    {label} (already applied, in the concurrent round's wording)")
            ok += 1
        elif old in t:
            p.write_text(t.replace(old, new, 1), encoding="utf-8")
            print(f"  ok    {label}")
            ok += 1
        else:
            print(f"  MISS  {label} -- neither the original text nor the correction is present")
            miss += 1

    for fname, needle in REQUIRED:
        t = (PAPER / fname).read_text(encoding="utf-8")
        if needle in t:
            print(f"  ok    post-condition: {fname} contains {needle!r}")
        else:
            print(f"  MISS  post-condition: {fname} lacks {needle!r}")
            miss += 1

    # the withdrawn word must be gone from the introduction, and if it survives anywhere in
    # the drafts it must sit next to a retirement marker
    for f in sorted(PAPER.glob("*-draft.md")):
        for i, line in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
            if "显著为正" in line and not any(m in line for m in RETIRE):
                print(f"  MISS  withdrawn wording without a retirement marker: "
                      f"{f.name}:{i}: {line.strip()[:70]}")
                miss += 1
    if not miss:
        print("  ok    no instance of the withdrawn 'failure correlation is significant' "
              "survives without its retraction")

    print(f"\n{ok} applied, {miss} problems")
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main())

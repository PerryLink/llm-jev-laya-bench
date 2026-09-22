"""Fix four provenance defects found by sentence-level tracing of section 5.

Each fix REMOVES a claim the artifacts do not support, rather than renumbering it. In every
case the honest statement is weaker than what was printed, and in every case the artifact
already contained what was needed to see that.

DEFECT 1 -- THE "SECOND RUN" DOES NOT EXIST AS A RUN.
  The paper's headline reproducibility finding is "同一脚本两次运行差异极大", with p50
  915 -> 1,192 ms (+30%), mean 1,001 -> 1,551 (+55%), max 1,802 -> 4,019 (+123%).
  915.1 is not a second run. It is the PRE-REPAIR value of a DERIVED field --
  `P27b-plugin-crossval.json.unmatched_direct_for_reference.p50_ms`, which is a copy of
  P27's own `latency.p50_ms`. The repair re-read that copy and it became 1191.8. No artifact
  anywhere records a Jev latency run with p50 = 915; the only `_superseded` copy of the P27
  artifact has a latency block BYTE-IDENTICAL to the current one.
  Worse, the +30/+55/+123 deltas compare statistics of DIFFERENT TYPES: a pre-repair p50
  against a post-repair mean, and a per-run max against a POOLED max. So none of the three is
  a run-to-run delta even if two runs had happened.
  What survives: one artifact-backed live run (n=20, p50 1191.8, mean 1550.6, max 4018.6), a
  pooled n=35 median of 1073.4 (P27-summary), and a mismatch between an earlier REPORT and the
  artifact -- which is a documentation gap, not a measured reproducibility finding.

DEFECT 2 -- THE LLM COST CEILING IS THE WRONG BATTERY'S.
  The paper prints "$0.0000326-$0.0000566". The floor is right; the ceiling is not a maximum
  of anything. P14's own 96 calls have max $0.00009645 -- 1.70x higher, so the printed ceiling
  understates by 70.4%. $0.0000484, printed as the range's midpoint, is a MEAN and exceeds
  nothing. The paper's own retroactive provenance block already recorded the correct pair.

DEFECT 3 -- THE JEV FLOOR IS ONE SUBSET'S MINIMUM.
  Printed $0.0000146; the family minimum across the artifact is $0.0000142 (truth-battery
  T7/T8). 2.8% low, and the paper prints four decimals elsewhere.

DEFECT 4 -- "OPTIMISTIC BY 12x" CONTRADICTS ITS OWN TABLE.
  The batch figure is 3.2 ms amortised on the sidecar's SELF-REPORTED 30.0 ms. Against the
  wall median the paper actually uses (37.4 ms) the factor is 11.7x; on the table's own basis
  it is 9.4x. 12 is reachable only by dividing the wall value by the self-reported batch
  figure -- mixing the two bases the surrounding text insists must not be mixed.

DEFECT 5 -- AN UNBACKED CONTROL ARM, AND IT IS LOAD-BEARING.
  Section 5.3.2's verdict ("truncation harm is real") rests on a control arm reported as
  "状态 79-92 token, truncated=false, 6/10 答更正后 / 4/10 答更正前, Fisher p = 0.011". None
  of those numbers exists in any artifact, script, or spend record -- only in paper prose and
  in AUDIT-FINDINGS.md. And 79-92 tokens is EXACTLY the state size of P26's own DISCARDED
  first prototype, which the probe report says "根本没有可截断的东西". So the tree cannot
  distinguish a new control run from the discarded prototype's numbers.
  The claim is therefore WITHDRAWN, not renumbered: the subsection keeps what P26's artifact
  actually shows and states that the isolating control was not persisted.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

FIXES: list[tuple[str, str, str]] = [
    # ---- DEFECT 1 -------------------------------------------------------------------
    ("05-results-A-draft.md",
     "| **Jev**（openrouter） | **~0.9–1.2 s**（两次独立运行 915 / 1,192 ms） | 1,001 / 1,551 ms | 1,802 / 4,019 ms | **20 / 20** | **墙体；单次运行波动大，见脚注 1** |",
     "| **Jev**（openrouter） | **1,192 ms**（n=20，**唯一有产物的一次运行**；合并 n=35 的中位 1,073 ms） | 1,551 ms | 4,019 ms | **20** | **墙体；单次抽样，见脚注 1** |"),
    # ---- DEFECT 4 -------------------------------------------------------------------
    ("05-results-A-draft.md",
     "引用 3.2 ms 会乐观 12 倍",
     "引用 3.2 ms 会乐观 **11.7 倍**（对墙体中位 37.4 ms；若按该表自身的摊销基准 30.0 ms 则为 **9.4 倍**——**两个基准不可混用**，早期版本印的「12 倍」正是把墙体值除以自报批量值得来的）"),
    # ---- DEFECT 2 -------------------------------------------------------------------
    ("05-results-A-draft.md",
     "$0.0000326–$0.0000566",
     "$0.0000326–**$0.00009645**"),
    # ---- DEFECT 5 -------------------------------------------------------------------
    ("05-results-A-draft.md",
     "**复核时补做了缺失的对照**：去掉填充使更正落入窗口（状态 79–92 token）后，Laya **答对 6/10、答错 4/10** ⇒ 截断把「答更正前」的比例从 **0.40 抬到 1.00（Fisher p = 0.011）**。",
     "**⚠️ 本小节的一处定量断言已【撤回】（第七轮）**：早期版本在此写「复核时补做了缺失的对照……Laya 答对 6/10、答错 4/10 ⇒ 截断把比例从 0.40 抬到 1.00（Fisher p = 0.011）」。**这组数字在整棵树中没有任何产物**——没有行、没有脚本、没有花费记录，只存在于论文正文与 `protocol\\AUDIT-FINDINGS.md`。**且其状态规模（79–92 token）恰好等于 P26 自己【已废弃的首版原型】的状态规模**，而该原型的报告原文是「根本没有可截断的东西」。故**本树无法区分「一次新的对照运行」与「被丢弃原型的数字」**。按本项目自己的标准（**无产物的数字不可作为证据**），该断言**撤回**。"),
]

WITHDRAWAL_NOTE = """
> **本小节现在能说的与不能说的**：P26 的**产物**显示两臂在 512 token 的可见前缀上**逐位相同**、且更正位于窗口之外（构造的必然）；**能证明「截断会发生」**（P24：60 步只有 14 步能塞进窗口；P26：20 次调用全部 `in_pad = 512`、`truncated = true`）。
> **不能证明「截断改变了答案」**——那需要一个把更正移入窗口的对照，而该对照**未被持久化**。
> ⇒ 故本小节的结论**降级为「截断确实发生，其伤害未能与位置效应分离」**。
"""


def main() -> int:
    applied = missed = 0
    for fname, old, new in FIXES:
        p = PAPER / fname
        t = p.read_text(encoding="utf-8")
        if old not in t:
            print(f"  MISS  {fname}: {old[:66]}...")
            missed += 1
            continue
        p.write_text(t.replace(old, new, 1), encoding="utf-8")
        print(f"  ok    {fname}: {old[:66]}...")
        applied += 1

    # the withdrawal note goes right after the sentence that carried the claim
    p = PAPER / "05-results-A-draft.md"
    t = p.read_text(encoding="utf-8")
    anchor = "按本项目自己的标准（**无产物的数字不可作为证据**），该断言**撤回**。"
    if anchor in t and WITHDRAWAL_NOTE.strip() not in t:
        t = t.replace(anchor, anchor + "\n" + WITHDRAWAL_NOTE, 1)
        p.write_text(t, encoding="utf-8")
        print("  ok    05-results-A-draft.md: withdrawal note appended")

    # the abstract carries the same two claims
    p = PAPER / "00-abstract-draft.md"
    t = p.read_text(encoding="utf-8")
    for old, new in [
        ("$0.0000326–$0.0000566", "$0.0000326–**$0.00009645**"),
        ("Jev 为**独立墙钟**，两次同脚本运行 p50 分别为 915 与 1,192 ms，**token 与成本逐位相同而延迟相差 30–123%**，故这是一个区间而非单值",
         "Jev 为**独立墙钟**，n=20 单次运行 p50 为 1,192 ms（合并 n=35 的中位为 1,073 ms）；**该轴只有一次有产物的运行，故不报告运行间极差**"),
        ("cross-language**——三者的并列依据见 §7.5/§7.7", "cross-language**——三者的并列依据见 §7.5/§7.7"),
    ]:
        if old in t:
            t = t.replace(old, new, 1)
            print(f"  ok    00-abstract-draft.md: {old[:52]}...")
    p.write_text(t, encoding="utf-8")

    # and section 1 / the discussion draft repeat the latency framing
    for fname in ("01-intro-02-related-draft.md", "09-10-11-discussion-limits-repro-draft.md"):
        p = PAPER / fname
        t = p.read_text(encoding="utf-8")
        old = "Jev 侧同一脚本两次运行 p50 为 915 与 1,192 ms"
        if old in t:
            t = t.replace(old, "Jev 侧**只有一次有产物的运行**（n=20，p50 1,192 ms；合并 n=35 的中位 1,073 ms），**运行间极差不可报告**", 1)
            p.write_text(t, encoding="utf-8")
            print(f"  ok    {fname}: latency framing")

    print(f"\n{applied} applied, {missed} not found")
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main())

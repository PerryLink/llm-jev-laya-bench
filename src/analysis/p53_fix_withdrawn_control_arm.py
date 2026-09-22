"""Fix the withdrawn P26 control arm, which is still asserted as fact in four places.

WHAT WAS FOUND
    Section 5.3.2's control arm -- state 79-92 tokens, 6/10 and 4/10, Fisher p = 0.011 -- was
    WITHDRAWN because it has no artifact and its state size matches a discarded prototype.
    The withdrawal was written at lines 188-190. But three OTHER lines went on asserting the
    same numbers as established fact:

        line 187  "truncation really does raise the proportion: 0.40 -> 1.00 (p = 0.011).
                   The truncation harm is real."
        line 194  "truncation really does raise the error rate (0.40 -> 1.00, p = 0.011)"
        line 197  "RULING: truncation happens (P24) and it also raises the error rate
                   (this control arm, p = 0.011), but it is a partial cause"

    Line 197 is the section's VERDICT. So the section withdrew its evidence and then ruled on
    it anyway -- four lines later.

    A fifth place, the section 5.4 summary table, still explains the latency ratio as taken
    from "Jev's two runs", which the seventh round withdrew.

WHY THE GUARD MISSED IT
    The J1 guard looks for the SPECIFIC STRINGS an auditor named. These lines use the numbers
    without the phrase "6/10 of the effect comes from truncation", so the patterns did not
    match. Same lesson as the ratio-basis fix: a retraction propagated against words, not
    against the claim.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

W = "**⚠️ 已于第七轮撤回**："
E = "**⚠️ WITHDRAWN in the seventh round**: "

ZH = [
    (PAPER / "05-results-A-draft.md",
     "⇒ **截断确实抬高「答更正前」的比例：0.40 → 1.00（Fisher 精确双侧 p = 0.011）。截断伤害是真的。**",
     "⇒ " + W + "早期版本在此写「截断确实抬高『答更正前』的比例：0.40 → 1.00（Fisher p = 0.011）。"
     "**截断伤害是真的**」。**这组数字（含 p = 0.011）没有任何产物**，其状态规模恰等于 P26 已废弃的原型，"
     "**故不得作为结论**。下方第 2 条与「裁定」两处同样使用该数字，一并撤回。",
     "line 187 the headline assertion"),
    (PAPER / "05-results-A-draft.md",
     "2. **截断确实抬高错误率（0.40 → 1.00，p = 0.011），但 P26 原设计的「两臂同答」不足以证明它**——那是构造必然。",
     "2. **⚠️ 撤回**：早期版本在此写「截断确实抬高错误率（0.40 → 1.00，p = 0.011）」——**该对照臂无产物**，见上。"
     "**仍成立的部分**：P26 原设计的「两臂同答」**是构造的必然**，不足以证明任何因果。",
     "line 194 the numbered assertion"),
    (PAPER / "05-results-A-draft.md",
     "**裁定**：**截断会发生（P24），也会抬高错误率（本对照臂，p = 0.011），但它是部分原因**——"
     "另有 4/10 的失败发生在证据完全可见时，说明除窗口之外还有第二个失效通道。",
     "**裁定（第七轮修订）**：**截断会发生（P24，有产物）**；**但「截断抬高错误率」所依据的对照臂无产物，"
     "故该因果关系不予断言**。早期版本的裁定写「也会抬高错误率（本对照臂，p = 0.011），但它是部分原因」"
     "并援引「另有 4/10 的失败发生在证据完全可见时」——**两处数字均已随该对照臂撤回**。"
     "⇒ **最终裁定：截断确实发生；其伤害未能与位置效应分离。**",
     "line 197 THE VERDICT"),
    (PAPER / "05-results-A-draft.md",
     "，下沿/上沿分别取自 Jev 的两次运行）",
     "，下沿/上沿分别取自合并 n=35 的中位与唯一有产物的那次运行——**两次运行的说法已于第七轮撤回**）",
     "line 206 the section 5.4 table cell"),
]

EN = [
    (PAPER / "en" / "05-results-A.md",
     "**truncation really does raise the proportion answered pre-correction: 0.40 -> 1.00 (two-sided Fisher exact p = 0.011). The truncation harm is real.**",
     E + "an earlier version wrote that truncation really does raise the proportion: 0.40 -> 1.00 "
     "(Fisher p = 0.011) and that **the truncation harm is real**. **These numbers, including "
     "p = 0.011, have no artifact**; their state size matches P26's discarded prototype, so they "
     "**must not stand as a conclusion**. The numbered item below and the Ruling both used the "
     "same number and are withdrawn with it.",
     "EN: the headline assertion"),
    (PAPER / "en" / "05-results-A.md",
     "**truncation really does raise the error rate (0.40 -> 1.00, p = 0.011), but P26's original \"both arms answer alike\" design cannot establish it**",
     "**WITHDRAWN**: an earlier version wrote that truncation really does raise the error rate "
     "(0.40 -> 1.00, p = 0.011) -- **that control arm has no artifact**, see above. **What still "
     "holds**: P26's original \"both arms answer alike\" design is a construction necessity and "
     "establishes no causation.",
     "EN: the numbered assertion"),
    (PAPER / "en" / "05-results-A.md",
     "the lower/upper bounds are taken from Jev's two runs respectively",
     "the lower and upper bounds are taken from the pooled n=35 median and from the one run that "
     "has an artifact, respectively -- **the two-run account was withdrawn in the seventh round**",
     "EN: the section 5.4 table cell"),
]

ok = miss = 0
for path, old, new, label in ZH + EN:
    if not path.exists():
        print(f"  SKIP  {label} (no such file)")
        continue
    t = path.read_text(encoding="utf-8")
    if old in t:
        path.write_text(t.replace(old, new, 1), encoding="utf-8")
        print(f"  ok    {label}")
        ok += 1
    else:
        print(f"  MISS  {label}")
        miss += 1

print(f"\n{ok} applied, {miss} not found")
sys.exit(1 if miss else 0)

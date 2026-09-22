"""Fix defects found by the section-8 trace audit.

Nine findings. The four fixed here are the ones that change what the paper ASSERTS; the
rest are recorded in the report for the next pass.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER, RESULTS  # noqa: E402

D = PAPER / "08-results-D-draft.md"
t = D.read_text(encoding="utf-8")
ok = miss = 0


def sub(old: str, new: str, label: str) -> None:
    global t, ok, miss
    if old in t:
        t = t.replace(old, new, 1)
        print(f"  ok    {label}")
        ok += 1
    else:
        print(f"  MISS  {label}")
        miss += 1


# ---- 1. SIGN ERROR. The 68-item cluster correlation is +0.243, and the paper's own
#         next clause says the pooled correlation is positive. An independent
#         recomputation gives r = +0.2432 with a permutation p of 0.0568.
sub("相关 −0.243", "相关 **+0.243**", "sign of the 68-item cluster correlation")

# ---- 2. THE RETRACTION WAS NOT PROPAGATED. Line 316 withdrew the P26 control arm, but
#         three later lines still assert its numbers as fact.
sub("该效应约 **6/10 来自截断**", "该效应**未能与位置效应分离**（原印「约 6/10 来自截断」已撤回）",
    "propagate: 6/10 assertion")
sub("另 **4/10 是「更正完全可见却未被采纳」**", "原印「另 4/10 是『更正完全可见却未被采纳』」亦一并撤回",
    "propagate: 4/10 assertion")
sub("那 4/10 上证据**在场**", "（该拆分已撤回：所依据的对照臂无产物）",
    "propagate: the 4/10 explanation")

# ---- 3. MISATTRIBUTION. The "Wald is narrower because of a zero cell" explanation is a
#         REGIME-2 fact; regime 3 has no zero cell (its cells are 17/29/3/19 etc.).
sub("(Wald narrower because of a zero cell)", "(regime 3's Wald interval is narrower for a different reason: its cell counts are 17/29/3/19, none zero — the zero-cell explanation belongs to regime 2 and was copied here in error)",
    "misattributed zero-cell explanation")
sub("（Wald 更窄因为零格）",
    "（**⚠️ 更正：本区制没有零格**——其三格为 17/29/3/19。零格是**区制二**的情形，此处系误植）",
    "misattributed zero-cell explanation (zh)")

# ---- 4. THE EXACT UPPER BOUNDS. 0.602 / 0.522 are the 97.5% one-sided bounds, not the
#         95% one-sided bounds P28 stores (0.5271 / 0.4507). And "compatible with Δ_catch
#         up to +0.35" is not a valid interval -- Newcombe's upper bounds are +0.253/+0.192.
sub("0/4 的精确上界为 **0.602**、0/5 为 **0.522**，即数据与高达 +0.35 的 Δ_catch 相容",
    "0/4 的 **95% 单侧精确上界为 0.527**、0/5 为 **0.451**（`P28-recomputed-statistics.json`；"
    "早期版本印的 0.602 / 0.522 是 **97.5% 单侧**界，对应双侧 95%）。"
    "**⚠️ 但不能就此说「数据与高达 +0.35 的 Δ_catch 相容」**——该说法不是任何区间："
    "**Newcombe 的上界为 +0.253（r1）与 +0.192（r3）**，这才是与数据相容的上限",
    "exact upper bounds and the invalid +0.35 claim")

D.write_text(t, encoding="utf-8")

# ---- 5. THE VERIFY GUARD MISSED THE MANUSCRIPT. The guard looks for "3次中2次CI排除零",
#         but the §9.6 line inserts "95%" between the numbers, so it slipped through.
V = PAPER / "verify_all.py"
v = V.read_text(encoding="utf-8")
old_guard = '    absent("zero-cell CI caveat is never dropped", "3次中2次CI排除零", unless_near=retire)'
new_guard = ('    # NOTE: the earlier guard looked for the exact string "3次中2次CI排除零" and\n'
             '    # MISSED the manuscript, which writes "3 次中 2 次 95% CI 排除零" -- the "95%"\n'
             '    # between the numbers defeated a literal match. Normalise before matching.\n'
             '    _flat_ci = re.sub(r"[\\s%95]", "", flat)\n'
             '    if "3次中2次CI排除零" in _flat_ci or "3次中2次CI排除0" in _flat_ci:\n'
             '        fail("C zero-cell CI caveat is never dropped",\n'
             '             "an unqualified \\"2 of 3 CIs exclude 0\\" survives in the text")\n'
             '    else:\n'
             '        ok("C zero-cell CI caveat is never dropped", "no unqualified form")')
if old_guard in v:
    V.write_text(v.replace(old_guard, new_guard, 1), encoding="utf-8")
    print("  ok    verify_all.py: guard now normalises whitespace and the stray 95%")

# ---- 6. P22f ARTIFACT BUG: the report says legacy_option_sets false for the P22b files,
#         but they were built with legacy_options=True. The published flags confirm it.
F = RESULTS / "P22f-ignore-superseded-denominator-repair.json"
if F.exists():
    doc = json.loads(F.read_text(encoding="utf-8"))
    fixed = 0
    for name, rec in doc.get("artifacts", {}).items():
        if name.startswith("P22b") and rec.get("legacy_option_sets") is False:
            rec["legacy_option_sets"] = True
            rec["_legacy_flag_correction"] = (
                "This flag read `false` and was WRONG. The P22b artifacts were reconstructed "
                "with `build_items(legacy_options=True)` (p22f_repair_denominator.py:200), and "
                "the published alt_in_options flags match the LEGACY construction on 68/68 "
                "items while differing from the new construction on 5 (CH-K4-005/015/018, "
                "CH-K8-021, CH-K16-012). The 61-item denominator the paper uses is therefore "
                "correct; only this descriptive flag was wrong.")
            fixed += 1
    if fixed:
        F.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  ok    P22f: corrected legacy_option_sets on {fixed} record(s)")

print(f"\n{ok} applied, {miss} not found")
sys.exit(1 if miss else 0)

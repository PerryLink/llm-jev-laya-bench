"""Fix a residual of the withdrawn "two runs" claim, in both languages.

WHAT WENT WRONG
    Round 6 fixed the latency ratio: "25-29x" took its low end from one run and its high end
    from the POOLED median, mixing two quantities. The fix stated the basis as "the first run
    (p50 915 ms)" and "the second run (p50 1,192 ms)".

    Round 7 then WITHDREW the claim that two runs exist at all: 915 ms is the pre-repair value
    of a DERIVED field, and only one run has an artifact.

    So the round-6 text now asserts the very thing round 7 retracted. It survived because the
    phrasing differs -- "first run / second run" rather than "two independent runs" -- so the
    J1 guard's patterns did not match it. This is the same failure the J1 guard exists to
    catch, one level down.

THE CORRECT STATEMENT
    * one artifact-backed run: n=20, p50 1,191.8 ms  -> ratio 31.9x
    * a pooled n=35 median, 1,073.4 ms, assembled from n=20 and n=15 collections at DIFFERENT
      state sizes -> ratio 28.7x
    * 915 ms survives only as a value in an earlier REPORT whose artifact was not kept, so the
      24.5x derived from it is NOT artifact-backed
    The honest range is therefore 28.7x-31.9x on artifact-backed numbers, with 24.5x marked
    as resting on an unkept measurement.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

ZH_5 = "**区间下沿 24.5 倍取自第一次 Jev 运行（p50 915 ms），上沿 31.9 倍取自第二次（p50 1,192 ms）**；合并 n=35 的中位为 28.7 倍。"
ZH_5_NEW = ("**区间只能取自有产物的数字：下沿 28.7 倍取自合并 n=35 的中位（1,073.4 ms），"
            "上沿 31.9 倍取自唯一有产物的那次运行（n=20，p50 1,191.8 ms）**。"
            "**⚠️ 早期版本在此写「下沿取自第一次运行、上沿取自第二次」——那两次运行的说法已于第七轮撤回"
            "（915.1 ms 是派生字段的修复前取值，不是一次运行），故 24.5 倍一并撤回**："
            "它依赖的 915 ms 只存在于一份**产物未被保留**的早期报告。")

ZH_1 = "**区间取自 Jev 侧的两次同脚本运行**：24.5 倍（p50 915 ms）至 31.9 倍（p50 1,192 ms）；合并 n=35 的中位为 28.7 倍）"
ZH_1_NEW = ("**区间取自有产物的数字**：28.7 倍（合并 n=35 的中位 1,073.4 ms）至 31.9 倍"
            "（唯一有产物的运行，n=20，p50 1,191.8 ms）。**⚠️ 早期版本写「取自两次同脚本运行」"
            "并给出下沿 24.5 倍——该说法已于第七轮撤回，见 §5.2 脚注 1**）")

FIXES = [
    (PAPER / "05-results-A-draft.md", ZH_5, ZH_5_NEW, "§5 the ratio basis (zh)"),
    (PAPER / "01-intro-02-related-draft.md", ZH_1, ZH_1_NEW, "§1 the ratio basis (zh)"),
]

ok = miss = 0
for path, old, new, label in FIXES:
    t = path.read_text(encoding="utf-8")
    if old in t:
        path.write_text(t.replace(old, new, 1), encoding="utf-8")
        print(f"  ok    {label}")
        ok += 1
    else:
        print(f"  MISS  {label}")
        miss += 1

# the English translation inherited the same error
en5 = PAPER / "en" / "05-results-A.md"
if en5.exists():
    t = en5.read_text(encoding="utf-8")
    old_en = ("**The interval's lower bound of 24.5× is taken from the first Jev run (p50 915 ms), "
              "and the upper bound of 31.9× from the second (p50 1,192 ms)**")
    new_en = ("**The interval can only be taken from artifact-backed numbers: the lower bound of "
              "28.7× from the pooled n=35 median (1,073.4 ms), and the upper bound of 31.9× from "
              "the one run that has an artifact (n=20, p50 1,191.8 ms)**. **⚠️ An earlier version "
              "wrote that the lower bound came from a first run and the upper from a second; that "
              "two-run account was withdrawn in the seventh round (915.1 ms is the pre-repair "
              "value of a derived field, not a run), so 24.5× is withdrawn with it** -- the 915 ms "
              "it rests on survives only in an earlier report whose artifact was not kept.")
    if old_en in t:
        en5.write_text(t.replace(old_en, new_en, 1), encoding="utf-8")
        print("  ok    §5 the ratio basis (en)")
        ok += 1
    else:
        # fall back to a looser match on the same sentence
        import re
        m = re.search(r"\*\*The interval's lower bound of 24\.5.{0,180}?second \(p50 1,192 ms\)\*\*", t)
        if m:
            en5.write_text(t[:m.start()] + new_en + t[m.end():], encoding="utf-8")
            print("  ok    §5 the ratio basis (en, loose match)")
            ok += 1
        else:
            print("  MISS  §5 the ratio basis (en)")
            miss += 1

print(f"\n{ok} applied, {miss} not found")
sys.exit(1 if miss else 0)

"""Fix the zero-cell misattribution in Regime 3 -- the last outstanding audit item.

THE DEFECT
    The section-8 audit found that a parenthetical explaining an interval as narrower "because of
    a zero cell" had been copied from REGIME 2 into REGIME 3. Regime 2 does have zero cells (two
    draws have judge-only-correct = 0). Regime 3 does NOT -- its cells are 17/29/3/19, none zero.

    A fix was written for this in p43 and BOTH its patterns reported MISS. I moved on. The
    misattribution survived, and was only caught again by the translator of section 8, who
    noticed that git showed the Regime-3 parenthetical being added by the very correction pass
    that was supposed to remove it.

    The lesson is not subtle: a fix that reports "not found" and is not chased is not a fix. Two
    of p43's seven patterns missed, and the other five were verified by the guard; these two were
    verified by nothing.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

ZH_OLD = "（3/3；未配对 Wald 下 2 次排除零，**但零格使该区间过窄，改用 Newcombe 后仅 1 次稳健排除、1 次在边界**"
ZH_NEW = ("（3/3；未配对 Wald 下 2 次排除零，**⚠️ 但该区间收窄的原因与区制二不同：本区制的格子是 "
          "17/29/3/19，没有零格**——零格是**区制二**的情形，早期版本把那条解释误植于此。"
          "改用 Newcombe 后**仅 1 次稳健排除、1 次在边界**")

EN_OLD = "under an unpaired Wald interval 2 of the 3 exclude zero, **but the zero cell makes that interval too narrow"
EN_NEW = ("under an unpaired Wald interval 2 of the 3 exclude zero, **but the reason this interval "
          "is narrower differs from regime 2's: this regime's cells are 17/29/3/19 and none is "
          "zero** -- the zero cell belongs to **regime 2**, and an earlier version misattributed "
          "that explanation here")

FIXES = [
    (PAPER / "08-results-D-draft.md", ZH_OLD, ZH_NEW, "ZH the regime-3 zero-cell claim"),
    (PAPER / "en" / "08-results-D.md", EN_OLD, EN_NEW, "EN the regime-3 zero-cell claim"),
]

ok = miss = 0
for path, old, new, label in FIXES:
    if not path.exists():
        print(f"  SKIP  {label} (file absent)")
        continue
    t = path.read_text(encoding="utf-8")
    if old in t:
        path.write_text(t.replace(old, new, 1), encoding="utf-8")
        print(f"  ok    {label}")
        ok += 1
    else:
        print(f"  MISS  {label}")
        # show the neighbourhood so the next attempt is not blind
        import re
        m = re.search(r".{0,60}零格.{0,90}", t) or re.search(r".{0,60}zero cell.{0,90}", t)
        if m:
            print(f"        nearby: {m.group(0)[:150]}")
        miss += 1

print(f"\n{ok} applied, {miss} not found")
sys.exit(1 if miss else 0)

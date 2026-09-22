"""Correct ERRATA section 10.1's file attributions, and record why they were wrong.

TWO ENTRIES NAMED THE WRONG FILE
    item 1  said the 0.9981 "highest confidence" claim is in 06-results-B-draft.
            It is in 07-results-C-draft.md:90.
    item 13 said the "eight live jev_check calls" line is in section 3.1.
            It is in 06-results-B-draft.md:150, which is section 3.5.

WHY THIS MATTERS MORE THAN A TYPO
    p44 and p45 both tried to fix these two items and BOTH REPORTED "not found" -- and I moved
    on, twice, without checking whether the pattern or the LOCATION was wrong. The location was
    wrong. ERRATA section 10.1 was the index I was searching against, so an error in the index
    silently converted two real defects into two apparent pattern mismatches.

    The project has a guard (J1) against a retraction that is not propagated. It has no guard
    against an INDEX that is wrong, and no habit of chasing a MISS. Both are recorded here.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import ROOT  # noqa: E402

p = ROOT / "results" / "ERRATA.md"
t = p.read_text(encoding="utf-8")

OLD1 = "| 1 | `06-results-B-draft`, the highest-confidence line |"
NEW1 = "| 1 | `07-results-C-draft.md:90` (section 6.2) -- **corrected file: this said `06-results-B-draft`** |"

OLD13 = "| 13 | `06-results-B-draft` 3.1 |"
NEW13 = ("| 13 | `06-results-B-draft.md:150` (section **3.5**, not 3.1) -- "
         "**corrected location** |")

ok = 0
for old, new in ((OLD1, NEW1), (OLD13, NEW13)):
    if old in t:
        t = t.replace(old, new, 1)
        ok += 1
        print(f"  ok    corrected: {old[:60]}")
    else:
        print(f"  MISS  {old[:60]}")

NOTE = """
### 10.5 Why two of these items survived four fix attempts

ERRATA 10.1 items 1 and 13 named the **wrong files**. Fix scripts `p44` and `p45` searched for
them, reported `MISS`, and moved on -- twice each -- on the assumption that the pattern did not
match. It did match; it was looked for in the wrong document.

The project has a guard (**J1**) against a retraction that fails to propagate. It has no guard
against an **index that is wrong**, and no habit of **chasing a MISS**. Both are now recorded,
because the failure was not that the defects were hard to find -- it is that a wrong entry in
this very table silently converted two real defects into two apparent pattern mismatches.

**Rule adopted**: a fix script that reports `MISS` is not finished. Either the pattern or the
location is wrong, and the difference must be established before moving on.
"""

if "### 10.5 Why two of these items" not in t:
    t = t.rstrip() + "\n" + NOTE
    print("  ok    section 10.5 added")

p.write_text(t, encoding="utf-8")
print(f"\n{ok}/2 corrections applied")

"""Fix the English regime-3 zero-cell misattribution (the Chinese is already fixed).

The English clause lives inside the long section-conclusion bullet, so the earlier
sentence-shaped patterns did not reach it. Matched here on the exact substring.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

p = PAPER / "en" / "08-results-D.md"
t = p.read_text(encoding="utf-8")

OLD = ("**but the zero cell makes that interval too narrow, and after switching to Newcombe "
       "only 1 robustly excludes and 1 sits at the boundary**")
NEW = ("**but the reason this interval is narrower differs from regime 2's: this regime's cells "
       "are 17/29/3/19 and none is zero -- the zero cell belongs to regime 2, and an earlier "
       "version misattributed that explanation here**; after switching to Newcombe **only 1 "
       "robustly excludes and 1 sits at the boundary**")

if OLD in t:
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("  ok    EN regime-3 zero-cell clause corrected")
    sys.exit(0)

print("  MISS  exact substring not found")
print("  nearby:", repr(t[t.find("zero cell makes that"):][:160]) if "zero cell makes that" in t
      else "no 'zero cell makes that' anywhere")
sys.exit(1)

"""Final pass: the English zero-cell fix, and the assembler's section-8 numbering.

Two independent misses, both of the same kind as earlier ones:

  1. The English translation of the regime-3 zero-cell clause uses different wording from the
     pattern I guessed, so the fix did not apply. The Chinese is already fixed, so the two
     languages currently disagree -- which is exactly the state the translation checks exist to
     prevent, except none of them compares PARAGRAPH CONTENT across languages.

  2. The English assembler expected section 8 to be numbered 8. The draft numbers it 7 (the
     assembler remaps 7->8). This is the SAME bug I fixed for results B/C an hour ago, in the
     same file, because I fixed the instance rather than auditing the whole SOURCES table.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

# ---- 1. the English zero-cell clause -------------------------------------------------
en = PAPER / "en" / "08-results-D.md"
t = en.read_text(encoding="utf-8")

NEW_EN = ("under an unpaired Wald interval 2 of the 3 exclude zero, **but the reason this "
          "interval is narrower differs from regime 2's: this regime's cells are 17/29/3/19 and "
          "none is zero** -- the zero cell belongs to **regime 2**, and an earlier version "
          "misattributed that explanation here. Under Newcombe **only 1 robustly excludes and 1 "
          "sits at the boundary**")

# find the regime-3 sentence: it mentions Newcombe and the 3 draws but is NOT the regime-2 note
pat = re.compile(
    r"unpaired Wald interval 2 of the 3 exclude zero[^。\n]{0,200}?"
    r"(?:zero cell|Newcombe)[^。\n]{0,200}", re.S)
m = pat.search(t)
if m:
    t = t[:m.start()] + NEW_EN + t[m.end():]
    en.write_text(t, encoding="utf-8")
    print("  ok    EN regime-3 zero-cell clause rewritten")
else:
    # fall back: locate by the surrounding regime-3 wording
    m2 = re.search(r"[^\n]{0,120}unpaired Wald[^\n]{0,240}", t)
    print("  MISS  EN pattern; nearby:", (m2.group(0)[:200] if m2 else "nothing"))

# ---- 2. the assembler's results-D numbering -------------------------------------------
A = PAPER / "en" / "_assemble.py"
a = A.read_text(encoding="utf-8")
OLD = '    ("08-results-D.md", ["8"], "Results D"),'
NEW = ('    # DRAFT numbering again: this draft calls itself section 7 and the assembler remaps\n'
       '    # 7 -> 8. Fixing only the results-B/C entry left this one wrong, which is what\n'
       '    # happens when an instance is fixed instead of the table audited.\n'
       '    ("08-results-D.md", ["7"], "Results D"),')
if OLD in a:
    A.write_text(a.replace(OLD, NEW, 1), encoding="utf-8")
    print("  ok    assembler: Results D numbering corrected to the draft's §7")
elif '("08-results-D.md", ["7"]' in a:
    print("  already correct")
else:
    print("  MISS  assembler entry")

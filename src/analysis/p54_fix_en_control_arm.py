"""Second pass on the English withdrawn-control-arm fix, matching on what is actually there."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

p = PAPER / "en" / "05-results-A.md"
t = p.read_text(encoding="utf-8")

E = "**WITHDRAWN in the seventh round**: "

SUBS = [
    # the Ruling is the section's VERDICT and still ruled on withdrawn evidence
    (r"\*\*Ruling\*\*:\s*\*\*truncation happens \(P24\) and it also raises the error rate \(this control arm, p = 0\.011\), but it is a partial cause\*\*[^\n]*",
     "**Ruling (revised in the seventh round)**: **truncation happens (P24, artifact-backed)**; "
     "**but the control arm behind \"truncation raises the error rate\" has no artifact, so that "
     "causal claim is NOT asserted.** An earlier version ruled that it \"also raises the error "
     "rate (this control arm, p = 0.011), but it is a partial cause\" and cited \"a further 4/10 "
     "of failures occurred with the evidence fully visible\" -- **both numbers are withdrawn with "
     "that arm**. => **Final ruling: truncation does happen; its harm was not separated from the "
     "position effect.**",
     "EN: THE VERDICT"),
    # any surviving live assertion of the p-value as evidence
    (r"(?<![Ww]ithdrawn)(?<![Nn]o artifact)[^\n]{0,40}\bp = 0\.011\b[^\n]{0,120}",
     E + "an earlier version asserted a control-arm result at `p = 0.011`; that arm has no "
     "artifact and its state size matches P26's discarded prototype, so the figure is withdrawn.",
     "EN: a surviving live p = 0.011"),
]

ok = miss = 0
for pat, new, label in SUBS:
    t2, n = re.subn(pat, new.replace("\\", "\\\\"), t, count=1)
    if n:
        t = t2
        print(f"  ok    {label}")
        ok += 1
    else:
        print(f"  MISS  {label}")
        miss += 1

p.write_text(t, encoding="utf-8")

# report any remaining unqualified p = 0.011 in either language
print()
for f in [PAPER / "05-results-A-draft.md", PAPER / "en" / "05-results-A.md",
          PAPER / "MANUSCRIPT.md"]:
    if not f.exists():
        continue
    for i, line in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
        if "0.011" in line and not re.search(r"撤回|withdrawn|WITHDRAWN", line):
            print(f"  REMAINING {f.name}:{i}  {line.strip()[:110]}")

print(f"\n{ok} applied, {miss} not found")
sys.exit(1 if miss else 0)

"""Final pass: withdraw the P26 control arm on the last English line that still asserts it."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

p = PAPER / "en" / "05-results-A.md"
lines = p.read_text(encoding="utf-8").split("\n")

NEW = (
    '2. **WITHDRAWN**: an earlier version wrote that truncation does raise the error rate '
    '(0.40 -> 1.00, p = 0.011). **That control arm has no artifact**, and its state size '
    "matches P26's discarded prototype. **What still holds**: P26's original \"both arms "
    'answer alike" design is a construction necessity and establishes no causation.'
)

fixed = 0
for i, l in enumerate(lines):
    if l.startswith("2. **Truncation does raise the error rate"):
        lines[i] = NEW
        print(f"  fixed EN line {i + 1}")
        fixed += 1

p.write_text("\n".join(lines), encoding="utf-8")
print(f"  {fixed} line(s) fixed")
sys.exit(0 if fixed else 1)

"""Correct the English abstract to match the section-5 withdrawals."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

p = PAPER / "en" / "00-abstract.md"
t = p.read_text(encoding="utf-8")
D = chr(36)
subs = [
    (f"{D}0.0000326\u2013{D}0.0000566", f"{D}0.0000326\u2013**{D}0.00009645**"),
    ("**1.19 s**", "**1.19 s** (one run of n=20; the pooled n=35 median is 1.07 s)"),
]
ok = miss = 0
for a, b in subs:
    if a in t:
        t = t.replace(a, b, 1)
        print(f"  ok    {a[:70]}")
        ok += 1
    else:
        print(f"  MISS  {a[:70]}")
        miss += 1
p.write_text(t, encoding="utf-8")
print(f"\n{ok} applied, {miss} not found")
sys.exit(1 if miss else 0)

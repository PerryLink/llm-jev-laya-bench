"""Compare the two Description values for completeness and agreement.

Raised because the two ended differently: the English body ends "...result above."
while the Chinese body ends with a boundary disclaimer ("we state our boundary
explicitly: all conclusions come from single-step decisions; long-horizon
autonomous running was NOT performed"). If the English version is missing that
paragraph, the two deposits would make different claims about scope -- and that
is a substantive difference, not a formatting one.

Checks:
  1. whether the Chinese boundary paragraph has an English counterpart;
  2. the tail of both bodies, side by side;
  3. that each body ends inside its own section rather than being cut short.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]

en_src = (ROOT / "paper" / "en" / "00-abstract.md").read_text(encoding="utf-8")
zh_src = (ROOT / "paper" / "00-abstract-draft.md").read_text(encoding="utf-8")

print("=" * 72)
print("CHINESE abstract body -- full text")
print("=" * 72)
lines = zh_src.splitlines()
start = next(i for i, l in enumerate(lines) if l.strip() == "## 摘要正文")
end = next(i for i in range(start + 1, len(lines))
           if lines[i].strip().startswith("## ") or lines[i].strip() == "---")
zh_body = "\n".join(lines[start + 1:end]).strip()
print(zh_body)

print()
print("=" * 72)
print("ENGLISH search for the boundary disclaimer")
print("=" * 72)
en_lines = en_src.splitlines()
for i, l in enumerate(en_lines, 1):
    if re.search(r"boundar|long-horizon|explicitly (state|declare)|does not carry|not executed",
                 l, re.I):
        print(f"  {i:>4}: {l.strip()[:110]}")

print()
print("=" * 72)
print("TAIL of each body (last 6 non-empty lines)")
print("=" * 72)
for label, path, head in (
    ("EN", ROOT / "paper" / "en" / "00-abstract.md", "## Abstract"),
    ("ZH", ROOT / "paper" / "00-abstract-draft.md", "## 摘要正文"),
):
    ls = path.read_text(encoding="utf-8").splitlines()
    s = next(i for i, l in enumerate(ls) if l.strip() == head)
    e = next(i for i in range(s + 1, len(ls))
             if ls[i].strip().startswith("## ") or ls[i].strip() == "---")
    body = [l for l in ls[s + 1:e] if l.strip()]
    print(f"\n[{label}] {len(body)} non-empty lines; last 6:")
    for l in body[-6:]:
        print(f"   {l.strip()[:105]}")

# Does the English abstract contain a sentence about scope limits at all?
print()
print("=" * 72)
en_body = "\n".join(l for l in en_lines[
    next(i for i, l in enumerate(en_lines) if l.strip() == "## Abstract") + 1:
    next(i for i in range(
        next(i for i, l in enumerate(en_lines) if l.strip() == "## Abstract") + 1,
        len(en_lines)) if en_lines[i].strip().startswith("## ")
        or en_lines[i].strip() == "---")
])
print(f"EN body chars {len(en_body):,} / ZH body chars {len(zh_body):,}")
print(f"EN mentions 'long-horizon'  : {en_body.lower().count('long-horizon')}")
print(f"ZH mentions '长线'          : {zh_body.count('长线')}")
print(f"ZH mentions '未执行'        : {zh_body.count('未执行')}")
print(f"EN mentions 'not executed'  : {en_body.lower().count('not executed')}")

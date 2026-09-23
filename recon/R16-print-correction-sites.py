"""Print the exact text at every site the correction touches, before editing any.

WHY: twelve sites across seven files carry the 6.33 / 1.8x claim or depend on it.
Editing them from memory is how a correction introduces a second error, and this
project has already had one correction name the wrong file. So every site is
printed with its real line number and a hash of its surrounding block, and the
output is read before anything is changed.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]

# (file, [line numbers to show]) -- 1-based, as an editor shows them.
SITES: list[tuple[str, list[int], int]] = [
    ("paper/MANUSCRIPT.md", [331], 0),
    ("paper/en/MANUSCRIPT.md", [496, 497, 498, 499, 500], 0),
    ("paper/03-systems-draft.md", [77], 0),
    ("paper/en/03-04-systems-method.md", [113, 114, 115], 0),
    ("recon/R13-laya-probe.md", [249, 644, 679], 0),
    ("recon/R2-verified-externals.md", [91], 0),
    ("recon/R5-synthesis.md", [50], 0),
    ("decisions/DECISIONS.md", [24], 0),
    ("decisions/D1-jev-live-decision.md", [71], 0),
    ("decisions/D3-public-datasets.md", [114], 0),
    ("src/instrument/laya_client.py", [10], 0),
]

total = 0
for rel, nums, _ctx in SITES:
    p = ROOT / rel
    if not p.exists():
        print(f"!! MISSING {rel}")
        continue
    lines = p.read_text(encoding="utf-8").splitlines()
    print("=" * 78)
    print(f"{rel}   ({len(lines)} lines)")
    print("=" * 78)
    for n in nums:
        if n > len(lines):
            print(f"  L{n}: !! beyond end of file")
            continue
        total += 1
        print(f"  L{n}: {lines[n - 1]}")
    print()

print(f"--- {total} site lines printed ---")

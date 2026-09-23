"""Locate the inventory-count sentence by character comparison, not by guessing.

Four consecutive sync attempts failed with "anchor not found" while every visual
check said the text was present. The escaping was rebuilt three times on the
assumption that the backslash count was wrong. Rather than a fifth guess, this
prints the code points of the actual sentence beside the code points of the
anchor, so the mismatch (if any) is visible instead of inferred.

Run:  python recon/R18-locate-count-sentence.py
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
BS = chr(92)          # backslash, spelled the unambiguous way

TARGETS = [
    ("paper/09-10-11-discussion-limits-repro-draft.md", "个 JSON", 26, 18),
    ("paper/en/09-10-11-discussion-limits-repro.md", "JSON files", 30, 22),
]

for rel, needle, back, fwd in TARGETS:
    p = ROOT / rel
    if not p.exists():
        print(f"!! missing {rel}")
        continue
    t = p.read_text(encoding="utf-8")
    i = t.find(needle)
    print("=" * 78)
    print(rel)
    print("=" * 78)
    if i < 0:
        print(f"  !! {needle!r} not found in this file at all")
        continue
    frag = t[i - back: i + fwd]
    print(f"  actual  : {frag!r}")
    print(f"  codepoints around the path:")
    j = t.find("esults", i - 120)
    for k in range(max(0, j - 4), min(len(t), j + 10)):
        c = t[k]
        mark = "  <-- backslash" if c == BS else ("  <-- backtick" if c == "`" else "")
        print(f"    [{k}] {c!r} U+{ord(c):04X}{mark}")
    print()

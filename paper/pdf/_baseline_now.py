"""Establish the CURRENT truth about the four deliverable files.

Raised because a verification run produced numbers that disagreed with the
manifest I wrote twenty minutes earlier, and the disagreement was not
explained by anything I had knowingly done. Before telling anyone to re-upload
a file, the local baseline has to be measured rather than remembered -- a
manifest that no longer describes the files is worse than no manifest, because
it is trusted.

Reports bytes, sha256 and md5 for each, checks them against
paper/pdf/README.md's recorded values, and flags any drift.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]

FILES = [
    "paper/pdf/paper-en.pdf",
    "paper/pdf/paper-zh.pdf",
    "paper/en/MANUSCRIPT.md",
    "paper/MANUSCRIPT.md",
]

manifest = (ROOT / "paper" / "pdf" / "README.md").read_text(encoding="utf-8")
recorded = set(re.findall(r"`([0-9a-f]{64})`", manifest))
print("paper/pdf/README.md 记录的 sha256:")
for h in sorted(recorded):
    print("   ", h)
print()

print(f"{'file':30} {'bytes':>10}  {'sha256':18} {'md5':18}")
print("-" * 82)
current = {}
for rel in FILES:
    p = ROOT / rel
    b = p.read_bytes()
    sha = hashlib.sha256(b).hexdigest()
    md5 = hashlib.md5(b).hexdigest()
    current[rel] = (len(b), sha, md5)
    mark = ""
    if sha in recorded:
        mark = "  <- matches manifest"
    elif rel.endswith(".pdf"):
        mark = "  <- PDF NOT IN MANIFEST (drifted)"
    print(f"{rel:30} {len(b):>10,}  {sha[:16]}     {md5[:16]}{mark}")

print()
print("=== 漂移判定 ===")
for rel in FILES:
    if not rel.endswith(".pdf"):
        continue
    size, sha, _ = current[rel]
    if sha in recorded:
        print(f"  {rel}: 与清单一致，无需重传")
    else:
        print(f"  {rel}: 与清单不一致 -- 清单已过期，需要重写清单，"
              f"并确认当前文件是否是要上传的版本")

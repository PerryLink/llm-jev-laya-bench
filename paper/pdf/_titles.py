"""Print the exact H1 title from each PDF, so the Zenodo form can be filled
with a string that provably matches the file.

Why: the deposit record and the PDF must not disagree about the title.  My
earlier ZENODO-STEPS.md used a short English title; the PDF may carry a longer
one.  Whichever is right, they have to be the same string.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pymupdf

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent

for name in ("paper-en.pdf", "paper-zh.pdf"):
    doc = pymupdf.open(HERE / name)
    page = doc[0]
    # The H1 is the largest text on page 1.
    spans = []
    for blk in page.get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            for sp in line["spans"]:
                if sp["text"].strip():
                    spans.append((round(sp["size"], 1), sp["text"].strip()))
    spans.sort(key=lambda s: -s[0])
    biggest = spans[0][0]
    title_lines = [t for sz, t in spans if abs(sz - biggest) < 0.6]
    print(f"\n=== {name}")
    print(f"  PDF /Title metadata : {doc.metadata.get('title')}")
    print(f"  largest font size   : {biggest} pt")
    print(f"  rendered H1 title   : {' '.join(title_lines)}")
    doc.close()

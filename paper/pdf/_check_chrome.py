"""Prove positionally that there is no running header/footer.

The text-content check is not enough: "12/97" could be a footer OR a fraction.
A running header/footer has two signatures the content test cannot see:
  1. it sits in a NARROW BAND near the page edge (top ~8% or bottom ~8%), and
  2. it occupies the SAME vertical band on essentially EVERY page.

So: for every page, collect the y-ranges of all text.  If a chrome band exists,
many pages will share a tight y-band outside the main text block.  If the text
block simply runs to different depths on different pages, there is no chrome.

Also reports the actual top/bottom text extent so the margins can be eyeballed
against the @page rule (20mm top/bottom, 18mm left/right).
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pymupdf

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
PT_PER_MM = 72.0 / 25.4

for name in ("paper-en.pdf", "paper-zh.pdf"):
    doc = pymupdf.open(HERE / name)
    # Chrome's footer, when enabled, sits roughly 10-14mm from the bottom edge.
    chrome_zone = doc[0].rect.height - 16 * PT_PER_MM      # bottom 16 mm
    head_zone = 16 * PT_PER_MM                             # top 16 mm

    in_foot_band: list[tuple[int, str]] = []
    in_head_band: list[tuple[int, str]] = []
    tops, bots = [], []

    for i, page in enumerate(doc):
        blocks = page.get_text("blocks")
        if not blocks:
            continue
        tops.append(min(b[1] for b in blocks))
        bots.append(max(b[3] for b in blocks))
        for b in blocks:
            txt = b[4].strip().replace("\n", " ")
            if b[3] > chrome_zone and txt:
                in_foot_band.append((i + 1, txt[:80]))
            if b[1] < head_zone and txt:
                in_head_band.append((i + 1, txt[:80]))

    n = doc.page_count
    print(f"\n{'=' * 66}\n{name}  ({n} pages, height {doc[0].rect.height:.1f} pt)")
    print(f"  text top  : min {min(tops):.1f} pt ({min(tops) / PT_PER_MM:.1f} mm)  "
          f"max {max(tops):.1f} pt")
    print(f"  text bot  : min {min(bots):.1f} pt  max {max(bots):.1f} pt "
          f"({max(bots) / PT_PER_MM:.1f} mm from top, "
          f"{(doc[0].rect.height - max(bots)) / PT_PER_MM:.1f} mm from bottom)")
    print(f"  bottom chrome zone: y > {chrome_zone:.1f} pt (bottom 16 mm)")
    print(f"  blocks in bottom zone: {len(in_foot_band)} across {n} pages")
    print(f"  blocks in top zone   : {len(in_head_band)} across {n} pages")

    if in_foot_band:
        print("  samples of bottom-zone text:")
        for pno, t in in_foot_band[:6]:
            print(f"    p{pno:>3}: {t!r}")
        # Does the SAME string recur on many pages?  That is what a running
        # footer looks like.  Content that ends a page varies.
        c = Counter(t for _, t in in_foot_band)
        repeated = [(t, k) for t, k in c.most_common(3) if k > 2]
        if repeated:
            print(f"  ⚠ REPEATED bottom-zone text (footer signature): {repeated}")
        else:
            print("  ok   no repeated string in the bottom zone -> not a footer")
    else:
        print("  ok   nothing at all in the bottom 16 mm -> no footer")

    if in_head_band:
        c = Counter(t for _, t in in_head_band)
        rep = [(t, k) for t, k in c.most_common(3) if k > 2]
        print(f"  top-zone repeats: {rep if rep else 'none -> not a header'}")
    else:
        print("  ok   nothing at all in the top 16 mm -> no header")

    doc.close()

print("\nRESULT: positional check complete")

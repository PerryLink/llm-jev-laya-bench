"""Verify the two print-ready PDFs before they are deposited on Zenodo.

WHY this file exists, and why it is the *third* version:
  v1 looked for `(...)Tj`, found none (Chrome emits hex runs), and reported
  "almost no text" -- a detector bug announced as a document defect.
  v2 decoded the hex runs but merged every font's ToUnicode CMap into one
  table, so glyph ids collided across subset fonts and the text came out as
  "rusually sold on the grounds that it saves money".
  v3 (this file) stops hand-rolling a PDF parser and uses PyMuPDF, which was
  installed all along.  The lesson is the project's own recurring one: a check
  that cannot see the thing it is checking will confidently report on it.

What it actually verifies, in the order that matters for deposition:
  1. page count and A4 geometry
  2. NO header/footer (the file:/// path and N/M page numbers must be absent)
  3. the text really is the manuscript -- terminology, section headings,
     citation markers, and the specific numbers the paper is built on
  4. CJK renders as real glyphs, not .notdef boxes
  5. renders sample pages to PNG for a human to look at

Exit code is non-zero if any check fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pymupdf

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
A4 = (595.0, 842.0)          # points; PyMuPDF rounds to integers at this size
TOL = 2.0

# Numbers the manuscript is built on.  If the PDF were truncated, these would
# be missing -- this is what "the whole paper is in there" means concretely.
EN_ANCHORS = [
    "judgment layer",
    "Laya",
    "DeepSeek-V4.1-Flash",
    "0.9909",          # judge accuracy when the answer is stated
    "0.2727",          # explicit_contra
    "0.3091",          # no_support
    "0.4795",          # the corrected P20 figure
    "2.32",            # the corrected P21 ratio
    "1,191.8" ,        # withdrawn Jev latency figure (must be discussed)
    "952.9",           # its replacement
    "\u0394_catch",    # written with a Unicode delta, not "Delta_catch"
    "Brier",
]
ZH_ANCHORS = [
    "判定层",
    "Laya",
    "0.9909",
    "0.2727",
    "0.3091",
    "0.4795",
    "952.9",
    "Brier",
]


def check(pdf: Path) -> list[str]:
    fails: list[str] = []
    doc = pymupdf.open(pdf)
    n = doc.page_count
    print(f"\n=== {pdf.name}  ({pdf.stat().st_size:,} bytes, {n} pages)")

    # --- 1. geometry ---------------------------------------------------
    bad = []
    for i, page in enumerate(doc):
        w, h = page.rect.width, page.rect.height
        if abs(w - A4[0]) > TOL or abs(h - A4[1]) > TOL:
            bad.append((i + 1, round(w, 1), round(h, 1)))
    if bad:
        fails.append(f"{pdf.name}: {len(bad)} page(s) not A4, e.g. {bad[:3]}")
        print(f"  FAIL non-A4 pages: {bad[:5]}")
    else:
        print(f"  ok   all {n} pages A4 ({A4[0]}x{A4[1]} pt)")

    text = "\n".join(page.get_text() for page in doc)
    print(f"  extracted text       : {len(text):,} characters")

    # --- 2. header / footer --------------------------------------------
    leaks = []
    for needle in ("file:///", "D:/Projects", "D:\\Projects",
                   "llm-jev-laya-bench", "paper/dist"):
        if needle in text:
            leaks.append(needle)
    if leaks:
        fails.append(f"{pdf.name}: header/footer leak {leaks}")
        print(f"  FAIL header/footer leak: {leaks}")
    else:
        print("  ok   no file:/// path or repo path anywhere in the text")

    # A running footer would render as "12/97" or "Page 12 of 97".  Text alone
    # cannot settle this -- "(21/46)" is a fraction, not a page number.  What
    # distinguishes a footer is POSITION: it sits in a narrow band near the
    # page edge, on essentially every page.  So require BOTH a shape match AND
    # a position in the bottom 16 mm.  _check_chrome.py does the full
    # positional analysis; this is the cheap in-line version of it.
    PT_PER_MM = 72.0 / 25.4
    foot_hits = 0
    for page in doc:
        zone = page.rect.height - 16 * PT_PER_MM
        for b in page.get_text("blocks"):
            if b[3] > zone:                      # block extends into the band
                if re.search(r"\b\d{1,3}\s*/\s*\d{1,3}\b", b[4]) or \
                   re.search(r"\bPage\s+\d+\s+of\s+\d+\b", b[4], re.I):
                    foot_hits += 1
    if foot_hits:
        fails.append(f"{pdf.name}: {foot_hits} page-number-shaped block(s) "
                     f"in the bottom margin band")
        print(f"  FAIL page-number footer in bottom band ({foot_hits}x)")
    else:
        print("  ok   no page-number-shaped text in the bottom margin band")

    # --- 3. content anchors --------------------------------------------
    anchors = ZH_ANCHORS if "zh" in pdf.name else EN_ANCHORS
    missing = [a for a in anchors if a not in text]
    if missing:
        fails.append(f"{pdf.name}: anchors missing {missing}")
        print(f"  FAIL anchor(s) missing: {missing}")
    else:
        print(f"  ok   all {len(anchors)} numeric/terminology anchors present")
    for a in anchors[:4]:
        print(f"       {a!r:24} x{text.count(a)}")

    # --- 4. CJK glyph sanity (Chinese only) -----------------------------
    if "zh" in pdf.name:
        cjk = re.findall(r"[\u4e00-\u9fff]", text)
        print(f"  CJK ideographs       : {len(cjk):,} distinct {len(set(cjk)):,}")
        if len(set(cjk)) < 500:
            fails.append(f"{pdf.name}: only {len(set(cjk))} distinct CJK glyphs")
            print("  FAIL too few distinct CJK characters -- possible tofu")
        else:
            print("  ok   CJK extracted as real characters, not boxes")
        # .notdef would show up as replacement characters.
        tofu = text.count("\ufffd") + text.count("\u25a1")
        if tofu:
            fails.append(f"{pdf.name}: {tofu} replacement/box characters")
            print(f"  FAIL {tofu} tofu/replacement characters")
        else:
            print("  ok   no tofu or replacement characters")
    else:
        odd = len(re.findall(r"[\ufffd]", text))
        if odd:
            fails.append(f"{pdf.name}: {odd} replacement characters")
            print(f"  FAIL {odd} replacement characters")
        else:
            print("  ok   no replacement characters")

    # --- 5. render sample pages for human inspection ---------------------
    picks = sorted({0, 1, n // 2, n - 1})
    for pno in picks:
        out = HERE / f"_page-{pdf.stem}-{pno + 1:03d}.png"
        pix = doc[pno].get_pixmap(dpi=110)
        pix.save(out)
    print(f"  rendered pages for review: {[p + 1 for p in picks]}")

    doc.close()
    return fails


def main() -> int:
    pdfs = sorted(HERE.glob("paper-*.pdf"))
    if not pdfs:
        print("FAIL no PDFs found")
        return 1
    all_fails: list[str] = []
    for pdf in pdfs:
        all_fails += check(pdf)

    print("\n" + "=" * 62)
    if all_fails:
        print(f"RESULT: {len(all_fails)} FAILURE(S)")
        for f in all_fails:
            print("  - " + f)
        return 1
    print("RESULT: both PDFs pass -- A4, no headers/footers, full manuscript text")
    return 0


if __name__ == "__main__":
    sys.exit(main())

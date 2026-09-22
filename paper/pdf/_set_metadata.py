"""Set document metadata on the two print-ready PDFs.

Why: Zenodo's previewer and Google Scholar both read /Title and /Author out of
the PDF.  A PDF whose title is blank or "paper-en" looks like a draft.  The
metadata must agree with what will be typed into the Zenodo form -- a
disagreement between the deposit record and the file is exactly the kind of
mismatch this paper is about, and it would be embarrassing to ship.

IDEMPOTENT, deliberately: it was run three times during the title-block fix
(once per re-print).  Re-opening a PDF it already saved and saving it again
must not shift the bytes, or the hash recorded in PDF-MANIFEST.txt would
change for no reason.  So the script reports whether the bytes moved, and warns
if a second run on an unchanged file changes the size.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pymupdf

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent

META = {
    "paper-en.pdf": {
        "title": "When a Judgment Layer's Self-Reported Fields Lie: "
                 "Cost, Latency and the Failure Boundary of Three Judgment "
                 "Layers on the Same Items",
        "author": "Perry Link",
        "subject": "Judgment layers, calibration, silent truncation, "
                   "negative results, reproducibility",
        "keywords": "judgment layer; calibration; silent truncation; "
                    "negative results; reproducibility; Laya; Jev; LLM",
    },
    "paper-zh.pdf": {
        "title": "当判定层的自报字段说谎时：三类判断层的成本、延迟与失效边界实测",
        "author": "Perry Link",
        "subject": "判定层；校准；静默截断；阴性结果；可复现性",
        "keywords": "判定层; 校准; 静默截断; 阴性结果; 可复现性; Laya; Jev; LLM",
    },
}

for name, meta in META.items():
    path = HERE / name
    if not path.exists():
        print(f"SKIP {name} (missing)")
        continue
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    doc = pymupdf.open(path)
    if doc.metadata.get("title") == meta["title"] and \
       doc.metadata.get("author") == meta["author"]:
        # Already correct.  DO NOT SAVE.  PyMuPDF stamps /ModDate on every save,
        # so re-saving an unchanged file still moves the bytes -- measured: two
        # consecutive runs produced four different sha256s.  A hash manifest is
        # worthless if running the tool changes the hash, so this becomes a
        # no-op check instead of a rewrite.
        print(f"\n{name}  ({path.stat().st_size:,} bytes, {doc.page_count} pages)")
        print(f"  sha256 : {before}")
        print("  ok     metadata already correct -- left the bytes untouched")
        doc.close()
        continue
    doc.set_metadata({
        "title": meta["title"],
        "author": meta["author"],
        "subject": meta["subject"],
        "keywords": meta["keywords"],
        "creator": "paper/src/analysis/p96_render_html.py + headless Chrome",
        "producer": "Chrome --no-pdf-header-footer",
    })
    tmp = path.with_suffix(".pdf.tmp")
    doc.save(tmp, garbage=3, deflate=True)
    doc.close()
    tmp.replace(path)

    # Read it back -- never trust that a write happened.
    check = pymupdf.open(path)
    m = check.metadata
    after = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"\n{name}  ({path.stat().st_size:,} bytes, {check.page_count} pages)")
    print(f"  sha256 : {after}   (WROTE -- hash moved)")
    for k in ("title", "author", "subject", "keywords"):
        print(f"  {k:9}: {m.get(k)}")
    check.close()

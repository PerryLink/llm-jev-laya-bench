"""Produce the exact text to paste into the Zenodo form, and put the longest
field (the abstract) on the clipboard.

WHY: the abstract body is 131 lines of markdown with bold runs, em dashes,
warning glyphs and section references.  Retyping or hand-copying it is how a
deposit record ends up subtly different from the PDF it describes -- and this
paper is about exactly that kind of mismatch.  So the strings are extracted
programmatically and printed for verification.

Prints EN and ZH abstract bodies and copies the EN one to the clipboard.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]


def section(text: str, heading: str, stop_prefix: str = "---") -> str:
    """Body of `## <heading>` up to the next `## ` heading or stop_prefix."""
    lines = text.splitlines()
    start = None
    for i, l in enumerate(lines):
        if l.strip() == heading:
            start = i + 1
            break
    if start is None:
        return ""
    out = []
    for l in lines[start:]:
        if l.strip().startswith("## ") or l.strip() == stop_prefix:
            break
        out.append(l)
    return "\n".join(out).strip("\n")


en = (ROOT / "paper" / "en" / "00-abstract.md").read_text(encoding="utf-8")
zh = (ROOT / "paper" / "00-abstract-draft.md").read_text(encoding="utf-8")

en_body = section(en, "## Abstract")
en_kw = section(en, "## Keywords").replace("\n", " ").replace(" · ", "; ")
zh_body = section(zh, "## 摘要正文")
zh_kw = section(zh, "## 关键词").replace("\n", " ").replace(" · ", "; ")

print("=" * 70)
print("EN ABSTRACT  ", len(en_body), "chars,", en_body.count("\n") + 1, "lines")
print("=" * 70)
print(en_body)
print()
print("EN keywords ->", en_kw or "(not found: check heading text)")
print()
print("=" * 70)
print("ZH ABSTRACT  ", len(zh_body), "chars,", zh_body.count("\n") + 1, "lines")
print("=" * 70)
print(zh_body[:1200])
print("   ... [truncated for display]")
print()
print("ZH keywords ->", zh_kw or "(see paper/00-abstract-draft.md)")

# Clipboard: Set-Clipboard handles unicode properly on Windows PowerShell.
try:
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "$input | Set-Clipboard", ],
        input=en_body.encode("utf-8"), check=True,
    )
    print("\n[copied] EN abstract body is now on the clipboard -- paste into Description")
except Exception as e:                                   # pragma: no cover
    print(f"\n[could not reach the clipboard: {e}]")

# Also drop both to files, so the user can open and copy by hand if needed.
out = ROOT / "paper" / "pdf" / "_zenodo-fields.txt"
out.write_text(
    "ZENODO — English deposit\n"
    "Title:\n"
    "When a Judgment Layer's Self-Reported Fields Lie: Cost, Latency and the "
    "Failure Boundary of Three Judgment Layers on the Same Items\n\n"
    "Creators: Family name = Link   Given names = Perry\n"
    "Resource type: Publication -> Preprint\n"
    "License: CC BY 4.0\n"
    "Language: English\n"
    "Keywords: " + en_kw + "\n\n"
    "Description (abstract body, markdown is fine):\n"
    + en_body +
    "\n\n\n" + "=" * 72 + "\n\n"
    "ZENODO — 中文稿\n"
    "Title:\n"
    "当判定层的自报字段说谎时：三类判断层的成本、延迟与失效边界实测\n\n"
    "Creators: Family name = Link   Given names = Perry\n"
    "Resource type: Publication -> Preprint\n"
    "License: CC BY 4.0\n"
    "Language: Chinese\n"
    "Keywords: " + zh_kw + "\n\n"
    "Description:\n" + zh_body + "\n",
    encoding="utf-8",
)
print(f"[wrote] {out}")

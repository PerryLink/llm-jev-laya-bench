"""Output ONLY the two Zenodo Description field values, cleanly and in full.

One file per language so either can be opened and copied without scrolling past
the other, and so there is no chance of pasting the English abstract into the
Chinese record.

Deliberately excludes the two things in `paper/en/00-abstract.md` that must NOT
go into a public abstract:
  * the translation note at the top ("English translation of ..."), which is a
    note to the reader about provenance, and
  * the "Disclosure compliance check (editor's record)" section at the bottom,
    which is an internal compliance record submitted with the paper.
Both sit outside the `## Abstract` heading, so cutting at the heading boundaries
drops them by construction rather than by remembering to.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def section(text: str, heading: str) -> str:
    """Body of `## <heading>` up to the next `## ` heading or a `---` rule."""
    lines = text.splitlines()
    start = None
    for i, l in enumerate(lines):
        if l.strip() == heading:
            start = i + 1
            break
    if start is None:
        raise SystemExit(f"heading not found: {heading!r}")
    out = []
    for l in lines[start:]:
        if l.strip().startswith("## ") or l.strip() == "---":
            break
        out.append(l)
    return "\n".join(out).strip("\n")


JOBS = [
    ("en", ROOT / "paper" / "en" / "00-abstract.md", "## Abstract",
     "_zenodo-description-en.md"),
    ("zh", ROOT / "paper" / "00-abstract-draft.md", "## 摘要正文",
     "_zenodo-description-zh.md"),
]

for label, src, heading, outname in JOBS:
    body = section(src.read_text(encoding="utf-8"), heading)
    out = HERE / outname
    out.write_text(body + "\n", encoding="utf-8")
    words = len(body.split())
    print(f"[{label}] {len(body):,} chars, {words:,} words, "
          f"{body.count(chr(10)) + 1} lines  ->  {outname}")
    # A deposit description that silently lost its tail is the failure this
    # project keeps meeting, so assert the ending is where it should be.
    print(f"      starts: {body.splitlines()[0][:70]!r}")
    print(f"      ends  : {body.splitlines()[-1][:70]!r}")
    for bad in ("Disclosure compliance check", "editor's record",
                "English translation of"):
        if bad in body:
            print(f"      LEAK: contains {bad!r} -- should have been cut")
    print()

"""Report which bibliography entries nothing in the paper actually cites.

An UNCITED reference is a different defect from a missing one: the entry sits in the .bib
looking verified while no claim rests on it. Worse, a claim can lose its citation during an
edit and nobody notices, because the .bib still looks complete. This script produces the
worklist for fixing that; `paper/verify_all.py` check H8 enforces it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402


def main() -> int:
    bib = (PAPER / "references.bib").read_text(encoding="utf-8")
    entries = re.findall(r"@(\w+)\{([^,]+),(.*?)\n\}", bib, re.S)
    body = (PAPER / "MANUSCRIPT.md").read_text(encoding="utf-8").split("# 参考文献")[0]

    uncited = []
    for _kind, key, blob in entries:
        key = key.strip()
        if f"[@{key}]" in body:
            continue
        m = re.search(r"author\s*=\s*\{(.*?)\}", blob, re.S)
        surname = ""
        if m:
            first = re.split(r"\s+and\s+", m.group(1).strip())[0]
            surname = first.split(",")[0].strip().strip("{}")
        year = (re.search(r"year\s*=\s*\{?(\d{4})", blob) or [None, ""])[1]
        hit = False
        if surname:
            hit = bool(re.search(rf"{re.escape(surname)}[^）)。\n]{{0,40}}{year}", body))
        if not hit and surname and surname in body and year in body:
            hit = True
        if hit:
            continue
        title = re.search(r"title\s*=\s*\{(.*?)\}", blob, re.S)
        t = re.sub(r"\s+", " ", title.group(1)).strip() if title else ""
        uncited.append((key, surname, year, t))

    print(f"{len(uncited)} of {len(entries)} entries are not cited in the paper:\n")
    for key, sur, year, title in uncited:
        print(f"  {key:30s} {sur:14s} {year}  {title[:62]}")
    print()
    print("Each of these either needs a citation at the sentence it supports, or does not")
    print("belong in the bibliography. An entry that supports nothing is not neutral: it")
    print("makes the list look more thorough than the argument is.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Fill the author block and wire the AI-assistance disclosure into both manuscripts.

The author chose: name = PerryLink, disclosure = Option B (long form).

The disclosure's numbers were checked against the tree rather than copied from the draft:
the draft said "31 automated checks" and "ten sections of self-reported defects", but
verify_all.py now runs 49 checks and ERRATA.md has 11 sections. A disclosure containing a
stale count would be self-refuting in a paper about unverified numbers, so the text states
the current figures.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER, ROOT  # noqa: E402

# ---- 1. the author block ---------------------------------------------------------------
c = ROOT / "CITATION.cff"
t = c.read_text(encoding="utf-8")
t = t.replace(
    '# NOTE BEFORE PUBLISHING: replace the placeholders below, then delete this comment.\n'
    '# `family-names` / `given-names` and `orcid` are REQUIRED for a citable record.\n'
    '# An ORCID iD is free and does not require an academic affiliation: https://orcid.org\n'
    'authors:\n'
    '  - family-names: "REPLACE"\n'
    '    given-names: "REPLACE"\n'
    '    # orcid: "https://orcid.org/0000-0000-0000-0000"\n'
    '    # affiliation: "Independent Researcher"\n'
    '    alias: "PerryLink"',
    '# The author publishes under this handle. CFF asks for family/given names; this author\n'
    '# uses a single handle rather than a legal name, so it is given as both, with the handle\n'
    '# also recorded as an alias. No ORCID is supplied (optional, and none is claimed).\n'
    'authors:\n'
    '  - family-names: "PerryLink"\n'
    '    given-names: "PerryLink"\n'
    '    alias: "PerryLink"\n'
    '    affiliation: "Independent Researcher"', 1)
c.write_text(t, encoding="utf-8")
print("  ok    CITATION.cff author block filled")
print("        contains REPLACE:", "REPLACE" in t)

# ---- 2. wire the disclosure into the Chinese assembler ---------------------------------
for path, entry, label in [
    (PAPER / "_assemble.py",
     '    "13-ai-disclosure-draft.md",\n', "Chinese assembler"),
    (PAPER / "en" / "_assemble.py",
     None, "English assembler"),
]:
    a = path.read_text(encoding="utf-8")
    if "13-ai-disclosure" in a:
        print(f"  ok    {label}: already lists the disclosure")
        continue
    if label == "Chinese assembler":
        # insert just before the references entry in SOURCES
        m = re.search(r'^(\s*)("12-references-draft\.md",.*)$', a, re.M)
        if m:
            a = a[:m.start()] + m.group(1) + '"13-ai-disclosure-draft.md",\n' + a[m.start():]
            path.write_text(a, encoding="utf-8")
            print(f"  ok    {label}: disclosure added to SOURCES")
        else:
            print(f"  MISS  {label}: no references entry found in SOURCES")
    else:
        # the English assembler uses a tuple list; add a plain entry at the end
        m = re.search(r'^(\s*\("09-10-11-discussion-limits-repro\.md".*?\),)$', a, re.M | re.S)
        if m:
            a = a[:m.end()] + '\n    ("13-ai-disclosure.md", [], "AI-assistance disclosure"),' + a[m.end():]
            path.write_text(a, encoding="utf-8")
            print(f"  ok    {label}: disclosure added to SOURCES")
        else:
            print(f"  MISS  {label}: anchor not found")

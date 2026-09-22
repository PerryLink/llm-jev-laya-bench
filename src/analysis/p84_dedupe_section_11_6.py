"""Remove the duplicated section 11.6 in both languages, and fix the guard that made it.

WHAT HAPPENED
-------------
p76 (Chinese) and p77 (English) each APPEND a new section 11.6 listing the twelve untraceable
number categories. Both scripts tested the ORIGINAL text first:

    if old in t:        # <- append
    elif new in t:      # <- already applied

For an append-style edit the original text REMAINS a substring of the patched file, so the
second run took the first branch and appended a second copy. The build then refused to write
(`duplicate subsection number ## 11.6 appears 2x`), which is the assembler doing exactly its
job -- the defect was caught by the project's own gate, not by review.

This is the same wrong-object guard as p70's sentinel, p73's branch order, p81's K4 anchor and
p80's call-site split. It is now the sixth instance in one session, and it is worth stating
plainly: **every one of them was written by the same hand that was, at the time, fixing other
people's guards.** That is the argument for wiring the checks (K1-K10) rather than trusting
the scripts that produced the text.

The duplicate is removed, the guard order is corrected in both scripts, and both assemblers are
re-run so the manuscripts are rebuilt from single copies.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER, ROOT  # noqa: E402

ZH = PAPER / "09-10-11-discussion-limits-repro-draft.md"
EN = PAPER / "en" / "09-10-11-discussion-limits-repro.md"
ALLOWED_COUNT = 1

BAD_GUARD_76 = """        t = cache[fname]
        if old in t:"""
GOOD_GUARD_76 = """        t = cache[fname]
        # `new` is tested FIRST: for an append-style edit the original text stays a substring
        # of the patched file, so testing `old` first re-appends on every run (this produced a
        # duplicate section 11.6 and the assembler refused to build).
        if new in t:
            print(f"  ok    {label} (already applied)")
            ok += 1
        elif old in t:"""


def dedupe(path: Path, heading: str) -> int:
    """Keep the FIRST copy of a duplicated block, drop the rest."""
    t = path.read_text(encoding="utf-8")
    n = t.count(heading)
    if n <= ALLOWED_COUNT:
        print(f"  ok    {path.name}: {n} copy of the section 11.6 block")
        return 0
    first = t.index(heading)
    second = t.index(heading, first + len(heading))
    # the duplicate runs from `second` to the next top-level '## ' heading after it (or EOF)
    nxt = t.find("\n## ", second + 1)
    if nxt < 0:
        nxt = len(t)
    path.write_text(t[:second] + t[nxt:].lstrip("\n"), encoding="utf-8")
    print(f"  ok    {path.name}: removed {n - 1} duplicated block(s) (was {n})")
    return n - 1


def main() -> int:
    problems = []
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                            # noqa: BLE001
        pass

    dedupe(ZH, "## 11.6 只能追溯到实验室记录")
    dedupe(EN, "## 11.6 Numbers traceable only to a lab record")

    # ---- correct the guard order in the two scripts that appended --------------------
    p76 = ROOT / "src" / "analysis" / "p76_mark_untraceable_numbers.py"
    s = p76.read_text(encoding="utf-8")
    if "`new` is tested FIRST" in s:
        print("  ok    p76's guard already tests `new` first")
    elif BAD_GUARD_76 in s:
        p76.write_text(s.replace(BAD_GUARD_76, GOOD_GUARD_76, 1), encoding="utf-8")
        print("  ok    p76's guard now tests `new` first")
    else:
        problems.append("p76's guard is not in the expected form")

    p77 = ROOT / "src" / "analysis" / "p77_sync_english_untraceable.py"
    s = p77.read_text(encoding="utf-8")
    if "already applied" in s and s.index('if old in t:') > s.index('if new in t:'):
        print("  ok    p77's guard already tests `new` first")
    elif "        if old in t:" in s:
        s = s.replace("""        if old in t:
            cache[fname] = t.replace(old, new, 1)
            print(f"  ok    {label}")
            ok += 1
        elif new in t:
            print(f"  ok    {label} (already applied)")
            ok += 1""",
                      """        # `new` first, for the same reason as p76: appended text leaves `old` intact.
        if new in t:
            print(f"  ok    {label} (already applied)")
            ok += 1
        elif old in t:
            cache[fname] = t.replace(old, new, 1)
            print(f"  ok    {label}")
            ok += 1""", 1)
        p77.write_text(s, encoding="utf-8")
        print("  ok    p77's guard now tests `new` first")
    else:
        problems.append("p77's guard is not in the expected form")

    # ---- rebuild both manuscripts ---------------------------------------------------
    for cmd, label in (([sys.executable, str(PAPER / "_assemble.py")], "zh"),
                       ([sys.executable, str(PAPER / "en" / "_assemble.py")], "en")):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=str(PAPER.parent))
        tail = [l for l in (r.stdout or "").splitlines() if l.strip()][-1:] or [""]
        print(f"  {'ok  ' if r.returncode == 0 else 'FAIL'}  {label} build: {tail[0][:90]}")
        if r.returncode != 0:
            problems.append(f"{label} build failed")

    for p in problems:
        print(f"  MISS  {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

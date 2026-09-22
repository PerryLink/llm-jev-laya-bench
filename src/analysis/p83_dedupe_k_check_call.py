"""Remove the duplicated K-check call, and fix the guard that allowed the duplicate.

TWO DEFECTS, ONE OF THEM MINE
-----------------------------
`check_trace_audit_invariants(t)` was wired into `main()` twice, so every K result was
reported twice and the check count was wrong. The cause is p80's call-site guard:

    if "check_trace_audit_invariants(t)" not in src.split("def check_trace_audit_invariants")[0]

It tests only the text BEFORE the function definition -- which is exactly where the call site
is NOT, after the first run. So the guard reported "not present" on every subsequent run and
appended another call. This is the FIFTH guard in this session to test the wrong object (p70's
sentinel, p73's branch order, p73's dedupe key, p81's K4 anchor, and now this), and it is the
same defect class the paper is about: the code was correct and the thing it LOOKED AT was not.

The duplicate is removed, and the guard is replaced with one that counts.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import ROOT  # noqa: E402

VERIFY = ROOT / "paper" / "verify_all.py"
P80 = ROOT / "src" / "analysis" / "p80_wire_trace_audit_checks.py"

CALL = "    check_trace_audit_invariants(t)"
GOOD_GUARD = '    if src.count("check_trace_audit_invariants(t)") != 1:'
BAD_GUARD = ('    if "check_trace_audit_invariants(t)" not in '
             'src.split("def check_trace_audit_invariants")[0]:')


def main() -> int:
    problems = []

    # ---- 1. de-duplicate the call site in verify_all.py ---------------------------------
    t = VERIFY.read_text(encoding="utf-8")
    n = t.count(CALL)
    if n == 1:
        print("  ok    exactly one K-check call site")
    elif n > 1:
        # drop every occurrence after the first
        first = t.index(CALL)
        head, tail = t[:first + len(CALL)], t[first + len(CALL):]
        tail = tail.replace(CALL + "\n", "")
        VERIFY.write_text(head + tail, encoding="utf-8")
        print(f"  ok    removed {n - 1} duplicated K-check call(s) (was {n})")
    else:
        problems.append("the K-check call site is missing entirely")

    # ---- 2. fix p80's guard so it cannot happen again -----------------------------------
    s = P80.read_text(encoding="utf-8")
    if GOOD_GUARD in s:
        print("  ok    p80's call-site guard already counts occurrences")
    elif BAD_GUARD in s:
        P80.write_text(s.replace(BAD_GUARD, GOOD_GUARD, 1), encoding="utf-8")
        print("  ok    p80's call-site guard now counts occurrences instead of splitting "
              "on the function definition")
    else:
        problems.append("p80's call-site guard is not in the expected form")

    for p in problems:
        print(f"  MISS  {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

"""Refuse a change that rewrites line endings across a file it was only supposed to edit.

WHY THIS EXISTS
---------------
`.gitattributes` sets `* -text` repo-wide, deliberately: `protocol/instrument-snapshot/` records
a SHA256 per module, `src/instrument/run_pinned_sidecar.py` re-hashes them and refuses to launch
on drift, and Git's default newline conversion on Windows would falsify those hashes on a clean
checkout. So in this repository a line-ending change is a REAL change, not a normalisation -- it
touches every line of the file and, in the pinned instrument, breaks the launcher.

That is not hypothetical. `src/analysis/p97_sync_declared_counts.py` rewrote 22 spans in 12 files
and silently converted **nine** of them from LF to CRLF on its first run, because `Path.read_text`
applies universal newlines and `Path.write_text` re-expands `\\n` to `os.linesep`. Every figure it
wrote was correct. The diff was the only sign, and it was 1,389 changed lines for an edit that
should have been 44. `p97` now opens with `newline=""` and refuses to write when a line outside
the ones it matched would move -- but the next script will not know that, and this is the check
that notices.

HOW IT DECIDES
--------------
For every file `git diff --name-only` reports, compare the newline style of the working-tree bytes
against the style of the same file in HEAD. Style is LF, CRLF, or MIXED -- a file that was wholly
one style and is now the other, or that has become mixed, is a failure. File length is not
compared, so growing a file is fine; only the endings are judged.

Usage:
    python src/analysis/p98_line_ending_audit.py            # audit the working tree
    python src/analysis/p98_line_ending_audit.py --staged   # audit what is staged instead

Exit code is 0 only when no reported file changed its newline style.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import ROOT  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass


def style(blob: bytes) -> str:
    """LF, CRLF, or MIXED. A style change means every line moved."""
    crlf = blob.count(b"\r\n")
    lone_lf = blob.count(b"\n") - crlf
    if crlf and lone_lf:
        return "MIXED"
    return "CRLF" if crlf else "LF"


def main() -> int:
    args = ["git", "diff", "--name-only", "--cached"] if "--staged" in sys.argv \
        else ["git", "diff", "--name-only"]

    changed = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                             encoding="utf-8").stdout.split()
    if not changed:
        print("  no changed files -- nothing to audit")
        return 0

    bad: list[str] = []
    print(f"  {len(changed)} changed file(s); comparing newline style against HEAD\n")
    print(f"  {'file':56} {'HEAD':>6} {'now':>6}")
    for rel in changed:
        head = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT,
                              capture_output=True).stdout
        path = ROOT / rel
        if not head:                       # new file: no HEAD version to compare with
            print(f"  {rel:56} {'(new)':>6} {style(path.read_bytes()):>6}")
            continue
        if not path.exists():
            print(f"  {rel:56} {style(head):>6} {'(gone)':>6}")
            continue
        before, after = style(head), style(path.read_bytes())
        flag = "" if before == after else "   <-- ENDINGS CHANGED"
        if before != after:
            bad.append(rel)
        print(f"  {rel:56} {before:>6} {after:>6}{flag}")

    print()
    if bad:
        print(f"RESULT: {len(bad)} file(s) changed newline style -- do NOT commit this")
        for rel in bad:
            print(f"  - {rel}")
        print("\n  A text edit that moves every line is the signature of a read-modify-write through")
        print("  an API that translates newlines. Open with newline=\"\" on both read and write.")
        return 1
    print("RESULT: no changed file moved its newline style")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Rewrite every stated check count and ERRATA section count so they match their sources.

WHY THIS IS A SCRIPT AND NOT AN EDIT
------------------------------------
`p59_author_and_disclosure.py` fixed this same defect by typing in the figures that were current
then -- "31 automated checks" became "49 checks", "ten sections" became "11 sections". Its reasoning
was right and the fix went stale anyway, because nothing read the numbers afterwards. Two rounds
later the manuscript described one script as running 24 checks in section 11 and 49 in section 13,
and ERRATA's section count appeared as 10, 11 and 12 in three different files.

So this script contains **no figures of its own**. It takes both from their sources:

  * the gate's size -- it runs `paper/verify_all.py` and parses the total the gate prints, even when
    the gate is failing, which is exactly the state it is in when this needs to run;
  * ERRATA's size -- it counts the numbered sections of `results/ERRATA.md`.

The difference from `p59` is the whole point: there is no number in here to go stale.

Generated files (`paper/MANUSCRIPT.md`, `paper/en/MANUSCRIPT.md`, `paper/dist/*.html`) are NOT
touched. They are rebuilt from the sources this script edits, and `verify_all.py`'s `L2` scans them
so that forgetting the rebuild fails the gate instead of shipping a stale PDF.

Usage:
    python src/analysis/p97_sync_declared_counts.py            # report and rewrite
    python src/analysis/p97_sync_declared_counts.py --check    # report only, non-zero if stale
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import ROOT  # noqa: E402

CHECK_ONLY = "--check" in sys.argv


def read_exact(path: Path) -> str:
    """Read a text file WITHOUT newline translation.

    `Path.read_text` applies universal newlines on read and `Path.write_text` re-expands `\\n` to
    `os.linesep`, so a read-modify-write round trip silently converts every LF in the file to CRLF
    on Windows. The first run of this script did exactly that to nine files, and the whole-file diff
    was the only sign. `newline=""` turns both translations off, so the bytes that come back are the
    bytes that went in.
    """
    with path.open(encoding="utf-8", newline="") as fh:
        return fh.read()


def write_exact(path: Path, body: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(body)


def gate_total() -> int:
    """The number `paper/verify_all.py` prints, read from the gate rather than restated."""
    proc = subprocess.run(
        [sys.executable, str(ROOT / "paper" / "verify_all.py")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    m = re.search(r"\((\d+) checks\)", proc.stdout or "")
    if not m:
        tail = "\n".join((proc.stdout or "").strip().splitlines()[-6:])
        raise SystemExit(f"could not read the gate's total from its output:\n{tail}")
    return int(m.group(1))


def errata_sections() -> int:
    """Numbered sections of ERRATA.md, excluding the section 0 preamble (same rule as check E)."""
    t = (ROOT / "results" / "ERRATA.md").read_text(encoding="utf-8")
    return len(re.findall(r"^## [1-9]\d*\.", t, re.M))


# (relative path, compiled pattern, replacement template, expected number of hits)
# The digits are always inside the pattern, so each rule is idempotent: re-running it rewrites the
# same span with the same text and the hit count is unchanged.
def rules(N: int, E: int) -> list[tuple[str, re.Pattern[str], str, int]]:
    return [
        # ---- the gate's own size ------------------------------------------------------
        ("README.md", re.compile(r"# \d+ checks over paper and artifacts"),
         f"# {N} checks over paper and artifacts", 1),
        ("RELEASE.md", re.compile(r"\d+ passed, 0 warnings, 0 failures  \(\d+ checks\)"),
         f"{N} passed, 0 warnings, 0 failures  ({N} checks)", 1),
        ("RELEASE.md", re.compile(r"green at \d+ checks"), f"green at {N} checks", 1),
        ("PUBLISHED.md", re.compile(r"# \d+ checks: paper vs artifacts, \d+/0/0"),
         f"# {N} checks: paper vs artifacts, {N}/0/0", 1),
        ("SUBMISSION-PLAN.md", re.compile(r"的 \d+ 项检查"), f"的 {N} 项检查", 1),
        ("HOW-TO-SUBMIT.md", re.compile(r"ships with \d+ automated checks"),
         f"ships with {N} automated checks", 1),
        ("HOW-TO-SUBMIT.md", re.compile(r"`\d+ automated checks;"), f"`{N} automated checks;", 1),
        ("OUTREACH.md", re.compile(r"the \d+-check suite"), f"the {N}-check suite", 1),
        ("OUTREACH.md", re.compile(r"a \d+-check verification suite"),
         f"a {N}-check verification suite", 1),
        ("paper/AI-DISCLOSURE-DRAFT.md", re.compile(r"执行 \d+ 项自动检查"),
         f"执行 {N} 项自动检查", 1),
        ("paper/AI-DISCLOSURE-DRAFT.md", re.compile(r"runs \d+ automated checks"),
         f"runs {N} automated checks", 1),
        ("paper/09-10-11-discussion-limits-repro-draft.md",
         re.compile(r"\*\*\d+ 项检查，全部通过。\*\*"), f"**{N} 项检查，全部通过。**", 1),
        ("paper/en/09-10-11-discussion-limits-repro.md",
         re.compile(r"\*\*\d+ checks, all passing\.\*\*"), f"**{N} checks, all passing.**", 1),
        ("paper/13-ai-disclosure-draft.md", re.compile(r"\*\*\d+ 项自动检查\*\*"),
         f"**{N} 项自动检查**", 1),
        ("paper/en/13-ai-disclosure.md", re.compile(r"\*\*\d+ automated checks\*\*"),
         f"**{N} automated checks**", 1),
        # ---- ERRATA's own size --------------------------------------------------------
        ("README.md", re.compile(r"ERRATA\.md  -- \d+ sections recording"),
         f"ERRATA.md  -- {E} sections recording", 1),
        ("README.md", re.compile(r"results/ERRATA\.md` — \d+ sections of self-reported defects"),
         f"results/ERRATA.md` — {E} sections of self-reported defects", 1),
        ("SUBMISSION-PLAN.md", re.compile(r"`ERRATA` 的 \d+ 节自查记录"),
         f"`ERRATA` 的 {E} 节自查记录", 1),
        ("ZENODO-EDIT-VS-VERSION.md", re.compile(r"`results/ERRATA\.md` 有 \d+ 节"),
         f"`results/ERRATA.md` 有 {E} 节", 1),
        ("paper/13-ai-disclosure-draft.md",
         re.compile(r"\*\*\d+ 节\*\*记录自查发现的缺陷"), f"**{E} 节**记录自查发现的缺陷", 1),
        ("paper/en/13-ai-disclosure.md",
         re.compile(r"\*\*\d+ sections\*\* recording self-reported defects"),
         f"**{E} sections** recording self-reported defects", 1),
        ("paper/AI-DISCLOSURE-DRAFT.md", re.compile(r"以 \d+ 节记录自查发现的缺陷"),
         f"以 {E} 节记录自查发现的缺陷", 1),
    ]


def main() -> int:
    N = gate_total()
    E = errata_sections()
    print(f"  gate prints {N} checks   ERRATA.md numbers {E} sections\n")

    touched: set[str] = set()
    stale: list[str] = []
    problems: list[str] = []

    # Collect first, apply second: the expected number of changed LINES is derived from the
    # distinct lines the rules touch, and two rules can share a line (SUBMISSION-PLAN.md has both
    # figures in one sentence).
    per_file: dict[str, list[tuple[int, int, str, str, int]]] = {}
    for rel, pat, repl, expect in rules(N, E):
        path = ROOT / rel
        if not path.exists():
            problems.append(f"{rel}: missing")
            continue
        body = read_exact(path)
        hits = pat.findall(body)
        if len(hits) != expect:
            problems.append(f"{rel}: {pat.pattern!r} matched {len(hits)}, expected {expect}")
            continue
        for m in pat.finditer(body):
            per_file.setdefault(rel, []).append(
                (m.start(), m.end(), m.group(0), repl, body.count("\n", 0, m.start()) + 1))

    for rel, subs in per_file.items():
        path = ROOT / rel
        body = read_exact(path)
        # Right-to-left, so every earlier offset stays valid as the text length changes.
        new = body
        for start, end, _found, repl, _line in sorted(subs, key=lambda s: -s[0]):
            new = new[:start] + repl + new[end:]

        # THE GUARD. Only the lines that hold a figure may differ. Anything else moving is the
        # signature of a line-ending or encoding change, which is what the first run of this script
        # did to nine files: `read_text`/`write_text` translate newlines, so a read-modify-write on
        # Windows silently converts every LF to CRLF and the whole file shows up in the diff. The
        # figures were right and the change was still wrong.
        old_lines = body.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)
        touched_idx = {line - 1 for *_, line in subs}
        stray = [i + 1 for i, (a, b) in enumerate(zip(old_lines, new_lines))
                 if i not in touched_idx and a != b]
        if len(old_lines) != len(new_lines) or stray:
            problems.append(
                f"{rel}: line(s) outside the {len(touched_idx)} that hold a figure would also "
                f"change ({stray[:5] or 'line count'}) -- REFUSING to write. That is the signature "
                f"of a line-ending or encoding change, not of a substitution.")
            continue

        real = [(found, repl) for _s, _e, found, repl, _l in subs if found != repl]
        for found, repl in real:
            stale.append(f"{rel}: {found.strip()} -> {repl.strip()}")
        if real:
            touched.add(rel)
            if not CHECK_ONLY:
                write_exact(path, new)

    for line in stale:
        print(f"  {'STALE' if CHECK_ONLY else ' fixed'}  {line}")
    for line in problems:
        print(f"  ERROR  {line}")

    print()
    print(f"  {len(stale)} stale span(s) in {len(touched)} file(s); {len(problems)} error(s)")
    if problems:
        return 2
    if CHECK_ONLY and stale:
        return 1
    if not CHECK_ONLY:
        print("  now rebuild: python paper/_assemble.py && python paper/en/_assemble.py")
        print("               python src/analysis/p96_render_html.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())

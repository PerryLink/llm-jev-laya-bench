"""Repair two defects in the K-checks that p80 wired into `verify_all.py`.

FOUND BY RUNNING THEM, WHICH IS THE ONLY WAY THESE ARE EVER FOUND

1. K3 matched 15 table rows instead of 10, because the MOCK battery's bin table in section 3.1
   has the same first two columns (`0.0-0.2 | 3 | ...`). A check that counts rows it should not
   count fails on correct data -- and a gate that fails on correct data gets switched off. The
   scan is now scoped to the ten labels the reliability artifact actually defines.

2. `verify_all.py` CRASHED while printing its own results: a detail string contained a
   character the host console's GBK codec cannot encode, so the run ended in a UnicodeEncodeError
   traceback instead of a report. The gate must not die while reporting. stdout is reconfigured
   to UTF-8 with `errors="replace"`, so an unprintable glyph degrades to a placeholder and the
   check's verdict still reaches the reader.

Both are the same species as the defects this whole section is about: correct logic attached to
the wrong object, and an instrument that fails silently (or here, loudly in the wrong place).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import ROOT  # noqa: E402

VERIFY = ROOT / "paper" / "verify_all.py"

OLD_SCAN = '''    printed = {b.replace("–", "-"): int(n.replace(",", ""))
               for b, n in _re.findall(
                   r"^\\| \\*?\\*?([0-9]\\.[0-9]–[0-9]\\.[0-9])\\*?\\*? \\| \\*?\\*?([0-9,]+)\\*?\\*?",
                   t, _re.M)}
    want_bins = {b["bin"]: b["n"] for b in bins}'''

NEW_SCAN = '''    want_bins = {b["bin"]: b["n"] for b in bins}
    # SCOPE THE SCAN TO THE RELIABILITY TABLE. The mock battery's bin table in section 3.1 has
    # the same first two columns (0.0-0.2 | 3 | ...), so an unscoped row regex collects 15 rows
    # and the check fails on correct data -- which is how a check gets switched off.
    printed = {}
    for label, n in _re.findall(
            r"^\\| \\*?\\*?([0-9]\\.[0-9]–[0-9]\\.[0-9])\\*?\\*? \\| \\*?\\*?([0-9,]+)\\*?\\*?",
            t, _re.M):
        key = label.replace("–", "-")
        if key in want_bins:
            printed[key] = int(n.replace(",", ""))'''

OLD_MAIN = "def main() -> int:\n    check_freshness()"

NEW_MAIN = '''def main() -> int:
    # The gate must not die while reporting: this host's console is GBK, and a detail string
    # containing a character it cannot encode aborted the run with a UnicodeEncodeError
    # instead of printing a verdict. Degrade the glyph, keep the finding.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                            # noqa: BLE001
        pass
    check_freshness()'''

# K4 fired on its own correction note, which QUOTES the withdrawn wording in order to retire it
# -- the same false positive the C-section `absent(..., unless_near=...)` helper exists to
# avoid. The exemption is the retirement vocabulary this paper already uses.
OLD_K4 = '''    bad = [l for l in t.split("\\n") if "0.9981" in l and "全探测**最高**" in l]'''
NEW_K4 = '''    # A VIOLATION IS AN ASSERTION, NOT A MENTION: the corrected row reads "并非全探测最高"
    # ("is NOT the probe maximum"), and the correction note quotes the old wording to retire it.
    # Both are the fix working, so both are exempt -- the third guard in this file to need the
    # distinction between a claim and a quotation of it.
    retire = ("并非", "不是", "更正", "原印", "撤回", "correction", "withdrawn")
    bad = [l for l in t.split("\\n")
           if "0.9981" in l and "全探测最高" in _re.sub(r"[*`]", "", l)
           and not any(m in l for m in retire)]'''


def main() -> int:
    src = VERIFY.read_text(encoding="utf-8")
    problems = []
    changed = 0

    if NEW_SCAN in src:
        print("  ok    the K3 scan is already scoped to the reliability bins")
    elif OLD_SCAN in src:
        src = src.replace(OLD_SCAN, NEW_SCAN, 1)
        changed += 1
        print("  ok    K3 scan scoped to the ten reliability bins")
    else:
        problems.append("anchor for the K3 row scan is missing")

    if 'sys.stdout.reconfigure(encoding="utf-8"' in src:
        print("  ok    stdout is already reconfigured")
    elif OLD_MAIN in src:
        src = src.replace(OLD_MAIN, NEW_MAIN, 1)
        changed += 1
        print("  ok    stdout reconfigured so a report cannot die on an unencodable glyph")
    else:
        problems.append("anchor for main()'s first line is missing")

    if problems:
        for p in problems:
            print(f"  MISS  {p}")
        return 1

    # K4, third pass. The first pass wrote `retire = ("更正", ...)`; the corrected row's own
    # denial ("并非全探测最高") and the correction note are BOTH the fix working, so both must be
    # exempt. Patch the tuple in place rather than re-matching a whole block whose exact text has
    # already moved once -- that is how the previous attempt reported MISS on its own output.
    if '"并非"' in src and "retire" in src:
        print("  ok    K4 already exempts the corrected row's own denial")
    elif 'retire = ("更正", "原印", "撤回", "已由", "instead", "correction", "withdrawn")' in src:
        src = src.replace(
            'retire = ("更正", "原印", "撤回", "已由", "instead", "correction", "withdrawn")',
            'retire = ("并非", "不是", "更正", "原印", "撤回", "correction", "withdrawn")', 1)
        changed += 1
        print("  ok    K4 also exempts the corrected row's own denial")
    elif "0.9981" in src and "全探测最高" in src:
        print("  warn  K4's retirement tuple is not in the expected form; left untouched")
    else:
        problems.append("K4's scan is absent from verify_all.py")

    if changed:
        VERIFY.write_text(src, encoding="utf-8")
        print(f"  patched {VERIFY.relative_to(ROOT)} ({changed} change(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())

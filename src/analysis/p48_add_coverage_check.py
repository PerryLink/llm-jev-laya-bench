"""Add a translation-COVERAGE check.

WHY: the English file for sections 9-11 was delivered with only sections 9 and 10, and left
a `<!-- TRANSLATION-CONTINUES-HERE -->` marker. Every existing check passed it -- the file
had no Han characters, declared its sections, and used only valid citation keys. None of
them asked the one question that mattered: does the English cover everything the Chinese
does?

A translation that is silently two-thirds complete is worse than one that is obviously
incomplete, because the checks go green. This adds the missing question.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

V = PAPER / "verify_all.py"
v = V.read_text(encoding="utf-8")

CHECK = '''

def check_translation_coverage() -> None:
    """Every numbered section in a Chinese draft must appear in its English translation.

    This is the check that was MISSING when the 9-10-11 file arrived carrying only 9 and 10
    plus a `TRANSLATION-CONTINUES-HERE` marker: the file had no Han characters, declared its
    sections, and used valid keys, so every existing check went green on a translation that
    was one third short. A silently incomplete translation is worse than an obviously
    incomplete one, because nothing complains.
    """
    # English file -> the Chinese sources it must cover
    PAIRS = {
        "00-abstract.md": ["00-abstract-draft.md"],
        "01-intro-02.md": ["01-intro-02-related-draft.md"],
        "03-04-systems-method.md": ["03-systems-draft.md", "04-method-draft.md"],
        "05-results-A.md": ["05-results-A-draft.md"],
        "06-07-results-BC.md": ["06-results-B-draft.md", "07-results-C-draft.md"],
        "08-results-D.md": ["08-results-D-draft.md"],
        "09-10-11-discussion-limits-repro.md":
            ["09-10-11-discussion-limits-repro-draft.md"],
    }
    en = PAPER / "en"
    problems = []
    for en_name, zh_names in PAIRS.items():
        f = en / en_name
        if not f.exists():
            continue                      # not translated yet; I1 reports the inventory
        t = f.read_text(encoding="utf-8")
        if "TRANSLATION-CONTINUES-HERE" in t:
            problems.append(f"{en_name}: carries a TRANSLATION-CONTINUES-HERE marker")
        want = set()
        for zh in zh_names:
            p = PAPER / zh
            if p.exists():
                want |= set(re.findall(r"^#\\s*§(\\d+)", p.read_text(encoding="utf-8"), re.M))
        have = set(re.findall(r"^#\\s*§(\\d+)", t, re.M))
        if en_name.startswith("00-"):
            continue                      # the abstract has no numbered sections
        missing = sorted(want - have)
        if missing:
            problems.append(f"{en_name}: missing section(s) {missing} "
                            f"(source has {sorted(want)}, translation has {sorted(have)})")
    if problems:
        fail("I5 every English file covers all of its source sections", "; ".join(problems[:3]))
    else:
        done = [n for n in PAIRS if (en / n).exists()]
        ok("I5 every English file covers all of its source sections",
           f"{len(done)} file(s) checked")
'''

if "def check_translation_coverage" not in v:
    v = v.replace("\ndef main() -> int:", CHECK + "\n\ndef main() -> int:", 1)
    v = v.replace("    check_translation()", "    check_translation()\n    check_translation_coverage()", 1)
    V.write_text(v, encoding="utf-8")
    print("  ok    verify_all.py: coverage check I5 added")
else:
    print("  already present")

"""Final integrity check on everything this session changed.

Every edit this session REMOVED support from a claim or corrected an attachment. That class
of edit has a characteristic failure mode: the claim is fixed in one place and left standing
in another. The §8 retraction was exactly that, and it was caught only by a second audit.

So this checks the PROPERTY rather than the instances: for every claim withdrawn or corrected
this session, is the old form gone EVERYWHERE, and does the new form appear wherever the
claim does?
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

TEXT = sorted(PAPER.glob("*-draft.md")) + [PAPER / "MANUSCRIPT.md"]

# (label, pattern that must NOT survive, pattern that must be present somewhere)
WITHDRAWN = [
    ("Jev 'two independent runs'", r"两次独立运行|two independent runs",
     r"只有一次有产物的运行|唯一有产物的"),
    ("mock battery n attached to Brier", r"14项校准电池产出合理的置信度分布，但",
     r"有二元真值的\s*\*{0,2}10"),
    ("latency ratio 25-29", r"25[–-]29\s*倍", r"25[–-]32\s*倍"),
    ("unqualified '2 of 3 CIs exclude 0'", r"3\s*次中\s*2\s*次\s*(?:95%\s*)?CI\s*排除零",
     r"Newcombe"),
    ("LLM cost ceiling 0.0000566", r"0\.0000566", r"0\.00009645"),
    ("sign of the 68-item cluster correlation", r"相关\s*[−-]0\.243", r"\+0\.243"),
    ("the P26 control arm's 6/10", r"约\s*\*{0,2}6/10\s*来自截断",
     r"撤回|无产物"),
]

problems: list[str] = []
for label, bad, good in WITHDRAWN:
    for f in TEXT:
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8")
        for i, line in enumerate(t.split("\n"), 1):
            if re.search(bad, line):
                # a line that also says it is withdrawing/correcting the form is fine
                if re.search(r"撤回|更正|原印|早期版本|已撤回|应为|符号错误|错误批次|"
                         r"withdrawn|correction|should be", line):
                    continue
                problems.append(f"{f.name}:{i} still asserts [{label}]: {line.strip()[:70]}")

# the companion check: the correction must actually BE somewhere
for label, _bad, good in WITHDRAWN:
    if not any(f.exists() and re.search(good, f.read_text(encoding="utf-8")) for f in TEXT):
        problems.append(f"[{label}] the correction text is absent from every document")

print(f"checked {len(WITHDRAWN)} withdrawn/corrected claims across {len(TEXT)} documents\n")
if problems:
    for p in problems:
        print(f"  FAIL  {p}")
    print(f"\n{len(problems)} problem(s)")
    sys.exit(1)
print("  all withdrawals and corrections are consistent across every document")
sys.exit(0)

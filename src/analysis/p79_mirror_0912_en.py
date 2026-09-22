"""Mirror the 0.912 -> 0.4795 correction into the English section files.

I applied it to the Chinese drafts and told the drafts editor to mirror it, but mirroring my own
change is my job and the English still carries the old figure in 12 places. The lesson of this
whole session applies: a correction that lives in only one language is a correction the English
reader does not get.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

EN = PAPER / "en"
FILES = ["01-intro-02.md", "06-07-results-BC.md"]

NOTE = (" (**⚠️ Eighth-round correction: 0.912 was measured with the SCORING RUBRIC WRONG** -- "
        "in the same artifact the true-item arm, whose rubric was correct in both script "
        "versions, reproduces 48 of 48 fields identically across all eight languages, while the "
        "false-item arm, whose published rubric named the wrong value, differs on 22. "
        "**Re-measured with the corrected rubric the figure is 0.4795** (non-Latin false-item "
        "mean P(true)). 0.912 was really measured, but what it measured is a judge that was "
        "asked a malformed question, not a judge that failed to notice an absence, so 0.4795 is "
        "the figure of record. **The qualitative finding stands on it** -- 0.4795 is still far "
        "above what a calibrated judge returns on items with no support.)")

total = 0
for name in FILES:
    p = EN / name
    if not p.exists():
        print(f"  MISS  {name}")
        continue
    t = p.read_text(encoding="utf-8")
    n = t.count("0.912")
    if not n:
        print(f"  ok    {name}: already corrected")
        continue
    t = t.replace("0.912", "0.4795")
    # put the note at the first prose occurrence of the corrected figure
    anchor = "**non-Latin false items reach P(true) 0.4795**"
    if anchor in t:
        t = t.replace(anchor, anchor + NOTE, 1)
    else:
        # fall back: attach to the first occurrence of the corrected value in a sentence
        i = t.find("0.4795")
        if i != -1:
            end = t.find("\n", i)
            t = t[:end] + NOTE + t[end:]
    p.write_text(t, encoding="utf-8")
    total += n
    print(f"  ok    {name}: {n} occurrence(s) -> 0.4795")

print(f"\n{total} occurrence(s) corrected in English")

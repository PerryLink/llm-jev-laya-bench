"""Establish whether P20's re-run is a real non-reproduction or another broken run.

This is the most consequential diff so far. The paper states that on non-Latin scripts the judge
gives false items a mean P(true) as high as 0.912; the re-run reports 0.4795. That is either

  (a) a genuine failure to reproduce a published claim, which would have to be reported as such
      and would change the paper, or
  (b) another run that did not actually measure anything.

P5c taught the lesson: it looked like a disagreement and was a missing dependency. So the rows
are examined here BEFORE any conclusion is drawn.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import RESULTS  # noqa: E402

cur = json.loads((RESULTS / "P20-language-misrouting.json").read_text(encoding="utf-8"))
old = json.loads((RESULTS / "_superseded"
                  / "P20-language-misrouting.json.pre-rerun").read_text(encoding="utf-8"))

cr, orr = cur.get("rows", []), old.get("rows", [])
print(f"rows: now {len(cr)}   before {len(orr)}")
print(f"top-level keys now: {sorted(cur.keys())}")

# Is every row an error, as in P5c?
errs = [r.get("error") for r in cr if r.get("error")]
print(f"\nrows carrying an `error` field: {len(errs)} of {len(cr)}")
for e in dict.fromkeys(str(x) for x in errs):
    print(f"  {e[:120]}")

# Are the measurement fields populated at all?
def populated(rows, keys=("p_true", "pred", "band", "correct")):
    return sum(1 for r in rows if any(r.get(k) is not None for k in keys))

print(f"\nrows with at least one populated measurement field: "
      f"now {populated(cr)} / {len(cr)}      before {populated(orr)} / {len(orr)}")

# Compare only the fields that ARE the measurement, on rows that exist in both.
if cr and orr and len(cr) == len(orr):
    diff = same = 0
    examples = []
    for i, (a, b) in enumerate(zip(cr, orr)):
        for k in set(a) | set(b):
            if k in ("error",) or "latency" in k or "elapsed" in k:
                continue
            if a.get(k) != b.get(k):
                diff += 1
                if len(examples) < 8:
                    examples.append((i, k, b.get(k), a.get(k)))
            else:
                same += 1
    print(f"\nrow fields compared {same + diff}:  identical {same}   differing {diff}")
    for i, k, b, a in examples:
        print(f"  row {i} {k}: {b!r} -> {a!r}")

print()
if errs and len(errs) == len(cr):
    print("VERDICT: BROKEN RUN -- every row is an error, nothing was measured.")
    print("         Not a non-reproduction. Re-run with the project venv.")
    sys.exit(0)
if populated(cr) == 0:
    print("VERDICT: BROKEN RUN -- no row carries a measurement.")
    sys.exit(0)
print("VERDICT: the rows carry real measurements and differ from the published ones.")
print("         This is a CANDIDATE NON-REPRODUCTION and must be established as carefully")
print("         as a reproduction would be: same items, same states, same interpreter, same")
print("         loadout -- before any claim in the paper is changed.")
sys.exit(1)

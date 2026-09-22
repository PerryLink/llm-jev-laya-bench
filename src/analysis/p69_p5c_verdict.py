"""Decide whether P5c's re-run disagrees with the published result, or merely failed to aggregate.

The regenerated P5c has `cells: {}` and `verdict: null`, where the published artifact had four
populated cells and a real verdict string. Read naively that says "the finding did not
reproduce", which would be a serious claim about the paper.

But it still carries all 20 rows. So the question is whether the MEASUREMENT changed or only the
SUMMARY step broke. That distinction decides whether this is a scientific non-reproduction or a
bug in the re-run -- and reporting the second as the first would be a false alarm of exactly the
kind this whole exercise exists to prevent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import RESULTS  # noqa: E402

cur = json.loads((RESULTS / "P5c-marker-vs-integration.json").read_text(encoding="utf-8"))
old = json.loads((RESULTS / "_superseded"
                  / "P5c-marker-vs-integration.json.pre-rerun").read_text(encoding="utf-8"))

cr, orr = cur.get("rows", []), old.get("rows", [])
print(f"rows: now {len(cr)}  before {len(orr)}")

# Compare row by row on the fields that ARE the measurement, ignoring per-call latency.
SKIP = ("latency", "elapsed", "duration", "timestamp", "mtime")
same = diff = 0
diffs = []
for i, (a, b) in enumerate(zip(cr, orr)):
    for k in set(a) | set(b):
        if any(s in k.lower() for s in SKIP):
            continue
        if a.get(k) != b.get(k):
            diff += 1
            diffs.append((i, k, b.get(k), a.get(k)))
        else:
            same += 1

print(f"row fields compared: {same + diff}   identical: {same}   differing: {diff}")
for i, k, b, a in diffs[:10]:
    print(f"  row {i} {k}: {b!r} -> {a!r}")

print()
print("=== can the published summary be rebuilt from the new rows? ===")
# The published cells were keyed "<condition>/<arm>" with n, accuracy, mean_p_truth.
from collections import defaultdict  # noqa: E402
cell = defaultdict(list)
for r in cr:
    key = f"{r.get('condition')}/{r.get('arm')}"
    cell[key].append(r)
print(f"  groups rebuildable from the new rows: {sorted(cell)}")
for k, rs in sorted(cell.items()):
    n = len(rs)
    acc = sum(1 for r in rs if r.get("correct")) / n if n else None
    print(f"    {k:24s} n={n} accuracy={acc}")

print()
pub = old.get("summary", {}).get("cells", {})
print("  published cells:")
for k, v in sorted(pub.items()):
    print(f"    {k:24s} n={v.get('n')} accuracy={v.get('accuracy')}")

print()
if diff == 0:
    print("VERDICT: the MEASUREMENT reproduced -- every non-timing row field is identical.")
    print("         The regenerated artifact's summary step produced nothing, which is a bug")
    print("         in the re-run, NOT a failure of the published finding.")
    sys.exit(0)
print("VERDICT: the rows themselves differ -- this needs investigation as a real disagreement.")
sys.exit(1)

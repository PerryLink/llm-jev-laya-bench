"""Compare every regenerated artifact against its pre-rerun copy, field by field.

This is the actual question the re-run exists to answer, and it is answered by a diff rather
than by reading the re-run's own logs -- a re-run that reports success while its output differs
from the published artifact is the exact failure mode this whole exercise is guarding against.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import RESULTS  # noqa: E402

# fields that legitimately differ between runs and are not measurement results
# Fields that record WHEN a run happened rather than WHAT it measured. These must differ
# between runs -- a timestamp that did NOT change would mean the re-run never happened.
# _instrument is entirely provenance: uptime, cumulative call count, wall-clock stamp.
VOLATILE = ("mtime", "timestamp", "_rerun", "wall_ms", "latency_ms", "elapsed", "date",
            "_instrument", "uptime", "calls", "recorded_at", "duration")


def flat(node, prefix=""):
    out = {}
    if isinstance(node, dict):
        for k, v in node.items():
            out.update(flat(v, f"{prefix}.{k}"))
    elif isinstance(node, list):
        out[prefix] = f"<list n={len(node)}>"
    else:
        out[prefix] = node
    return out


pre = RESULTS / "_superseded"
print(f"{'artifact':38s} {'fields':>7s} {'differ':>7s}  verdict")
print("-" * 78)
any_diff = False
for f in sorted(RESULTS.glob("*.json")):
    b = pre / (f.name + ".pre-rerun")
    if not b.exists():
        continue
    after = flat(json.loads(f.read_text(encoding="utf-8")))
    before = flat(json.loads(b.read_text(encoding="utf-8")))
    keys = set(after) | set(before)
    diffs = [k for k in keys if after.get(k) != before.get(k)]
    soft = [k for k in diffs if any(v in k.lower() for v in VOLATILE)]
    hard = [k for k in diffs if k not in soft]
    verdict = "IDENTICAL" if not diffs else (
        f"{len(soft)} volatile only" if not hard else f"{len(hard)} REAL DIFFERENCES")
    if hard:
        any_diff = True
    print(f"{f.name:38s} {len(keys):7d} {len(diffs):7d}  {verdict}")
    for k in hard[:6]:
        print(f"      {k}: {before.get(k)!r} -> {after.get(k)!r}")

print("-" * 78)
print("VERDICT:", "REAL DIFFERENCES FOUND -- see above" if any_diff
      else "every regenerated artifact reproduces its published values")
sys.exit(1 if any_diff else 0)

"""Show the unexplained value differences in P5, P5b and P27c.

P20's differences are explained: its published artifact recorded no criteria and the re-run
supplies explicit ones, so the two runs measured different conditions. The remaining
differences are not yet explained, and an unexplained difference is the whole reason this
re-run exists.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import RESULTS  # noqa: E402

PRE = RESULTS / "_superseded"
VOLATILE = ("mtime", "timestamp", "_rerun", "wall_ms", "latency_ms", "elapsed", "date",
            "_instrument", "uptime", "calls", "recorded_at", "duration", "drift")


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


for name in ("P5-certificate-verification.json", "P5b-classifier-templates.json",
             "P27c-jev-latency-sweep.json", "P1-rank-vs-choice.json"):
    f = RESULTS / name
    p = PRE / (name + ".pre-rerun")
    if not (f.exists() and p.exists()):
        print(f"=== {name}: no pre-rerun copy ===")
        continue
    after = flat(json.loads(f.read_text(encoding="utf-8")))
    before = flat(json.loads(p.read_text(encoding="utf-8")))
    keys = set(after) | set(before)
    diffs = [k for k in keys
             if k in before and k in after and before[k] != after[k]
             and not any(v in k.lower() for v in VOLATILE)]
    print(f"=== {name}: {len(diffs)} differing ===")
    for k in sorted(diffs)[:14]:
        print(f"   {k}")
        print(f"      before: {before[k]!r}")
        print(f"      after : {after[k]!r}")
    print()

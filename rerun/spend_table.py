"""Recompute the published per-artifact spend from the BASELINE byte-copy.

Read-only. Used only to establish what the published campaign cost, so the re-run's
own spend can be compared against the same accounting.
"""
from __future__ import annotations

import glob
import json
import os
import sys

KEYS = ("cost_usd", "off_peak_usd", "costUsd", "llm_cost", "cost_off",
        "cost_usd_mean", "mean_cost_usd")
PER_CALL = ("off_peak_usd", "cost_usd", "costUsd", "llm_cost", "cost_off",
            "cost_usd_mean", "mean_cost_usd")


def collect(node, keys=KEYS):
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k in keys and isinstance(v, (int, float)):
                out.append((k, v))
            else:
                out += collect(v, keys)
    elif isinstance(node, list):
        for v in node:
            out += collect(v, keys)
    return out


root = sys.argv[1] if len(sys.argv) > 1 else "results"
tot = 0.0
rows = []
for f in sorted(glob.glob(os.path.join(root, "*.json"))):
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception as exc:
        print("SKIP", f, exc)
        continue
    vals = collect(d)
    off = [v for k, v in vals if k in PER_CALL]
    s = sum(off)
    if s > 0:
        rows.append((os.path.basename(f), len(off), s))
        tot += s
for n, c, s in rows:
    print("%-52s n=%5d  $%.9f" % (n, c, s))
print("TOTAL (off-peak, one leaf per call) = $%.6f" % tot)

"""What did the re-run actually cost? Sum per-call costs from the live artifacts.

Also compares against the hardcoded figures in
src/instrument/p29_backfill_llm_provenance.py, because those constants are what a
re-run of p29 would re-insert as the artifact's retroactive provenance block.
"""
from __future__ import annotations

import json
from pathlib import Path

KEYS = ("off_peak_usd", "cost_usd", "llm_cost_usd", "llm_cost", "costUsd",
        "cost_off", "cost_usd_mean", "mean_cost_usd")


def collect(node):
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k in KEYS and isinstance(v, (int, float)):
                out.append(v)
            else:
                out += collect(v)
    elif isinstance(node, list):
        for v in node:
            out += collect(v)
    return out


for name in ("P14-llm-arm-full", "P21-thinking-mode-cost", "P23-llm-logprobs",
             "P15b-rep-r1", "P22b-fixed-r1", "P22-chain-audit", "P24-reduced-horizon",
             "P19-calibration"):
    cur = Path("results") / f"{name}.json"
    base = Path("rerun/baseline") / f"{name}.json"
    if not cur.exists():
        print(f"{name:26s} (not regenerated)")
        continue
    c = collect(json.loads(cur.read_text(encoding="utf-8")))
    b = collect(json.loads(base.read_text(encoding="utf-8"))) if base.exists() else []
    print(f"{name:26s} n_calls={len(c):5d}  rerun=${sum(c):.9f}   "
          f"published=${sum(b):.9f}   delta=${sum(c)-sum(b):+.9f}")

print()
print("hardcoded in p29_backfill_llm_provenance.py:")
src = Path("src/instrument/p29_backfill_llm_provenance.py").read_text(encoding="utf-8")
for line in src.splitlines():
    if "recorded_off_peak_spend_usd" in line or "calls_made" in line:
        print("   ", line.strip())

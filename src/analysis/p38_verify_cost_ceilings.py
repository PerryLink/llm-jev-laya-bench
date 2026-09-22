"""Verify the cost ceilings in the paper against the artifacts.

Triggered by a trace audit that reported the LLM ceiling covers the WRONG battery: the
printed range is the floor-to-mean of one arm, while the paper's own 96-call arm has a
measured maximum 1.7x higher.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import RESULTS  # noqa: E402


def load(n: str) -> dict:
    return json.loads((RESULTS / n).read_text(encoding="utf-8"))


def collect(node, keys=("cost_usd", "off_peak_usd", "costUsd", "llm_cost_usd",
                        "mean_cost_usd", "cost_usd_mean")):
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


print("=" * 74)
print("P14 — the LLM arm, 48 items x 2 arms = 96 calls")
print("=" * 74)
p14 = load("P14-llm-arm-full.json")
vals = [v for k, v in collect(p14) if k in ("off_peak_usd", "llm_cost_usd")]
if vals:
    print(f"  per-call off-peak: n={len(vals)}  min={min(vals):.8f}  "
          f"max={max(vals):.8f}  mean={sum(vals)/len(vals):.8f}")
for k in sorted(p14.get("summary", {})):
    if "cost" in k.lower():
        print(f"  summary.{k} = {p14['summary'][k]}")

print()
print("=" * 74)
print("P21 — thinking-mode cost, 4 efforts x 6 items")
print("=" * 74)
p21 = load("P21-thinking-mode-cost.json")
for e in p21.get("by_effort", []):
    print(f"  effort={str(e.get('effort')):6s} n={e.get('n')} "
          f"mean={e.get('cost_usd_mean') or e.get('mean_cost_usd')}")

print()
print("=" * 74)
print("P27 — Jev, all per-call costs in the artifact")
print("=" * 74)
p27 = load("P27-jev-live.json")
jv = [v for _k, v in collect(p27)]
if jv:
    print(f"  n={len(jv)}  min={min(jv):.8f}  max={max(jv):.8f}")

print()
print("=" * 74)
print("WHAT THE PAPER PRINTS vs WHAT THE ARTIFACTS HOLD")
print("=" * 74)
if vals and jv:
    print(f"  LLM floor   paper 0.0000326   artifact {min(vals):.7f}   "
          f"{'OK' if abs(min(vals) - 0.0000326) < 1e-7 else 'MISMATCH'}")
    print(f"  LLM ceiling paper 0.0000566   artifact {max(vals):.7f}   "
          f"{'OK' if abs(max(vals) - 0.0000566) < 1e-7 else 'MISMATCH'}"
          f"   -> understated by {(max(vals)/0.0000566 - 1)*100:.1f}%")
    print(f"  Jev floor   paper 0.0000146   artifact {min(jv):.7f}   "
          f"{'OK' if abs(min(jv) - 0.0000146) < 1e-7 else 'MISMATCH'}")

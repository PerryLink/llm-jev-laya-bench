"""Check the re-run's spend against the authorised ceiling.

The author authorised about $0.08-0.10. This compares each regenerated artifact's recorded
per-call costs against its pre-rerun backup, so any NEW spend shows up as a delta. Artifacts
that only use the local Laya sidecar cost nothing; the API-backed ones are where spend appears.

A re-run that quietly exceeds its budget is a failure regardless of what it finds, so this is
checked rather than assumed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import RESULTS  # noqa: E402

COST_KEYS = ("llm_cost", "cost_usd", "off_peak_usd", "costUsd", "mean_cost_usd")


def total(node) -> float:
    """Sum every cost-looking field in a nested structure."""
    if isinstance(node, dict):
        return sum(v if k in COST_KEYS and isinstance(v, (int, float)) else total(v)
                   for k, v in node.items())
    if isinstance(node, list):
        return sum(total(v) for v in node)
    return 0.0


CEILING = 0.10
pre = RESULTS / "_superseded"

print(f"{'artifact':40s} {'before':>11s} {'after':>11s} {'delta':>11s}")
print("-" * 76)
net = 0.0
regenerated = 0
for f in sorted(RESULTS.glob("*.json")):
    b = pre / (f.name + ".pre-rerun")
    if not b.exists():
        continue
    try:
        after = json.loads(f.read_text(encoding="utf-8"))
        before = json.loads(b.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  {f.name:38s} unreadable: {e}")
        continue
    ta, tb = total(after), total(before)
    net += ta - tb
    regenerated += 1
    flag = "" if abs(ta - tb) < 1e-9 else "  <-- NEW SPEND"
    print(f"{f.name:40s} {tb:11.6f} {ta:11.6f} {ta - tb:+11.6f}{flag}")

print("-" * 76)
print(f"{regenerated} artifact(s) regenerated")
print(f"NET NEW SPEND : ${net:.6f}")
print(f"CEILING       : ${CEILING:.2f}")
print(f"REMAINING     : ${CEILING - net:.6f}")
print()
print("PASS" if net <= CEILING else "OVER BUDGET -- STOP AND REPORT")
sys.exit(0 if net <= CEILING else 1)

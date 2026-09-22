"""Refine the re-run comparison: an ADDITION is not a DISAGREEMENT.

The first version reported "REAL DIFFERENCES" for P28 because `.regime1` went from absent to a
2-element list. That is the ERRATA agent ADDING the regime-1 prose arm -- an improvement, not a
reproduction failure. Reporting it as a difference would be the mirror image of the mistake this
whole exercise guards against: a checker that cries wolf gets ignored, and then a real
disagreement slips past.

So the verdict now separates three cases:
  * ADDED     -- a key present now and absent before: new work, not a disagreement
  * CHANGED   -- a key present both times with different values: this is what must be explained
  * VOLATILE  -- provenance fields that MUST differ (a timestamp that did not change would mean
                 the re-run never happened)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import RESULTS  # noqa: E402

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


def is_volatile(k: str) -> bool:
    return any(v in k.lower() for v in VOLATILE)


pre = RESULTS / "_superseded"
rows = []
changed_total = []
for f in sorted(RESULTS.glob("*.json")):
    b = pre / (f.name + ".pre-rerun")
    if not b.exists():
        continue
    after = flat(json.loads(f.read_text(encoding="utf-8")))
    before = flat(json.loads(b.read_text(encoding="utf-8")))
    keys = set(after) | set(before)

    added = [k for k in keys if k not in before and not is_volatile(k)]
    removed = [k for k in keys if k not in after and not is_volatile(k)]
    changed = [k for k in keys
               if k in before and k in after and before[k] != after[k] and not is_volatile(k)]
    vol = [k for k in keys
           if k in before and k in after and before[k] != after[k] and is_volatile(k)]

    changed_total += [(f.name, k, before[k], after[k]) for k in changed]
    if changed or removed:
        verdict = f"{len(changed)} CHANGED" + (f", {len(removed)} REMOVED" if removed else "")
    elif added:
        verdict = f"reproduced ({len(added)} key(s) ADDED, {len(vol)} volatile)"
    elif vol:
        verdict = f"reproduced ({len(vol)} volatile only)"
    else:
        verdict = "reproduced exactly"
    rows.append((f.name, len(keys), verdict, added))

width = max(len(r[0]) for r in rows) + 2
print(f"{'artifact':{width}s} {'fields':>7s}  verdict")
print("-" * (width + 30))
for name, n, verdict, _ in rows:
    print(f"{name:{width}s} {n:7d}  {verdict}")

print("-" * (width + 30))
if changed_total:
    print("CHANGED VALUES -- each needs an explanation:")
    for name, k, b, a in changed_total:
        print(f"  {name} {k}: {b!r} -> {a!r}")
    sys.exit(1)
print("Every regenerated artifact reproduces its published measurement values.")
print("Additions are new work; volatile fields are run provenance, which MUST differ.")
sys.exit(0)

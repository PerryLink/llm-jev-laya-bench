"""Correct the re-run verdict: an artifact that was never rewritten is NOT a reproduction.

THE FLAW IN p68
    It diffed `results/X.json` against `results/_superseded/X.json.pre-rerun`. But the archiver
    copies the artifact to that path BEFORE attempting the run. So when a run fails or is never
    attempted, the backup is a byte-copy of the artifact itself, and the diff compares a file
    against itself and reports "reproduced exactly".

    Ten artifacts came back that way. Every one of them was a false positive.

    This is the same class of error the whole project keeps finding: a check that reports success
    because it cannot see the failure. A backup diff cannot distinguish "reproduced" from "never
    ran" -- only a change in the artifact's own bytes can establish that a run happened.

THE FIX
    Compare each artifact against the IMMUTABLE baseline taken before anything was touched
    (`rerun/baseline/`). Three cases:

      UNCHANGED  -- identical to the baseline: the run never happened. NOT a result.
      CHANGED    -- the run happened; now compare values against the pre-rerun copy.
      MISSING    -- no baseline to compare against; report rather than assume.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import RESULTS, ROOT  # noqa: E402

BASELINE = ROOT / "rerun" / "baseline"
PRE = RESULTS / "_superseded"

VOLATILE = ("mtime", "timestamp", "_rerun", "wall_ms", "latency_ms", "elapsed", "date",
            "_instrument", "uptime", "calls", "recorded_at", "duration", "drift")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


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


def volatile(k: str) -> bool:
    return any(v in k.lower() for v in VOLATILE)


if not BASELINE.exists():
    print(f"no immutable baseline at {BASELINE} -- cannot distinguish ran from never-ran")
    sys.exit(2)

rows, changed_values = [], []
for f in sorted(RESULTS.glob("*.json")):
    b = BASELINE / f.name
    if not b.exists():
        rows.append((f.name, "no baseline", ""))
        continue
    if sha(f) == sha(b):
        rows.append((f.name, "UNCHANGED", "never re-run -- not a result"))
        continue

    # the run happened; compare values against the pre-rerun copy
    p = PRE / (f.name + ".pre-rerun")
    if not p.exists() or sha(p) == sha(f):
        rows.append((f.name, "CHANGED (bytes)", "ran; no usable pre-rerun copy"))
        continue
    after, before = flat(json.loads(f.read_text(encoding="utf-8"))), flat(
        json.loads(p.read_text(encoding="utf-8")))
    keys = set(after) | set(before)
    hard = [k for k in keys
            if k in before and k in after and before[k] != after[k] and not volatile(k)]
    added = [k for k in keys if k not in before and not volatile(k)]
    changed_values += [(f.name, k, before[k], after[k]) for k in hard]
    rows.append((f.name, "CHANGED (bytes)",
                 f"{len(hard)} value(s) differ" + (f", {len(added)} added" if added else "")))

w = max(len(r[0]) for r in rows) + 2
print(f"{'artifact':{w}s} {'status':16s} note")
print("-" * (w + 46))
for name, status, note in rows:
    print(f"{name:{w}s} {status:16s} {note}")

ran = sum(1 for r in rows if r[1].startswith("CHANGED"))
never = sum(1 for r in rows if r[1] == "UNCHANGED")
print("-" * (w + 46))
print(f"{ran} artifact(s) were actually re-run; {never} were never rewritten.")
print("Only the former can be called a reproduction, in either direction.")
if changed_values:
    print(f"\n{len(changed_values)} measurement value(s) differ -- each needs an explanation:")
    for name, k, b, a in changed_values[:20]:
        print(f"  {name} {k}: {b!r} -> {a!r}")
sys.exit(0)

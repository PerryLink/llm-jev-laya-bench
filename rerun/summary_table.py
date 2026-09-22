"""Master comparison: every artifact, regenerated or not, against the immutable baseline.

Prints one row per artifact for the report. It does NOT classify -- classification is a
judgement about which differing paths are measurements and which are instrumentation
state, and that judgement is written out by hand in RERUN-REPORT.md with the numbers.

The 'non-instrument' column excludes paths whose NAME marks them as run state or as
network timing (latency, wall clock, uptime, call counters, timestamps). Those MUST differ
between two runs; they are separated so a real disagreement is not hidden among them.
"""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path("rerun/baseline")
CUR = Path("results")
SCRATCH = Path(r"D:\Projects\llm-jev-laya-bench-rerun-scratch\results")

INSTRUMENTISH = ("latency", "recorded_at", "timestamp", "uptime", "cold_start",
                 "restart_count", "/calls", "elapsed", "generated_at", "mtime",
                 "wall", "duration", "_spend_usd", "run_at")


def leaves(node, path="$"):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from leaves(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from leaves(v, f"{path}[{i}]")
    else:
        yield path, node


rows = []
for b in sorted(BASE.glob("*.json")):
    name = b.name
    live = CUR / name
    scr = SCRATCH / name
    src = live if live.exists() else (scr if scr.exists() else None)
    if src is None:
        rows.append((name, "NO FILE", "", "", "", ""))
        continue
    bo = dict(leaves(json.loads(b.read_text(encoding="utf-8"))))
    no = dict(leaves(json.loads(src.read_text(encoding="utf-8"))))
    changed = [p for p in set(bo) & set(no) if bo[p] != no[p]]
    only_old = sorted(set(bo) - set(no))
    only_new = sorted(set(no) - set(bo))
    non_instr = [p for p in changed
                 if not any(m in p.lower() for m in INSTRUMENTISH)]
    # structural drift in the provenance manifest is counted separately
    prov = [p for p in (only_old + only_new) if "instrument_hash" in p]
    other_struct = [p for p in (only_old + only_new) if "instrument_hash" not in p]
    same_bytes = (b.read_bytes() == src.read_bytes())
    rows.append((name, "SAME BYTES" if same_bytes else "REWRITTEN",
                 len(bo), len(no), len(changed), len(non_instr),
                 len(only_old), len(only_new), len(prov), len(other_struct)))

print(f"{'artifact':48s} {'status':11s} {'old':>5} {'new':>5} {'chg':>5} "
      f"{'non-instr':>9} {'-only':>6} {'+only':>6} {'prov':>5} {'struct':>6}")
print("-" * 122)
for r in rows:
    if r[1] == "NO FILE":
        print(f"{r[0]:48s} {r[1]}")
        continue
    print(f"{r[0]:48s} {r[1]:11s} {r[2]:>5} {r[3]:>5} {r[4]:>5} {r[5]:>9} "
          f"{r[6]:>6} {r[7]:>6} {r[8]:>5} {r[9]:>6}")

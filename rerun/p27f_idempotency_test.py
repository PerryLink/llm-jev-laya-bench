"""P27f IDEMPOTENCY TEST -- run the repair twice on a byte-identical copy of the tree.

The published `results/P27b-plugin-crossval.json` and its `.pre-repair` copy already show
the symptom; this reproduces it live so the defect is demonstrated rather than inferred.

Runs against D:\\Projects\\llm-jev-laya-bench-rerun-scratch (a byte copy), so the published
tree is not touched. No API calls.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRATCH = Path(r"D:\Projects\llm-jev-laya-bench-rerun-scratch")
PY = r"D:\Projects\laya-family\.venv-laya\Scripts\python.exe"
ART = SCRATCH / "results" / "P27b-plugin-crossval.json"
LIVE = SCRATCH / "results" / "P27-jev-live.json"


def snapshot(tag: str) -> dict:
    d = json.loads(ART.read_text(encoding="utf-8"))
    L = d["latency_self_report_vs_wall_clock"]
    out = {
        "tag": tag,
        "top_level_ratio_unmatched": L["ratio_of_medians_unmatched"],
        "top_level_unmatched_p50": L["unmatched_direct_for_reference"]["p50_ms"],
        "stale_superseded": L.get("_stale_superseded"),
    }
    print(f"--- {tag}")
    print(f"    ratio_of_medians_unmatched          = {out['top_level_ratio_unmatched']}")
    print(f"    unmatched_direct_for_reference.p50  = {out['top_level_unmatched_p50']}")
    ss = out["stale_superseded"]
    if ss:
        print(f"    _stale_superseded.superseded_p50    = "
              f"{ss.get('superseded_unmatched_p50_ms')}")
        print(f"    _stale_superseded.superseded_ratio  = "
              f"{ss.get('superseded_ratio_of_medians_unmatched')}")
    else:
        print("    _stale_superseded                   = ABSENT")
    return out


states = [snapshot("BEFORE any p27f run (scratch = published bytes)")]

for i in (1, 2, 3):
    r = subprocess.run([PY, str(SCRATCH / "src/instrument/p27f_repair_p27_family.py")],
                       cwd=str(SCRATCH), capture_output=True, text=True)
    print(f"\n=== p27f pass {i}: exit={r.returncode} ===")
    print("\n".join("    " + ln for ln in r.stdout.strip().splitlines()[:8]))
    if r.returncode:
        print("    STDERR:", r.stderr[-600:])
    states.append(snapshot(f"after p27f pass {i}"))

print()
print("=" * 76)
print("VERDICT")
p1 = states[1]["stale_superseded"] or {}
p0 = states[0]["stale_superseded"] or {}
print(f"  before pass 1, the record said superseded p50 = "
      f"{p0.get('superseded_unmatched_p50_ms')} / ratio "
      f"{p0.get('superseded_ratio_of_medians_unmatched')}")
print(f"  after  pass 1, the record says  superseded p50 = "
      f"{p1.get('superseded_unmatched_p50_ms')} / ratio "
      f"{p1.get('superseded_ratio_of_medians_unmatched')}")
print(f"  identical to the post-repair top-level values? "
      f"{p1.get('superseded_unmatched_p50_ms') == states[1]['top_level_unmatched_p50']}")
print(f"  pass 2 and pass 3 leave it unchanged? "
      f"{states[2]['stale_superseded'] == states[3]['stale_superseded']}")

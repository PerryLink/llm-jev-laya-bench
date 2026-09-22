"""Which copy pins the published chain numbers, and is the n=69 pilot still intact?

Two questions the Option-A fix depends on, both answered from the tree rather than assumed:
  1. which on-disk copy reproduces the PUBLISHED fixed-battery numbers (LLM 0.6765 / 0.6618 /
     0.6618, Delta_catch -0.2332 / -0.2473 / -0.1816)? It must be one the paper can cite and a
     check can read.
  2. is the n=69 PILOT still the published recorded round, and does it still carry the `_repair`
     note the 61-item denominator depends on? (RERUN-P22-PILOT-OVERWRITTEN.md says the live
     artifact was overwritten with an n=68 battery.)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "results"


def show(label: str, path: Path) -> dict | None:
    if not path.exists():
        print(f"  {label:44s} ABSENT  {path}")
        return None
    raw = path.read_bytes()
    d = json.loads(raw.decode("utf-8"))
    s = d.get("summary", {})
    conf = s.get("confusion", {})
    print(f"  {label:44s} rows={len(d.get('rows', [])):3d}  "
          f"llm={s.get('llm_overall_accuracy')}  "
          f"delta={s.get('delta_catch')}  conf={conf}  "
          f"_repair={'yes' if '_repair' in s else 'NO'}  "
          f"sha256={hashlib.sha256(raw).hexdigest()[:12]}")
    return d


print("=== fixed battery (n=68) ===")
for i in (1, 2, 3):
    show(f"live P22b-fixed-r{i}", R / f"P22b-fixed-r{i}.json")
for i in (1, 2, 3):
    show(f"_superseded .pre-repair r{i}", R / "_superseded" / f"P22b-fixed-r{i}.json.pre-repair")
for i in (1, 2, 3):
    show(f"rerun/baseline r{i}", ROOT / "rerun" / "baseline" / f"P22b-fixed-r{i}.json")

print("\n=== pilot (n=69, the recorded draw) ===")
show("live P22-chain-audit", R / "P22-chain-audit.json")
show("_superseded .pre-rerun", R / "_superseded" / "P22-chain-audit.json.pre-rerun")
show("rerun/baseline", ROOT / "rerun" / "baseline" / "P22-chain-audit.json")

# is the live pilot byte-identical to the immutable baseline?
live = (R / "P22-chain-audit.json").read_bytes()
base = (ROOT / "rerun" / "baseline" / "P22-chain-audit.json").read_bytes()
print(f"\n  live pilot == immutable baseline: {live == base}")

# does the seed still rebuild the pilot? ask the generator directly, without writing anything
try:
    import subprocess
    import sys
    gen = ROOT / "src" / "items" / "p22_chain_audit.py"
    src = gen.read_text(encoding="utf-8")
    print(f"  generator {gen.name}: builds n="
          f"{'fixed 68' if '68' in src and 'p22f' in src else 'unknown'} "
          f"(mentions alt-preinsertion rule: {'alt' in src})")
    print("  note: the pilot's item set is SEEDED, so it is rebuildable only by code that still "
          "implements the OLD option-set policy")
except Exception as exc:                                         # noqa: BLE001
    print(f"  generator probe failed: {exc}")

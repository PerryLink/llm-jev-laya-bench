"""P22b: are the OPTION SETS the same? The artifacts record the chosen VALUE but not the
criteria, so membership of the published chosen value in the current option set is the
test that separates 'the judge answered differently' from 'the options changed'.

Read-only; makes no model calls.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src" / "instrument"))
sys.path.insert(0, str(ROOT / "src" / "items"))

spec = importlib.util.spec_from_file_location(
    "p22_mod", str(ROOT / "src" / "items" / "p22_chain_audit.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

items = {it["item_id"]: it for it in mod.build_items()}
pub = json.load(open("results/P22b-fixed-r1.json", encoding="utf-8"))
new = json.load(open("results/P22b-fixed-r1.json", encoding="utf-8"))

print(f"current build_items() -> {len(items)} items")

base = json.load(open("rerun/baseline/P22b-fixed-r1.json", encoding="utf-8"))
br = {r["item_id"]: r for r in base["rows"]}

same_set = diff_set = missing = 0
examples = []
for iid, r in br.items():
    it = items.get(iid)
    if it is None:
        missing += 1
        continue
    cur_vals = set(it["criteria"].values())
    if str(r["truth"]) not in cur_vals:
        # truth must always be offered; if not, the item itself changed
        diff_set += 1
        examples.append((iid, "TRUTH NOT IN CURRENT OPTIONS", r["truth"], sorted(cur_vals)))
        continue
    if str(r["laya_value"]) in cur_vals:
        same_set += 1
    else:
        diff_set += 1
        if len(examples) < 8:
            examples.append((iid, "published chosen value not offered now",
                             r["laya_value"], sorted(cur_vals)))

print(f"published item_ids missing from current battery : {missing}")
print(f"published chosen VALUE still offered now        : {same_set}")
print(f"published chosen VALUE no longer offered        : {diff_set}")
for e in examples[:8]:
    print(f"   {e[0]}: {e[1]}  published={e[2]}  current_options={e[3]}")

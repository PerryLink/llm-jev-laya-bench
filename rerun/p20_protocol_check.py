"""P20: did the re-run measure a DIFFERENT PROTOCOL rather than disagree with a run?

Reads the published (baseline) artifact, the re-run artifact, and the current script's
criteria construction, and prints the evidence side by side. Read-only.
"""
from __future__ import annotations

import json

b = json.load(open("rerun/baseline/P20-language-misrouting.json", encoding="utf-8"))
n = json.load(open("results/P20-language-misrouting.json", encoding="utf-8"))

print("== provenance of the two files ==")
print("  published artifact rows keys :", sorted(b["rows"][0].keys()))
print("  re-run    artifact rows keys :", sorted(n["rows"][0].keys()))
print("  published records criteria?  :", "criteria_used" in b["rows"][0])
print("  re-run    records criteria?  :", "criteria_used" in n["rows"][0])

print()
print("== source: src/items/p20_language_misrouting.py ==")
src = open("src/items/p20_language_misrouting.py", encoding="utf-8").read().splitlines()
for i in range(103, 116):
    print(f"  {i+1:4d}| {src[i]}")

print()
print("== the numbers the paper quotes ==")
for label, d in (("published", b), ("re-run", n)):
    s = d["summary"]
    print(f"  {label}:")
    for grp_name in ("english_native", "other_latin_script", "non_latin_script"):
        g = s.get(grp_name) or {}
        print(f"    {grp_name:20s} n={g.get('n')} acc={g.get('accuracy')} "
              f"p_true|true={g.get('mean_p_true_on_true_items')} "
              f"p_true|FALSE={g.get('mean_p_true_on_false_items')}")
    print(f"    always_true_baseline n_at_or_above = "
          f"{s.get('groups_exceeding_always_true_baseline')}")
    print(f"    verdict = {str(s.get('verdict'))[:180]}")

print()
print("== per-language p_true on the FALSE item ==")
print(f"  {'lang':6} {'published':>10} {'re-run':>10}   band published -> re-run   correct")
for rb, rn in zip(b["rows"], n["rows"]):
    fb, fn = rb.get("false_item") or {}, rn.get("false_item") or {}
    print(f"  {rb['lang']:6} {str(fb.get('p_true')):>10} {str(fn.get('p_true')):>10}   "
          f"{str(fb.get('band')):>10} -> {str(fn.get('band')):<10} "
          f"{fb.get('correct')} -> {fn.get('correct')}")

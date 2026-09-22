"""P14: compare the SUMMARY, not the rows, for a single-draw stochastic arm.

Per-item text and token counts must move when temperature is not pinned (ERRATA 9). The
question is whether the published point estimates survive.
"""
from __future__ import annotations

import json

b = json.load(open("rerun/baseline/P14-llm-arm-full.json", encoding="utf-8"))
n = json.load(open("results/P14-llm-arm-full.json", encoding="utf-8"))

print("=" * 74)
print("SUMMARY -- published vs re-run")
print("=" * 74)
bs, ns = b["summary"], n["summary"]
for k in sorted(set(bs) | set(ns)):
    if isinstance(bs.get(k), dict) or isinstance(ns.get(k), dict):
        continue
    same = "SAME" if bs.get(k) == ns.get(k) else "DIFF"
    print(f"  {same}  {k}")
    if same == "DIFF":
        print(f"          published={bs.get(k)}   re-run={ns.get(k)}")
for k in sorted(set(bs) | set(ns)):
    if isinstance(bs.get(k), dict):
        for kk in sorted(set(bs[k]) | set((ns.get(k) or {}))):
            a, c = bs[k].get(kk), (ns.get(k) or {}).get(kk)
            if isinstance(a, (dict, list)) or isinstance(c, (dict, list)):
                continue
            if a != c:
                print(f"  DIFF  {k}.{kk}: {a} -> {c}")

print()
print("=" * 74)
print("COMPLEMENTARITY -- forced-choice arm and PROSE arm")
print("=" * 74)
for label, key in (("forced choice", "complementarity"),
                   ("PROSE arm", "complementarity_prose_arm")):
    bb = (b.get(key) or {})
    nn = (n.get(key) or {})
    print(f"\n  --- {label}")
    for k in ("n_paired", "llm_accuracy_on_paired", "typed_accuracy_on_paired",
              "P_typed_correct_given_llm_wrong", "P_typed_correct_given_llm_right",
              "delta_catch", "kappa_agreement"):
        same = "SAME" if bb.get(k) == nn.get(k) else "DIFF"
        print(f"    {same}  {k:36s} published={bb.get(k)}  re-run={nn.get(k)}")
    for k in ("confusion",):
        print(f"          {k}: published={bb.get(k)}  re-run={nn.get(k)}")

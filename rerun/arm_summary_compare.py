"""Summary-level comparison for the complementarity arms (regimes 2 and 3).

These are single unpinned draws, so per-item rows must move. The question is whether the
published point estimates -- accuracy, delta_catch, kappa, confusion -- survive.
"""
from __future__ import annotations

import json

ARMS = ["P15-complementarity-strong-regime",
        "P15b-rep-r1", "P15b-rep-r2", "P15b-rep-r3",
        "P22-chain-audit", "P22b-fixed-r1", "P22b-fixed-r2", "P22b-fixed-r3",
        "P24-reduced-horizon"]

KEYS = ["n_items", "laya_hierarchical_accuracy", "laya_group_selection_accuracy",
        "llm_flat77_accuracy", "llm_accuracy_by_k", "laya_accuracy_by_k",
        "llm_overall_accuracy", "laya_overall_accuracy",
        "P_typed_correct_given_llm_wrong", "P_typed_correct_given_llm_right",
        "delta_catch", "kappa_agreement", "confusion", "llm_sampling"]

for name in ARMS:
    try:
        b = json.load(open(f"rerun/baseline/{name}.json", encoding="utf-8"))["summary"]
        d = json.load(open(f"results/{name}.json", encoding="utf-8"))["summary"]
    except Exception as exc:
        print(f"{name}: {exc}")
        continue
    diffs = []
    for k in KEYS:
        if k in b or k in d:
            if b.get(k) != d.get(k):
                diffs.append((k, b.get(k), d.get(k)))
    print("=" * 78)
    print(f"{name}   ({'IDENTICAL headline summary' if not diffs else str(len(diffs)) + ' differing headline fields'})")
    for k, x, y in diffs:
        print(f"   {k}")
        print(f"      published = {json.dumps(x, ensure_ascii=False)[:300]}")
        print(f"      re-run    = {json.dumps(y, ensure_ascii=False)[:300]}")
    if not diffs:
        keep = {k: b.get(k) for k in ("llm_flat77_accuracy", "delta_catch",
                                      "llm_overall_accuracy", "laya_hierarchical_accuracy")
                if k in b}
        print("   ", json.dumps(keep, ensure_ascii=False))

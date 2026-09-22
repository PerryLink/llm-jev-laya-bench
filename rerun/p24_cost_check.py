"""Why did P24 cost 4.5x less on the re-run? Compare structure and error counts.

A cheaper arm is not automatically a wrong arm (fewer reasoning tokens is a legitimate
outcome), but it must be explained before it is reported.
"""
from __future__ import annotations

import json

b = json.load(open("rerun/baseline/P24-reduced-horizon.json", encoding="utf-8"))
n = json.load(open("results/P24-reduced-horizon.json", encoding="utf-8"))

for lbl, d in (("published", b), ("re-run", n)):
    rows = d.get("rows") or []
    costs = [r.get("llm_cost") for r in rows if isinstance(r.get("llm_cost"), (int, float))]
    errs = [r for r in rows if r.get("llm_error")]
    print(f"--- {lbl}: rows={len(rows)} cost_rows={len(costs)} "
          f"sum=${sum(costs):.9f} mean=${sum(costs)/max(1,len(costs)):.9f} "
          f"llm_errors={len(errs)}")
    comp = [r.get("llm_completion_tokens") for r in rows
            if isinstance(r.get("llm_completion_tokens"), (int, float))]
    if comp:
        print(f"    completion_tokens: n={len(comp)} mean={sum(comp)/len(comp):.1f} "
              f"max={max(comp)}")
    else:
        k = sorted(rows[0].keys()) if rows else []
        print(f"    row keys: {k}")
    s = d.get("summary") or {}
    for kk in ("n_items", "horizon", "llm_accuracy", "laya_accuracy", "verdict"):
        if kk in s:
            print(f"    summary.{kk} = {json.dumps(s[kk], ensure_ascii=False)[:160]}")

print()
print("summary diff:")
bs, ns = b.get("summary") or {}, n.get("summary") or {}
for k in sorted(set(bs) | set(ns)):
    if isinstance(bs.get(k), (dict, list)) or isinstance(ns.get(k), (dict, list)):
        continue
    if bs.get(k) != ns.get(k):
        print(f"  {k}: {bs.get(k)} -> {ns.get(k)}")

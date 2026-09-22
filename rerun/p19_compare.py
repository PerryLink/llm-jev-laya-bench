"""P19 (n=1100): the headline calibration numbers, published vs re-run."""
from __future__ import annotations

import json

b = json.load(open("rerun/baseline/P19-calibration.json", encoding="utf-8"))
n = json.load(open("results/P19-calibration.json", encoding="utf-8"))

for lbl, d in (("published", b), ("re-run", n)):
    s = d["summary"]
    L = s["laya"]
    print(f"--- {lbl}: n_items={s['n_items']}")
    for k, v in L.items():
        if k == "calibration":
            c = v
            print(f"    laya.calibration: n={c.get('n')} ece={c.get('ece')} "
                  f"brier={c.get('brier')}")
            for binn in (c.get("bins") or [])[:3]:
                print(f"        {binn}")
        elif not isinstance(v, (dict, list)):
            print(f"    laya.{k} = {v}")
    for k in ("llm", "llm_accuracy", "llm_false_rate"):
        if k in s:
            v = s[k]
            print(f"    {k} = {json.dumps(v, ensure_ascii=False)[:200]}")
    print(f"    summary keys: {sorted(s.keys())}")

# per-row Laya agreement: Laya is deterministic, so the Laya column should match exactly
br = {r["item_id"]: r for r in b["rows"]}
nr = {r["item_id"]: r for r in n["rows"]}
common = sorted(set(br) & set(nr))
print()
print(f"rows: published={len(br)} re-run={len(nr)} common={len(common)}")
for f in ("level", "truth", "laya_p", "laya_pred", "laya_correct",
          "llm_label", "llm_p", "llm_pred", "llm_correct"):
    diff = [i for i in common if br[i].get(f) != nr[i].get(f)]
    print(f"  {f:14s} differs on {len(diff):5d}/{len(common)}")

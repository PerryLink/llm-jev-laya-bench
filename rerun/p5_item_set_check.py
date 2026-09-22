"""P5: is the disagreement a different ITEM SET rather than a different judgement?

`true_pos` is a property of the deterministic item generator (`pipeline.generate`,
seed 20260922), not of the judge. If it moved, the generator changed and the two runs
did not measure the same input. Read-only.
"""
from __future__ import annotations

import json
from pathlib import Path

b = json.load(open("rerun/baseline/P5-certificate-verification.json", encoding="utf-8"))
n = json.load(open("results/P5-certificate-verification.json", encoding="utf-8"))

print(f"{'item':16}{'level':>6}{'true_pos old':>14}{'true_pos new':>14}"
      f"{'tok old':>9}{'tok new':>9}   with_carrier_correct old->new")
for rb, rn in zip(b["rows"], n["rows"]):
    print(f"{rb['item_id']:16}{rb['level']:>6}{rb['true_pos']:>14}{rn['true_pos']:>14}"
          f"{rb['state_tokens']:>9}{rn['state_tokens']:>9}   "
          f"{str(rb['with_carrier_correct']):>5} -> {rn['with_carrier_correct']}")

print()
print("published by_level:", json.dumps(b["summary"]["by_level"]))
print("re-run    by_level:", json.dumps(n["summary"]["by_level"]))

# does a frozen copy of the generated items exist?
for cand in ("src/items/evidence-brief-pilot.json", "items/evidence-brief-pilot.json"):
    p = Path(cand)
    print(f"\n{cand}: exists={p.exists()}"
          + (f"  size={p.stat().st_size}" if p.exists() else ""))
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        print("  generated_at_utc:", d.get("generated_at_utc"))
        print("  n_items:", d.get("n_items"))
        it = (d.get("items") or [])
        if it:
            print("  first item meta:", json.dumps(it[0].get("meta"))[:200])
            print("  item_id/true_pos:", [(x["item_id"], (x.get("meta") or {}).get("true_pos"))
                                          for x in it])

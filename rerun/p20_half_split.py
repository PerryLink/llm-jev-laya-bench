"""P20: is the disagreement confined to the half of the battery that had the bad rubric?

If the diagnosis (false-item rubric named the wrong value) is right, then the TRUE-item
arm -- whose rubric was correct in both versions -- must reproduce exactly, and only the
FALSE-item arm may move. Read-only.
"""
from __future__ import annotations

import json

b = json.load(open("rerun/baseline/P20-language-misrouting.json", encoding="utf-8"))
n = json.load(open("results/P20-language-misrouting.json", encoding="utf-8"))

fields = ("p_true", "pred", "correct", "band", "detected_lang", "model_used")
for arm in ("true_item", "false_item"):
    same = diff = 0
    moved = []
    for rb, rn in zip(b["rows"], n["rows"]):
        x, y = rb.get(arm) or {}, rn.get(arm) or {}
        for f in fields:
            if x.get(f) == y.get(f):
                same += 1
            else:
                diff += 1
                moved.append((rb["lang"], f, x.get(f), y.get(f)))
    print(f"{arm:11s}: identical fields={same}  differing={diff}")
    for m in moved[:14]:
        print(f"     {m[0]:>3} {m[1]:<14} {str(m[2]):>10} -> {str(m[3])}")

print()
print("state templates are shared by both arms (one state per language):",
      json.load(open("rerun/baseline/P20-language-misrouting.json",
                     encoding="utf-8"))["summary"]["per_language"]["en"]["true_item"]
      is not None)

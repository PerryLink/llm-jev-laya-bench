"""P22b: distinguish "Laya answered differently" from "the options were ordered differently".

The rows record both the chosen LABEL and the chosen VALUE. If only the label moved, the
option order changed (a code change); if the value moved, the judge changed its answer.
Read-only.
"""
from __future__ import annotations

import json

b = json.load(open("rerun/baseline/P22b-fixed-r1.json", encoding="utf-8"))
n = json.load(open("results/P22b-fixed-r1.json", encoding="utf-8"))
br = {r["item_id"]: r for r in b["rows"]}
nr = {r["item_id"]: r for r in n["rows"]}
common = sorted(set(br) & set(nr))

key_diff = [i for i in common if br[i].get("laya_label") != nr[i].get("laya_label")]
val_diff = [i for i in common if br[i].get("laya_value") != nr[i].get("laya_value")]
corr_diff = [i for i in common if br[i].get("laya_correct") != nr[i].get("laya_correct")]
print(f"items compared                 : {len(common)}")
print(f"laya_label differs on          : {len(key_diff)}")
print(f"laya_VALUE differs on          : {len(val_diff)}")
print(f"laya_correct differs on        : {len(corr_diff)}")
print()
print("sample rows where the label moved:")
for i in (key_diff + val_diff)[:8]:
    print(f"  {i}")
    print(f"     published: label={br[i].get('laya_label')} value={br[i].get('laya_value')} "
          f"correct={br[i].get('laya_correct')} truth={br[i].get('truth')}")
    print(f"     re-run   : label={nr[i].get('laya_label')} value={nr[i].get('laya_value')} "
          f"correct={nr[i].get('laya_correct')} truth={nr[i].get('truth')}")

print()
print("was the correct answer the SAME CHOICE POSITION in both?")
print("  (laya_label is o01..o04 -- a position; laya_value is the number chosen)")
pos_flip_value_same = sum(1 for i in key_diff if br[i].get("laya_value") == nr[i].get("laya_value"))
print(f"  of {len(key_diff)} label changes, {pos_flip_value_same} kept the SAME value "
      f"-> the option order moved, the judgement did not")

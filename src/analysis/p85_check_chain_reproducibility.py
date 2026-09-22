import json
from pathlib import Path

R = Path("results")
SUP = R / "_superseded"


def rows(p):
    return {r["item_id"]: r for r in json.loads(Path(p).read_text(encoding="utf-8"))["rows"]}


new = {k: rows(R / f"P22b-fixed-r{k}.json") for k in (1, 2, 3)}
sup = {k: rows(SUP / f"P22b-fixed-r{k}.json.pre-repair") for k in (1, 2, 3)}
pilot_new = rows(R / "P22-chain-audit.json")
pilot_old = rows(SUP / "P22-chain-audit.json.pre-rerun")

print("live P22b r1 n =", len(new[1]), "| backup P22b r1 n =", len(sup[1]))
print("live pilot n  =", len(pilot_new), "| backup pilot n =", len(pilot_old))

common = set(new[1]) & set(new[2]) & set(new[3])
print("shared items across the three new draws:", len(common))


def agree(a, b, key):
    shared = set(a) & set(b)
    same = sum(1 for i in shared if a[i].get(key) == b[i].get(key))
    return f"{same}/{len(shared)}"


for key in ("laya_label", "llm_label", "laya_correct", "llm_correct"):
    print(f"  {key:14s} r1 vs r2: {agree(new[1], new[2], key)}   "
          f"r1 vs r3: {agree(new[1], new[3], key)}   "
          f"r1(new) vs r1(old backup): {agree(new[1], sup[1], key)}")

# Laya determinism is a published claim: is the judge arm still a deterministic function?
judge_diffs = [(i, sup[1][i]["laya_label"], new[1][i]["laya_label"])
               for i in set(sup[1]) & set(new[1])
               if sup[1][i]["laya_label"] != new[1][i]["laya_label"]]
print("Laya label changes between the old and new r1:", judge_diffs[:5], f"({len(judge_diffs)})")
print("Laya accuracy now:", sum(1 for r in new[1].values() if r["laya_correct"]) / len(new[1]))
print("Laya accuracy backup:", sum(1 for r in sup[1].values() if r["laya_correct"]) / len(sup[1]))
print("LLM accuracy now:", sum(1 for r in new[1].values() if r["llm_correct"]) / len(new[1]))
print("LLM accuracy backup:", sum(1 for r in sup[1].values() if r["llm_correct"]) / len(sup[1]))
print("alt_in_options present now:", "alt_in_options" in next(iter(new[1].values())))
print("alt not offered (new r1):",
      sum(1 for r in new[1].values() if r.get("alt_in_options") is False))

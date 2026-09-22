import json
from pathlib import Path

R = Path("results")
d = json.loads((R / "P28-recomputed-statistics.json").read_text(encoding="utf-8"))
print("=== P28 regime3 (recomputed from the LIVE artifacts) ===")
for b in d["regime3"]:
    vm = b.get("vs_marginal_one_sided") or {}
    print(f"{b['label']:24s} n={b['n']:3d} tbl={b['table']} "
          f"delta={b['delta_catch']} fisher={b['fisher_p']} phi={b['phi']}")
    print(f"{'':24s} exact_binom={vm.get('exact_binomial_lower_tail')} "
          f"normal={vm.get('normal_approximation')} x/n={vm.get('x')}/{vm.get('n')} "
          f"base={vm.get('baseline')}")

print("\n=== what the manuscript still prints (chain block) ===")
t = (Path("paper") / "MANUSCRIPT.md").read_text(encoding="utf-8")
for needle in ("0.6765", "0.2941", "0.2332", "0.086", "0.052", "0.076", "86.8", "61/61"):
    print(f"  {needle!r:12s} in manuscript: {needle in t}")

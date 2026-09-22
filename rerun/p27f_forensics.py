"""P27f idempotency forensics -- read-only over the published tree.

Establishes, from bytes already on disk, what p27f's first and second passes each did.
"""
from __future__ import annotations

import json
from pathlib import Path

R = Path("results")


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


cur = load(R / "P27b-plugin-crossval.json")
pre = load(R / "_superseded" / "P27b-plugin-crossval.json.pre-repair")

for label, d in (("CURRENT  results/P27b-plugin-crossval.json", cur),
                 ("PRE-REPAIR  _superseded/...pre-repair", pre)):
    L = d["latency_self_report_vs_wall_clock"]
    print("=" * 76)
    print(label)
    print("  unmatched_direct_for_reference.p50_ms      =",
          L["unmatched_direct_for_reference"]["p50_ms"])
    print("  unmatched_direct_for_reference.mean_cost_usd =",
          L["unmatched_direct_for_reference"].get("mean_cost_usd"))
    print("  ratio_of_medians_unmatched                 =",
          L["ratio_of_medians_unmatched"])
    print("  ratio_of_medians_matched                   =",
          L["ratio_of_medians_matched"])
    print("  _stale_superseded =",
          json.dumps(L.get("_stale_superseded"), ensure_ascii=False, indent=4))

# full structural diff between the two, ignoring nothing
def leaves(node, path="$"):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from leaves(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from leaves(v, f"{path}[{i}]")
    else:
        yield path, node


a = dict(leaves(pre))
b = dict(leaves(cur))
diff = [p for p in sorted(set(a) & set(b)) if a[p] != b[p]]
print("=" * 76)
print(f"leaves: pre-repair={len(a)} current={len(b)} differing={len(diff)} "
      f"only_in_pre={sorted(set(a) - set(b))} only_in_cur={sorted(set(b) - set(a))}")
for p in diff:
    print(f"  ~ {p}\n      pre-repair={json.dumps(a[p], ensure_ascii=False)[:200]}"
          f"\n      current   ={json.dumps(b[p], ensure_ascii=False)[:200]}")

# the P27 ledger artifact too
print("=" * 76)
c = load(R / "P27-jev-live.json")
p27pre = load(R / "_superseded" / "P27-jev-live.json.pre-repair")
print("P27-jev-live.json  _spend_usd                       =", c["_spend_usd"])
print("  cost._ledger_reconciliation present in current     =",
      "_ledger_reconciliation" in (c.get("cost") or {}))
print("  cost._ledger_reconciliation present in pre-repair  =",
      "_ledger_reconciliation" in (p27pre.get("cost") or {}))
if "_ledger_reconciliation" in (c.get("cost") or {}):
    print("  residual_usd =", c["cost"]["_ledger_reconciliation"]["unpersisted_residual_usd"],
          " n_rows =", c["cost"]["_ledger_reconciliation"]["n_persisted_cost_rows"])

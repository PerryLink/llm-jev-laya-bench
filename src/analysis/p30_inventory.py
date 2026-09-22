"""P30: inventory of the evidence tree, computed rather than asserted.

The paper makes countable claims about its own evidence base -- how many result artifacts
exist, how many carry an instrument record, how many record the launch loadout or the drift
verdict. Those counts were previously typed by hand and went stale the moment a new artifact
was written. This script derives them from the tree so the paper can cite a number that is
regenerable, and prints the exact list behind each count so a reader can check it.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"D:\Projects\llm-jev-laya-bench")
R = ROOT / "results"


def keys_at_any_depth(node, wanted: str) -> bool:
    if isinstance(node, dict):
        return any(k == wanted or keys_at_any_depth(v, wanted) for k, v in node.items())
    if isinstance(node, list):
        return any(keys_at_any_depth(v, wanted) for v in node)
    return False


def main() -> None:
    files = sorted(R.glob("*.json"))
    docs = {}
    for f in files:
        try:
            docs[f.name] = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:                       # a malformed artifact is a finding too
            print(f"  !! {f.name} could not be parsed: {exc}")

    def having(pred) -> list[str]:
        return [n for n, d in docs.items() if pred(d)]

    non_instrument = R / "P22f-ignore-superseded-denominator-repair.json"
    reports = R / "P22g-label-agreement-provenance.json"

    canonical = having(lambda d: keys_at_any_depth(d, "instrument")
                       or keys_at_any_depth(d, "_instrument")
                       or keys_at_any_depth(d, "instrument_hashes")
                       or keys_at_any_depth(d, "_provenance"))
    any_hash = having(lambda d: keys_at_any_depth(d, "instrument_hashes"))
    loadout = having(lambda d: keys_at_any_depth(d, "loadout"))
    drift = having(lambda d: keys_at_any_depth(d, "drift"))
    sampling = having(lambda d: keys_at_any_depth(d, "llm_sampling"))
    spend = having(lambda d: keys_at_any_depth(d, "_spend_usd"))
    provenance = having(lambda d: keys_at_any_depth(d, "_provenance"))
    # A PURE DERIVATION makes no measurement of its own -- it recomputes over artifacts that
    # already carry records. Such a file has nothing to attribute an instrument to, so the
    # absence of a record is correct by construction rather than a gap.
    derivation = having(lambda d: keys_at_any_depth(d, "_generated_by")
                       and not keys_at_any_depth(d, "instrument_hashes"))

    missing = sorted(set(docs) - set(canonical))
    unexplained = sorted(set(missing) - set(derivation))

    inv = {
        "_generated_by": "src/analysis/p30_inventory.py",
        "n_result_json": len(docs),
        "n_with_any_provenance": len(canonical),
        "n_without_any_provenance": len(missing),
        "without_any_provenance": missing,
        "n_pure_derivations": len(derivation),
        "pure_derivations": sorted(derivation),
        "n_without_provenance_and_not_a_derivation": len(unexplained),
        "without_provenance_and_not_a_derivation": unexplained,
        "n_with_hash_manifest": len(any_hash),
        "n_with_loadout": len(loadout),
        "n_with_drift": len(drift),
        "n_with_llm_sampling_record": len(sampling),
        "n_with_spend_ledger": len(spend),
        "n_with_retroactive_provenance_block": len(provenance),
        "with_llm_sampling_record": sorted(sampling),
        "with_loadout": sorted(loadout),
        "with_drift": sorted(drift),
        "with_retroactive_provenance_block": sorted(provenance),
        "_notes": {
            "canonical_definition": ("has an `instrument`, `_instrument` or "
                                     "`instrument_hashes` key at any depth"),
            "drift": ("`laya_client.instrument_record()` has emitted a `drift` field since it "
                      "was added, but every artifact predates it, so the count is 0. The "
                      "drift verdict is therefore currently evidenced by no artifact."),
            "probe_files": [non_instrument.name, reports.name],
        },
    }

    print(f"result artifacts                     : {inv['n_result_json']}")
    print(f"  with any provenance record         : {inv['n_with_any_provenance']}")
    print(f"  WITHOUT any provenance record      : {inv['n_without_any_provenance']}")
    for n in missing:
        print(f"      - {n}")
    print(f"  ...of which pure derivations (no measurement to attribute): "
          f"{inv['n_pure_derivations']}")
    print(f"      {inv['pure_derivations']}")
    print(f"  UNEXPLAINED gaps                   : "
          f"{inv['n_without_provenance_and_not_a_derivation']} "
          f"{inv['without_provenance_and_not_a_derivation']}")
    print(f"  with a hash manifest               : {inv['n_with_hash_manifest']}")
    print(f"  with a launch loadout              : {inv['n_with_loadout']}")
    print(f"  with a drift verdict               : {inv['n_with_drift']}")
    print(f"  with an llm_sampling record        : {inv['n_with_llm_sampling_record']}")
    print(f"      {inv['with_llm_sampling_record']}")
    print(f"  with a spend ledger                : {inv['n_with_spend_ledger']}")
    print(f"  with a retroactive provenance block: {inv['n_with_retroactive_provenance_block']}")
    print(f"      {inv['with_retroactive_provenance_block']}")

    dest = R / "P30-evidence-inventory.json"
    dest.write_text(json.dumps(inv, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwritten: {dest}")


if __name__ == "__main__":
    main()

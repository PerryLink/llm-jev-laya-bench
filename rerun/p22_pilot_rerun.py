"""Re-measure the P22 PILOT draw (n=69) -- the recorded unpinned run of regime 3.

WHY THIS IS A SEPARATE SCRIPT
-----------------------------
`src/items/p22_chain_audit.py` writes to `results/P22-chain-audit.json` BY DEFAULT, but its
`run()` calls `build_items()` with the module defaults (`legacy_options=False`,
`legacy_simulate=False`) -- i.e. the FIXED 68-item battery, not the 69-item pilot.

So running the script as documented replaces the PILOT with the FIXED battery under the
pilot's filename. That is what happened during this re-measurement, and the pilot artifact
was restored byte-for-byte from `results/_superseded/P22-chain-audit.json.pre-rerun`.

The pilot item set IS still reconstructible: `build_items(legacy_options=True,
legacy_simulate=True)` is exactly what `p22f_repair_denominator.legacy_items()` uses. This
script rebuilds it, PROVES the reconstruction faithful against the published rows (same
item_id and same truth for all 69, the assertion p22f itself uses), and then re-measures it
through the module's own `run()` with `build_items` patched to return the legacy items.

Output goes to `rerun/`, never to `results/`, so the restored pilot artifact is not touched.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src" / "instrument"))
sys.path.insert(0, str(ROOT / "src" / "items"))

SPEC = importlib.util.spec_from_file_location(
    "p22_mod", str(ROOT / "src" / "items" / "p22_chain_audit.py"))

PUBLISHED = ROOT / "results" / "P22-chain-audit.json"
OUT = ROOT / "rerun" / "P22-chain-audit-PILOT-rerun.json"


def main() -> int:
    mod = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(mod)          # main() is guarded by __name__

    pub = json.loads(PUBLISHED.read_text(encoding="utf-8"))
    pub_rows = pub["rows"]

    # ---- STEP 1: rebuild the pilot item set and PROVE the reconstruction faithful -------
    legacy = mod.build_items(legacy_options=True, legacy_simulate=True)
    print(f"rebuilt legacy pilot battery: {len(legacy)} items; published artifact: "
          f"{len(pub_rows)} rows")
    if len(legacy) != len(pub_rows):
        print(f"  !! ITEM COUNT MISMATCH: {len(legacy)} vs {len(pub_rows)}")
    by_id = {it["item_id"]: it for it in legacy}
    bad = [r["item_id"] for r in pub_rows
           if r["item_id"] not in by_id or by_id[r["item_id"]]["truth"] != r["truth"]]
    print(f"  faithfulness: {len(pub_rows) - len(bad)}/{len(pub_rows)} published rows "
          f"match the reconstruction on (item_id, truth)")
    if bad:
        print(f"  MISMATCHED: {bad[:10]}")
        print("  the pilot item set is NOT reconstructible from current code -- stopping")
        return 2

    # ---- STEP 2: re-measure the pilot through the module's own run() ---------------------
    mod.build_items = lambda *a, **k: legacy          # noqa: E731  (the one intervention)
    out = mod.run(temperature=0.0, replication="pilot-rerun")
    payload = {"_note": ("re-measurement of the P22 PILOT battery (n=69). The pilot is the "
                         "RECORDED DRAW; results/P22-chain-audit.json holds the published "
                         "one and was restored byte-for-byte before this ran."),
               "published_artifact": "results/P22-chain-audit.json",
               "temperature": 0.0, "replication": "pilot-rerun",
               **out}
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---- STEP 3: compare against the recorded draw --------------------------------------
    print()
    print("=" * 78)
    print("PILOT: published recorded draw vs this re-measurement")
    print("=" * 78)
    bs, ns = pub["summary"], out["summary"]
    fields = ["n_items", "llm_overall_accuracy", "laya_overall_accuracy",
              "delta_catch", "kappa_agreement", "confusion",
              "llm_accuracy_by_k", "laya_accuracy_by_k",
              "llm_picked_ignore_superseded_rate_eligible",
              "laya_picked_ignore_superseded_rate_eligible"]
    for k in fields:
        same = "SAME" if bs.get(k) == ns.get(k) else "DIFF"
        print(f"  {same}  {k}")
        if same == "DIFF":
            print(f"        published={json.dumps(bs.get(k), ensure_ascii=False)[:220]}")
            print(f"        re-run   ={json.dumps(ns.get(k), ensure_ascii=False)[:220]}")
    print(f"\nwritten: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

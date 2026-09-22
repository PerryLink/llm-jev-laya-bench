"""P22b: the Laya arm is deterministic, so if it moved, the INPUT moved.

Three published draws and three re-run draws each give an IDENTICAL Laya accuracy profile
within their group, and the two groups differ. That is only possible if the battery or the
question changed between them. This locates the change, per item, from the artifacts'
own recorded rows.
"""
from __future__ import annotations

import json

pairs = [("P22b-fixed-r1", "rerun/baseline/P22b-fixed-r1.json", "results/P22b-fixed-r1.json"),
         ("P22-chain-audit pilot", "results/P22-chain-audit.json",
          "rerun/P22-chain-audit-PILOT-rerun.json")]

for label, bp, np_ in pairs:
    b = json.load(open(bp, encoding="utf-8"))
    n = json.load(open(np_, encoding="utf-8"))
    br = {r["item_id"]: r for r in b["rows"]}
    nr = {r["item_id"]: r for r in n["rows"]}
    common = sorted(set(br) & set(nr))
    print("=" * 78)
    print(f"{label}: published rows={len(br)}  re-run rows={len(nr)}  common={len(common)}")
    print(f"  only in published: {sorted(set(br) - set(nr))[:8]}")
    print(f"  only in re-run   : {sorted(set(nr) - set(br))[:8]}")

    truth_mismatch = [i for i in common if br[i].get("truth") != nr[i].get("truth")]
    tok_mismatch = [i for i in common
                    if br[i].get("state_tokens_laya") != nr[i].get("state_tokens_laya")]
    laya_mismatch = [i for i in common if br[i].get("laya_correct") != nr[i].get("laya_correct")]
    llm_mismatch = [i for i in common if br[i].get("llm_correct") != nr[i].get("llm_correct")]
    print(f"  truth differs on            : {len(truth_mismatch)}/{len(common)}")
    print(f"  state_tokens_laya differs on: {len(tok_mismatch)}/{len(common)}")
    print(f"  LAYA answer differs on      : {len(laya_mismatch)}/{len(common)}")
    print(f"  LLM answer differs on       : {len(llm_mismatch)}/{len(common)}")
    if tok_mismatch[:4]:
        for i in tok_mismatch[:4]:
            print(f"    {i}: state_tokens_laya {br[i].get('state_tokens_laya')} -> "
                  f"{nr[i].get('state_tokens_laya')}   truth {br[i].get('truth')} -> "
                  f"{nr[i].get('truth')}")
    published_profile = sorted({(r.get("k"), r.get("laya_correct")) for r in b["rows"]})
    print(f"  published laya correctness profile (k, correct) distinct = "
          f"{len(published_profile)}")

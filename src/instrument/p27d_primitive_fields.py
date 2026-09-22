# -*- coding: utf-8 -*-
"""P27d — which answer fields does the PROVIDER return, per primitive?

WHY: the first version of §6.4.1 generalised "the provider's answer object has only
{type, noul}" from a single `noul` call. A correction round tested all three primitives
and found `choice` and `score` additionally return `probabilities`, `confidence` and
(for score) `legend`. That is a real provider field, so the access-layer attribution had
to be narrowed. This probe is the artifact behind the corrected table.
"""

# Paths resolve through bench_env, which locates the repository root by walking
# up from this file and honours environment overrides (LAYA_ROOT, DSH_CREDENTIALS,
# ...). Run `python bench_env.py` to print what was resolved. The aliased imports
# keep this block independent of whatever this module imported above, so it can
# sit at any top-level position.
import sys as _sys
from pathlib import Path as _Path

_p = _Path(__file__).resolve()
while not (_p / "bench_env.py").exists():
    if _p.parent == _p:
        raise RuntimeError(f"bench_env.py not found above {__file__}")
    _p = _p.parent
ROOT = _p
_sys.path.insert(0, str(ROOT))
from bench_env import INSTRUMENT  # noqa: E402

import json, sys
from pathlib import Path

sys.path.insert(0, str(INSTRUMENT))
from jev_client import ask, cost_of, input_tokens_of, resolved_model  # noqa: E402


RESULTS = ROOT / "results"

STATE = ("Audit memo. Invoice INV-4471 is fraudulent. The forensic accountant confirmed "
         "the fraud and the vendor admitted it in writing. Invoice INV-9902 is entirely "
         "correct and no irregularities were identified.")

CASES = {
    "noul": {"q": {"type": "noul",
                   "instructions": "Is invoice INV-4471 fraudulent?",
                   "criteria": {"true": "asserts fraud", "false": "does not assert fraud"}}},
    "choice": {"q": {"type": "choice",
                     "instructions": "Which invoice is described as fraudulent?",
                     "criteria": {"o1": "INV-4471", "o2": "INV-9902"}}},
    "score": {"q": {"type": "score",
                    "instructions": "How strong is the evidence that INV-4471 is fraudulent?",
                    "criteria": ["none", "weak", "moderate", "strong"]}},
}

# fields the DSH plugin synthesizes on top of the provider body
PLUGIN_ONLY_CANDIDATES = ["band", "probability", "answer", "truncated", "stateChars",
                          "questionsChars", "redactions", "latencyMs", "warnings"]

out = {"_instrument": {"route": "direct HTTP POST /api/v1/systemone",
                       "model": "typesafe/jev-1.13",
                       "credential_value_stored": False},
       "_spend_usd": 0.0, "per_primitive": {}}

for name, q in CASES.items():
    r = ask(STATE, q)
    out["_spend_usd"] += cost_of(r) or 0.0
    ans = (r.get("answers") or {}).get("q") or {}
    out["per_primitive"][name] = {
        "requested_type": name,
        "returned_type": ans.get("type"),
        "type_echoed_correctly": ans.get("type") == name,
        "provider_top_level_keys": sorted(k for k in r if not k.startswith("_")),
        "provider_answer_keys": sorted(ans.keys()),
        "provider_answer_body": ans,
        "input_tokens": input_tokens_of(r),
        "cost_usd": cost_of(r),
        "resolved_model": resolved_model(r),
        "plugin_only_fields_present_in_provider_body": [
            f for f in PLUGIN_ONLY_CANDIDATES
            if f in ans or f in r or f in (r.get("usage") or {})],
    }

allkeys = set()
for v in out["per_primitive"].values():
    allkeys |= set(v["provider_answer_keys"])

out["union_of_provider_answer_keys"] = sorted(allkeys)
out["never_returned_by_provider"] = [
    f for f in PLUGIN_ONLY_CANDIDATES if f not in allkeys]
out["conclusion"] = (
    "The provider returns a DIFFERENT answer-key set per primitive, so a claim about "
    "'which fields are provider-reported' cannot be generalised from one primitive. "
    "Fields never returned by the provider under any primitive tested are therefore "
    "access-layer synthesis; `confidence` and `probabilities` (plural) ARE provider "
    "fields and must not be listed as self-reports.")
out["primitive_coverage_caveat"] = (
    "3 primitives x 1 call each. This establishes WHICH KEYS appear, not their "
    "distributions; and `check`/`rank` were not exercised here.")
out["_spend_usd"] = round(out["_spend_usd"], 9)

p = RESULTS / "P27d-primitive-fields.json"
p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
for name, v in out["per_primitive"].items():
    print("%-7s type_ok=%-5s keys=%s" % (name, v["type_echoed_correctly"],
                                         v["provider_answer_keys"]))
print("union         :", out["union_of_provider_answer_keys"])
print("never returned:", out["never_returned_by_provider"])
print("spend: $%.6f" % out["_spend_usd"])
print("written:", p)

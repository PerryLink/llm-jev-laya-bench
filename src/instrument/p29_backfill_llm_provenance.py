"""Attach a RETROACTIVE provenance block to the three artifacts that carry none.

THE PROBLEM
-----------
`P14-llm-arm-full.json`, `P14-llm-arm-probe.json` and `P21-thinking-mode-cost.json` contain
no provenance at all: the scripts that produce them (`p14_llm_arm.py`,
`p21_thinking_mode_cost.py`) never import or call `instrument_record()` -- the token
"instrument" does not occur in either file -- and no script produces `P14-llm-arm-probe.json`
at all.

TWO WRONG FIXES, BOTH REJECTED
------------------------------
1. RE-RUNNING is unsafe as a provenance patch. Both scripts call `chat()` with NO
   `temperature`, and `deepseek_client.py` only sets the field when one is passed, so the
   API's default sampling applied. Re-running would move published numbers (the paper cites
   LLM 1.0000 at n=48 and 0.958 for the prose arm) in order to fix a metadata gap. ERRATA §5
   documents exactly this failure mode for P22: two re-runs under default sampling agreed
   with the recording on only 58.8% of items.
2. BACKFILLING a Laya `instrument_record()` would be a CATEGORY ERROR: these arms never call
   the Laya sidecar. They call DeepSeek. Writing a Laya hash manifest into them would
   fabricate provenance for an instrument that did not participate -- and a hash computed
   today is an honest record of the snapshot as it exists NOW, not of what ran THEN.

WHAT THIS DOES INSTEAD
----------------------
Writes a block that states only what is independently knowable, and labels itself as
retroactive. No measured number is touched. The block records: the route and model, the
sampling caveat, the exact spend, the artefacts the arm consumes or produces, and -- for
the probe -- that it is superseded and has no producing script.

Also closes a real gap noted by the audit: `deepseek_client.py` is hashed NOWHERE in the
project, so the LLM arm's own instrument is unpinned. The block records its hash, which is
what a future run should pin.
"""

from __future__ import annotations

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


import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


R = ROOT / "results"
CLIENT = ROOT / "src" / "instrument" / "deepseek_client.py"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


BLOCKS = {
    "P14-llm-arm-full.json": {
        "producing_script": "src/items/p14_llm_arm.py",
        "calls_made": 96,
        "calls_note": "48 items x 2 arms (forced choice + prose), p14_llm_arm.py:89-90 and :98-99",
        "recorded_off_peak_spend_usd": 0.00531221,
        "spend_breakdown": {"prose_arm": 0.00299130, "forced_choice_arm": 0.00232091},
        "per_call_usd_range": [0.00003263, 0.00009645],
        "consumes": ["results/P9b-template-validation-separated-n48.json"],
        "published_figures_at_risk": [
            "LLM 1.0000 (n=48) -- authority location",
            "prose arm 0.958",
        ],
    },
    "P14-llm-arm-probe.json": {
        "producing_script": None,
        "calls_made": 24,
        "recorded_off_peak_spend_usd": None,
        "superseded": True,
        "superseded_by": "P14-llm-arm-full.json",
        "note": ("No script in the repository produces this file (grep 'llm-arm-probe' over "
                 "*.py returns nothing). ERRATA §3 already declares it superseded: it "
                 "recorded 5/12 parse failures as wrong answers."),
        "published_figures_at_risk": [],
    },
    "P21-thinking-mode-cost.json": {
        "producing_script": "src/items/p21_thinking_mode_cost.py",
        "calls_made": 24,
        "calls_note": "4 reasoning efforts x 6 items, p21_thinking_mode_cost.py:56 and :70-71",
        "recorded_off_peak_spend_usd": 0.00183090,
        "spend_by_effort": {"none": 0.00023895, "low": 0.00046785,
                            "high": 0.00051825, "max": 0.00060585},
        "max_peak_cost_per_call_usd": 0.00025980,
        "published_figures_at_risk": ["thinking-mode cost multiples (up to 2.54x)"],
    },
}


def main() -> None:
    client_hash = sha256_file(CLIENT)
    now = datetime.now(timezone.utc).isoformat()
    print(f"deepseek_client.py sha256 = {client_hash}")

    for name, blk in BLOCKS.items():
        path = R / name
        doc = json.loads(path.read_text(encoding="utf-8"))
        if "_provenance" in doc:
            print(f"  {name}: already has a _provenance block -- skipping")
            continue

        doc["_provenance"] = {
            "status": "RETROACTIVE -- added by src/instrument/p29_backfill_llm_provenance.py",
            "added_at_utc": now,
            "no_runtime_record_was_captured": True,
            "why": ("This arm's script never called instrument_record(), so no contemporaneous "
                    "instrument record exists. This block was reconstructed from the script "
                    "and the artifact after the fact. IT IS NOT A CONTEMPORANEOUS RECORD."),
            "laya_sidecar_participated": False,
            "laya_instrument_record_would_be_a_category_error": (
                "this arm calls DeepSeek, not the Laya sidecar; a Laya hash manifest here "
                "would describe an instrument that did not participate"),
            "measured_instrument": {
                "route": "DeepSeek official API",
                "client": "src/instrument/deepseek_client.py",
                "client_sha256": client_hash,
                "model_id": "deepseek-flash (DeepSeek-V4.1-Flash)",
                "client_hashed_elsewhere_in_the_project": False,
                "client_hash_note": ("recorded here because deepseek_client.py is pinned by "
                                     "no other artifact -- that unpinned client is why "
                                     "P14-llm-arm-probe went stale (ERRATA §3)"),
            },
            "sampling": {
                "temperature": None,
                "temperature_semantics": ("`chat()` sets `temperature` only when one is "
                                          "explicitly passed AND effort=='none' "
                                          "(deepseek_client.py:154-155), so the API default "
                                          "sampling applied"),
                "consequence": ("the arm is a SINGLE draw under default sampling; its point "
                                "estimates must not be read as precise. See ERRATA §5 for the "
                                "measured cost of this: 58.8% item-level label agreement "
                                "between an unpinned run and a pinned one on the same battery."),
            },
            **blk,
        }
        backup = path.with_suffix(".json.pre-provenance")
        if not backup.exists():
            shutil.copy2(path, backup)
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  {name}: provenance block added")

    print("\ndone -- no measured number was modified in any artifact")


if __name__ == "__main__":
    main()

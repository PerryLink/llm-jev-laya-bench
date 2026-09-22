"""Restore a provenance block on the re-measured LLM arms -- derived, not hardcoded.

WHY THIS EXISTS
---------------
`src/instrument/p29_backfill_llm_provenance.py` added a retroactive `_provenance` block to
P14-llm-arm-full.json, P14-llm-arm-probe.json and P21-thinking-mode-cost.json, because
those arms call DeepSeek and never called `instrument_record()` (ERRATA 9).

Re-running the GENERATOR destroys that block, because the generator cannot produce it:
it is not output, it is a later repair layer. After the re-measurement, P21 had top-level
keys `['rows','summary']` -- i.e. no provenance of any kind, which is exactly the defect
ERRATA 9 existed to fix. P14 is in the same position.

WHY NOT JUST RE-RUN p29
-----------------------
p29's spend figures are HARDCODED against the original campaign (P21: $0.00183090). The
re-run measured $0.00189870, so re-running p29 unmodified would write a stale number into a
freshly measured artifact. Everything here is therefore DERIVED from the artifact it
describes.

The original block is not lost: it survives in
`results/_superseded/<name>.pre-rerun`, and this block points at it.

Idempotent: an artifact that already carries `_provenance` is skipped. Writes no credential
value (only a boolean saying none is stored).
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bench_env import RESULTS  # noqa: E402

CLIENT = ROOT / "src" / "instrument" / "deepseek_client.py"
SUP = RESULTS / "_superseded"

#: every per-call cost field used anywhere in this project's LLM artifacts
COST_KEYS = ("off_peak_usd", "llm_cost_usd", "llm_cost", "cost_usd", "costUsd",
             "cost_off", "cost_usd_mean", "mean_cost_usd")

#: which script produced each arm, and which figure the paper takes from it
ARMS = {
    "P14-llm-arm-full.json": {
        "producing_script": "src/items/p14_llm_arm.py",
        "consumes": ["results/P9b-template-validation-separated-n48.json"],
        "published_figures": [
            "LLM 1.0000 (n=48) -- authority location",
            "prose arm 0.958",
            "prose-arm delta_catch (ERRATA 10.1 item 3)",
        ],
    },
    "P21-thinking-mode-cost.json": {
        "producing_script": "src/items/p21_thinking_mode_cost.py",
        "consumes": [],
        "published_figures": ["thinking-mode cost multiples (up to 2.54x)"],
    },
}


def costs(node) -> list[float]:
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k in COST_KEYS and isinstance(v, (int, float)):
                out.append(float(v))
            else:
                out += costs(v)
    elif isinstance(node, list):
        for v in node:
            out += costs(v)
    return out


def main() -> int:
    client_hash = hashlib.sha256(CLIENT.read_bytes()).hexdigest().upper()
    now = datetime.now(timezone.utc).isoformat()
    changed = 0
    for name, meta in ARMS.items():
        p = RESULTS / name
        doc = json.loads(p.read_text(encoding="utf-8"))
        if "_provenance" in doc:
            print(f"  {name}: already has _provenance -- skipped")
            continue
        c = costs(doc)
        doc["_provenance"] = {
            "status": ("RETROACTIVE -- added by rerun/restore_llm_provenance.py after the "
                       "re-measurement. IT IS NOT A CONTEMPORANEOUS RECORD."),
            "added_at_utc": now,
            "measured_at_utc_approx": datetime.fromtimestamp(
                p.stat().st_mtime, timezone.utc).isoformat(),
            "no_runtime_record_was_captured": True,
            "why": ("This arm's script never calls instrument_record(): it calls DeepSeek, "
                    "not the Laya sidecar. A Laya hash manifest here would describe an "
                    "instrument that did not participate. The block states only what is "
                    "independently knowable, and every number in it is derived from this "
                    "artifact's own per-call rows rather than hardcoded."),
            "laya_sidecar_participated": False,
            "producing_script": meta["producing_script"],
            "consumes": meta["consumes"],
            "measured_instrument": {
                "route": "DeepSeek official API",
                "client": "src/instrument/deepseek_client.py",
                "client_sha256": client_hash,
                "model_id": "deepseek-flash (DeepSeek-V4.1-Flash)",
                "client_hashed_elsewhere_in_the_project": False,
                "client_hash_note": ("deepseek_client.py is pinned by no artifact other than "
                                     "this block -- the project can pin its judge and cannot "
                                     "pin its generator"),
            },
            "derived_from_this_artifact": {
                "calls_with_a_cost_row": len(c),
                "off_peak_spend_usd": round(sum(c), 9),
                "per_call_usd_range": [round(min(c), 9), round(max(c), 9)] if c else None,
            },
            "sampling_caveat": (
                "the arm is a single draw and was NOT run at a pinned temperature "
                "(deepseek_client.py sets `temperature` only when one is passed), so the "
                "published figures are one sample, not a repeatable measurement"),
            "published_figures_at_risk": meta["published_figures"],
            "previous_provenance_block": (
                f"results/_superseded/{name}.pre-rerun holds the artifact as published, "
                "including the original p29 backfill block. Its spend figures describe the "
                "ORIGINAL campaign and must not be read as this artifact's."),
            "credential_value_stored": False,
        }
        p.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  {name}: _provenance restored  calls={len(c)} "
              f"spend=${sum(c):.9f} range=$[{min(c):.9f},{max(c):.9f}]" if c else
              f"  {name}: _provenance restored (no cost rows found)")
        changed += 1
    print(f"{changed} artifact(s) updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())

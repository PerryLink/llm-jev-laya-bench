# -*- coding: utf-8 -*-
"""P27e — derive `P27-summary.json` from the P27 family.

AUDIT FIX (round 5): `P27-summary.json` previously existed in `results/` with no
generator script and no `_instrument` block, yet the paper's manifest listed it as a
reproducible artifact. It is now produced by this script, from the artifacts, with
provenance, so the claim is true.
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


import json
import statistics
import sys
from pathlib import Path


sys.path.insert(0, str(ROOT / "src" / "instrument"))
from jev_client import instrument_record  # noqa: E402

R = ROOT / "results"


def load(n):
    return json.loads((R / n).read_text(encoding="utf-8"))


p27 = load("P27-jev-live.json")
p27c = load("P27c-jev-latency-sweep.json")
p27b = load("P27b-plugin-crossval.json")
p27d = load("P27d-primitive-fields.json")

wall = p27["latency"]["all_ms"] + [x for row in p27c["by_size"]
                                   for x in row["latency_ms_wall"]["all"]]
ladder_costs = [r["cost_usd"] for r in p27["state_window"]["ladder"] if "cost_usd" in r]
sweep_costs = [row["cost_usd_mean"] for row in p27c["by_size"] if row["cost_usd_mean"]]
all_costs = ladder_costs + sweep_costs

# AUDIT FIX (round 5): the P27b plugin battery's 7 calls were charged to the account but
# omitted from this sum, while `_sources` below lists the file -- so the summary cited a
# source it did not actually count. P27b stores them per row and has no `_spend_usd`.
p27b_costs = [r["costUsd"] for r in p27b["raw_plugin_rows"] if r.get("costUsd") is not None]
spend_parts = {
    "P27-jev-live.json": p27["_spend_usd"],
    "P27b-plugin-crossval.json": round(sum(p27b_costs), 9),
    "P27c-jev-latency-sweep.json": p27c["_spend_usd"],
    "P27d-primitive-fields.json": p27d["_spend_usd"],
}

# design-range cost: the paper's D2 design states are 300-1,500 tokens
design = [row["cost_usd_mean"] for row in p27c["by_size"]
          if row["input_tokens_median"] and row["input_tokens_median"] <= 1500]

out = {
    "_instrument": instrument_record("derived from the P27 family; no new API calls made"),
    "_generated_by": "src/instrument/p27e_summary.py",
    "_sources": ["P27-jev-live.json", "P27b-plugin-crossval.json",
                 "P27c-jev-latency-sweep.json", "P27d-primitive-fields.json"],
    "latency_wall_ms_combined": {
        "n": len(wall), "p50": round(statistics.median(wall), 1),
        "mean": round(statistics.fmean(wall), 1), "min": min(wall), "max": max(wall),
        "sources": "P27 latency run (n=20) + P27c sweep (n=15)",
        "measurement_point": "wall clock, independent of any self-report",
    },
    "comparison_points": {
        "laya_ms_p50": 37.4, "llm_ms_p50": 671,
        "ratio_jev_over_laya": round(statistics.median(wall) / 37.4, 1),
        "ratio_llm_over_laya": round(671 / 37.4, 1),
        "ratio_jev_over_llm": round(statistics.median(wall) / 671, 1),
        "caveat": ("all three rungs are CLIENT wall clock around the HTTP call, not provider "
                   "self-report (Laya local socket, LLM perf_counter in deepseek_client.py, "
                   "Jev perf_counter in jev_client.py), but they still have different state "
                   "sizes and different transports; the ratio is a ladder, not a "
                   "like-for-like comparison"),
    },
    "selfreport_vs_wall": {
        "plugin_latencyMs_p50": p27b["latency_self_report_vs_wall_clock"]["plugin_latencyMs"]["p50"],
        "matched_direct_p50": p27b["latency_self_report_vs_wall_clock"]["matched_direct_wall_ms"]["p50"],
        "ratio_matched": p27b["latency_self_report_vs_wall_clock"]["ratio_of_medians_matched"],
        "ratio_unmatched_old_figure": p27b["latency_self_report_vs_wall_clock"]["ratio_of_medians_unmatched"],
        "status": "FLAG, not a finding (unpaired bursts; the 403 control overlaps)",
    },
    "cost_usd": {
        "n_size_steps": len(all_costs),
        "min": min(all_costs), "max": max(all_costs),
        "design_range_max": max(design) if design else None,
        "per_120_checkpoints_at_max": round(max(all_costs) * 120, 6),
        "per_120_checkpoints_design_range": round(max(design) * 120, 6) if design else None,
        "note": ("the ceiling over the states actually run; the earlier published "
                 "ceiling of 0.0001048 covered only the P27c sweep and understated the "
                 "39,927-character ladder point by ~2.3x"),
    },
    "state_window": {
        "max_state_accepted_chars": p27["state_window"]["max_accepted_chars"],
        "evidence": ("input tokens grow monotonically with characters (~12 tok per 111 "
                     "chars), so no fixed character cap applies; the probe does NOT test "
                     "for silent tail truncation"),
        "provider_cap_found": False,
    },
    "truth_battery": "%d/%d" % (p27["truth_battery"]["correct"], p27["truth_battery"]["n"]),
    "criteria_moved": p27["criteria_sensitivity"]["moved"],
    "provider_answer_keys_by_primitive": {
        k: v["provider_answer_keys"] for k, v in p27d["per_primitive"].items()},
    "never_returned_by_provider": p27d["never_returned_by_provider"],
    "spend_usd": round(sum(spend_parts.values()), 9),
    "spend_usd_by_artifact": spend_parts,
    "spend_usd_note": (
        "Summed over ALL FOUR sources listed in `_sources`. Earlier versions of this summary "
        "omitted P27b-plugin-crossval.json -- 7 charged calls, $0.000102018 -- while still "
        "listing it as a source. P27-jev-live.json's own `_spend_usd` also exceeds the sum of "
        "its persisted cost rows by exactly one call ($0.000014280, the provider-field "
        "inventory call), so a total recomputed from rows alone understates by that amount; "
        "the figure here counts CALLS, not rows."),
}

(R / "P27-summary.json").write_text(json.dumps(out, indent=2, ensure_ascii=False),
                                    encoding="utf-8")
print("latency n=%d p50=%.1f  ratio vs Laya=%.1fx"
      % (out["latency_wall_ms_combined"]["n"], out["latency_wall_ms_combined"]["p50"],
         out["comparison_points"]["ratio_jev_over_laya"]))
print("cost range $%.8f - $%.8f  (design-range max $%.8f)"
      % (out["cost_usd"]["min"], out["cost_usd"]["max"], out["cost_usd"]["design_range_max"]))
print("per-120 at max: $%.6f | design range: $%.6f"
      % (out["cost_usd"]["per_120_checkpoints_at_max"],
         out["cost_usd"]["per_120_checkpoints_design_range"]))
print("selfreport ratio (matched) = %.2fx" % out["selfreport_vs_wall"]["ratio_matched"])
print("written:", R / "P27-summary.json")

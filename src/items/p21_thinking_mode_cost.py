"""Thinking-mode cost: the one unmeasured variable in "cost is not the binding constraint".

WHY THIS MATTERS, AND WHY IT IS THE LAST ONE
--------------------------------------------
Every LLM cost figure in this project was taken with `thinking: disabled`. That was not
an arbitrary choice: the API documentation states that `temperature` has no effect in
thinking mode, so a k-sample self-consistency arm CANNOT be run there and must run
non-thinking. But thinking is the DEFAULT effort level (`high`), and V3 measured that
reasoning tokens are billed as output while being invisible in the message content, and
that `outputTokens` demonstrably includes them.

So the project has been reporting the cost of a configuration it deliberately disabled.
If thinking mode costs an order of magnitude more, the claim "money is not the constraint"
would rest on a setting most deployments would not actually use. This measures it.

WHAT IS MEASURED
  For each reasoning_effort in {none, low, high, max}, on the SAME items:
    * completion_tokens and, where reported, completion_tokens_details.reasoning_tokens
    * cost computed from the provider's own token accounting, in both price regimes
    * accuracy, so a cost increase can be read against any quality change
    * latency, which under thinking is expected to grow far more than cost

PRE-DECLARED READING
  If the max-effort cost stays within ~2 orders of magnitude of non-thinking on this
  workload, the thesis holds as stated and the configuration is a footnote. If it is
  materially larger, the thesis must be restated as conditional on effort, with the
  numbers for each level given.

NOTE ON PRICE: off-peak and peak are both reported. R2 verified peak is exactly 2x
off-peak on every line, so publishing only one would be a choice the reader cannot audit.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(r"D:\Projects\llm-jev-laya-bench")
sys.path.insert(0, str(ROOT / "src" / "instrument"))
sys.path.insert(0, str(ROOT / "src" / "items"))
from deepseek_client import chat, parse_label, parse_prob, prompt_forced_choice  # noqa: E402

RESULTS = ROOT / "results"

ITEMS = [
    ("pallets shipped in Q3", "units", 4182, 9700),
    ("authentication outage duration", "minutes", 47, 240),
    ("invoice INV-4471 amount", "USD", 18400, 14800),
    ("late deliveries in March", "parcels", 312, 521),
    ("warranty battery replacements", "cells", 918, 1200),
    ("median ticket resolution time", "hours", 26, 62),
]

EFFORTS = ["none", "low", "high", "max"]


def item_state(label: str, unit: str, v: int, w: int) -> tuple[str, dict, dict, str]:
    state = (f"Ledger extract. Successive revisions may appear; the line marked (current) "
             f"is authoritative.\n{label} = {v} {unit} (current)\n{label} = {w} {unit}")
    crit = {"true": f"the state records {v} {unit} as the current {label}",
            "false": f"the state does not record {v} {unit} as the current {label}"}
    q = f"Does the state record {v} {unit} as the current {label}?"
    return state, crit, {"label": label}, q


def run() -> dict:
    rows: list[dict] = []
    for effort in EFFORTS:
        for label, unit, v, w in ITEMS:
            state, crit, _, q = item_state(label, unit, v, w)
            try:
                r = chat(prompt_forced_choice(state, q, crit), effort=effort,
                         json_mode=True, max_tokens=2048)
                lab = parse_label(r, crit)
                conf = parse_prob(r)
                pred = None if lab is None else (lab == "true")
                usage = r.usage or {}
                det = usage.get("completion_tokens_details") or {}
                rows.append({
                    "effort": effort, "label": label,
                    "correct": (pred is True),
                    "label_chosen": lab, "conf": conf,
                    "completion_tokens": usage.get("completion_tokens"),
                    "reasoning_tokens": det.get("reasoning_tokens"),
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "cache_hit": usage.get("prompt_cache_hit_tokens"),
                    "cost_off": r.cost.get("off_peak_usd"),
                    "cost_peak": r.cost.get("peak_usd"),
                    "latency_ms": round(r.latency_ms, 1),
                    "finish": r.finish_reason,
                    "reasoning_present": bool(r.reasoning),
                    "error": r.error,
                })
            except Exception as exc:
                rows.append({"effort": effort, "label": label, "error": str(exc)[:200]})
            r0 = rows[-1]
            print(f"{effort:<5} {label[:28]:<30} ok={r0.get('correct')} "
                  f"out={r0.get('completion_tokens')} reason={r0.get('reasoning_tokens')} "
                  f"${r0.get('cost_off')} {r0.get('latency_ms')}ms")

    by: dict = {}
    for e in EFFORTS:
        # The success path records `error: None`, so the filter must test FALSINESS.
        # Testing `"error" not in r` dropped every row and produced an empty summary --
        # a silent aggregation failure that still printed a plausible "NO DATA" verdict.
        sub = [r for r in rows if r["effort"] == e and not r.get("error")]
        if not sub:
            continue
        costs = [r["cost_off"] for r in sub if r.get("cost_off") is not None]
        lats = [r["latency_ms"] for r in sub if r.get("latency_ms")]
        outs = [r["completion_tokens"] for r in sub if r.get("completion_tokens")]
        reas = [r["reasoning_tokens"] for r in sub if r.get("reasoning_tokens") is not None]
        by[e] = {
            "n": len(sub),
            "accuracy": round(sum(1 for r in sub if r["correct"]) / len(sub), 4),
            "mean_completion_tokens": round(statistics.fmean(outs), 1) if outs else None,
            "mean_reasoning_tokens": round(statistics.fmean(reas), 1) if reas else None,
            "mean_cost_usd_offpeak": round(statistics.fmean(costs), 8) if costs else None,
            "mean_cost_usd_peak": round(
                statistics.fmean([r["cost_peak"] for r in sub
                                  if r.get("cost_peak") is not None]), 8),
            "p50_latency_ms": statistics.median(lats) if lats else None,
            "max_latency_ms": max(lats) if lats else None,
            "reasoning_field_present": any(r.get("reasoning_present") for r in sub),
        }

    base = (by.get("none") or {}).get("mean_cost_usd_offpeak")
    summary = {
        "by_effort": by,
        "cost_ratio_vs_non_thinking": {
            e: (round(v["mean_cost_usd_offpeak"] / base, 3)
                if (base and v.get("mean_cost_usd_offpeak")) else None)
            for e, v in by.items()},
        "verdict": None,
        "caveat": ("6 items per effort level, single sample. Descriptive of the cost "
                   "structure; not an accuracy estimate."),
    }
    ratios = [v for v in summary["cost_ratio_vs_non_thinking"].values() if v]
    worst = max(ratios) if ratios else None
    if worst is None:
        summary["verdict"] = "NO DATA"
    elif worst <= 100:
        summary["verdict"] = (
            f"THESIS HOLDS AS STATED: the most expensive effort level costs {worst}x the "
            f"non-thinking configuration, still within two orders of magnitude, so the "
            f"effort setting is a reported footnote rather than a qualifier on the claim")
    else:
        summary["verdict"] = (
            f"THESIS MUST BE QUALIFIED: effort costs up to {worst}x non-thinking, so "
            f"'money is not the constraint' holds only for the non-thinking configuration "
            f"and must be restated with the per-effort numbers")
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run()
    p = RESULTS / "P21-thinking-mode-cost.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== BY EFFORT ===")
    print(json.dumps(out["summary"]["by_effort"], indent=2))
    print("\n=== COST RATIOS vs non-thinking ===")
    print(json.dumps(out["summary"]["cost_ratio_vs_non_thinking"], indent=2))
    print("\n=== VERDICT ===")
    print(out["summary"]["verdict"])
    print(f"written: {p}")

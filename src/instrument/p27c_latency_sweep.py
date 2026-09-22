# -*- coding: utf-8 -*-
"""P27c — Jev latency as a function of state size, measured by wall clock.

WHY: the paper's latency ladder compares Laya's wall clock, the LLM's provider
self-report, and Jev's PLUGIN self-report. P27b showed the plugin's `latencyMs` runs
~2.02x the independently measured wall clock for the SAME state, so the Jev rung of that
ladder was inflated relative to the others. This probe re-measures Jev latency
independently and across state sizes, so the paper can quote a figure whose measurement
point is stated rather than assumed.
"""
from __future__ import annotations

import json, statistics, sys
from pathlib import Path

ROOT = Path(r"D:\Projects\llm-jev-laya-bench")
sys.path.insert(0, str(ROOT / "src" / "instrument"))
from jev_client import ask, cost_of, input_tokens_of, noul_of, instrument_record, JevError  # noqa: E402

RESULTS = ROOT / "results"
REPS = 5

BASE = ("Audit memo. Invoice INV-4471 is fraudulent. The forensic accountant confirmed "
        "the fraud and the vendor admitted it in writing.")
FILLER = ("Quarterly logistics review. The warehouse processed routine shipments and "
          "filed standard compliance paperwork. ")
Q = {"q": {"type": "noul", "instructions": "Is invoice INV-4471 fraudulent?",
           "criteria": {"true": "the state asserts that invoice INV-4471 is fraudulent",
                        "false": "the state does not assert that invoice INV-4471 is fraudulent"},
           "boundary": {"true": "the state asserts that invoice INV-4471 is fraudulent",
                        "false": "the state does not assert that invoice INV-4471 is fraudulent"}}}

TARGET_CHARS = [len(BASE), 8_000, 16_000]


def main() -> int:
    out = {"_instrument": instrument_record(
        "direct HTTP route; latency is wall clock measured by this client, NOT the "
        "plugin's self-reported latencyMs (which runs ~2x this, see P27b)"),
        "_spend_usd": 0.0, "reps_per_size": REPS, "by_size": []}

    for chars in TARGET_CHARS:
        pad = max(0, chars - len(BASE))
        state = BASE + FILLER * (pad // len(FILLER))
        lat, toks, nouls, costs, errs = [], [], [], [], 0
        attempts: list[int] = []
        for _ in range(REPS):
            try:
                r = ask(state, Q)
                lat.append(r["_latency_ms_wall"])
                toks.append(input_tokens_of(r))
                nouls.append(noul_of(r))
                # AUDIT FIX (round 5): the sweep discarded `_attempts`, so it could neither
                # exclude nor quantify the retry bias that P27 documents -- a
                # timeout-then-success call contributes only its SHORT final leg to the
                # distribution, biasing it short. Now recorded per rep and summarised below.
                attempts.append(r.get("_attempts") or 1)
                c = cost_of(r) or 0.0
                costs.append(c)
                out["_spend_usd"] += c
            except JevError as exc:
                errs += 1
                print("  error:", str(exc)[:90])
        row = {
            "state_chars": len(state),
            "input_tokens_median": statistics.median(toks) if toks else None,
            "n_ok": len(lat), "n_errors": errs,
            "latency_ms_wall": {
                "p50": round(statistics.median(lat), 1) if lat else None,
                "mean": round(statistics.fmean(lat), 1) if lat else None,
                "min": min(lat) if lat else None,
                "max": max(lat) if lat else None,
                "all": lat,
            },
            "cost_usd_mean": round(statistics.fmean(costs), 9) if costs else None,
            "distinct_noul": sorted({n for n in nouls if n is not None}),
            "attempts": {
                "n_recorded": len(attempts),
                "max": max(attempts) if attempts else None,
                "n_calls_needing_a_retry": sum(1 for a in attempts if a > 1),
                "note": ("only the FINAL attempt's elapsed time is recorded as the call's "
                         "latency, so a retried call enters the distribution as its short "
                         "final leg -- the distribution is biased SHORT, not long"),
            },
        }
        out["by_size"].append(row)
        print("  %6d chars / %5s tok : p50=%7.0f ms  min=%5.0f max=%5.0f  cost=%.8f"
              % (row["state_chars"], row["input_tokens_median"],
                 row["latency_ms_wall"]["p50"] or -1,
                 row["latency_ms_wall"]["min"] or -1,
                 row["latency_ms_wall"]["max"] or -1,
                 row["cost_usd_mean"] or 0))

    lat_all = [x for row in out["by_size"] for x in row["latency_ms_wall"]["all"]]
    out["pooled"] = {
        "n": len(lat_all),
        "p50": round(statistics.median(lat_all), 1) if lat_all else None,
        "mean": round(statistics.fmean(lat_all), 1) if lat_all else None,
        "min": min(lat_all) if lat_all else None,
        "max": max(lat_all) if lat_all else None,
    }
    out["_spend_usd"] = round(out["_spend_usd"], 9)
    p = RESULTS / "P27c-jev-latency-sweep.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\npooled n=%d p50=%.0f ms  spend=$%.6f" %
          (out["pooled"]["n"], out["pooled"]["p50"] or -1, out["_spend_usd"]))
    print("written:", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
